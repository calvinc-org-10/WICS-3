import time, datetime
import os, uuid
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.urls import reverse
from django import forms
from django.shortcuts import render
from cMenu.models import getcParm
from cMenu.utils import makebool
from userprofiles.models import WICSuser
#from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from openpyxl import load_workbook
from userprofiles.models import WICSuser
from WICS.models import ActualCounts, MaterialList, CountSchedule, WhsePartTypes
import datetime


# do not use - this pulls down too many records
# class CountFormGoTo(forms.Form):
#     gotoItem = forms.ModelChoiceField(queryset=ActualCounts.objects.none(), required=False)

# between org and the way I present Material on the CountEntry form (<input type="list">/<datalist>),
# ModelForms want to do way too much in the verification and cleaning.  So I'm taking the 
# controls and growing CountEntryForm from a simple Form
class CountEntryForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    CountDate = forms.DateField(required=True, initial=datetime.date.today())
    CycCtID = forms.CharField(required=False)
    Material = forms.CharField(required=True)
        # Material is handled this way because of the way it's done in the html.
        # later, create a DropdownText widget??
    Counter = forms.CharField(required=True)
    LocationOnly = forms.BooleanField(required=False)
    BLDG = forms.CharField(required=True)
    LOCATION = forms.CharField(required=False)
    CTD_QTY_Expr = forms.CharField(required=False)
    FLAG_PossiblyNotRecieved = forms.BooleanField(required=False)
    FLAG_MovementDuringCount = forms.BooleanField(required=False)
    PKGID_Desc = forms.CharField(required=False)
    TAGQTY = forms.CharField(required=False)
    Notes  = forms.CharField(required=False)
    class Meta:
        model = ActualCounts
        fields = ['CountDate', 'CycCtID', 'Counter', 'LocationOnly', 
                'BLDG', 'LOCATION', 'CTD_QTY_Expr', 'PKGID_Desc', 'TAGQTY',
                'FLAG_PossiblyNotRecieved', 'FLAG_MovementDuringCount', 'Notes']
    def __init__(self, org, *args, **kwargs):
        self.org = org
        super().__init__(*args, **kwargs)
    def save(self):
        if not self.is_valid():
            return None
        dbmodel = self.Meta.model
        required_fields = ['CountDate', 'Material', 'Counter'] #id, org handled separately
        PriK = self['id'].value()
        M = MaterialList.objects.get(org=self.org, Material=self.cleaned_data['Material']) 
        if not str(PriK).isnumeric(): PriK = -1
        existingrec = dbmodel.objects.filter(pk=PriK).exists()
        if existingrec: rec = dbmodel.objects.get(pk=PriK)
        else:   rec = dbmodel()
        for fldnm in self.changed_data + required_fields:
            if fldnm=='id' or fldnm=='org': continue
            if fldnm=='Material':
                setattr(rec,fldnm, M)
            else:
                setattr(rec, fldnm, self.cleaned_data[fldnm])
        rec.org = self.org
        
        rec.save()
        return rec

class RelatedMaterialInfo(forms.ModelForm):
    Description = forms.CharField(max_length=250, disabled=True, required=False)
    PartType = forms.ModelChoiceField(queryset=WhsePartTypes.objects.none(), empty_label=None, required=False)
    TypicalContainerQty = forms.IntegerField(required=False)
    TypicalPalletQty = forms.IntegerField(required=False)
    Notes = forms.CharField(required=False)
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


class RelatedScheduleInfo(forms.ModelForm):
    CountDate = forms.DateField(disabled=True, required=False)
    Counter = forms.CharField(max_length=250, disabled=True, required=False)
    Priority = forms.CharField(max_length=50, disabled=True, required=False)
    ReasonScheduled = forms.CharField(max_length=250, disabled=True, required=False)
    CMPrintFlag = forms.BooleanField(disabled=True, required=False)
    Notes = forms.CharField(max_length=250, disabled=True, required=False)
    class Meta:
        model = CountSchedule
        fields = ['CountDate', 'Counter', 'Priority', 'ReasonScheduled', 
                'CMPrintFlag', 'Notes']
    def __init__(self, org, id, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.id = id
        self.org = org
    def save(self):
        if not self.is_valid():
            return None
        dbmodel = self.Meta.model
        required_fields = ['CountDate', 'Material'] #id, org handled separately
        PriK = self.id
        M = MaterialList.objects.get(org=self.org, Material=self.cleaned_data['Material']) 
        if not str(PriK).isnumeric(): PriK = -1
        existingrec = dbmodel.objects.filter(pk=PriK).exists()
        if existingrec: rec = dbmodel.objects.get(pk=PriK)
        else:  raise Exception('Saving Related Schedule Info with no PK')   # rec = dbmodel()
        for fldnm in self.changed_data + required_fields:
            if fldnm=='id' or fldnm=='org': continue
            if fldnm=='Material':
                setattr(rec,fldnm, M)
            else:
                setattr(rec, fldnm, self.cleaned_data[fldnm])
        rec.org = self.org
        
        rec.save()
        return rec


@login_required
def fnCountEntryForm(req, formname, recNum = 0, 
    loadMatlInfo = None, 
    passedCountDate=str(datetime.date.today()), 
    gotoCommand=None
    ):

    _userorg = WICSuser.objects.get(user=req.user).org

    # the string 'None' is not the same as the value None
    if loadMatlInfo=='None': loadMatlInfo=None
    if gotoCommand=='None': gotoCommand=None

    # if a record number was passed in, retrieve it
    # # later, handle record not found (i.e. - invalid recNum passed in)
    if recNum <= 0:
        currRec = ActualCounts.objects.filter(org=_userorg).none()
        if loadMatlInfo:
            matlRec = MaterialList.objects.get(Material=loadMatlInfo)
        else:
            matlRec = MaterialList.objects.none()
    else:
        currRec = ActualCounts.objects.filter(org=_userorg).get(pk=recNum)
        matlRec = currRec.Material
    # endif
    MaterialID = getattr(matlRec, 'pk', None)
    
    prefixvals = {}
    prefixvals['main'] = 'counts'
    prefixvals['matl'] = 'matl'
    prefixvals['schedule'] = 'schedule'
    initialvals = {}
    initialvals['main'] = {'CountDate':datetime.date.fromisoformat(passedCountDate)}
    initialvals['matl'] = {}
    initialvals['schedule'] = {'CountDate':datetime.date.fromisoformat(passedCountDate)}

    changes_saved = {
        'main': False,
        'matl': False,
        'schedule': False
        }
    chgd_dat = {
        'main':None, 
        'matl': None, 
        'schedule': None
        }

    if req.method == 'POST':
        # changed data is being submitted.  process and save it
        # process mainFm AND subforms.

        gotoCommand = None

        # process main form
        if currRec: mainFm = CountEntryForm(_userorg, req.POST, instance=currRec,  prefix=prefixvals['main'])   # do I need to pass in intial?
        else: mainFm = CountEntryForm(_userorg, req.POST, initial=initialvals['main'],  prefix=prefixvals['main']) 
        matlSubFm = RelatedMaterialInfo(_userorg, MaterialID, req.POST, instance=s.Material, prefix=prefixvals['matl'])
        #schedSet = RelatedScheduleInfo(_userorg, SchedID, req.POST, prefix=prefixvals['schedule'], initial=initialvals['schedule'])

        s = ActualCounts.objects.none()

        # if mainFm.is_valid() and matlSubFm.is_valid() and schedFm.is_valid():
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
            # count schedule subform
            # if schedSet.has_changed():
            #      schedSet.save()
            #      chgd_dat['schedule'] = schedSet.changed_data
            #      changes_saved['schedule'] = True

            gotoCommand = "New"
        else:
            gotoCommand = "Invalid"

    #endif req.method=='POST'

    # if this is a gotoCommand, get the correct record
    if gotoCommand=="First" or (gotoCommand=="Prev" and recNum <=0):
        currRec = ActualCounts.objects.filter(org=_userorg).order_by('id').first()
        if currRec: 
            recNum = currRec.id
            loadMatlInfo = currRec.Material.Material
            matlRec = currRec.Material
            MaterialID = matlRec.id
        else: recNum = 0
    elif gotoCommand=="Prev":
        currRec = ActualCounts.objects.filter(org=_userorg,pk__lt=recNum).order_by('id').last()
        if currRec: 
            recNum = currRec.id
            loadMatlInfo = currRec.Material.Material
            matlRec = currRec.Material
            MaterialID = matlRec.id
        else: recNum = 0
    elif gotoCommand=="Next":
        currRec = ActualCounts.objects.filter(org=_userorg,pk__gt=recNum).order_by('id').first()
        if currRec: 
            recNum = currRec.id
            loadMatlInfo = currRec.Material.Material
            matlRec = currRec.Material
            MaterialID = matlRec.id
        else: recNum = 0
    elif gotoCommand=="Last":
        currRec = ActualCounts.objects.filter(org=_userorg).order_by('id').last()
        if currRec: 
            recNum = currRec.id
            loadMatlInfo = currRec.Material.Material
            matlRec = currRec.Material
            MaterialID = matlRec.id
        else: recNum = 0
    elif gotoCommand=="Invalid":
        # this command occurs when a form (new or existing) is submitted, but it has errors
        # currRec is already set above
        if currRec: 
            recNum = currRec.id
            loadMatlInfo = currRec.Material.Material
            matlRec = currRec.Material
            MaterialID = matlRec.id
        else: recNum = 0
    elif gotoCommand=="New":
        currRec = ActualCounts.objects.filter(org=_userorg).none()
        recNum=0
        loadMatlInfo = None
        matlRec = getattr(currRec,'Material', '')
        MaterialID = getattr(matlRec, 'pk', None)
    else:
        if currRec:
            recNum = currRec.id
            loadMatlInfo = currRec.Material.Material
            matlRec = currRec.Material
            MaterialID = matlRec.id
        else:
            # recNum remains whatever was passed in (0 - else there would be a currRec)
            # passedMatlNum remains whatever was passed in
            # matlRec remains what was constructed above
            MaterialID = getattr(matlRec, 'pk', None)
    #endif

    # prep the forms for the template
    # mainFm and matlSubFm
    if gotoCommand != "Invalid":
        if currRec: 
            mainFm = CountEntryForm(_userorg, instance=currRec, prefix=prefixvals['main'])
        else:       
            mainFm = CountEntryForm(_userorg, initial=initialvals['main'],  prefix=prefixvals['main'])
        if matlRec:
            matlSubFm = RelatedMaterialInfo(_userorg, MaterialID, instance=matlRec, prefix=prefixvals['matl'])
        else:
            matlSubFm = RelatedMaterialInfo(_userorg, MaterialID, initial=initialvals['matl'], prefix=prefixvals['matl'])
    # all counts for this Material today
    if matlRec: 
        todayscounts = ActualCounts.objects.filter(CountDate=passedCountDate,Material=matlRec)
    else: 
        todayscounts = ActualCounts.objects.none()
    # schedFm
    if currRec:
        getDate = currRec.CountDate
        if CountSchedule.objects.filter(org=_userorg, CountDate=getDate, Material=matlRec).exists():
            schedinfo = CountSchedule.objects.filter(org=_userorg, CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
        else:
            schedinfo = CountSchedule.objects.none()
    elif (loadMatlInfo!=None) and (gotoCommand==None):
        # review and clean up this block!
        if loadMatlInfo != None:
            # fill in MatlInfo and CountSchedInfo
            if recNum > 0: getDate = currRec.CountDate 
            else: getDate = passedCountDate
            if CountSchedule.objects.filter(org=_userorg, CountDate=getDate, Material=matlRec).exists():
                schedinfo = CountSchedule.objects.filter(org=_userorg, CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
            else:
                schedinfo = CountSchedule.objects.none()
        elif recNum > 0:
            # ??????????? shouldn't this already be handled?  Think about it...
            # fill in MatlInfo and CountSchedInfo
            getDate = currRec.CountDate
            if CountSchedule.objects.filter(org=_userorg, CountDate=getDate, Material=matlRec).exists():
                schedinfo = CountSchedule.objects.filter(org=_userorg, CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
            else:
                schedinfo = CountSchedule.objects.none()
    else: schedinfo = CountSchedule.objects.none()
    if not schedinfo: schedFm = RelatedScheduleInfo(_userorg, None, initial=initialvals['schedule'], prefix=prefixvals['schedule'])
    else: schedFm = RelatedScheduleInfo(_userorg, schedinfo.pk, instance=schedinfo, prefix=prefixvals['schedule'])

    # CountEntryForm MaterialList dropdown
    matlchoiceForm = {}
    if currRec:
        matlchoiceForm['gotoItem'] = currRec
    else:
        if loadMatlInfo==None: loadMatlInfo = ''
        matlchoiceForm['gotoItem'] = {'Material':loadMatlInfo}
    matlchoiceForm['choicelist'] = MaterialList.objects.filter(org=_userorg).values('id','Material')

    # display the form
    cntext = {'frmMain': mainFm,
            'frmMatlInfo': matlSubFm,
            'todayscounts': todayscounts,
            'matlchoiceForm':matlchoiceForm,
            'noSchedInfo':(schedinfo==[]),
            'frmSchedInfo': schedFm,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            'recNum': recNum,
            'matlnum_changed': loadMatlInfo,
            'formID':formname, 'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'frm_CountEntry.html'
    return render(req, templt, cntext)

##############################################################
##############################################################
##############################################################

@login_required
def fnUploadActCountSprsht(req):
    _userorg = WICSuser.objects.get(user=req.user).org

    if req.method == 'POST':
        # save the file so we can open it as an excel file
        SAPFile = req.FILES['CEFile']
        svdir = getcParm('SAP-FILELOC')
        fName = svdir+"tmpCE"+str(uuid.uuid4())+".xlsx"
        with open(fName, "wb") as destination:
            for chunk in SAPFile.chunks():
                destination.write(chunk)

        wb = load_workbook(filename=fName, read_only=True)
        ws = wb.active

        # I map Table Fields directly to spreadsheet columns because it's MY spreadsxheet and 
        # I have defin ed the format.  If that changes, see fnUpdateMatlListfromSAP in SAPMatlUpdt.py
        # for an alternative way of handling this mapping
        SAPcolmnMap = {
                    'CountDate': 0,
                    'Counter': 1,
                    'BLDG': 2,
                    'LOCATION': 3,
                    'Material': 4,
                    'LocationOnly': 5,
                    'CTD_QTY_Expr': 6,
                    'TypicalContainerQty': 7,
                    'TypicalPalletQty': 8,
                    'Notes':9,
                    }
        
        UplResults = []
        nRows = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            try:
                MatObj = MaterialList.objects.get(org=_userorg, Material=row[SAPcolmnMap['Material']])
            except:
                MatObj = None

            if MatObj:
                MatChanged = False
                SRec = ActualCounts(org = _userorg)
                for fldName, colNum in SAPcolmnMap.items():
                    V = row[colNum]
                    if V==None: V = ''

                    if   fldName == 'CountDate': setattr(SRec, fldName, V)
                    elif fldName == 'Counter': setattr(SRec, fldName, V)
                    elif fldName == 'BLDG': 
                        # later, make sure BLDG not blank
                        setattr(SRec, fldName, V)
                    elif fldName == 'LOCATION': setattr(SRec, fldName, V)
                    elif fldName == 'Material': setattr(SRec, fldName, MatObj)
                    elif fldName == 'LocationOnly': setattr(SRec, fldName, makebool(V))
                    elif fldName == 'CTD_QTY_Expr': setattr(SRec, fldName, V)
                    elif fldName == 'Notes': setattr(SRec, fldName, V)
                    elif fldName == 'TypicalContainerQty' \
                      or fldName == 'TypicalPalletQty':
                        if V == '' or V == None: V = 0
                        if V != getattr(MatObj,fldName,0): 
                            setattr(MatObj, fldName, V)
                            MatChanged = True
                    
                SRec.save()
                if MatChanged: MatObj.save()
                qs = type(SRec).objects.filter(pk=SRec.pk).values().first()
                res = {'error': False, 'TypicalQty':MatChanged}
                res.update(qs)
                ## why am I doing this this way????
                #for V in type(SRec).objects.filter(pk=SRec.pk).values().first():
                #    res = res.append(V)
                UplResults.append(res)
                nRows += 1
            else:
                if row[SAPcolmnMap['Material']]:
                    UplResults.append({'error':row[SAPcolmnMap['Material']]+' does not exist in MaterialList'})
                else:
                    UplResults.append({'error':'invalid row with no Material given'})

        # close and kill temp files
        wb.close()
        os.remove(fName)

        cntext = {'UplResults':UplResults, 'nRowsAdded':nRows,
                'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
                }
        templt = 'frm_uploadCountEntry_Success.html'
    else:
        cntext = {'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
                }
        templt = 'frm_UploadCountEntrySprdsht.html'
    #endif

    return render(req, templt, cntext)

