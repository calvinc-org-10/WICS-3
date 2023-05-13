# import datetime
from django import forms
from cMenu.utils import calvindate
from WICS.models import MaterialList, ActualCounts, CountSchedule, WhsePartTypes
from WICS.procs_misc import HolidayList
from userprofiles.models import WICSuser


class CountEntryForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    CountDate = forms.DateField(required=True, initial=calvindate().today().as_datetime())
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
        fields = ['id', 'CountDate', 'CycCtID', 'Counter', 'LocationOnly', 
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
        # PriK = self.data['RecPK']
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


class CountScheduleRecordForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    CountDate = forms.DateField(required=True, 
        initial=calvindate().nextWorkdayAfter(extraNonWorkdayList=HolidayList()).as_datetime
        )
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
        fields = ['id', 'CountDate', 'Counter', 'Priority', 'ReasonScheduled', 'CMPrintFlag', 'Notes']
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


class RequestCountScheduleRecordForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    CountDate = forms.DateField(required=True, 
        initial=calvindate().nextWorkdayAfter(extraNonWorkdayList=HolidayList()).as_datetime
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
    CMPrintFlag = forms.BooleanField(required=False, initial=False)
    Notes  = forms.CharField(required=False)

    class Meta:
        model = CountSchedule
        fields = ['id', 'CountDate', 'Requestor', 'RequestFilled', 'Counter', 'Priority', 'ReasonScheduled', 'CMPrintFlag', 'Notes']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def save(self, savingUser: WICSuser) -> CountSchedule:
        if not self.is_valid():
            return None
        dbmodel = self.Meta.model
        required_fields = ['CountDate', 'Material', 'Requestor'] #id, org handled separately
        PriK = self['id'].value()
        M = MaterialList.objects.get(org=savingUser.org, Material=self.cleaned_data['Material']) 
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
        rec.org = savingUser.org
        rec.Requestor_userid = savingUser
        
        rec.save()
        return rec

# class RequestCountScheduleListForm(forms.ModelForm):
#     """
#         This form is used (at least now) so that MaterialList is not loaded for each record.
#         For now, Material will be r/o
#     """
#     id = forms.IntegerField(required=False, widget=forms.HiddenInput)
#     CountDate = forms.DateField(required=True, 
#         initial=calvindate().nextWorkdayAfter(extraNonWorkdayList=HolidayList()).as_datetime
#         )
#     Requestor = forms.CharField(max_length=100, required=True)
#       # the requestor can type whatever they want here, but WICS will record the userid behind-the-scenes
#     RequestFilled = forms.BooleanField(required=False, initial=False)
#     Material = forms.CharField(max_length=100, disabled=True)
#         # Material is handled this way because of the way it's done in the html.
#         # later, create a DropdownText widget??
#     Counter = forms.CharField(required=False)
#     Priority = forms.CharField(max_length=50, required=False)
#     ReasonScheduled = forms.CharField(max_length=250, required=False)
#     CMPrintFlag = forms.BooleanField(required=False, initial=False)
#     Notes  = forms.CharField(required=False)

#     class Meta:
#         model = CountSchedule
#         fields = ['id', 'CountDate', 'Requestor', 'RequestFilled', 'Counter', 'Priority', 'ReasonScheduled', 'CMPrintFlag', 'Notes']
#     # def __init__(self, *args, **kwargs):
#     #     super().__init__(*args, **kwargs)
#     # def save(self, savingUser: WICSuser) -> CountSchedule:
#     #     if not self.is_valid():
#     #         return None
#     #     dbmodel = self.Meta.model
#     #     required_fields = ['CountDate', 'Material', 'Requestor'] #id, org handled separately
#     #     PriK = self['id'].value()
#     #     M = MaterialList.objects.get(org=savingUser.org, Material=self.cleaned_data['Material']) 
#     #     if not str(PriK).isnumeric(): PriK = -1
#     #     existingrec = dbmodel.objects.filter(pk=PriK).exists()
#     #     if existingrec: rec = dbmodel.objects.get(pk=PriK)
#     #     else: rec = dbmodel()
#     #     for fldnm in self.changed_data + required_fields:
#     #         if fldnm=='id' or fldnm=='org': continue
#     #         elif fldnm=='Material':
#     #             setattr(rec,fldnm, M)
#     #         else:
#     #             setattr(rec, fldnm, self.cleaned_data[fldnm])
#     #     rec.org = savingUser.org
#     #     rec.Requestor_userid = savingUser
        
#     #     rec.save()
#     #     return rec

################################
################################

class RelatedMaterialInfo(forms.ModelForm):
    Description = forms.CharField(max_length=250, disabled=True, required=False)
    PartType = forms.ModelChoiceField(queryset=WhsePartTypes.objects.none(), empty_label=None, required=False)
    TypicalContainerQty = forms.IntegerField(required=False)
    TypicalPalletQty = forms.IntegerField(required=False)
    Notes = forms.CharField(required=False)
    class Meta:
        model = MaterialList
        fields = ['id', 'Description', 'PartType', 
                'TypicalContainerQty', 'TypicalPalletQty', 'Notes']
    def __init__(self, org, id, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.id = id
        self.org = org
        self.fields['PartType'].queryset=WhsePartTypes.objects.filter(org=org).order_by('WhsePartType').all()
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
        fields = ['id', 'CountDate', 'Counter', 'Priority', 'ReasonScheduled', 
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
