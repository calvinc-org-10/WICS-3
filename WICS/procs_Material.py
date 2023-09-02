import datetime
from datetime import MINYEAR
from operator import attrgetter
from django import forms, urls
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Value, Sum, Max
from django.db.models import F, Value, Case, When, Exists, Subquery, OuterRef
from django.db.models.functions import Concat
from django.db.models.query import QuerySet
from django.forms import inlineformset_factory, formset_factory
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import ListView
from cMenu.models import getcParm
from cMenu.utils import calvindate
from mathematical_expressions_parser.eval import evaluate
from userprofiles.models import WICSuser
from WICS.globals import _defaultOrg
from WICS.forms import MaterialForm, MaterialCountSummary, PartTypesForm
from WICS.models import MaterialList, VIEW_materials, WhsePartTypes
from WICS.models import CountSchedule, ActualCounts, FoundAt
from WICS.models import SAP_SOHRecs, UnitsOfMeasure #, VIEW_SAP
from WICS.procs_SAP import fnSAPList
from typing import Any, Dict


class MaterialLocationsList(LoginRequiredMixin, ListView):
    #login_url = reverse('WICSlogin')
    # ordering = ['org_id','Material']  - ordering should not be defined on a raw queryset
    context_object_name = 'MatlList'
    template_name = 'rpt_PartLocations.html'
    SAPSums = {}

    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self._user = req.user
        #TODO: Lose the view in the sql below
        # get last count date (incl LocationOnly) for each Material (prefetch_related?)
        #sqlLFA = "SELECT MATL.id, MATL.OrgName, MATL.Material, MATL.Description, MATL.PartType_id, LFA.CountDate AS LFADate, LFA.FoundAt AS LFALocation,"
        #sqlLFA += " MATL.Notes, 0 AS SAPList, FALSE AS DoNotShow"
        #sqlLFA += " FROM VIEW_LastFoundAt LFA JOIN VIEW_materials MATL ON LFA.Material_id = MATL.id"
        #sqlLFA += " ORDER BY MATL.org_id, MATL.Material"
        #qs = MaterialList.objects.raw(sqlLFA)
        qs = VIEW_materials.objects.all().annotate(
                        SAPList=Value(0),
                        DoNotShow=Value(False),
                    )

        # it's more efficient to pull this all now and store it for the upcoming qs request
        SAP = fnSAPList()
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
            rec.DoNotShow = (not rec.SAPList.exists()) and (testdate < calvindate().today()-int(getcParm('LOCRPT-COUNTDAYS-IFNOSAP')))

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
    modelSubs = [S for S in [ActualCounts, CountSchedule]]

    FormFieldsSubs = [
        # 0 = ActualCounts Subform
        ['id', 'CountDate', 'Counter', 'LocationOnly', 'CTD_QTY_Expr', 'LOCATION', 'FLAG_PossiblyNotRecieved', 'FLAG_MovementDuringCount', 'Notes',],
        # 1 = CountSchedule SubForm
        ['id','CountDate','Counter', 'Priority', 'ReasonScheduled', 'Notes',],
    ]

    # get current record
    currRec = None
    if req.method == 'POST':
        currRec = modelMain.objects.filter(pk=req.POST['MatlPK']).first()
    else:
        if newRec:
            # provide new record
            currRec = modelMain(org=_defaultOrg)
        elif recNum <= 0:
            currRec = modelMain.objects.first()
        else:
            try:
                currRec = modelMain.objects.get(pk=recNum)
            except:
                pass    # currRec remains None
        # endif newRec, recNum
    #endif set currRec

    thisPK = 0
    if not newRec and currRec:
        thisPK = currRec.pk

    prefixvals = {
        'main': 'material',
        'counts': 'countset',
        'schedule': 'schedset',
        }
    initialvals = {
        'main': {'gotoItem': thisPK, 'showPK': thisPK, 'org':_defaultOrg},
        'counts': {},
        'schedule': {},
        }

    changes_saved = {
        'main': False,
        'counts': False,
        'schedule': False,
        }
    chgd_dat = {'main':None, 'counts': None, 'schedule': None}

    if newRec:
        SAP_SOH = fnSAPList(matl='-')
    else:
        SAP_SOH = fnSAPList(matl=currRec)

    gotoForm = {}
    gotoForm['choicelist'] = \
    VIEW_materials.objects.all().values('id','Material_org')
    gotoForm['gotoItem'] = currRec

    if req.method == 'POST':
        # changed data is being submitted.  process and save it
        # process mtlFm AND subforms.

        # process forms
        # mtlFm = FormMain(req.POST, instance=currRec,  initial=initialvals['main'],  prefix=prefixvals['main'])
        mtlFm = FormMain(req.POST, instance=currRec,  prefix=prefixvals['main'])
        mtlFm.fields['PartType'].queryset=WhsePartTypes.objects.all().order_by('WhsePartType')
        countSubFm_class = inlineformset_factory(modelMain,modelSubs[0],
                    fields=FormFieldsSubs[0],
                    extra=0,can_delete=False)
        countSet = countSubFm_class(req.POST, instance=currRec, prefix=prefixvals['counts'], initial=initialvals['counts'],
                    queryset=modelSubs[0].objects.order_by('-CountDate'))
                    # queryset=modelSubs[0].objects.filter(CountDate__gte=HistoryCutoffDate).order_by('-CountDate'))
        SchedSubFm_class = inlineformset_factory(modelMain,modelSubs[1],
                    fields=FormFieldsSubs[1],
                    extra=0,can_delete=False)
        schedSet = SchedSubFm_class(req.POST, instance=currRec, prefix=prefixvals['schedule'], initial=initialvals['schedule'],
                    queryset=modelSubs[1].objects.order_by('-CountDate'))
                    # queryset=modelSubs[1].objects.filter(CountDate__gte=HistoryCutoffDate).order_by('-CountDate'))

        # is there a request to copy a count?
        if ('copyCountFromid' in req.POST) and ('copyCountToDate' in req.POST):
            copyCountFromid = req.POST['copyCountFromid']
            copyCountToDate = req.POST['copyCountToDate']
            copyCountRec = ActualCounts.objects.get(pk=copyCountFromid)
            copyCountRec.pk = None
            copyCountRec.CountDate = copyCountToDate
            copyCountRec.save()

        if mtlFm.is_valid() and countSet.is_valid() and schedSet.is_valid():
            if mtlFm.has_changed():
                try:
                    mtlFm.save()
                    chgd_dat['main'] = mtlFm.changed_data
                    changes_saved['main'] = True
                except Exception as err:
                    messages.add_message(req,messages.ERROR,err)
            if countSet.has_changed():
                try:
                    countSet.save()
                    chgd_dat['counts'] = countSet.changed_objects
                    changes_saved['counts'] = True
                except Exception as err:
                    messages.add_message(req,messages.ERROR,err)
            if schedSet.has_changed():
                try:
                    schedSet.save()
                    chgd_dat['schedule'] = schedSet.changed_objects
                    changes_saved['schedule'] = True
                except Exception as err:
                    messages.add_message(req,messages.ERROR, err)

        # count summary form is r/o.  It will not be changed
    else: # request.method == 'GET' or something else
        mtlFm = FormMain(instance=currRec, initial=initialvals['main'], prefix=prefixvals['main'])
        mtlFm.fields['PartType'].queryset=WhsePartTypes.objects.all().order_by('WhsePartType')

        CountSubFm_class = inlineformset_factory(modelMain,modelSubs[0],
                    fields=FormFieldsSubs[0],
                    extra=0,can_delete=False)
        countSet = CountSubFm_class(instance=currRec, prefix=prefixvals['counts'], initial=initialvals['counts'],
                    queryset=modelSubs[0].objects.order_by('-CountDate'))
                    # queryset=modelSubs[0].objects.filter(CountDate__gte=HistoryCutoffDate).order_by('-CountDate'))

        SchedSubFm_class = inlineformset_factory(modelMain,modelSubs[1],
                    fields=FormFieldsSubs[1],
                    extra=0,can_delete=False)
        schedSet = SchedSubFm_class(instance=currRec, prefix=prefixvals['schedule'], initial=initialvals['schedule'],
                    queryset=modelSubs[1].objects.order_by('-CountDate'))
                    # queryset=modelSubs[1].objects.filter(CountDate__gte=HistoryCutoffDate).order_by('-CountDate'))
    # endif

    # count summary subform
    # add another 30 days to the SAP cutoff in case the earliest Count records don't have an SAP count from the same day
    SAPTotals = SAP_SOHRecs.objects.filter(Material=currRec)\
        .values('uploaded_at','MaterialPartNum')\
        .annotate(SAPQty=Sum('Amount')).annotate(mult=Subquery(UnitsOfMeasure.objects.filter(UOM=OuterRef('BaseUnitofMeasure')).values('Multiplier1')[:1]))\
        .order_by('uploaded_at', 'MaterialPartNum')
    raw_countdata = ActualCounts.objects.filter(Material=currRec).order_by('Material__Material','-CountDate').annotate(QtyEval=Value(0, output_field=models.IntegerField()))
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
        PIQty = initdata[-1]['CountQTY_Eval'] + r.QtyEval
        initdata[-1]['CountQTY_Eval'] = PIQty
        initdata[-1]['Diff'] = PIQty - SAPQty
        divsr = 1
        if PIQty!=0 or SAPQty!=0: divsr = max(PIQty, SAPQty)
        initdata[-1]['Accuracy'] = f"{min(PIQty, SAPQty) / divsr * 100:.2f}%"
    subFm_class = formset_factory(MaterialCountSummary,extra=0)
    summarySet = subFm_class(initial=initdata, prefix='summaryset')

    # display the form
    cntext = {
            'frmMain': mtlFm,
            'userReadOnly': req.user.has_perm('WICS.Material_onlyview') and not req.user.has_perm('WICS.SuperUser'),
            'lastFoundAt': VIEW_materials.objects.filter(pk=currRec.pk).values('LastCountDate','LastFoundAt')[0],
            'FoundAt': FoundAt(currRec),
            'gotoForm': gotoForm,
            'countset': countSet,
            'scheduleset': schedSet,
            'countsummset': summarySet,
            'SAPSet': SAP_SOH,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            }
    templt = 'frm_Material.html'
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
        #self.queryset = MaterialList.objects.order_by(*self.ordering).annotate(LFADate=Value(0), LFALocation=Value(''), SAPQty=Value(0), HasSAPQty=Value(False), SAPValue=Value(0), SAPCurrency=Value(''))
        self.queryset = VIEW_materials.objects.order_by(*self.ordering).annotate(SAPQty=Value(0), HasSAPQty=Value(False), SAPValue=Value(0), SAPCurrency=Value(''), UnitValue=Value(0))

        # it's more efficient to pull this all now and store it for the upcoming qs request
        SAP = fnSAPList()
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
        cntext['SAPDate'] = self.SAPDate
        cntext['rptName'] = self.rptName
        cntext['groupBy'] = self.groupBy
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

    locations_qs = ActualCounts.objects.raw(DoABuildSQLFunction)

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
        currRec = WhsePartTypes.objects.get(pk=recNum)
    if not currRec:
        if recNum < 0:
            currRec = WhsePartTypes.objects.first()
        elif recNum == 0:
            # provide new record
            currRec = WhsePartTypes()
        else:
            currRec = WhsePartTypes.objects.get(pk=recNum)   # later, handle record not found
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

    # we cannot use VIEW_materials because inlineformset_factory needs a real FK to PartTypes
    # but I want Material_org to present to the user, so...
    #TODO: use the tools I've already built for other forms
    #MaterialList_qs = MaterialList.objects.all().select_related('org')\
    #    .annotate(Material_org=
    #              Case(
    #                When(Exists(Subquery(MaterialList.objects.exclude(org=OuterRef('org')))),then=Concat(F('org__orgname'),Value(' '),F('Material'),output_field=models.CharField())),
    #                default=F('Material'),
    #                )
    #            )\
    #    .order_by('Material_org')
    MaterialList_qs = VIEW_materials.objects.all().select_related('org').order_by('Material_org')

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
                PtTypFm.save()
                chgd_dat['main'] = PtTypFm.changed_data
                changes_saved['main'] = True

            if MaterialSubFm.has_changed():
                MaterialSubFm.save()
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
    # endif

    gotoForm = {}
    gotoForm['choicelist'] = WhsePartTypes.objects.all().values('id','WhsePartType')
    gotoForm['gotoItem'] = currRec

    # display the form
    cntext = {'frmMain': PtTypFm,
            'showID': currRec.pk,
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
    currRec = WhsePartTypes.objects.get(id=recNum)
    # later, handle record not found -- but then, that really shouldn't happen

    if MaterialList.objects.filter(PartType=currRec).exists():
        messages.add_message(req,messages.ERROR,'There is Material with Part Type %s.  The Part Type cannot be removed' % currRec.WhsePartType)
        next = urls.reverse('ReloadPTypForm',args=[currRec.pk])
    else:
        deletedPT = currRec.WhsePartType
        currRec.delete()
        messages.add_message(req,messages.SUCCESS,'Part Type %s has been removed' % deletedPT)
        next = urls.reverse('PartTypeForm')

    return HttpResponseRedirect(next)

