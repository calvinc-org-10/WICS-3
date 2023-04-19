from django.db import models
# from django.db.models import Value

# Create your models here.
# I'm quite happy with automaintained pk fields, so I don't specify any

class Organizations(models.Model):
    orgname = models.CharField(max_length=250)

    class Meta:
        ordering = ['orgname']

    def __str__(self) -> str:
        return self.orgname.__str__()
        # return super().__str__()


def org_queryset(modl: models.Model, org: Organizations) -> models.QuerySet:
    if hasattr(modl, 'org'):
        return modl.objects.filter(org=org)
    else:
        return modl.objects.none()

class WhsePartTypes(models.Model):
    org = models.ForeignKey(Organizations, on_delete=models.CASCADE, blank=True, editable=False)
    WhsePartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()
    InactivePartType = models.BooleanField(blank=True, default=False)

    class Meta:
        ordering = ['org','WhsePartType']
        constraints = [
                models.UniqueConstraint('org', 'WhsePartType', name='PTypeUNQ_org_PType'),
                models.UniqueConstraint('org', 'PartTypePriority', name='PTypeUNQ_org_PTypePrio'),
            ]

    def __str__(self) -> str:
        return self.WhsePartType.__str__()
        # return super().__str__()


class MaterialList(models.Model):
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT, blank=True)
    Material = models.CharField(max_length=100)
    Description = models.CharField(max_length=250, blank=True)
    PartType = models.ForeignKey(WhsePartTypes, null=True, on_delete=models.RESTRICT)
    SAPMaterialType = models.CharField(max_length=100, blank=True)
    SAPMaterialGroup = models.CharField(max_length=100, blank=True)
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True)
    TypicalContainerQty = models.IntegerField(null=True, blank=True)
    TypicalPalletQty = models.IntegerField(null=True, blank=True)
    Notes = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ['org','Material']
        constraints = [
                models.UniqueConstraint(fields=['org', 'Material'],name="wics_materiallist_realpk"),
            ]
        indexes = [
            models.Index(fields=['PartType']),
        ]
        

    def __str__(self) -> str:
        return self.Material.__str__()
        # return super().__str__()
class tmpMaterialListUpdate(models.Model):
    Material = models.CharField(primary_key=True, max_length=100, blank=False)
    Description = models.CharField(max_length=250, blank=True)
    SAPMaterialType = models.CharField(max_length=100, blank=True)
    SAPMaterialGroup = models.CharField(max_length=100, blank=True)
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True)


class CountSchedule(models.Model):
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT, blank=True)
    CountDate = models.DateField(null=False)
    Material = models.ForeignKey(MaterialList, on_delete=models.RESTRICT)
    Counter = models.CharField(max_length=250, blank=True)
    Priority = models.CharField(max_length=50, blank=True)
    ReasonScheduled = models.CharField(max_length=250, blank=True)
    CMPrintFlag = models.BooleanField(blank=True, default=False)
    Notes = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ['org','CountDate', 'Material']
        constraints = [
                models.UniqueConstraint(fields=['org', 'CountDate', 'Material'], name="wics_countschedule_realpk"),
            ]
        indexes = [
            models.Index(fields=['org','CountDate','Material']),
            models.Index(fields=['org','Material']),
            models.Index(fields=['org','CountDate']),
        ]

        
    def __str__(self) -> str:
        return str(self.pk) + ": " + str(self.CountDate) + " / " + str(self.Material) + " / " + str(self.Counter)
        # return super().__str__()


class ActualCounts(models.Model):
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT, blank=False)
    CountDate = models.DateField(null=False)
    CycCtID = models.CharField(max_length=100, blank=True)
    Material = models.ForeignKey(MaterialList, on_delete=models.RESTRICT)
    Counter = models.CharField(max_length=250, blank=False, null=False)
    LocationOnly = models.BooleanField(blank=True, default=False)
    CTD_QTY_Expr = models.CharField(max_length=500, blank=True)
    BLDG = models.CharField(max_length=100, blank=True)
    LOCATION = models.CharField(max_length=250, blank=True)
    PKGID_Desc = models.CharField(max_length=250, blank=True)
    TAGQTY = models.CharField(max_length=250, blank=True)
    FLAG_PossiblyNotRecieved = models.BooleanField(blank=True, default=False)
    FLAG_MovementDuringCount = models.BooleanField(blank=True, default=False)
    Notes = models.CharField(max_length = 250, blank=True)

    class Meta:
        ordering = ['org', 'CountDate', 'Material']
        indexes = [
            models.Index(fields=['org','CountDate','Material']),
            models.Index(fields=['org','Material']),
            models.Index(fields=['org','BLDG','LOCATION']),
        ]

    def __str__(self) -> str:
        return str(self.pk) + ": " + str(self.CountDate) + " / " + str(self.Material) + " / " + str(self.Counter) + " / " + str(self.BLDG) + "_" + str(self.LOCATION)
        # return super().__str__()

def LastFoundAt(matl):
    try:
        lastCountDate = ActualCounts.objects.filter(Material=matl).latest('CountDate').CountDate
    except:
        lastCountDate = None
    LFAString = ''
    LFAList = []
    if lastCountDate:
        countrecs = ActualCounts.objects.filter(Material=matl,CountDate=lastCountDate)\
                    .order_by('BLDG','LOCATION')\
                    .values('BLDG','LOCATION')\
                    .distinct()
        for rec in countrecs:
            if LFAString: LFAString += ', '
            LFAString += rec['BLDG'] + '_' + rec['LOCATION']
            LFAList.append({'BLDG':rec['BLDG'],'LOCATION':rec['LOCATION']})
    
    return {'lastCountDate': lastCountDate, 'lastFoundAt': LFAString, 'lastFoundAt_list': LFAList}

def FoundAt(matl):
    # get Dict of all dates this material counted
    FA_qs =  ActualCounts.objects.filter(Material=matl)\
                .order_by('-CountDate')\
                .values('CountDate')\
                .distinct()
    FADict = {rec['CountDate']: '' for rec in FA_qs}

    # get found locations by date, and tie to each dict entry
    countrecs = ActualCounts.objects.filter(Material=matl)\
                .order_by('-CountDate','BLDG','LOCATION')\
                .values('CountDate','BLDG','LOCATION')\
                .distinct()
    for rec in countrecs:
        LFAString = FADict[rec['CountDate']]
        if LFAString: LFAString += ', '
        LFAString += rec['BLDG'] + '_' + rec['LOCATION']
        FADict[rec['CountDate']] = LFAString

    # convert it back to the type of dictionary produced by the QS (easier for caller to work with)
    FA_qs = [{'CountDate': k, 'FoundAt': v} for (k,v) in FADict.items()]
    
    return FA_qs


class SAP_SOHRecs(models.Model):
    uploaded_at = models.DateField()
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT, blank=True)
    Material = models.CharField(max_length=100)
    Description = models.CharField(max_length=250, blank=True)
    Plant = models.CharField(max_length=20, blank=True)
    MaterialType = models.CharField(max_length=50, blank=True)
    StorageLocation = models.CharField(max_length=20, blank=True)
    BaseUnitofMeasure = models.CharField(max_length=20, blank=True)
    Amount = models.FloatField(blank=True)
    Currency = models.CharField(max_length=20, blank=True)
    ValueUnrestricted = models.FloatField(blank=True)
    SpecialStock = models.CharField(max_length=20, blank=True)
    Batch = models.CharField(max_length=20, blank=True)

    class Meta:
        get_latest_by = 'uploaded_at'
        ordering = ['uploaded_at', 'org', 'Material']
        indexes = [
            models.Index(fields=['uploaded_at', 'org', 'Material']),
        ]

class UnitsOfMeasure(models.Model):
    UOM = models.CharField(max_length=50, unique=True)
    UOMText = models.CharField(max_length=100, blank=True, default='')
    DimensionText = models.CharField(max_length=100, blank=True, default='')
    Multiplier1 = models.FloatField(default=1.0)


class WorksheetZones(models.Model):
    zone = models.IntegerField(primary_key=True)
    zoneName = models.CharField(max_length=10,blank=True)


class Location_WorksheetZone(models.Model):
    location = models.CharField(max_length=50,blank=False)
    zone = models.ForeignKey('WorksheetZones', on_delete=models.RESTRICT)



class WICSPermissions(models.Model):
    class Meta:
        managed = False  # No database table creation or deletion  \
                         # operations will be performed for this model. 
        default_permissions = () # disable "add", "change", "delete"
                                 # and "view" default permissions
        permissions = [ 
            ('Material_onlyview', 'For restricting Material Form to view only'),  
        ]

        
############################################################
#####  These are implemented as VIEWS in the database 
############################################################
############################################################
############################################################
#####  SQL definitions in WICS VIEWS.sql
############################################################

class VIEW_materials(models.Model):
    id = models.IntegerField(primary_key=True)
    Material = models.CharField(max_length=100, blank=True, default='')
    Description = models.CharField(max_length=250, blank=True, default='')
    SAPMaterialType = models.CharField(max_length=100, blank=True, default='')
    SAPMaterialGroup = models.CharField(max_length=100, blank=True, default='')
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True)
    TypicalContainerQty = models.IntegerField(null=True, blank=True)
    TypicalPalletQty = models.IntegerField(null=True, blank=True)
    Notes = models.CharField(max_length=250, blank=True, default='')
    PartType_id = models.IntegerField()
    PartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()
    org_id = models.IntegerField()
    OrgName = models.CharField(max_length=250)

    class Meta:
        db_table = 'VIEW_materials'
        managed = False

############################################

class VIEW_SAP(models.Model):
    id = models.IntegerField(primary_key=True)
    uploaded_at = models.DateField
    Material = models.CharField(max_length=100)
    Material_id = models.IntegerField()
    Plant = models.CharField(max_length=20)
    StorageLocation = models.CharField(max_length=20)
    BaseUnitofMeasure = models.CharField(max_length=20)
    Amount = models.FloatField()
    Currency = models.CharField(max_length=20)
    ValueUnrestricted = models.FloatField(blank=True)
    UOM = models.CharField(max_length=50)
    UOMText = models.CharField(max_length=100)
    DimensionText = models.CharField(max_length=100)
    mult = models.FloatField()
    SpecialStock = models.CharField(max_length=20)
    Batch = models.CharField(max_length=20)
    Description = models.CharField(max_length=250, blank=True, default='')
    SAPMaterialType = models.CharField(max_length=100, blank=True, default='')
    SAPMaterialGroup = models.CharField(max_length=100, blank=True, default='')
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True)
    TypicalContainerQty = models.IntegerField(null=True, blank=True)
    TypicalPalletQty = models.IntegerField(null=True, blank=True)
    Notes = models.CharField(max_length=250, blank=True, default='')
    PartType_id = models.IntegerField()
    PartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()
    org_id = models.IntegerField()
    OrgName = models.CharField(max_length=250)

    class Meta:
        db_table = 'VIEW_SAP'
        managed = False

 
class VIEW_actualcounts(models.Model):
    id = models.IntegerField(primary_key=True)
    CountDate = models.DateField()
    Material_id = models.IntegerField()
    Material = models.CharField(max_length=100)
    CycCtID = models.CharField(max_length=100)
    Counter = models.CharField(max_length=250)
    LocationOnly = models.CharField(max_length=100, blank=True, default='')
    CTD_QTY_Expr = models.CharField(max_length=500)
    BLDG = models.CharField(max_length=100)
    LOCATION = models.CharField(max_length=250)
    FLAG_PossiblyNotRecieved = models.BooleanField()
    FLAG_MovementDuringCount = models.BooleanField()
    CountNotes = models.CharField(max_length=250)
    Description = models.CharField(max_length=250, blank=True, default='')
    SAPMaterialType = models.CharField(max_length=100, blank=True, default='')
    SAPMaterialGroup = models.CharField(max_length=100, blank=True, default='')
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True)
    TypicalContainerQty = models.IntegerField(null=True, blank=True)
    TypicalPalletQty = models.IntegerField(null=True, blank=True)
    MaterialNotes = models.CharField(max_length=250, blank=True, default='')
    PartType_id = models.IntegerField()
    PartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()
    org_id = models.IntegerField()
    OrgName = models.CharField(max_length=250)

    class Meta:
        db_table = 'VIEW_actualcounts'
        managed = False
    
   
class VIEW_countschedule(models.Model):
    id = models.IntegerField(primary_key=True)
    CountDate = models.DateField()
    Material_id = models.IntegerField()
    Material = models.CharField(max_length=100)
    Counter = models.CharField(max_length=250)
    Priority = models.CharField(max_length=50)
    ReasonScheduled = models.CharField(max_length=250)
    CMPrintFlag = models.BooleanField()
    ScheduleNotes = models.CharField(max_length=250)
    Description = models.CharField(max_length=250, blank=True, default='')
    SAPMaterialType = models.CharField(max_length=100, blank=True, default='')
    SAPMaterialGroup = models.CharField(max_length=100, blank=True, default='')
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True)
    TypicalContainerQty = models.IntegerField(null=True, blank=True)
    TypicalPalletQty = models.IntegerField(null=True, blank=True)
    MaterialNotes = models.CharField(max_length=250, blank=True, default='')
    PartType_id = models.IntegerField()
    PartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()
    org_id = models.IntegerField()
    OrgName = models.CharField(max_length=250)

    class Meta:
        db_table = 'VIEW_countschedule'
        managed = False
    

class VIEW_FoundAt(models.Model):
    org_id = models.IntegerField()
    OrgName = models.CharField(max_length=100)
    Material_id = models.IntegerField()
    Material = models.CharField(max_length=100)
    CountDate = models.DateField()
    FoundAt = models.CharField(max_length=1024)

    class Meta:
        db_table = 'VIEW_FoundAt'
        managed = False


class VIEW_LastFoundAt(models.Model):
    org_id = models.IntegerField()
    OrgName = models.CharField(max_length=250)
    Material_id = models.IntegerField()
    Material = models.CharField(max_length=100)
    CountDate = models.DateField()
    FoundAt = models.CharField(max_length=1024)

    class Meta:
        db_table = 'VIEW_LastFoundAt'
        managed = False


class VIEW_LastFoundAtList(models.Model):
    org_id = models.IntegerField()
    OrgName = models.CharField(max_length=100)
    Material_id = models.IntegerField()
    Material = models.CharField(max_length=100)
    CountDate = models.DateField()
    BLDG = models.CharField(max_length=100)
    LOCATION = models.CharField(max_length=250)
    FoundAt = models.CharField(max_length=1024)

    class Meta:
        db_table = 'VIEW_LastFoundAtList'
        managed = False

   
class VIEW_LastSAP(models.Model):
    id = models.IntegerField(primary_key=True)
    uploaded_at = models.DateField
    Material = models.CharField(max_length=100)
    Material_id = models.IntegerField()
    Plant = models.CharField(max_length=20)
    StorageLocation = models.CharField(max_length=20)
    BaseUnitofMeasure = models.CharField(max_length=20)
    Amount = models.FloatField()
    Currency = models.CharField(max_length=20)
    ValueUnrestricted = models.FloatField(blank=True)
    UOM = models.CharField(max_length=50)
    UOMText = models.CharField(max_length=100)
    DimensionText = models.CharField(max_length=100)
    mult = models.FloatField()
    SpecialStock = models.CharField(max_length=20)
    Batch = models.CharField(max_length=20)
    Description = models.CharField(max_length=250, blank=True, default='')
    SAPMaterialType = models.CharField(max_length=100, blank=True, default='')
    SAPMaterialGroup = models.CharField(max_length=100, blank=True, default='')
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True)
    TypicalContainerQty = models.IntegerField(null=True, blank=True)
    TypicalPalletQty = models.IntegerField(null=True, blank=True)
    Notes = models.CharField(max_length=250, blank=True, default='')
    PartType_id = models.IntegerField()
    PartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()
    org_id = models.IntegerField()
    OrgName = models.CharField(max_length=250)

    class Meta:
        db_table = 'VIEW_LastSAP'
        managed = False

 
class VIEW_MaterialLocationListWithLastSAP(models.Model):
    id = models.IntegerField(primary_key=True)
    org_id = models.IntegerField()
    Material = models.CharField(max_length=100, blank=True, default='')
    Description = models.CharField(max_length=250, blank=True, default='')
    SAPMaterialType = models.CharField(max_length=100, blank=True, default='')
    SAPMaterialGroup = models.CharField(max_length=100, blank=True, default='')
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True)
    TypicalContainerQty = models.IntegerField(null=True, blank=True)
    TypicalPalletQty = models.IntegerField(null=True, blank=True)
    Notes = models.CharField(max_length=250, blank=True, default='')
    PartType_id = models.IntegerField()
    PartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()
    OrgName = models.CharField(max_length=250)
    CountDate = models.DateField()
    FoundAt = models.CharField(max_length=1024)
    SAP_id = models.IntegerField()
    SAPDate = models.DateField()
    Plant = models.CharField(max_length=20)
    StorageLocation = models.CharField(max_length=20)
    Amount = models.FloatField()
    BaseUnitofMeasure = models.CharField(max_length=20)
    Currency = models.CharField(max_length=20)
    ValueUnrestricted = models.FloatField(blank=True)
    UOM = models.CharField(max_length=50)
    UOMText = models.CharField(max_length=100)
    DimensionText = models.CharField(max_length=100)
    mult = models.FloatField()
    SpecialStock = models.CharField(max_length=20)
    Batch = models.CharField(max_length=20)
    DoNotShow = models.BooleanField()

    class Meta:
        db_table = 'VIEW_MaterialLocationListWithLastSAP'
        managed = False


