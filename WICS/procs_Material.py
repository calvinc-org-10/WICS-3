import datetime
from datetime import MINYEAR
from operator import attrgetter
#import dateutil.utils
from django import forms, urls
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Value, Sum
from django.db.models.query import QuerySet
from django.forms import inlineformset_factory, formset_factory
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import ListView
from cMenu.models import getcParm
from cMenu.utils import calvindate
from userprofiles.models import WICSuser
from WICS.models import org_queryset, MaterialList, ActualCounts, CountSchedule, SAP_SOHRecs, \
                        WhsePartTypes, LastFoundAt, FoundAt
from WICS.procs_SAP import fnSAPList
from typing import Any, Dict



ExcelWorkbook_fileext = ".XLSX"


class MaterialLocationsList(LoginRequiredMixin, ListView):
    #login_url = reverse('WICSlogin')
    ordering = ['Material']
    context_object_name = 'MatlList'
    template_name = 'rpt_PartLocations.html'
    SAPSums = {}

    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self._user = req.user
        self._userorg = WICSuser.objects.get(user=self._user).org
        # get last count date (incl LocationOnly) for each Material (prefetch_related?)
        qs = MaterialList.objects.filter(org=self._userorg).order_by('Material').annotate(LFADate=Value(0), LFALocation=Value(''), SAPList=Value(0), DoNotShow=Value(False))   # figure out how to pass in self.ordering

        # it's more efficient to pull this all now and store it for the upcoming qs request
        SAP = fnSAPList(self._userorg)
        self.SAPDate = SAP['SAPDate']
        self.SAPTable = SAP['SAPTable']

        self.queryset = qs
        return super().setup(req, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()
        for rec in qs:
            L = LastFoundAt(rec)
            rec.LFADate = L['lastCountDate']
            rec.LFALocation = L['lastFoundAt']
            rec.SAPList = self.SAPTable.filter(Material=rec.Material)
            # filter Material in SAP_SOH for date OR last count date within 30d
            testdate = rec.LFADate
            if testdate == None: testdate = calvindate(MINYEAR, 1, 1)
            rec.DoNotShow = (not rec.SAPList.exists()) and (testdate < calvindate().today()-int(getcParm('LOCRPT-COUNTDAYS-IFNOSAP')))

        return qs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        cntext = super().get_context_data(**kwargs)
        cntext.update({
            'SAPDate': self.SAPDate,
            'showSAP': False,
            'orgname': self._userorg.orgname,  'uname':self._user.get_full_name(),
            })
        return cntext

    # def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    #     return super().get(request, *args, **kwargs)

    def render_to_response(self, context: Dict[str, Any], **response_kwargs: Any) -> HttpResponse:
        return super().render_to_response(context, **response_kwargs)


class MaterialForm(forms.ModelForm):
    showPK = forms.IntegerField(label='ID', disabled=True, required=False)
    class Meta:
        model = MaterialList
        fields = ['id', 'org', 'Material', 'Description','PartType',
                'SAPMaterialType', 'SAPMaterialGroup', 'Price',
                'TypicalContainerQty', 'TypicalPalletQty', 'PriceUnit', 'Notes']
        # fields = '__all__'

class MaterialCountSummary(forms.Form):
    Material = forms.CharField(max_length=100, disabled=True)
    CountDate = forms.DateField(required=False, disabled=True)
    CountQTY_Eval = forms.IntegerField(required=False, disabled=True)
    SAPDate = forms.DateField(required=False, disabled=True)
    SAPQty = forms.CharField(max_length=20, required=False, disabled=True)
    Diff = forms.CharField(max_length=20, required=False, disabled=True)
    Accuracy = forms.CharField(max_length=20, required=False, disabled=True)


@login_required
def fnMaterialForm(req, recNum = -1, gotoMatl=None, gotoRec=False, newRec=False):
    _userorg = WICSuser.objects.get(user=req.user).org
    if not _userorg: raise Exception('User is corrupted!!')

    # get current record
    currRec = None
    if gotoRec and req.method == 'GET' and gotoMatl:
        currRec = MaterialList.objects.filter(org=_userorg, Material=gotoMatl).first()
    elif req.method == 'POST':
        currRec = MaterialList.objects.filter(org=_userorg, Material=req.POST['OrigMaterial']).first()

    if not currRec:
        if newRec:
            # provide new record
            currRec = MaterialList(org=_userorg)
        elif recNum <= 0:
            currRec = MaterialList.objects.filter(org=_userorg).first()
        else:
            currRec = MaterialList.objects.get(org=_userorg, pk=recNum)   # later, handle record not found
        # endif
    #endif

    if not currRec: #there are no MaterialList records for this org!!
        thisPK = 0
    else:
        thisPK = currRec.pk

    prefixvals = {
        'main': 'material',
        'counts': 'countset',
        'schedule': 'schedset',
        }
    initialvals = {
        'main': {'gotoItem': thisPK, 'showPK': thisPK, 'org':_userorg},
        'counts': {'org': _userorg},
        'schedule': {'org': _userorg},
        }

    changes_saved = {
        'main': False,
        'counts': False,
        'schedule': False,
        }
    chgd_dat = {'main':None, 'counts': None, 'schedule': None}

    if newRec:
        SAP_SOH = fnSAPList(_userorg,matl='-')
    else:
        SAP_SOH = fnSAPList(_userorg, matl=currRec.Material)

    gotoForm = {}
    gotoForm['gotoItem'] = currRec
    gotoForm['choicelist'] = MaterialList.objects.filter(org=_userorg).values('id','Material')

    CountSubFormFields = ('id', 'CountDate', 'CycCtID', 'Counter', 'LocationOnly', 'CTD_QTY_Expr', 'BLDG', 'LOCATION', 'PKGID_Desc', 'TAGQTY', 'FLAG_PossiblyNotRecieved', 'FLAG_MovementDuringCount', 'Notes',)
    ScheduleSubFormFields = ('id','CountDate','Counter', 'Priority', 'ReasonScheduled', 'CMPrintFlag', 'Notes',)

    if req.method == 'POST':
        # changed data is being submitted.  process and save it
        # process mtlFm AND subforms.

        # process forms
        mtlFm = MaterialForm(req.POST, instance=currRec,  initial=initialvals['main'],  prefix=prefixvals['main'])
        mtlFm.fields['PartType'].queryset=WhsePartTypes.objects.filter(org=_userorg).order_by('WhsePartType').all()
        countSubFm_class = inlineformset_factory(MaterialList,ActualCounts,
                    fields=CountSubFormFields,
                    extra=0,can_delete=False)
        countSet = countSubFm_class(req.POST, instance=currRec, prefix=prefixvals['counts'], initial=initialvals['counts'],
                    queryset=ActualCounts.objects.order_by('-CountDate'))
        SchedSubFm_class = inlineformset_factory(MaterialList,CountSchedule,
                    fields=ScheduleSubFormFields,
                    extra=0,can_delete=False)
        schedSet = SchedSubFm_class(req.POST, instance=currRec, prefix=prefixvals['schedule'], initial=initialvals['schedule'],
                    queryset=CountSchedule.objects.order_by('-CountDate'))

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
        mtlFm = MaterialForm(instance=currRec, initial=initialvals['main'], prefix=prefixvals['main'])
        mtlFm.fields['PartType'].queryset=WhsePartTypes.objects.filter(org=_userorg).order_by('WhsePartType').all()

        CountSubFm_class = inlineformset_factory(MaterialList,ActualCounts,
                    fields=CountSubFormFields,
                    extra=0,can_delete=False)
        countSet = CountSubFm_class(instance=currRec, prefix=prefixvals['counts'], initial=initialvals['counts'],
                    queryset=ActualCounts.objects.order_by('-CountDate'))

        SchedSubFm_class = inlineformset_factory(MaterialList,CountSchedule,
                    fields=ScheduleSubFormFields,
                    extra=0,can_delete=False)
        schedSet = SchedSubFm_class(instance=currRec, prefix=prefixvals['schedule'], initial=initialvals['schedule'],
                    queryset=CountSchedule.objects.order_by('-CountDate'))
    # endif

    # count summary subform
    SAPTotals = SAP_SOHRecs.objects.filter(org=_userorg).values('uploaded_at','Material').annotate(SAPQty=Sum('Amount')).order_by('uploaded_at', 'Material')
    raw_countdata = ActualCounts.objects.filter(Material=currRec).order_by('Material','-CountDate').annotate(QtyEval=Value(0, output_field=models.IntegerField()))
    LastMaterial = None ; LastCountDate = None
    initdata = []
    for r in raw_countdata:
        try:
            r.QtyEval = eval(r.CTD_QTY_Expr)    # later, use ast.literal_eval, or write a parser
        # except (ValueError, SyntaxError):
        except:
            r.QtyEval = 0
        if (r.Material != LastMaterial or r.CountDate != LastCountDate):
            LastMaterial = r.Material ; LastCountDate = r.CountDate
            if SAPTotals.filter(Material=r.Material,uploaded_at__lte=r.CountDate).exists():
                SAPDate = SAPTotals.filter(Material=r.Material,uploaded_at__lte=r.CountDate).latest()['uploaded_at']
                SAPQty = SAPTotals.filter(Material=r.Material,uploaded_at__lte=r.CountDate).latest()['SAPQty']
            else:
                if SAPTotals.filter(Material=r.Material).exists():
                    SAPDate = SAPTotals.filter(Material=r.Material).first()['uploaded_at']
                    SAPQty = SAPTotals.filter(Material=r.Material).first()['SAPQty']
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
    cntext = {'frmMain': mtlFm,
            'userReadOnly': req.user.has_perm('WICS.Material_onlyview') and not req.user.has_perm('WICS.SuperUser'),
            'lastFoundAt': LastFoundAt(currRec),
            'FoundAt': FoundAt(currRec),
            'gotoForm': gotoForm,
            'countset': countSet,
            'scheduleset': schedSet,
            'countsummset': summarySet,
            'SAPSet': SAP_SOH,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            'recNum': recNum,
            'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'frm_Material.html'
    return render(req, templt, cntext)


#####################################################################
#####################################################################
#####################################################################

class MaterialListCommonView(LoginRequiredMixin, ListView):
    #login_url = reverse('WICSlogin')
    context_object_name = 'MatlList'
    template_name = 'frm_MatlListing.html'

    SAPSums = {}

    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self._user = req.user
        self._userorg = WICSuser.objects.get(user=self._user).org
        self.queryset = org_queryset(MaterialList,self._userorg).order_by(*self.ordering).annotate(LFADate=Value(0), LFALocation=Value(''), SAPQty=Value(0), HasSAPQty=Value(False), SAPValue=Value(0), SAPCurrency=Value(''))

        # it's more efficient to pull this all now and store it for the upcoming qs request
        SAP = fnSAPList(self._userorg)
        self.SAPDate = SAP['SAPDate']
        rawsums = SAP['SAPTable'].values('Material','mult','Currency').annotate(TotalAmount=Sum('Amount',default=0), TotalValue=Sum('ValueUnrestricted',default=0))
        for x in rawsums:
            self.SAPSums[x['Material']] = {
                'Qty': x['TotalAmount']*x['mult'],
                'Value': x['TotalValue'],
                'Currency': x['Currency'],
                }

        return super().setup(req, *args, **kwargs)

    # this sdhould get called (super) and added to for the child classes
    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()
        for rec in qs:
            L = LastFoundAt(rec)
            if L['lastCountDate']:
                rec.LFADate = L['lastCountDate']
            else:
                rec.LFADate = datetime.date(MINYEAR,1,1)
            rec.LFALocation = L['lastFoundAt']
            rec.SAPQty = 0
            if rec.Material in self.SAPSums:
                rec.SAPQty = self.SAPSums[rec.Material]['Qty']
                rec.SAPValue = self.SAPSums[rec.Material]['Value']
                rec.SAPCurrency = self.SAPSums[rec.Material]['Currency']
                rec.HasSAPQty = True

        return qs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        cntext = super().get_context_data(**kwargs)
        cntext['SAPDate'] = self.SAPDate
        cntext['rptName'] = self.rptName
        cntext['groupBy'] = self.groupBy
        cntext.update({'orgname': self._userorg.orgname,  'uname':self._user.get_full_name()})
        return cntext

#####################################################################

class MaterialByPartType(MaterialListCommonView):
    ordering = ['PartType__PartTypePriority', 'PartType__WhsePartType', 'Material']
    rptName = 'Material By Part Type'

    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self.groupBy = 'PartType'
        return super().setup(req, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset()

#####################################################################

class MaterialByLastCountDate(MaterialListCommonView):
    ordering = ['Material']   # ordering is actually based on a field to be added, and is changed in get_queryset
    rptName = 'Material By Last Count Date'

    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self.groupBy = ''
        return super().setup(req, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()

        q_list = list(qs)
        # already sorted by Material
        # .order_by('-HasSAPQty', 'LFADate', 'Material')
        q_list.sort(key=attrgetter('LFADate'))
        q_list.sort(key=attrgetter('HasSAPQty'),reverse=True)
        return q_list

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
    _userorg = WICSuser.objects.get(user=req.user).org

    DoABuildSQLFunction = "SELECT DISTINCT 0 as id, Material_id, Material as strMaterial, CountDate, Description, BLDG, LOCATION"
    DoABuildSQLFunction += " FROM WICS_actualcounts act JOIN WICS_materiallist matl ON act.Material_id=matl.id"
    DoABuildSQLFunction += " WHERE ROW(Material_id, CountDate) IN ("
    DoABuildSQLFunction +=   " SELECT Material_id, Max(CountDate) as LastCountDate"
    DoABuildSQLFunction +=   " FROM WICS_actualcounts maxdate "
    DoABuildSQLFunction +=   " WHERE maxdate.org_id = " + str(_userorg.pk)
    DoABuildSQLFunction +=   " GROUP BY Material_id"
    DoABuildSQLFunction +=   ") AND matl.org_id = " + str(_userorg.pk)
    DoABuildSQLFunction += " ORDER BY BLDG, LOCATION"
    DoABuildSQLFunction +=";"

    locations_qs = ActualCounts.objects.raw(DoABuildSQLFunction)

    cntext = {
            'locations': locations_qs,
            'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'frm_LocationList.html'
    return render(req, templt, cntext)


class PartTypesForm(forms.ModelForm):
    class Meta:
        model = WhsePartTypes
        fields = ['WhsePartType', 'PartTypePriority', 'InactivePartType']

MatlSubFm_fldlist = ['id','org','Material', 'Description', 'PartType', 'Price', 'PriceUnit', 'TypicalContainerQty', 'TypicalPalletQty', 'Notes']

# later -- check for uniqueness of (org, WhsePartType), (org,PartTypePriority)
@login_required
def fnPartTypesForm(req, recNum = -1, gotoRec=False):
    _userorg = WICSuser.objects.get(user=req.user).org
    if not _userorg: raise Exception('User is corrupted!!')

    # get current record
    currRec = None
    #if gotoRec and req.method == 'GET' and 'realGotoID' in req.GET:
    if gotoRec and req.method == 'GET' and recNum > 0:
        currRec = WhsePartTypes.objects.get(org=_userorg, pk=recNum)
    if not currRec:
        if recNum < 0:
            currRec = WhsePartTypes.objects.filter(org=_userorg).first()
        elif recNum == 0:
            # provide new record
            currRec = WhsePartTypes(org=_userorg)
        else:
            currRec = WhsePartTypes.objects.filter(org=_userorg).get(pk=recNum)   # later, handle record not found
        # endif
    #endif

    initvals = {
        'main': {'org':_userorg},
        'matl': {'org':_userorg},
    }
    #{'gotoItem': thisPK, 'showPK': thisPK, 'org':_userorg}
    prefixes = {
        'main': 'parttype',
        'matl': 'matl'
    }
    changes_saved = {
        'main': False,
        'matl': False,
    }
    chgd_dat = {'main':None, 'matl': None, }

    if req.method == 'POST':
        # changed data is being submitted.  process and save it
        # process PTypFm AND subforms.

        # process main form
        #if currRec:
        PtTypFm = PartTypesForm(req.POST, instance=currRec,  initial=initvals['main'],  prefix=prefixes['main'])
        #else:
        #    PtTypFm = MaterialForm(req.POST, initial={'gotoItem': thisPK, 'showPK': thisPK, 'org':_userorg},  prefix='material')
        #endif

        # Material subform
        MaterialSubFm_class = forms.inlineformset_factory(WhsePartTypes,MaterialList,
                    fields=MatlSubFm_fldlist,
                    extra=0,can_delete=False)
        # MaterialSubFm_class.PartType.queryset=WhsePartTypes.objects.filter(org=_userorg).order_by('WhsePartType').all() - rendered manually
        #if currRec:
        MaterialSubFm = MaterialSubFm_class(req.POST, instance=currRec, prefix=prefixes['matl'], initial=initvals['matl'], queryset=MaterialList.objects.filter(org=_userorg).order_by('Material'))
        #else:
        #    countSet = countSubFm_class(req.POST, prefix='countset', initial={'org': _userorg}, queryset=ActualCounts.objects.order_by('-CountDate'))

        if PtTypFm.is_valid() and MaterialSubFm.is_valid():
            if PtTypFm.has_changed():
                PtTypFm.save()
                chgd_dat['main'] = PtTypFm.changed_data
                changes_saved['main'] = True
                #raise Exception('main saved')

            if MaterialSubFm.has_changed():
                MaterialSubFm.save()
                chgd_dat['matl'] = MaterialSubFm.changed_objects
                changes_saved['matl'] = True
                #raise Exception('counts saved')

    else: # request.method == 'GET' or something else
        if currRec:
            PtTypFm = PartTypesForm(instance=currRec, initial=initvals['main'], prefix=prefixes['main'])
        else:
            PtTypFm = PartTypesForm(initial=initvals['main'], prefix=prefixes['main'])

        # Material subform
        MaterialSubFm_class = forms.inlineformset_factory(WhsePartTypes,MaterialList,
                    fields=MatlSubFm_fldlist,
                    extra=0,can_delete=False)
        # MaterialSubFm_class.PartType.queryset=WhsePartTypes.objects.filter(org=_userorg).order_by('WhsePartType').all() - rendered manually
        #if currRec:
        MaterialSubFm = MaterialSubFm_class(instance=currRec, prefix=prefixes['matl'], initial=initvals['matl'], queryset=MaterialList.objects.filter(org=_userorg).order_by('Material'))
        #else:
        #    countSet = countSubFm_class(req.POST, prefix='countset', initial={'org': _userorg}, queryset=ActualCounts.objects.order_by('-CountDate'))

    # endif

    gotoForm = {}
    gotoForm['gotoItem'] = currRec
    gotoForm['choicelist'] = WhsePartTypes.objects.filter(org=_userorg).values('id','WhsePartType')

    # display the form
    cntext = {'frmMain': PtTypFm,
            'showID': currRec.pk,
            'gotoForm': gotoForm,
            'materials': MaterialSubFm,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            'recNum': recNum,
            'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'frm_PartTypes.html'
    return render(req, templt, cntext)


def fnDeletPartTypes(req, recNum):
    _userorg = WICSuser.objects.get(user=req.user).org
    if not _userorg: raise Exception('User is corrupted!!')

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

