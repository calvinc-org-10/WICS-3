import time
import datetime
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django import forms
from django.db import models
from django.forms import inlineformset_factory, formset_factory
from django.shortcuts import render
from django.db.models import Value
from cMenu.models import getcParm
from WICS.models import MaterialList, ActualCounts, CountSchedule, SAPFiles, WhsePartTypes, Organizations
from WICS.SAPLists import fnSAPList
from userprofiles.models import WICSuser
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from django.db.models.query import EmptyQuerySet, QuerySet
from django.views.generic import ListView
from typing import Any, Dict


ExcelWorkbook_fileext = ".XLSX"
#_userorg = WICSuser.objects.none().org
_userorg = None


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


@login_required
def fnMaterialForm(req, formname, recNum = -1, gotoRec=False):
    _userorg = WICSuser.objects.get(user=req.user).org
    if not _userorg: raise Exception('User is corrupted!!')

    # get current record
    currRec = None
    if gotoRec:
        currRec = MaterialList.objects.filter(org=_userorg, Material=req.GET['gotoID']).first()
    if not currRec:
        if recNum <= 0:
            currRec = MaterialList.objects.filter(org=_userorg).first()
        else:
            currRec = MaterialList.objects.filter(org=_userorg).get(pk=recNum)   # later, handle record not found
        # endif
    #endif
    if not currRec: #there are no Material records for this org!!
        thisPK = 0
    else:
        thisPK = currRec.pk

    SAP_SOH = fnSAPList(_userorg, matl=currRec)

    gotoForm = {}
    gotoForm['gotoItem'] = currRec
    gotoForm['choicelist'] = MaterialList.objects.filter(org=_userorg).values('id','Material')

    changes_saved = {
        'main': False,
        'counts': False,
        'schedule': False
        }
    chgd_dat = {'main':None, 'counts': None, 'schedule': None}

    CountSubFormFields = ('id', 'CountDate', 'CycCtID', 'Counter', 'LocationOnly', 'CTD_QTY_Expr', 'BLDG', 'LOCATION', 'PKGID_Desc', 'TAGQTY', 'FLAG_PossiblyNotRecieved', 'FLAG_MovementDuringCount', 'Notes',)
    ScheduleSubFormFields = ('id','CountDate','Counter', 'Priority', 'ReasonScheduled', 'CMPrintFlag', 'Notes',)

    if req.method == 'POST':
        # changed data is being submitted.  process and save it
        # process mtlFm AND subforms.

        # process main form
        #if currRec:
        mtlFm = MaterialForm(req.POST, instance=currRec,  initial={'gotoItem': thisPK, 'showPK': thisPK, 'org':_userorg},  prefix='material')
        #else:
        #    mtlFm = MaterialForm(req.POST, initial={'gotoItem': thisPK, 'showPK': thisPK, 'org':_userorg},  prefix='material')
        #endif
        if mtlFm.is_valid():
            if mtlFm.has_changed():
                mtlFm.save()
                chgd_dat['main'] = mtlFm.changed_data
                changes_saved['main'] = True
                #raise Exception('main saved')

        # count detail subform
        countSubFm_class = inlineformset_factory(MaterialList,ActualCounts,
                    fields=CountSubFormFields,
                    extra=0,can_delete=False)
        #if currRec:
        countSet = countSubFm_class(req.POST, instance=currRec, prefix='countset', initial={'org': _userorg}, queryset=ActualCounts.objects.order_by('-CountDate'))
        #else:
        #    countSet = countSubFm_class(req.POST, prefix='countset', initial={'org': _userorg}, queryset=ActualCounts.objects.order_by('-CountDate'))
        if countSet.is_valid():
            if countSet.has_changed():
                countSet.save()
                chgd_dat['counts'] = countSet.changed_objects
                changes_saved['counts'] = True
                #raise Exception('counts saved')

        # count schedule subform
        SchedSubFm_class = inlineformset_factory(MaterialList,CountSchedule,
                    fields=ScheduleSubFormFields,
                    extra=0,can_delete=False)
        #if currRec:
        schedSet = SchedSubFm_class(req.POST, instance=currRec, prefix='schedset', initial={'org': _userorg}, queryset=CountSchedule.objects.order_by('-CountDate'))
        #else:
        #    schedSet = SchedSubFm_class(req.POST, prefix='schedset', initial={'org': _userorg}, queryset=CountSchedule.objects.order_by('-CountDate'))
        if schedSet.is_valid():
            if schedSet.has_changed():
                schedSet.save()
                chgd_dat['schedule'] = schedSet.changed_objects
                changes_saved['schedule'] = True
                #raise Exception('sched saved')

        # count summary form is r/o.  It will not be changed
    else: # request.method == 'GET' or something else
        #if currRec:
        mtlFm = MaterialForm(instance=currRec, initial={'gotoItem': thisPK, 'showPK': thisPK, 'org':_userorg}, prefix='material')
        #else:
        #    mtlFm = MaterialForm(initial={'gotoItem': thisPK, 'showPK': thisPK, 'org':_userorg}, prefix='material')

        CountSubFm_class = inlineformset_factory(MaterialList,ActualCounts,
                    fields=CountSubFormFields,
                    extra=0,can_delete=False)
        #if currRec:
        countSet = CountSubFm_class(instance=currRec, prefix='countset', initial={'org':_userorg}, queryset=ActualCounts.objects.order_by('-CountDate'))
        #else:
        #    countSet = CountSubFm_class(prefix='countset', initial={'org':_userorg}, queryset=ActualCounts.objects.order_by('-CountDate'))

        SchedSubFm_class = inlineformset_factory(MaterialList,CountSchedule,
                    fields=ScheduleSubFormFields,
                    extra=0,can_delete=False)
        #if currRec:
        schedSet = SchedSubFm_class(instance=currRec, prefix='schedset', initial={'org':_userorg}, queryset=CountSchedule.objects.order_by('-CountDate'))
        #else:
        #    schedSet = SchedSubFm_class(prefix='schedset', initial={'org':_userorg}, queryset=CountSchedule.objects.order_by('-CountDate'))
    # endif

    # count summary subform
    raw_countdata = ActualCounts.objects.filter(Material=currRec).order_by('Material','-CountDate').annotate(QtyEval=Value(0, output_field=models.IntegerField()))
    LastMaterial = None ; LastCountDate = None
    initdata = []
    for r in raw_countdata:
        try:
            r.QtyEval = eval(r.CTD_QTY_Expr)    # later, use ast.literal_eval
        # except (ValueError, SyntaxError):
        except:
            r.QtyEval = 0
        if (r.Material != LastMaterial or r.CountDate != LastCountDate):
            LastMaterial = r.Material ; LastCountDate = r.CountDate
            initdata.append({
                'Material': r.Material,
                'CountDate': r.CountDate,
                'CountQTY_Eval': 0,
            })
        n = initdata[-1]['CountQTY_Eval'] + r.QtyEval
        initdata[-1]['CountQTY_Eval'] = n
    subFm_class = formset_factory(MaterialCountSummary,extra=0)
    summarySet = subFm_class(initial=initdata, prefix='summaryset')

    #countSet['org'].is_hidden = True
    #schedSet['org'].is_hidden = True

    # display the form
    cntext = {'frmMain': mtlFm,
            'gotoForm': gotoForm,
            'countset': countSet,
            'scheduleset': schedSet,
            'countsummset': summarySet,
            'SAPSet': SAP_SOH,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            'recNum': recNum,
            'formID':formname, 'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'frm_Material.html'
    return render(req, templt, cntext)

#####################################################################################################
#####################################################################################################
#####################################################################################################

class UploadSAPForm(forms.ModelForm):
    class Meta:
        model = SAPFiles
        fields = ('org', 'uploaded_at', 'SAPFile', 'Notes', )

@login_required
def fnUploadSAP(req, formname):
    _userorg = WICSuser.objects.get(user=req.user).org

    if req.method == 'POST':
        form = UploadSAPForm(req.POST, req.FILES, initial={'org':_userorg})
        if form.is_valid():
            svdir = getcParm('SAP-FILELOC')
            instance = SAPFiles(SAPFile=req.FILES['SAPFile'])
            instance.org = _userorg
            instance.uploaded_at = req.POST['uploaded_at']
            # upload_to is handled by the model and django settings (MEDIA_ROOT)
            #instance.SAPFile.upload_to=svdir + "SAP" + str(time.ctime(time.time())).replace(":","-").strip() + ExcelWorkbook_fileext
            #instance.SAPFile.upload_to=svdir + "SAP/"
            instance.save()
            cntext = {'uploaded_at':instance.uploaded_at, 'filenm':instance.SAPFile.name, 'svdir':svdir,
                    'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
                    }
            templt = 'frm_upload_SAP_Success.html'
            return render(req, templt, cntext)
    else:
        form = UploadSAPForm(initial={'org':_userorg})
    #endif

    cntext = {'form': form, 
            'formID':formname, 'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'frm_upload_SAP.html'
    return render(req, templt, cntext)

#####################################################################################################
#####################################################################################################
#####################################################################################################


# do not use - this pulls down too many records
# class CountFormGoTo(forms.Form):
#     gotoItem = forms.ModelChoiceField(queryset=ActualCounts.objects.none(), required=False)


# between org and the way I present Material on the CountEntry form (<input type="list">/<datalist>),
# ModelForms want to do way too much in the verification and cleaning.  So I'm taking the 
# controls and growing CountEntryForm from a simple Form
class CountEntryForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    org = forms.CharField(widget=forms.HiddenInput,  required=False)
    #org = forms.ModelChoiceField(queryset=Organizations.objects.all(), widget=forms.HiddenInput,  required=False)
    CountDate = forms.DateField(required=True, initial=datetime.date.today())
    CycCtID = forms.CharField(required=False)
    Material = forms.CharField(required=True)
        # Material is handled this way because of the way it's done in the html.
        # later, create a DropdownText widget??
    Counter = forms.CharField(required=True)
    LocationOnly = forms.BooleanField(required=False)
    BLDG = forms.CharField(required=False)
    LOCATION = forms.CharField(required=False)
    CTD_QTY_Expr = forms.CharField(required=False)
    FLAG_PossiblyNotRecieved = forms.BooleanField(required=False)
    FLAG_MovementDuringCount = forms.BooleanField(required=False)
    PKGID_Desc = forms.CharField(required=False)
    TAGQTY = forms.CharField(required=False)
    Notes  = forms.CharField(required=False)
    class Meta:
        model = ActualCounts
        fields = ['id', 'CountDate', 'CycCtID', 'Counter', 'LocationOnly', 
                'BLDG', 'LOCATION', 'CTD_QTY_Expr', 'PKGID_Desc', 'TAGQTY',
                'FLAG_PossiblyNotRecieved', 'FLAG_MovementDuringCount', 'Notes']
    def save(self, in_org):
        if not self.is_valid():
            return None
        dbmodel = self.Meta.model
        required_fields = ['CountDate', 'Material', 'Counter'] #id, org handled separately
        PriK = self['id'].value()
        M = MaterialList.objects.get(org=in_org, Material=self.cleaned_data['Material']) 
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
        rec.org = in_org
        
        return rec.save()

class RelatedMaterialInfo(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    # org = forms.CharField(widget=forms.HiddenInput,  required=False)
    #org = forms.ModelChoiceField(queryset=Organizations.objects.all(), required=False, widget=forms.HiddenInput)
    Material = forms.CharField(required=False, widget=forms.HiddenInput)
    Description = forms.CharField(max_length=250, disabled=True, required=False)
    PartType = forms.ModelChoiceField(queryset=WhsePartTypes.objects.none(), empty_label=None, required=False)
    TypicalContainerQty = forms.IntegerField(required=False)
    TypicalPalletQty = forms.IntegerField(required=False)
    class Meta:
        model = MaterialList
        fields = ['id', 'Material', 'Description', 'PartType', 
                'TypicalContainerQty', 'TypicalPalletQty', 'Notes']
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['Material'].queryset=MaterialList.objects.filter(org=_userorg).all()
        self.fields['PartType'].queryset=WhsePartTypes.objects.filter(org=_userorg).all()
    def save(self, in_org):
        if not self.is_valid():
            return None
        dbmodel = self.Meta.model
        required_fields = [] #id, org handled separately
        PriK = self['id'].value()
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
        rec.org = in_org
        
        return rec.save()


class RelatedScheduleInfo(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    # org = forms.CharField(widget=forms.HiddenInput,  required=False)
    #org = forms.ModelChoiceField(queryset=Organizations.objects.all(), required=False, widget=forms.HiddenInput)
    CMPrintFlag = forms.BooleanField(disabled=True, required=False)
    CountDate = forms.DateField(disabled=True, required=False)
    # Material = forms.CharField(required=False, widget=forms.HiddenInput)
    # Material = forms.ModelChoiceField(MaterialList.objects.all(), required=False, widget=forms.HiddenInput)
    Counter = forms.CharField(max_length=250, disabled=True, required=False)
    Priority = forms.CharField(max_length=50, disabled=True, required=False)
    ReasonScheduled = forms.CharField(max_length=250, disabled=True, required=False)
    Notes = forms.CharField(max_length=250, disabled=True, required=False)
    class Meta:
        model = CountSchedule
        fields = ['id', 'CountDate', 'Material', 'Counter', 'Priority', 'ReasonScheduled', 
                'CMPrintFlag', 'Notes']
    def save(self, in_org):
        if not self.is_valid():
            return None
        dbmodel = self.Meta.model
        required_fields = ['CountDate', 'Material'] #id, org handled separately
        PriK = self['id'].value()
        M = MaterialList.objects.get(org=in_org, Material=self.cleaned_data['Material']) 
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
        rec.org = in_org
        
        return rec.save()


@login_required
def fnCountEntryForm(req, formname, recNum = 0, 
    loadMatlInfo = None, 
    passedCountDate=str(datetime.date.today()), 
    gotoCommand=None
    ):

    _userorg = WICSuser.objects.get(user=req.user).org

    # the string 'None' is not the same as the value None
    if loadMatlInfo=='None': loadMatlInfo=None
    if passedCountDate=='None': passedCountDate=None
    if passedCountDate==None: passedCountDate=str(datetime.date.today())
    if gotoCommand=='None': gotoCommand=None

    # if a record number was passed in, retrieve it
    # # later, handle record not found (i.e. - invalid recNum passed in)
    if recNum <= 0:
        currRec = ActualCounts.objects.filter(org=_userorg).none()
    else:
        currRec = ActualCounts.objects.filter(org=_userorg).get(pk=recNum)
    # endif
    
    prefixvals = {}
    prefixvals['main'] = 'counts'
    prefixvals['matl'] = 'matl'
    prefixvals['schedule'] = 'schedule'
    initialvals = {}
    initialvals['main'] = {'org':_userorg, 'CountDate':datetime.date.fromisoformat(passedCountDate)}
    initialvals['matl'] = {'org': _userorg}
    initialvals['schedule'] = {'org': _userorg, 'CountDate':datetime.date.fromisoformat(passedCountDate)}

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
        if currRec: mainFm = CountEntryForm(req.POST, instance=currRec,  prefix=prefixvals['main'])   # do I need to pass in intial?
        else: mainFm = CountEntryForm(req.POST, initial=initialvals['main'],  prefix=prefixvals['main']) 
        mainFm.fields['Material'].choices = MaterialList.objects.filter(org=_userorg).values('Material','id')

        if mainFm.is_valid():
            if mainFm.has_changed():
                mainFm.save(_userorg)
                chgd_dat['main'] = mainFm.changed_data
                changes_saved['main'] = True

            # prepare a new empty record for next entry
            gotoCommand = "New"
        else:
            gotoCommand = "Invalid"

        # material info subform
        matlSubFm = RelatedMaterialInfo(req.POST, prefix=prefixvals['matl'], initial=initialvals['matl'])
        if matlSubFm.is_valid():
            if matlSubFm.has_changed():
                matlSubFm.save(_userorg)
                chgd_dat['matl'] = matlSubFm.changed_data
                changes_saved['matl'] = True

        # count schedule subform
        #schedSet = RelatedScheduleInfo(req.POST, prefix=prefixvals['schedule'], initial=initialvals['schedule'])
        #if schedSet.is_valid():
        #    if schedSet.has_changed():
        #        schedSet.save(_userorg)
        #        chgd_dat['schedule'] = schedSet.changed_data
        #        changes_saved['schedule'] = True
    #endif req.method=='POST'

    # if this is a gotoCommand, get the correct record
    if gotoCommand=="First" or (gotoCommand=="Prev" and recNum <=0):
        currRec = ActualCounts.objects.filter(org=_userorg).order_by('id').first()
        if currRec: recNum = currRec.id
        else: recNum = 0
    elif gotoCommand=="Prev":
        currRec = ActualCounts.objects.filter(org=_userorg,pk__lt=recNum).order_by('id').last()
        if currRec: recNum = currRec.id
        else: recNum = 0
    elif gotoCommand=="Next":
        currRec = ActualCounts.objects.filter(org=_userorg,pk__gt=recNum).order_by('id').first()
        if currRec: recNum = currRec.id
        else: recNum = 0
    elif gotoCommand=="Last":
        currRec = ActualCounts.objects.filter(org=_userorg).order_by('id').last()
        if currRec: recNum = currRec.id
        else: recNum = 0
    elif gotoCommand=="Invalid":
        # this command occurs when a form (new or existing) is submitted, but it has errors
        # currRec is already set above
        if currRec: recNum = currRec.id
        else: recNum = 0
    elif gotoCommand=="New":
        currRec = ActualCounts.objects.filter(org=_userorg).none()
        loadMatlInfo = None
        recNum=0
    #endif

    # CLEAN ME UP CLEAN ME UP!!!!
    matlinfo = schedinfo = []
    # if there is a currRec by now, get matlInfo and schedinfo from it
    if currRec:
        matlinfo = currRec.Material
        getDate = currRec.CountDate
        if CountSchedule.objects.filter(org=_userorg, CountDate=getDate, Material=matlinfo).exists():
            schedinfo = CountSchedule.objects.filter(org=_userorg, CountDate=getDate, Material=matlinfo)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
        else:
            schedinfo = []
    # has the date or Material changed and we're looking for update Matl/Sched info?
    elif (loadMatlInfo!=None or passedCountDate!=None) and (gotoCommand==None):
        # review and clean up this block!
        if loadMatlInfo != None:
            # fill in MatlInfo and CountSchedInfo
            matlinfo = MaterialList.objects.get(org=_userorg, Material=loadMatlInfo)   # this better exist, else something is seriously wrong
            if recNum > 0: getDate = currRec.CountDate 
            else: getDate = passedCountDate
            if CountSchedule.objects.filter(org=_userorg, CountDate=getDate, Material=matlinfo).exists():
                schedinfo = CountSchedule.objects.filter(org=_userorg, CountDate=getDate, Material=matlinfo)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
            else:
                schedinfo = []
        elif recNum > 0:
            # ??????????? shouldn't this already be handled?  Think about it...
            # fill in MatlInfo and CountSchedInfo
            matlinfo = MaterialList.objects.get(org=_userorg, Material=currRec.Material)   # this better exist, else something is seriously wrong
            getDate = currRec.CountDate
            if CountSchedule.objects.filter(org=_userorg, CountDate=getDate, Material=matlinfo).exists():
                schedinfo = CountSchedule.objects.filter(org=_userorg, CountDate=getDate, Material=matlinfo)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
            else:
                schedinfo = []
        #endif

        # the rest of the processing is now a subcase of the gotoCommand logic
    
    # prep the forms for the template
    if gotoCommand != "Invalid":
        if currRec: mainFm = CountEntryForm(instance=currRec, prefix=prefixvals['main'])
        else:       mainFm = CountEntryForm(initial=initialvals['main'],  prefix=prefixvals['main'])
        mainFm.fields['Material'].choices = MaterialList.objects.filter(org=_userorg).values('Material') 

    if matlinfo==[]: 
        matlSubFm = RelatedMaterialInfo(initial=initialvals['matl'], prefix=prefixvals['matl']) 
        todayscounts = ActualCounts.objects.none()
    else: 
        matlSubFm = RelatedMaterialInfo(instance=matlinfo, prefix=prefixvals['matl'])
        todayscounts = ActualCounts.objects.filter(CountDate=passedCountDate,Material=matlinfo)
    #matlSubFm.fields['Material'].queryset=MaterialList.objects.filter(org=_userorg).all()
    matlSubFm.fields['PartType'].queryset=WhsePartTypes.objects.filter(org=_userorg).all()

    if schedinfo==[]: schedFm = RelatedScheduleInfo(initial=initialvals['schedule'], prefix=prefixvals['schedule'])
    else: schedFm = RelatedScheduleInfo(instance=schedinfo, prefix=prefixvals['schedule'])

    # CountEntryForm Material dropdown
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

###### OLD CountEntry fm #######################    
@login_required
def fnCountEntryForm_OLD(req, formname, recNum = -1, 
    loadMatlInfo = None, 
    passedCountDate=None, 
    gotoCommand=None
    ):

    _userorg = WICSuser.objects.get(user=req.user).org

    # the string 'None' is not the same as the value None
    if loadMatlInfo=='None': loadMatlInfo=None
    if passedCountDate=='None': passedCountDate=None
    if gotoCommand=='None': gotoCommand=None
    
    # later, handle record not found
    # get current record
    if recNum <= 0:
        currRec = ActualCounts.objects.filter(org=_userorg).none()
    else:
        currRec = ActualCounts.objects.filter(org=_userorg).get(pk=recNum)
    # endif
    # if this is a gotoCommand, get the correct record
    if gotoCommand=="First" or (gotoCommand=="Prev" and recNum <=0):
        currRec = ActualCounts.objects.filter(org=_userorg).first()
        if currRec: recNum = currRec.id
        else: recNum = -1
    elif gotoCommand=="Prev":
        currRec = ActualCounts.objects.filter(org=_userorg,pk__lt=recNum).first()
        if currRec: recNum = currRec.id
        else: recNum = -1
    elif gotoCommand=="Next":
        currRec = ActualCounts.objects.filter(org=_userorg,pk__gt=recNum).first()
        if currRec: recNum = currRec.id
        else: recNum = -1
    elif gotoCommand=="Last":
        currRec = ActualCounts.objects.filter(org=_userorg).last()
        if currRec: recNum = currRec.id
        else: recNum = -1
    elif gotoCommand=="New":
        currRec = ActualCounts.objects.filter(org=_userorg).none()
        recNum=-1
    #endif

    ##  too much, to be removed
    # gotoForm = CountFormGoTo({'gotoItem':currRec})
    # gotoForm.fields['gotoItem'].queryset=ActualCounts.objects.filter(org=_userorg)
    # gotoForm.fields['gotoItem'].queryset=ActualCounts.objects.none()

    changes_saved = {
        'main': False,
        'matl': False,
        'schedule': False
        }
    chgd_dat = {'main':None, 'matl': None, 'schedule': None}

    prepNewRec = (req.method != 'POST' and recNum <= 0)

    if req.method == 'POST':
        # changed data is being submitted.  process and save it
        # process mainFm AND subforms.

        # process main form
        mainFm = CountEntryForm(req.POST, initial={'org':_userorg, 'CountDate':datetime.date.today()},  prefix='counts') if isinstance(currRec, EmptyQuerySet) else CountEntryForm(req.POST, instance=currRec,  initial={'org':_userorg, 'CountDate':datetime.date.today()},  prefix='counts')
        if mainFm.is_valid():
            if mainFm.has_changed():
                mainFm.save()
                chgd_dat['main'] = mainFm.changed_data
                changes_saved['main'] = True
                #raise Exception('main saved')

                # prepare a new empty record for next entry
                prepNewRec = True

        ## making LIMITED changes in the subforms will come later ...
        # material info subform
        # matlSubFm = RelatedMaterialInfo(req.POST, prefix='matl', initial={'org': _userorg})
        # if matlSubFm.is_valid():
        #     if matlSubFm.has_changed():
        #         matlSubFm.save()
        #         chgd_dat['matl'] = matlSubFm.changed_objects
        #         changes_saved['matl'] = True
        #         #raise Exception('matl saved')

        # count schedule subform
        # SchedSubFm_class = inlineformset_factory(MaterialList,CountSchedule,
        #             fields=('id', 'CountDate','Counter', 'Priority', 'ReasonScheduled', 'CMPrintFlag', 'Notes',),
        #             extra=0,can_delete=False)
        # schedSet = SchedSubFm_class(req.POST, instance=currRec, prefix='schedset', initial={'org': _userorg})
        # if schedSet.is_valid():
        #     if schedSet.has_changed():
        #         schedSet.save()
        #         chgd_dat['schedule'] = schedSet.changed_objects
        #         changes_saved['schedule'] = True
        #         #raise Exception('sched saved')
    #endif

    if prepNewRec: # request.method == 'GET' or something else, or last record was valid and saved
        if currRec: mainFm = CountEntryForm(instance=currRec, initial={'org':_userorg, 'CountDate':datetime.date.today()},  prefix='counts')
        else:       mainFm = CountEntryForm(initial={'org':_userorg, 'CountDate':datetime.date.today()},  prefix='counts') 
    else:
        mainFm = CountEntryForm(instance=currRec, initial={'org':_userorg},  prefix='counts')
    # endif

    # review and clean up this block!
    if loadMatlInfo != None:
        # fill in MatlInfo and CountSchedInfo
        matlinfo = MaterialList.objects.get(Material=loadMatlInfo)   # this better exist, else something is seriously wrong
        getDate = currRec.CountDate if recNum > 0 else passedCountDate
        getID = currRec.Material_id if recNum > 0 else loadMatlInfo
        try:
            schedinfo = CountSchedule.objects.filter(org=_userorg, CountDate=getDate, Material=matlinfo)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
        except (CountSchedule.DoesNotExist, IndexError):
            schedinfo = []
    elif recNum > 0:
        # ???????????
        # fill in MatlInfo and CountSchedInfo
        matlinfo = MaterialList.objects.get(Material=currRec.Material)   # this better exist, else something is seriously wrong
        getDate = currRec.CountDate if recNum > 0 else passedCountDate
        getID = currRec.Material_id if recNum > 0 else loadMatlInfo
        try:
            schedinfo = CountSchedule.objects.filter(org=_userorg, CountDate=getDate, Material=matlinfo)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
        except (CountSchedule.DoesNotExist, IndexError):
            schedinfo = []
    else:
        matlinfo = []
        schedinfo = []
    #endif

    # load dropdowns
    # CountEntryForm Material
    matlchoiceForm = {}
    if currRec:
        matlchoiceForm['gotoItem'] =currRec
    else:
        if loadMatlInfo==None: loadMatlInfo = ''
        matlchoiceForm['gotoItem'] = {'Material':loadMatlInfo}
    matlchoiceForm['choicelist'] = MaterialList.objects.filter(org=_userorg).values('id','Material')


    matlSubFm = RelatedMaterialInfo() if matlinfo==[] else RelatedMaterialInfo(instance=matlinfo)
    matlSubFm.fields['Material'].queryset=MaterialList.objects.filter(org=_userorg).all()
    matlSubFm.fields['PartType'].queryset=WhsePartTypes.objects.filter(org=_userorg).all()

    schedFm = RelatedScheduleInfo() if schedinfo==[] else RelatedScheduleInfo(instance=schedinfo)

    # display the form
    cntext = {'frmMain': mainFm,
            'frmMatlInfo': matlSubFm,
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

#####################################################################
#####################################################################
#####################################################################

class CountScheduleForm(ListView):
    ordering = ['-CountDate', 'Material']
    context_object_name = 'CtSchdList'
    template_name = 'frm_CountScheduleList.html'
    
    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
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
        return super().render_to_response(context, **response_kwargs)


