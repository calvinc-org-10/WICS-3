# import datetime
from django import forms
from cMenu.utils import calvindate
from WICS.models import MaterialList, ActualCounts, CountSchedule, WhsePartTypes
from WICS.procs_misc import HolidayList


class CountEntryForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    CountDate = forms.DateField(required=True, initial=calvindate().today().as_datetime())
    CycCtID = forms.CharField(required=False)
    Material = forms.CharField(required=True)
        # Material is handled this way because of the way it's done in the html.
        # later, create a DropdownText widget??
    Counter = forms.CharField(required=True)
    LocationOnly = forms.BooleanField(required=False)
    LOCATION = forms.CharField(required=True)
    CTD_QTY_Expr = forms.CharField(required=False)
    FLAG_PossiblyNotRecieved = forms.BooleanField(required=False)
    FLAG_MovementDuringCount = forms.BooleanField(required=False)
    PKGID_Desc = forms.CharField(required=False)
    TAGQTY = forms.CharField(required=False)
    Notes  = forms.CharField(required=False)
    class Meta:
        model = ActualCounts
        fields = ['id', 'CountDate', 'CycCtID', 'Counter', 'LocationOnly', 
                'LOCATION', 'CTD_QTY_Expr', 'PKGID_Desc', 'TAGQTY',
                'FLAG_PossiblyNotRecieved', 'FLAG_MovementDuringCount', 'Notes']
    def save(self):
        if not self.is_valid():
            return None
        dbmodel = self.Meta.model
        required_fields = ['CountDate', 'Material', 'Counter'] #id handled separately
        PriK = self['id'].value()
        M = MaterialList.objects.get(pk=self.data['MatlPK']) 
        if not str(PriK).isnumeric(): PriK = -1
        existingrec = dbmodel.objects.filter(pk=PriK).exists()
        if existingrec: rec = dbmodel.objects.get(pk=PriK)
        else:   rec = dbmodel()
        for fldnm in self.changed_data + required_fields:
            if fldnm=='id': continue
            if fldnm=='Material':
                setattr(rec,fldnm, M)
            else:
                setattr(rec, fldnm, self.cleaned_data[fldnm])
        
        rec.save()
        return rec


class CountScheduleRecordForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    CountDate = forms.DateField(required=True, 
        initial=calvindate().nextWorkdayAfter(extraNonWorkdayList=HolidayList()).as_datetime()
        )
    Material = forms.CharField(required=True)
        # Material is handled this way because of the way it's done in the html.
        # later, create a DropdownText widget??
    Counter = forms.CharField(required=False)
    Priority = forms.CharField(max_length=50, required=False)
    ReasonScheduled = forms.CharField(max_length=250, required=False)
    Requestor = forms.CharField(max_length=100, required=False)
    RequestFilled = forms.BooleanField(required=False, initial=False)
    Notes  = forms.CharField(required=False)

    class Meta:
        model = CountSchedule
        fields = ['id', 'CountDate', 'Counter', 'Priority', 'ReasonScheduled', 'Requestor', 'RequestFilled', 'Notes']
    def save(self):
        if not self.is_valid():
            return None
        dbmodel = self.Meta.model
        required_fields = ['CountDate', 'Material'] #id handled separately
        PriK = self['id'].value()
        M = MaterialList.objects.get(pk=self.data['MatlPK']) 
        if not str(PriK).isnumeric(): PriK = -1
        existingrec = dbmodel.objects.filter(pk=PriK).exists()
        if existingrec: rec = dbmodel.objects.get(pk=PriK)
        else: rec = dbmodel()
        for fldnm in self.changed_data + required_fields:
            if fldnm=='id': continue
            elif fldnm=='Material':
                setattr(rec,fldnm, M)
            else:
                setattr(rec, fldnm, self.cleaned_data[fldnm])
        
        rec.save()
        return rec

class RequestCountScheduleRecordForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    CountDate = forms.DateField(required=True, 
        initial=calvindate().nextWorkdayAfter(extraNonWorkdayList=HolidayList()).as_datetime()
        )
    Requestor = forms.CharField(max_length=100, required=True)
      # the requestor can type whatever they want here, but WICS will record the userid behind-the-scenes
    RequestFilled = forms.BooleanField(required=False, initial=False)
    Material = forms.CharField(required=True)
        # Material is handled this way because of the way it's done in the html.
        # later, create a DropdownText widget??
    Counter = forms.CharField(required=False)
    Priority = forms.CharField(max_length=50, required=False)
    ReasonScheduled = forms.CharField(max_length=250, required=False)
    Notes  = forms.CharField(required=False)

    class Meta:
        model = CountSchedule
        fields = ['id', 'CountDate', 'Requestor', 'Counter', 'Priority', 'ReasonScheduled', 'Notes']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def save(self, savingUser) -> CountSchedule:
        if not self.is_valid():
            return None
        dbmodel = self.Meta.model
        required_fields = ['CountDate', 'Material', 'Requestor'] #id handled separately
        PriK = self['id'].value()
        M = MaterialList.objects.get(pk=self.data['MatlPK']) 
        if not str(PriK).isnumeric(): PriK = -1
        existingrec = dbmodel.objects.filter(pk=PriK).exists()
        if existingrec: rec = dbmodel.objects.get(pk=PriK)
        else: rec = dbmodel()
        for fldnm in self.changed_data + required_fields:
            if fldnm=='id': continue
            elif fldnm=='Material':
                setattr(rec,fldnm, M)
            else:
                setattr(rec, fldnm, self.cleaned_data[fldnm])
        rec.Requestor_userid = savingUser
        
        rec.save()
        return rec


################################
################################

class RelatedMaterialInfo(forms.ModelForm):
    Description = forms.CharField(max_length=250, disabled=True, required=False)
    PartType = forms.ModelChoiceField(queryset=WhsePartTypes.objects.none(), empty_label=None, required=False)
    TypicalContainerQty = forms.CharField(max_length=100,required=False)
    TypicalPalletQty = forms.CharField(max_length=100,required=False)
    Notes = forms.CharField(required=False)
    class Meta:
        model = MaterialList
        fields = ['id', 'Description', 'PartType', 
                'TypicalContainerQty', 'TypicalPalletQty', 'Notes']
    def __init__(self, id, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.id = id
        self.fields['PartType'].queryset=WhsePartTypes.objects.all().order_by('WhsePartType').all()
    def save(self):
        if not self.is_valid():
            return None
        dbmodel = self.Meta.model
        required_fields = [] #id handled separately
        PriK = self.id
        if not str(PriK).isnumeric(): PriK = -1
        existingrec = dbmodel.objects.filter(pk=PriK).exists()
        if existingrec: rec = dbmodel.objects.get(pk=PriK)
        else:  raise Exception('Saving Related Material with no PK')  # rec = dbmodel()
        for fldnm in self.changed_data + required_fields:
            if fldnm=='id': continue
            if fldnm=='Material':
                # no special processing - Material is a string here, not a ForeignField
                setattr(rec, fldnm, self.cleaned_data[fldnm])
            else:
                setattr(rec, fldnm, self.cleaned_data[fldnm])
        
        rec.save()
        return rec


class RelatedScheduleInfo(forms.ModelForm):
    CountDate = forms.DateField(disabled=True, required=False)
    Counter = forms.CharField(max_length=250, disabled=True, required=False)
    Priority = forms.CharField(max_length=50, disabled=True, required=False)
    ReasonScheduled = forms.CharField(max_length=250, disabled=True, required=False)
    Notes = forms.CharField(max_length=250, disabled=True, required=False)
    class Meta:
        model = CountSchedule
        fields = ['id', 'CountDate', 'Counter', 'Priority', 'ReasonScheduled', 
                'Notes']
    def __init__(self, id, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.id = id
    def save(self):
        if not self.is_valid():
            return None
        dbmodel = self.Meta.model
        required_fields = ['CountDate', 'Material'] #id handled separately
        PriK = self.id
        M = MaterialList.objects.get(pk=self.data['MatlPK']) 
        if not str(PriK).isnumeric(): PriK = -1
        existingrec = dbmodel.objects.filter(pk=PriK).exists()
        if existingrec: rec = dbmodel.objects.get(pk=PriK)
        else:  raise Exception('Saving Related Schedule Info with no PK')   # rec = dbmodel()
        for fldnm in self.changed_data + required_fields:
            if fldnm=='id': continue
            if fldnm=='Material':
                setattr(rec,fldnm, M)
            else:
                setattr(rec, fldnm, self.cleaned_data[fldnm])
        
        rec.save()
        return rec

############################################################
############################################################
############################################################

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

############################################################
############################################################
############################################################

class PartTypesForm(forms.ModelForm):
    class Meta:
        model = WhsePartTypes
        fields = ['WhsePartType', 'PartTypePriority', 'InactivePartType']
#MatlSubFm_fldlist = ['id','org','Material', 'Description', 'PartType', 'Price', 'PriceUnit', 'TypicalContainerQty', 'TypicalPalletQty', 'Notes']
