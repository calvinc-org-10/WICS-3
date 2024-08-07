import datetime
from datetime import MINYEAR
from operator import attrgetter
from django import forms, urls
from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Value, Sum
from django.db.models import F, Value, Subquery, OuterRef
from django.db.models.query import QuerySet
from django.forms import inlineformset_factory, formset_factory, modelformset_factory
from django.http import HttpRequest, HttpResponseRedirect #, HttpResponse
from django.shortcuts import render
from django.views.generic import ListView
from cMenu.models import getcParm
from cMenu.utils import modelobj_to_dict, calvindate, ExcelWorkbook_fileext, Excelfile_fromqs
from cMenu.views import user_db
from mathematical_expressions_parser.eval import evaluate
from WICS.globals import _defaultOrg
from WICS.forms import MaterialForm, MaterialCountSummary, MfrPNtoMaterialForm, PartTypesForm
from WICS.models import MaterialList, MaterialPhotos, VIEW_materials, WhsePartTypes, MfrPNtoMaterial
from WICS.models import CountSchedule, ActualCounts, FoundAt
from WICS.models import SAP_SOHRecs, UnitsOfMeasure #, VIEW_SAP
from WICS.procs_SAP import fnSAPList
from typing import Any, Dict


class MaterialLocationsList(LoginRequiredMixin, ListView):
    # ordering = ['org_id','Material']  - ordering should not be defined on a raw queryset
    context_object_name = 'MatlList'
    template_name = 'rpt_PartLocations.html'
    SAPSums = {}

    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self._user = req.user
        qs = VIEW_materials.objects.using(user_db(req)).all().annotate(
                        SAPList=Value(0),
                        DoNotShow=Value(False),
                    )

        # it's more efficient to pull this all now and store it for the upcoming qs request
        SAP = fnSAPList(req)   
        self.SAPDate = SAP['SAPDate']
        self.SAPTable = SAP['SAPTable']

        self.queryset = qs
        return super().setup(req, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()
        for rec in qs:
            #pass in Material record
            rec.SAPList = self.SAPTable.filter(Material_id=rec.pk)
            # filter Material in SAP_SOH for date OR last count date within 30d
            testdate = rec.LastCountDate
            if testdate == None: testdate = calvindate(MINYEAR, 1, 1)
            rec.DoNotShow = (not rec.SAPList.exists()) and (testdate < calvindate().today()-int(getcParm(self._user, 'LOCRPT-COUNTDAYS-IFNOSAP')))

        return qs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        cntext = super().get_context_data(**kwargs)
        cntext.update({
            'SAPDate': self.SAPDate,
            'showSAP': False,
            })
        return cntext


@login_required
def fnMaterialForm(req, recNum = -1, gotoRec=False, newRec=False, HistoryCutoffDate=None):

    FormMain = MaterialForm

    modelMain = FormMain.Meta.model
    #TODO: make this a dictionary rather than an indexed list, more like prefixvals, initialvals, etc, below
    #      mebbe make the indices a list
    #      subFormIndices = ['main', 'counts', 'schedule', 'MfrPN',]
    modelSubs = [S for S in [ActualCounts, CountSchedule, MfrPNtoMaterial]]

    #TODO: make this a dictionary rather than an indexed list, more like prefixvals, initialvals, etc, below
    FormFieldsSubs = [
        # 0 = ActualCounts Subform
        ['id', 'CountDate', 'Counter', 'LocationOnly', 'CTD_QTY_Expr', 'LOCATION', 'FLAG_PossiblyNotRecieved', 'FLAG_MovementDuringCount', 'Notes',],
        # 1 = CountSchedule SubForm
        ['id','CountDate','Counter', 'Priority', 'ReasonScheduled', 'Notes',],
        # 2 = MfrPN SubForm
        ['id', 'MfrPN', 'Manufacturer', 'Notes',],
    ]

    # get current record
    currRec = None
    if req.method == 'POST':
        currRec = modelMain.objects.using(user_db(req)).filter(pk=req.POST['MatlPK']).first()
    else:
        if newRec:
            # provide new record
            currRec = modelMain(org_id=_defaultOrg)
        elif recNum <= 0:
            currRec = modelMain.objects.using(user_db(req)).first()
        else:
            try:
                currRec = modelMain.objects.using(user_db(req)).get(pk=recNum)
            except:
                pass    # currRec remains None
        # endif newRec, recNum
    #endif set currRec based on req.method

    thisPK = 0
    if not newRec and currRec:
        thisPK = currRec.pk

    prefixvals = {
        'main': 'material',
        'counts': 'countset',
        'schedule': 'schedset',
        'MfrPN': 'MPN',
        }
    initialvals = {
        'main': {'gotoItem': thisPK, 'showPK': thisPK, 'org':_defaultOrg},
        'counts': {},
        'schedule': {},
        'MfrPN': {},
        }

    changes_saved = {
        'main': False,
        'counts': False,
        'schedule': False,
        'MfrPN': False,
        }
    chgd_dat = {
        'main':None, 
        'counts': None, 
        'schedule': None,
        'MfrPN': None,
        }

    if newRec:
        SAP_SOH = fnSAPList(req, matl='-')
    else:
        SAP_SOH = fnSAPList(req, matl=currRec)

    gotoForm = {}
    gotoForm['choicelist'] = VIEW_materials.objects.using(user_db(req)).values('id','Material_org')
    gotoForm['gotoItem'] = currRec

    if req.method == 'POST':
        # changed data is being submitted.  process and save it
        # process mtlFm AND subforms.

        # is a Photo being attached?
        if req.POST['PhotoOp'] == "ADD":
            MaterialPhotos(
                Material = currRec,
                Photo = req.FILES["newPhoto"],
            ).save(using=user_db(req))

        # is a photo being removed?
        if req.POST['PhotoOp'][:3] == "DEL":
            photoID = req.POST['PhotoOp'][4:]
            MaterialPhotos.objects.using(user_db(req)).filter(pk=photoID).delete()

        # process forms
        mtlFm = FormMain(req.POST, instance=currRec,  prefix=prefixvals['main'])
        mtlFm.fields['PartType'].queryset=WhsePartTypes.objects.using(user_db(req)).order_by('WhsePartType')
        countSubFm_class = inlineformset_factory(modelMain,modelSubs[0],
                    fields=FormFieldsSubs[0],
                    extra=0,can_delete=False)
        countSet = countSubFm_class(req.POST, instance=currRec, prefix=prefixvals['counts'], initial=initialvals['counts'],
                    queryset=modelSubs[0].objects.using(user_db(req)).order_by('-CountDate'))
                    # queryset=modelSubs[0].objects.filter(CountDate__gte=HistoryCutoffDate).order_by('-CountDate'))
        SchedSubFm_class = inlineformset_factory(modelMain,modelSubs[1],
                    fields=FormFieldsSubs[1],
                    extra=0,can_delete=False)
        schedSet = SchedSubFm_class(req.POST, instance=currRec, prefix=prefixvals['schedule'], initial=initialvals['schedule'],
                    queryset=modelSubs[1].objects.using(user_db(req)).order_by('-CountDate'))
                    # queryset=modelSubs[1].objects.filter(CountDate__gte=HistoryCutoffDate).order_by('-CountDate'))
        MPNSubFm_class = inlineformset_factory(modelMain,modelSubs[2],
                    fields=FormFieldsSubs[2],
                    extra=1,can_delete=True)
        MPNSet = MPNSubFm_class(req.POST, instance=currRec, prefix=prefixvals['MfrPN'], initial=initialvals['MfrPN'],
                    queryset=modelSubs[2].objects.using(user_db(req)).order_by('MfrPN'))

        # is there a request to copy a count?
        if ('copyCountFromid' in req.POST) and ('copyCountToDate' in req.POST):
            copyCountFromid = req.POST['copyCountFromid']
            copyCountToDate = req.POST['copyCountToDate']
            copyCountRec = ActualCounts.objects.using(user_db(req)).get(pk=copyCountFromid)
            copyCountRec.pk = None
            copyCountRec.CountDate = copyCountToDate
            copyCountRec.save(using=user_db(req))

        if all([mtlFm.is_valid(), countSet.is_valid(), schedSet.is_valid(), MPNSet.is_valid(), ]):
            if mtlFm.has_changed():
                try:
                    mtlFm.save()  # hopefully saves to same db: using=user_db(req))
                    chgd_dat['main'] = mtlFm.changed_data
                    changes_saved['main'] = True
                except Exception as err:
                    messages.add_message(req,messages.ERROR,err)
            if countSet.has_changed():
                try:
                    countSet.save()  # hopefully saves to same db: using=user_db(req))
                    chgd_dat['counts'] = countSet.changed_objects
                    changes_saved['counts'] = True
                except Exception as err:
                    messages.add_message(req,messages.ERROR,err)
            if schedSet.has_changed():
                try:
                    schedSet.save()  # hopefully saves to same db: using=user_db(req))
                    chgd_dat['schedule'] = schedSet.changed_objects
                    changes_saved['schedule'] = True
                except Exception as err:
                    messages.add_message(req,messages.ERROR, err)
            if MPNSet.has_changed():
                try:
                    MPNSet.save(using=user_db(req))
                    chgd_dat['MfrPN'] = MPNSet.changed_objects
                    chgd_dat['MfrPN'].append(MPNSet.deleted_objects)
                    chgd_dat['MfrPN'].append(MPNSet.new_objects)
                    changes_saved['MfrPN'] = True
    
                    # regenerate mainFm (mainly to get new add row)
                    MPNSet = MPNSubFm_class(instance=currRec, prefix=prefixvals['MfrPN'], initial=initialvals['MfrPN'],
                                queryset=modelSubs[2].objects.using(user_db(req)).order_by('MfrPN'))
                except Exception as err:
                    messages.add_message(req,messages.ERROR, err)

        # count summary form is r/o.  It will not be changed
    else: # request.method == 'GET' or something else
        mtlFm = FormMain(instance=currRec, initial=initialvals['main'], prefix=prefixvals['main'])
        mtlFm.fields['PartType'].queryset=WhsePartTypes.objects.using(user_db(req)).order_by('WhsePartType')

        CountSubFm_class = inlineformset_factory(modelMain,modelSubs[0],
                    fields=FormFieldsSubs[0],
                    extra=0,can_delete=False)
        countSet = CountSubFm_class(instance=currRec, prefix=prefixvals['counts'], initial=initialvals['counts'],
                    queryset=modelSubs[0].objects.using(user_db(req)).order_by('-CountDate'))
                    # queryset=modelSubs[0].objects.filter(CountDate__gte=HistoryCutoffDate).order_by('-CountDate'))
        SchedSubFm_class = inlineformset_factory(modelMain,modelSubs[1],
                    fields=FormFieldsSubs[1],
                    extra=0,can_delete=False)
        schedSet = SchedSubFm_class(instance=currRec, prefix=prefixvals['schedule'], initial=initialvals['schedule'],
                    queryset=modelSubs[1].objects.using(user_db(req)).order_by('-CountDate'))
                    # queryset=modelSubs[1].objects.filter(CountDate__gte=HistoryCutoffDate).order_by('-CountDate'))
        MPNSubFm_class = inlineformset_factory(modelMain,modelSubs[2],
                    fields=FormFieldsSubs[2],
                    extra=1,can_delete=True)
        MPNSet = MPNSubFm_class(instance=currRec, prefix=prefixvals['MfrPN'], initial=initialvals['MfrPN'],
                    queryset=modelSubs[2].objects.using(user_db(req)).order_by('MfrPN'))
    # endif req.method

    # count summary subform
    SAPTotals = SAP_SOHRecs.objects.using(user_db(req)).filter(Material=currRec)\
        .values('uploaded_at','MaterialPartNum')\
        .annotate(SAPQty=Sum('Amount')).annotate(mult=Subquery(UnitsOfMeasure.objects.filter(UOM=OuterRef('BaseUnitofMeasure')).values('Multiplier1')[:1]))\
        .order_by('uploaded_at', 'MaterialPartNum')
    raw_countdata = ActualCounts.objects.using(user_db(req)).filter(Material=currRec, LocationOnly=False).order_by('Material__Material','-CountDate').annotate(QtyEval=Value(0, output_field=models.IntegerField()))
    LastMaterial = None ; LastCountDate = None
    initdata = []
    for r in raw_countdata:
        try:
            r.QtyEval = evaluate(r.CTD_QTY_Expr)
        # except (ValueError, SyntaxError):
        except:
            r.QtyEval = 0
        if (r.Material != LastMaterial or r.CountDate != LastCountDate):
            LastMaterial = r.Material ; LastCountDate = r.CountDate
            if SAPTotals.filter(uploaded_at__lte=r.CountDate).exists():
                SAPDate = SAPTotals.filter(uploaded_at__lte=r.CountDate).latest('uploaded_at')['uploaded_at']
                SQ = SAPTotals.filter(uploaded_at__lte=r.CountDate).latest('uploaded_at')
                SAPQty = SQ['SAPQty'] * SQ['mult']
            else:
                if SAPTotals.exists():
                    SAPDate = SAPTotals.first()['uploaded_at']
                    SQ = SAPTotals.first()
                    SAPQty = SQ['SAPQty'] * SQ['mult']
                else:
                    SAPDate = ''
                    SAPQty = 0

            initdata.append({
                'Material': r.Material,
                'CountDate': r.CountDate,
                'CountQTY_Eval': 0,
                'SAPDate': SAPDate,
                'SAPQty': SAPQty,
            })
        #endif (r.material or r.CountDate change)
        PIQty = initdata[-1]['CountQTY_Eval'] + r.QtyEval
        initdata[-1]['CountQTY_Eval'] = PIQty
        initdata[-1]['Diff'] = PIQty - SAPQty
        divsr = 1
        if PIQty!=0 or SAPQty!=0: divsr = max(PIQty, SAPQty)
        initdata[-1]['Accuracy'] = f"{min(PIQty, SAPQty) / divsr * 100:.2f}%"
    subFm_class = formset_factory(MaterialCountSummary,extra=0)
    summarySet = subFm_class(initial=initdata, prefix='summaryset')

    # Material photos
    PhotoSet = MaterialPhotos.objects.using(user_db(req)).filter(Material=currRec)

    # display the form
    if req.user.has_perm('WICS.Material_onlyview') and not req.user.has_perm('WICS.SuperUser'): templt = 'frm_Material_RO.html'
    else: templt = 'frm_Material.html'
    
    LastFA = None if not currRec else VIEW_materials.objects.using(user_db(req)).filter(pk=currRec.pk).values('LastCountDate','LastFoundAt')[0]

    cntext = {
            'frmMain': mtlFm,
            'PhotoSet': PhotoSet, 
            'userReadOnly': req.user.has_perm('WICS.Material_onlyview') and not req.user.has_perm('WICS.SuperUser'),
            'lastFoundAt': LastFA,
            'FoundAt': FoundAt(currRec),
            'gotoForm': gotoForm,
            'countset': countSet,
            'scheduleset': schedSet,
            'countsummset': summarySet,
            'MPNset': MPNSet,
            'SAPSet': SAP_SOH,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            }
    
    return render(req, templt, cntext)


#####################################################################
#####################################################################
#####################################################################


class MaterialListCommonView(LoginRequiredMixin, ListView):
    #login_url = reverse('WICSlogin')
    ordering = []
    context_object_name = 'MatlList'
    template_name = 'frm_MatlListing.html'

    SAPSums = {}

    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self._user = req.user
        
        # checking if tabnle is empty, otherwise order_by will crash
        if VIEW_materials.objects.using(user_db(req)).exists():
            self.queryset = VIEW_materials.objects.using(user_db(req)).order_by(*self.ordering).annotate(SAPQty=Value(0), HasSAPQty=Value(False), SAPValue=Value(0), SAPCurrency=Value(''), UnitValue=Value(0))
        else:
            self.queryset = VIEW_materials.objects.using(user_db(req)).annotate(SAPQty=Value(0), HasSAPQty=Value(False), SAPValue=Value(0), SAPCurrency=Value(''), UnitValue=Value(0))

        # it's more efficient to pull this all now and store it for the upcoming qs request
        SAP = fnSAPList(req)
        self.SAPDate = SAP['SAPDate']
        rawsums = SAP['SAPTable'].values('Material_id','mult','Currency').annotate(TotalAmount=Sum('Amount',default=0), TotalValue=Sum('ValueUnrestricted',default=0))
        for x in rawsums:
            self.SAPSums[x['Material_id']] = {
                'Qty': x['TotalAmount']*x['mult'],
                'Value': x['TotalValue'],
                'Currency': x['Currency'],
                }

        return super().setup(req, *args, **kwargs)

    # this should get called (super) and added to for the child classes
    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()
        for rec in qs:
            rec.SAPQty = 0
            if rec.id in self.SAPSums:
                rec.SAPQty = self.SAPSums[rec.id]['Qty']
                rec.SAPValue = self.SAPSums[rec.id]['Value']
                rec.SAPCurrency = self.SAPSums[rec.id]['Currency']
                rec.HasSAPQty = True
                rec.UnitValue = 0 if not rec.SAPQty else rec.SAPValue/rec.SAPQty

        return qs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        cntext = super().get_context_data(**kwargs)

        qs = self.get_queryset()
        qs_listofdict = [modelobj_to_dict(qsobj) for qsobj in qs]

        ExcelFileNamePrefix = self.rptName+' '
        svdir = django_settings.STATIC_ROOT if django_settings.STATIC_ROOT is not None else django_settings.STATICFILES_DIRS[0]
        fName_base = '/tmpdl/'+ExcelFileNamePrefix + f'{calvindate():%Y-%m-%d}'
        fName = svdir + fName_base
        ExcelFileName = Excelfile_fromqs(qs_listofdict, fName)

        cntext['SAPDate'] = self.SAPDate
        cntext['rptName'] = self.rptName
        cntext['groupBy'] = self.groupBy
        cntext['FilSavLoc'] = ExcelFileName
        cntext['ExcelFileName'] = fName_base+ExcelWorkbook_fileext
        return cntext

#####################################################################

class MaterialByPartType(MaterialListCommonView):
    ordering = ['PartTypeName', 'Material']
    rptName = 'Material By Part Type'

    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self.groupBy = 'PartType'
        return super().setup(req, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset()

#####################################################################

class MaterialByLastCountDate(MaterialListCommonView):
    ordering = ['LastCountDate','Material']   # ordering is actually based on a field to be added, and is changed in get_queryset
    finalordering = ['-HasSAPQty','LastCountDate','Material']   # ordering is actually based on a field to be added, and is changed in get_queryset
    rptName = 'Material By Last Count Date'

    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self.groupBy = ''
        return super().setup(req, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()

        q_list = list(qs)
        # already sorted by LastCountDate and Material
        # .order_by('-HasSAPQty', 'LFADate', 'Material')
        q_list.sort(key=attrgetter('HasSAPQty'),reverse=True)
        return q_list

        # return qs

#####################################################################

class MaterialByDESCValue(MaterialListCommonView):
    ordering = ['Material']   # ordering is actually based on a field to be added, and is changed in get_queryset
    rptName = 'Material By Descending Value'

    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self.groupBy = ''
        return super().setup(req, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()

        q_list = list(qs)
        # already sorted by Material
        # qs.order_by('-SAPValue', 'Material')
        q_list.sort(key=attrgetter('SAPValue'),reverse=True)
        return q_list


#####################################################################
#####################################################################
#####################################################################

def fnLocationList(req):

    DoABuildSQLFunction = "SELECT DISTINCT 0 as id, Material_id, Material as strMaterial, CountDate, Description, LOCATION"
    DoABuildSQLFunction += " FROM WICS_actualcounts act JOIN WICS_materiallist matl ON act.Material_id=matl.id"
    DoABuildSQLFunction += " WHERE ROW(Material_id, CountDate) IN ("
    DoABuildSQLFunction +=   " SELECT Material_id, Max(CountDate) as LastCountDate"
    DoABuildSQLFunction +=   " FROM WICS_actualcounts maxdate "
    DoABuildSQLFunction +=   " GROUP BY Material_id)"
    DoABuildSQLFunction += " ORDER BY LOCATION"
    DoABuildSQLFunction +=";"

    locations_qs = ActualCounts.objects.using(user_db(req)).raw(DoABuildSQLFunction)

    cntext = {
            'locations': locations_qs,
            }
    templt = 'frm_LocationList.html'
    return render(req, templt, cntext)


MatlSubFm_fldlist = ['id','org','Material', 'Description', 'PartType', 'Price', 'PriceUnit', 'TypicalContainerQty', 'TypicalPalletQty', 'Notes']

@login_required
def fnPartTypesForm(req, recNum = -1, gotoRec=False):
    # get current record
    currRec = None
    if gotoRec and req.method == 'GET' and recNum > 0:
        currRec = WhsePartTypes.objects.using(user_db(req)).get(pk=recNum)
    if not currRec:
        if recNum < 0:
            currRec = WhsePartTypes.objects.using(user_db(req)).first()
        elif recNum == 0:
            # provide new record
            currRec = WhsePartTypes()
        else:
            currRec = WhsePartTypes.objects.using(user_db(req)).get(pk=recNum)   # later, handle record not found
        # endif
    #endif

    initvals = {
        'main': {},
        'matl': {},
    }
    prefixes = {
        'main': 'parttype',
        'matl': 'matl'
    }
    changes_saved = {
        'main': False,
        'matl': False,
    }
    chgd_dat = {'main':None, 'matl': None, }

    MaterialList_qs = VIEW_materials.objects.using(user_db(req)).all().select_related('org').order_by('Material_org')

    if req.method == 'POST':
        # changed data is being submitted.  process and save it
        # process PTypFm AND subforms.

        # process main form
        PtTypFm = PartTypesForm(req.POST, instance=currRec,  prefix=prefixes['main'])

        # Material subform
        MaterialSubFm_class = forms.inlineformset_factory(WhsePartTypes,MaterialList,
                    fields=MatlSubFm_fldlist,
                    extra=0,can_delete=False)
        MaterialSubFm = MaterialSubFm_class(req.POST, instance=currRec, prefix=prefixes['matl'], initial=initvals['matl'], queryset=MaterialList_qs)

        if PtTypFm.is_valid() and MaterialSubFm.is_valid():
            if PtTypFm.has_changed():
                PtTypFm.save()  # hopefully saves to same db: using=user_db(req))
                chgd_dat['main'] = PtTypFm.changed_data
                changes_saved['main'] = True

            if MaterialSubFm.has_changed():
                MaterialSubFm.save()  # hopefully saves to same db: using=user_db(req))
                chgd_dat['matl'] = MaterialSubFm.changed_objects
                changes_saved['matl'] = True

    else: # request.method == 'GET' or something else
        if currRec:
            PtTypFm = PartTypesForm(instance=currRec, prefix=prefixes['main'])
        else:
            PtTypFm = PartTypesForm(initial=initvals['main'], prefix=prefixes['main'])

        # Material subform
        MaterialSubFm_class = forms.inlineformset_factory(WhsePartTypes,MaterialList,
                    fields=MatlSubFm_fldlist,
                    extra=0,can_delete=False)
        MaterialSubFm = MaterialSubFm_class(instance=currRec, prefix=prefixes['matl'], initial=initvals['matl'], queryset=MaterialList_qs)
    # endif req.method

    gotoForm = {}
    gotoForm['choicelist'] = WhsePartTypes.objects.using(user_db(req)).all().values('id','WhsePartType')
    gotoForm['gotoItem'] = currRec

    # display the form
    cntext = {'frmMain': PtTypFm,
            'showID': None if not currRec else currRec.pk,
            'gotoForm': gotoForm,
            'materials': MaterialSubFm,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            'recNum': recNum,
            }
    templt = 'frm_PartTypes.html'
    return render(req, templt, cntext)


def fnDeletPartTypes(req, recNum):
    # get record.  If related Material, cannot delete, else do so
    currRec = WhsePartTypes.objects.using(user_db(req)).get(id=recNum)
    # later, handle record not found -- but then, that really shouldn't happen

    if MaterialList.objects.using(user_db(req)).filter(PartType=currRec).exists():
        messages.add_message(req,messages.ERROR,'There is Material with Part Type %s.  The Part Type cannot be removed' % currRec.WhsePartType)
        next = urls.reverse('ReloadPTypForm',args=[currRec.pk])
    else:
        deletedPT = currRec.WhsePartType
        currRec.delete(using=user_db(req))
        messages.add_message(req,messages.SUCCESS,'Part Type %s has been removed' % deletedPT)
        next = urls.reverse('PartTypeForm')

    return HttpResponseRedirect(next)


@login_required
def fnMPNView(req):

    FormMain = MfrPNtoMaterialForm

    modelMain = FormMain.Meta.model

    prefixvals = {
        'main': 'material',
        }
    initialvals = {
        'main': {},
        }
    fieldlist = {
        'main': FormMain.Meta.fields # ('id', 'MfrPN', 'Manufacturer', 'Material', 'Notes',)  
    }
    excludelist = {
        'main': ()
    }

    changes_saved = {
        'main': False,
        }
    chgd_dat = {'main':None, }

    mainFm_class = modelformset_factory(modelMain,
                fields=fieldlist['main'],
                exclude=excludelist['main'],
                # form=FormMain,
                extra=5,can_delete=True)

    MPNqs = MfrPNtoMaterial.objects.using(user_db(req)).all().order_by('MfrPN')

    if req.method == 'POST':
        mainFm = mainFm_class(req.POST, prefix=prefixvals['main'], initial=initialvals['main'],
                    queryset=MPNqs)

        if mainFm.is_valid():
            if mainFm.has_changed():
                try:
                    mainFm.save(using=user_db(req))
                    chgd_dat['main'] = mainFm.changed_objects
                    changes_saved['main'] = True

                    # regenerate mainFm (mainly to get 5 new add rows)
                    MPNqs = MfrPNtoMaterial.objects.using(user_db(req)).all().order_by('MfrPN')     # to force reload of qs
                    mainFm = mainFm_class(prefix=prefixvals['main'], initial=initialvals['main'],
                                queryset=MPNqs)
                except Exception as err:
                    messages.add_message(req,messages.ERROR,err)
    else:  # req.method != 'POST'
        mainFm = mainFm_class(prefix=prefixvals['main'], initial=initialvals['main'],
                    queryset=MPNqs)
    # endif req.method == 'POST'

    gotoForm = {}
    gotoForm['choicelist'] = VIEW_materials.objects.using(user_db(req)).all().values('id','Material_org')
    gotoForm['gotoItem'] = None

    # display the form
    cntext = {
        'MPNList': mainFm,
        'gotoForm': gotoForm,
        }
    templt = 'frm_MPNtoMatl.html'
    return render(req, templt, cntext)

