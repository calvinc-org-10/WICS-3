import datetime
# TODO: skip Sat, Sun using dateutil, dateutil.rrule, dateutil.rruleset
# implement skipping holidays
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.urls import reverse
from django import forms
from django.forms import inlineformset_factory
from django.shortcuts import render
from WICS.forms import CountScheduleForm
from cMenu.models import getcParm
from WICS.models import MaterialList, ActualCounts, CountSchedule, \
                        WhsePartTypes, LastFoundAt
from userprofiles.models import WICSuser
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from django.db.models.query import QuerySet
from django.views.generic import ListView
from typing import *


_userorg = None

from django.core.files.base import File
from django.db.models.base import Model
#from django.db.models.query import QuerySet, _BaseQuerySet
from django.forms.utils import ErrorList


class CountScheduleRecordForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    CountDate = forms.DateField(required=True, initial=datetime.date.today())
    Material = forms.CharField(required=True)
        # Material is handled this way because of the way it's done in the html.
        # later, create a DropdownText widget??
    Counter = forms.CharField(required=False)
    Priority = forms.CharField(max_length=50, required=False)
    ReasonScheduled = forms.CharField(max_length=250, required=False)
    CMPrintFlag = forms.BooleanField(required=False, initial=False)
    Notes  = forms.CharField(required=False)

    class Meta:
        model = CountSchedule
        fields = ['CountDate', 'Counter', 'Priority', 'ReasonScheduled', 'CMPrintFlag', 'Notes']
    def __init__(self, org, *args, **kwargs):
        self.org = org
        super().__init__(*args, **kwargs)
    def save(self):
        if not self.is_valid():
            return None
        dbmodel = self.Meta.model
        required_fields = ['CountDate', 'Material'] #id, org handled separately
        PriK = self['id'].value()
        M = MaterialList.objects.get(org=self.org, Material=self.cleaned_data['Material']) 
        if not str(PriK).isnumeric(): PriK = -1
        existingrec = dbmodel.objects.filter(pk=PriK).exists()
        if existingrec: rec = dbmodel.objects.get(pk=PriK)
        else: rec = dbmodel()
        for fldnm in self.changed_data + required_fields:
            if fldnm=='id' or fldnm=='org': continue
            elif fldnm=='Material':
                setattr(rec,fldnm, M)
            else:
                setattr(rec, fldnm, self.cleaned_data[fldnm])
        rec.org = self.org
        
        rec.save()
        return rec

class RelatedMaterialInfo(forms.ModelForm):
    Description = forms.CharField(max_length=250, required=False)
    PartType = forms.ModelChoiceField(queryset=WhsePartTypes.objects.filter(org=_userorg))
    TypicalContainerQty = forms.IntegerField(required=False)
    TypicalPalletQty = forms.IntegerField(required=False)
    Notes = forms.CharField(max_length=250, required=False)
    class Meta:
        model = MaterialList
        fields = ['Description', 'PartType', 
                'TypicalContainerQty', 'TypicalPalletQty', 'Notes']
    def __init__(self, org, id, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.id = id
        self.org = org
        self.fields['PartType'].queryset=WhsePartTypes.objects.filter(org=org).all()
    def save(self):
        if not self.is_valid():
            return None
        dbmodel = self.Meta.model
        required_fields = [] #id, org handled separately
        PriK = self.id
        if not str(PriK).isnumeric(): PriK = -1
        existingrec = dbmodel.objects.filter(pk=PriK).exists()
        if existingrec: rec = dbmodel.objects.get(pk=PriK)
        else:  raise Exception('Saving Related Material with no PK')  # rec = dbmodel()
        for fldnm in self.changed_data + required_fields:
            if fldnm=='id' or fldnm=='org': continue
            if fldnm=='Material':
                # no special processing - Material is a string here, not a ForeignField
                setattr(rec, fldnm, self.cleaned_data[fldnm])
            else:
                setattr(rec, fldnm, self.cleaned_data[fldnm])
        rec.org = self.org
        
        rec.save()
        return rec

@login_required
def fnCountScheduleRecordForm(req, recNum = 0, 
    passedMatlNum = None, 
    passedCountDate=str(datetime.date.today()), 
    gotoCommand=None
    ):

    _userorg = WICSuser.objects.get(user=req.user).org

    # the string 'None' is not the same as the value None
    if passedMatlNum=='None': passedMatlNum=None
    if gotoCommand=='None': gotoCommand=None

    # this is used often enough to have it as a baseline
    allCtSchdRecs = CountSchedule.objects.filter(org=_userorg)

    # if a record number was passed in, retrieve it
    # # later, handle record not found (i.e. - invalid recNum passed in)
    if recNum <= 0:
        currRec = allCtSchdRecs.none()
        # set Matl flds
        if passedMatlNum:
            matlRec = MaterialList.objects.get(Material=passedMatlNum)
        else:
            matlRec = MaterialList.objects.none()
    else:
        currRec = allCtSchdRecs.get(pk=recNum)
        matlRec = currRec.Material
    # endif
    MaterialID = getattr(matlRec, 'pk', None)
    
    prefixvals = {}
    prefixvals['main'] = 'sched'
    prefixvals['matl'] = 'matl'
    initialvals = {}
    initialvals['main'] = {'CountDate':datetime.date.fromisoformat(passedCountDate)}
    initialvals['matl'] = {}

    changes_saved = {
        'main': False,
        'matl': False,
        }
    chgd_dat = {
        'main':None, 
        'matl': None, 
        }

    if req.method == 'POST':
        # changed data is being submitted.  process and save it
        # process mainFm AND subforms.

        gotoCommand = None

        # process main form
        if currRec: mainFm = CountScheduleRecordForm(_userorg, req.POST, instance=currRec,  prefix=prefixvals['main'])
        else: mainFm = CountScheduleRecordForm(_userorg, req.POST, initial=initialvals['main'],  prefix=prefixvals['main']) 
        matlSubFm = RelatedMaterialInfo(_userorg, MaterialID, req.POST, instance=matlRec, prefix=prefixvals['matl'])

        s = CountSchedule.objects.none()

        if mainFm.is_valid() and matlSubFm.is_valid():
            if mainFm.has_changed():
                s = mainFm.save()
                chgd_dat['main'] = mainFm.changed_data
                changes_saved['main'] = s.id
            # material info subform
            if matlSubFm.has_changed():
                matlSubFm.save()
                chgd_dat['matl'] = matlSubFm.changed_data
                changes_saved['matl'] = True

            gotoCommand = "New"
        else:
            gotoCommand = "Invalid"

    # if this is a gotoCommand, get the correct record
    if gotoCommand=="First" or (gotoCommand=="Prev" and recNum <=0):
        currRec = allCtSchdRecs.order_by('id').first()
        if currRec: 
            recNum = currRec.id
            passedMatlNum = currRec.Material.Material
            matlRec = currRec.Material
            MaterialID = matlRec.id
        else: recNum = 0
    elif gotoCommand=="Prev":
        currRec = allCtSchdRecs.filter(pk__lt=recNum).order_by('id').last()
        if currRec: 
            recNum = currRec.id
            passedMatlNum = currRec.Material.Material
            matlRec = currRec.Material
            MaterialID = matlRec.id
        else: recNum = 0
    elif gotoCommand=="Next":
        currRec = allCtSchdRecs.filter(pk__gt=recNum).order_by('id').first()
        if currRec: 
            recNum = currRec.id
            passedMatlNum = currRec.Material.Material
            matlRec = currRec.Material
            MaterialID = matlRec.id
        else: recNum = 0
    elif gotoCommand=="Last":
        currRec = allCtSchdRecs.order_by('id').last()
        if currRec: 
            recNum = currRec.id
            passedMatlNum = currRec.Material.Material
            matlRec = currRec.Material
            MaterialID = matlRec.id
        else: recNum = 0
    elif gotoCommand=="Invalid":
        # this command occurs when a form (new or existing) is submitted, but it has errors
        # currRec is already set above
        if currRec: 
            recNum = currRec.id
            passedMatlNum = currRec.Material.Material
            matlRec = currRec.Material
            MaterialID = matlRec.id
        else: recNum = 0
    elif gotoCommand=="New":
        currRec = allCtSchdRecs.none()
        recNum=0
        passedMatlNum = None
        matlRec = getattr(currRec, 'Material', '')
        MaterialID = getattr(matlRec, 'pk', None)
    else:
        if currRec: 
            recNum = currRec.id
            passedMatlNum = currRec.Material.Material
            matlRec = currRec.Material
            MaterialID = matlRec.id
        else: 
            # recNum remains whatever was passed in (0 - else there would be a currRec)
            # passedMatlNum remains whatever was passed in
            # matlRec remains what was constructed above
            MaterialID = getattr(matlRec, 'pk', None)
    #endif

    # prep the forms for the template
    if gotoCommand != "Invalid":
        if currRec: 
            mainFm = CountScheduleRecordForm(_userorg, instance=currRec, prefix=prefixvals['main'])
        else:       
            mainFm = CountScheduleRecordForm(_userorg, initial=initialvals['main'],  prefix=prefixvals['main'])
        if matlRec:
            matlSubFm = RelatedMaterialInfo(_userorg, MaterialID, instance=matlRec, prefix=prefixvals['matl'])
        else:
            matlSubFm = RelatedMaterialInfo(_userorg, MaterialID, initial=initialvals['matl'], prefix=prefixvals['matl'])

    # CountEntryForm MaterialList dropdown
    matlchoiceForm = {}
    if currRec:
        matlchoiceForm['gotoItem'] = currRec
    else:
        if passedMatlNum==None: passedMatlNum = ''
        matlchoiceForm['gotoItem'] = {'Material':passedMatlNum}
    matlchoiceForm['choicelist'] = MaterialList.objects.filter(org=_userorg).values('id','Material')

    #finally, if this is a new rec, and a rec already exists for this CountDate and Material, the Material must be rejected
    msgDupSched = ''
    if (not currRec) and fnCountScheduleRecord(_userorg,passedCountDate,passedMatlNum):
        msgDupSched = 'A count for ' + str(passedMatlNum) + ' is already scheduled for ' + str(passedCountDate)
        passedMatlNum = None

    # display the form
    cntext = {'frmMain': mainFm,
            'frmMatl': matlSubFm,
            'matlchoiceForm':matlchoiceForm,
            "msgDupSched": msgDupSched,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            'recNum': recNum,
            'matlnum_changed': passedMatlNum,
            'MaterialID': MaterialID,
            'allCountSchedRecs': allCtSchdRecs.order_by('-CountDate', 'Material'),
            'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'frm_CountScheduleRec.html'
    return render(req, templt, cntext)

def fnCountScheduleRecord(org, CtDate, Matl):
    """
    used to check if a CountSchedule redcord exists for the given CtDate and Material
    (only one such record is allowed).
    If the record exists, it is the return value, else a None CountSchedule rec
    """
    if isinstance(Matl,MaterialList):
        MatObj = Matl 
    else:
        try:
            MatObj = MaterialList.objects.get(org=org,Material=Matl)
        except:
            MatObj = MaterialList.objects.none()

    try:
        rec = CountSchedule.objects.get(org=org, CountDate=CtDate, Material=MatObj)
    except:
        rec = CountSchedule.objects.none()

    return rec

#####################################################################
#####################################################################
#####################################################################

class CountScheduleListForm(ListView):
    ordering = ['-CountDate', 'Material']
    context_object_name = 'CtSchdList'
    template_name = 'frm_CountScheduleList.html'
    
    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self._user = req.user
        self._userorg = WICSuser.objects.get(user=req.user).org
        self.queryset = CountSchedule.objects.filter(org=self._userorg).order_by('-CountDate', 'Material')   # figure out how to pass in self.ordering
        return super().setup(req, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset()

    # def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    #     return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return HttpResponse('Stop rushing me!!')

    def render_to_response(self, context: Dict[str, Any], **response_kwargs: Any) -> HttpResponse:
        # I want to break here to see what's going on
        context.update({'orgname': self._userorg.orgname,  'uname':self._user.get_full_name()})
        return super().render_to_response(context, **response_kwargs)

