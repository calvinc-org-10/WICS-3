from django.db import models
from userprofiles.models import WICSuser        


# I'm quite happy with automaintained pk fields, so I don't specify any

class Organizations(models.Model):
    orgname = models.CharField(max_length=250)

    class Meta:
        ordering = ['orgname']

    def __str__(self) -> str:
        return str(self.orgname)
        # return super().__str__()


class WhsePartTypes(models.Model):
    WhsePartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()
    InactivePartType = models.BooleanField(blank=True, default=False)

    class Meta:
        ordering = ['WhsePartType']
        constraints = [
                models.UniqueConstraint(fields=['WhsePartType'], name='PTypeUNQ_PType'),
                models.UniqueConstraint(fields=['PartTypePriority'], name='PTypeUNQ_PTypePrio'),
            ]

    def __str__(self) -> str:
        return self.WhsePartType.__str__()
        # return super().__str__()


class MaterialList(models.Model):
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT, blank=True)
    Material = models.CharField(max_length=100)
    Description = models.CharField(max_length=250, blank=True, default='')
    PartType = models.ForeignKey(WhsePartTypes, null=True, on_delete=models.RESTRICT, default=None)
    Plant = models.CharField(max_length=20, blank=True, default='')
    SAPMaterialType = models.CharField(max_length=100, blank=True, default='')
    SAPMaterialGroup = models.CharField(max_length=100, blank=True, default='')
    Price = models.FloatField(null=True, blank=True, default=0.0)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True, default=1)
    Currency = models.CharField(max_length=20, blank=True, default='')
    TypicalContainerQty = models.CharField(max_length=100, null=True, blank=True, default=None)
    TypicalPalletQty = models.CharField(max_length=100, null=True, blank=True, default=None)
    Notes = models.CharField(max_length=250, blank=True, default='')

    class Meta:
        ordering = ['org','Material']
        constraints = [
                models.UniqueConstraint(fields=['org', 'Material'],name="wics_materiallist_realpk"),
            ]
        indexes = [
            models.Index(fields=['Material']),
        ]

    def __str__(self) -> str:
        if MaterialList.objects.filter(Material=self.Material).exclude(org=self.org).exists():
            # there is a Material with this number in another org; specify this org
            return str(self.Material) + ' (' + str(self.org) + ')'
        else:
            return str(self.Material)
class tmpMaterialListUpdate(models.Model):
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT, blank=True, null=True)
    Material = models.CharField(max_length=100, blank=False)
    MaterialLink = models.ForeignKey(MaterialList, on_delete=models.RESTRICT, blank=True, null=True)
    Description = models.CharField(max_length=250, blank=True)
    Plant = models.CharField(max_length=20, blank=True, default='')
    SAPMaterialType = models.CharField(max_length=100, blank=True)
    SAPMaterialGroup = models.CharField(max_length=100, blank=True)
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True)
    Currency = models.CharField(max_length=20, blank=True)


class CountSchedule(models.Model):
    CountDate = models.DateField(null=False)
    Material = models.ForeignKey(MaterialList, on_delete=models.RESTRICT)
    Requestor = models.CharField(max_length=100, null=True, blank=True)     
      # the requestor can type whatever they want here, but WICS will record the userid behind-the-scenes
    Requestor_userid = models.ForeignKey(WICSuser, on_delete=models.SET_NULL, null=True)
    RequestFilled = models.BooleanField(null=True, default=0)
    Counter = models.CharField(max_length=250, blank=True)
    Priority = models.CharField(max_length=50, blank=True)
    ReasonScheduled = models.CharField(max_length=250, blank=True)
    Notes = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ['CountDate', 'Material']
        constraints = [
                models.UniqueConstraint(fields=['CountDate', 'Material'], name="wics_countschedule_realpk"),
            ]
        indexes = [
            models.Index(fields=['Material']),
            models.Index(fields=['CountDate']),
        ]

    def __str__(self) -> str:
        return str(self.pk) + ": " + str(self.CountDate) + " / " + str(self.Material) + " / " + str(self.Counter)
        # return super().__str__()


class ActualCounts(models.Model):
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
        ordering = ['CountDate', 'Material']
        indexes = [
            models.Index(fields=['CountDate','Material']),
            models.Index(fields=['Material']),
            models.Index(fields=['BLDG','LOCATION']),
        ]

    def __str__(self) -> str:
        return str(self.pk) + ": " + str(self.CountDate) + " / " + str(self.Material) + " / " + str(self.Counter) + " / " + str(self.BLDG) + "_" + str(self.LOCATION)
        # return super().__str__()


def LastFoundAt(matl):
    lastCountDate = None
    LFAString = ''
    LFAqs = VIEW_LastFoundAt.objects.filter(Material_id=matl.id)

    if LFAqs: 
        lastCountDate = LFAqs[0].CountDate
        LFAString = LFAqs[0].FoundAt
    
    return {'lastCountDate': lastCountDate, 'lastFoundAt': LFAString,}

def FoundAt(matl):
    # get Dict of all dates this material counted
    FA_qs =  VIEW_FoundAt.objects.filter(Material_id=matl.id)\
                .order_by('-CountDate')
    
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
    Blocked = models.FloatField(blank=True, null=True)
    ValueBlocked = models.FloatField(blank=True, null=True)
    Batch = models.CharField(max_length=20, blank=True, null=True)
    Vendor = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        get_latest_by = 'uploaded_at'
        ordering = ['uploaded_at', 'org', 'Material']
        indexes = [
            models.Index(fields=['uploaded_at', 'org', 'Material']),
            models.Index(fields=['Plant']),
        ]

class SAPPlants_org(models.Model):
    SAPPlant = models.CharField(max_length=20, primary_key=True)
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT, blank=False)
    
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
    org_id = models.IntegerField()
    Material = models.CharField(max_length=100, blank=True, default='')
    Description = models.CharField(max_length=250, blank=True, default='')
    Plant = models.CharField(max_length=20, blank=True, default='')
    SAPMaterialType = models.CharField(max_length=100, blank=True, default='')
    SAPMaterialGroup = models.CharField(max_length=100, blank=True, default='')
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True)
    Currency = models.CharField(max_length=20, blank=True, default='')
    TypicalContainerQty = models.CharField(max_length=100,null=True, blank=True)
    TypicalPalletQty = models.CharField(max_length=100,null=True, blank=True)
    Notes = models.CharField(max_length=250, blank=True, default='')
    PartType_id = models.IntegerField()
    PartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()
    OrgName = models.CharField(max_length=250)
    Material_org = models.CharField(max_length=512)

    class Meta:
        db_table = 'VIEW_materials'
        managed = False

############################################

class VIEW_SAP(models.Model):
    id = models.IntegerField(primary_key=True)
    uploaded_at = models.DateField()
    Material_id = models.IntegerField()
    Material = models.CharField(max_length=100)
    Material_org = models.CharField(max_length=200)
    Plant = models.CharField(max_length=20)
    StorageLocation = models.CharField(max_length=20)
    BaseUnitofMeasure = models.CharField(max_length=20)
    Amount = models.FloatField()
    Currency = models.CharField(max_length=20)
    ValueUnrestricted = models.FloatField(blank=True)
    BlockedAmount = models.FloatField(blank=True)
    ValueBlocked = models.FloatField(blank=True)
    UOM = models.CharField(max_length=50)
    UOMText = models.CharField(max_length=100)
    DimensionText = models.CharField(max_length=100)
    mult = models.FloatField()
    SpecialStock = models.CharField(max_length=20)
    Batch = models.CharField(max_length=20)
    Vendor = models.CharField(max_length=20, blank=True)
    Description = models.CharField(max_length=250, blank=True, default='')
    SAPMaterialType = models.CharField(max_length=100, blank=True, default='')
    SAPMaterialGroup = models.CharField(max_length=100, blank=True, default='')
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True)
    TypicalContainerQty = models.CharField(max_length=100,null=True, blank=True)
    TypicalPalletQty = models.CharField(max_length=100,null=True, blank=True)
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
    Material = models.CharField(max_length=100)
    Material_id = models.IntegerField()
    Material_org = models.CharField(max_length=200)
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
    TypicalContainerQty = models.CharField(max_length=100,null=True, blank=True)
    TypicalPalletQty = models.CharField(max_length=100,null=True, blank=True)
    MaterialNotes = models.CharField(max_length=250, blank=True, default='')
    PartType_id = models.IntegerField()
    PartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()

    class Meta:
        db_table = 'VIEW_actualcounts'
        managed = False
    
   
class VIEW_countschedule(models.Model):
    id = models.IntegerField(primary_key=True)
    CountDate = models.DateField()
    Material_id = models.IntegerField()
    Material = models.CharField(max_length=100)
    Material_org = models.CharField(max_length=200)
    Requestor = models.CharField(max_length=100)
      # the requestor can type whatever they want here, but WICS will record the userid behind-the-scenes
    Requestor_userid_id = models.IntegerField()
    RequestFilled = models.BooleanField()
    Counter = models.CharField(max_length=250)
    Priority = models.CharField(max_length=50)
    ReasonScheduled = models.CharField(max_length=250)
    ScheduleNotes = models.CharField(max_length=250)
    Description = models.CharField(max_length=250, blank=True, default='')
    SAPMaterialType = models.CharField(max_length=100, blank=True, default='')
    SAPMaterialGroup = models.CharField(max_length=100, blank=True, default='')
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True)
    TypicalContainerQty = models.CharField(max_length=100,null=True, blank=True)
    TypicalPalletQty = models.CharField(max_length=100,null=True, blank=True)
    MaterialNotes = models.CharField(max_length=250, blank=True, default='')
    PartType_id = models.IntegerField()
    PartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()

    class Meta:
        db_table = 'VIEW_countschedule'
        managed = False
    

class VIEW_FoundAt(models.Model):
    Material_id = models.IntegerField()
    Material = models.CharField(max_length=100)
    Material_org = models.CharField(max_length=200)
    CountDate = models.DateField()
    FoundAt = models.CharField(max_length=1024)

    class Meta:
        db_table = 'VIEW_FoundAt'
        managed = False


class VIEW_LastFoundAt(models.Model):
    Material_id = models.IntegerField()
    Material = models.CharField(max_length=100)
    Material_org = models.CharField(max_length=200)
    CountDate = models.DateField()
    FoundAt = models.CharField(max_length=1024)

    class Meta:
        db_table = 'VIEW_LastFoundAt'
        managed = False


class VIEW_LastFoundAtList(models.Model):
    Material_id = models.IntegerField()
    Material = models.CharField(max_length=100)
    Material_org = models.CharField(max_length=200)
    CountDate = models.DateField()
    BLDG = models.CharField(max_length=100)
    LOCATION = models.CharField(max_length=250)
    FoundAt = models.CharField(max_length=1024)

    class Meta:
        db_table = 'VIEW_LastFoundAtList'
        managed = False

   
class VIEW_LastSAP(models.Model):
    id = models.IntegerField(primary_key=True)
    uploaded_at = models.DateField()
    org_id = models.IntegerField()
    Material_id = models.IntegerField()
    Material = models.CharField(max_length=100)
    Material_org = models.CharField(max_length=200)
    Plant = models.CharField(max_length=20)
    StorageLocation = models.CharField(max_length=20)
    BaseUnitofMeasure = models.CharField(max_length=20)
    Amount = models.FloatField()
    Currency = models.CharField(max_length=20)
    ValueUnrestricted = models.FloatField(blank=True)
    BlockedAmount = models.FloatField(blank=True)
    ValueBlocked = models.FloatField(blank=True)
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
    TypicalContainerQty = models.CharField(max_length=100,null=True, blank=True)
    TypicalPalletQty = models.CharField(max_length=100,null=True, blank=True)
    Notes = models.CharField(max_length=250, blank=True, default='')
    PartType_id = models.IntegerField()
    PartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()
    OrgName = models.CharField(max_length=250)

    class Meta:
        db_table = 'VIEW_LastSAP'
        managed = False

 
class VIEW_MaterialLocationListWithSAP(models.Model):
    id = models.IntegerField(primary_key=True)
    Material = models.CharField(max_length=100, blank=True, default='')
    Material_org = models.CharField(max_length=200)
    Description = models.CharField(max_length=250, blank=True, default='')
    SAPMaterialType = models.CharField(max_length=100, blank=True, default='')
    SAPMaterialGroup = models.CharField(max_length=100, blank=True, default='')
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True)
    Notes = models.CharField(max_length=250, blank=True, default='')
    PartType_id = models.IntegerField()
    PartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()
    TypicalContainerQty = models.CharField(max_length=100,null=True, blank=True)
    TypicalPalletQty = models.CharField(max_length=100,null=True, blank=True)
    OrgName = models.CharField(max_length=250)
    CountDate = models.DateField()
    FoundAt = models.CharField(max_length=1024)
    SAP_id = models.IntegerField()
    SAPDate = models.DateField()
    Plant = models.CharField(max_length=20)
    StorageLocation = models.CharField(max_length=20)
    Amount = models.FloatField()
    BaseUnitofMeasure = models.CharField(max_length=20)
    UOM = models.CharField(max_length=50)
    UOMText = models.CharField(max_length=100)
    DimensionText = models.CharField(max_length=100)
    mult = models.FloatField()
    ValueUnrestricted = models.FloatField(blank=True)
    Currency = models.CharField(max_length=20)
    SpecialStock = models.CharField(max_length=20)
    Batch = models.CharField(max_length=20)
    DoNotShow = models.BooleanField()

    class Meta:
        db_table = 'VIEW_MaterialLocationListWithSAP'
        managed = False

class VIEW_MaterialLocationListWithLastSAP(models.Model):
    id = models.IntegerField(primary_key=True)
    Material = models.CharField(max_length=100, blank=True, default='')
    Material_org = models.CharField(max_length=200)
    Description = models.CharField(max_length=250, blank=True, default='')
    SAPMaterialType = models.CharField(max_length=100, blank=True, default='')
    SAPMaterialGroup = models.CharField(max_length=100, blank=True, default='')
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True, blank=True)
    TypicalContainerQty = models.CharField(max_length=100,null=True, blank=True)
    TypicalPalletQty = models.CharField(max_length=100,null=True, blank=True)
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
