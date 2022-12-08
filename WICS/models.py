from django.db import models
from sqlalchemy import UniqueConstraint
from django.utils import timezone

# Create your models here.
# I'm quite happy with automaintained pk fields, so I don't specify any

class Organizations(models.Model):
    orgname = models.CharField(max_length=250)

    class Meta:
        ordering = ['orgname']

    def __str__(self) -> str:
        return self.orgname
        # return super().__str__()


# is this table really needed?
class org_SAPPlant(models.Model):
    org = models.ForeignKey(Organizations, on_delete=models.CASCADE)
    SAPPlant = models.CharField(max_length=50)
    SAPStorLoc = models.CharField(max_length=50)
    UniqueConstraint('SAPPlant', 'SAPStorLoc')


class WhsePartTypes(models.Model):
    # oldWICSID = models.IntegerField(null=True, blank=True)      # kill this field once data is tied to new ID in WICS2
    org = models.ForeignKey(Organizations, on_delete=models.CASCADE, blank=True)
    WhsePartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()
    InactivePartType = models.BooleanField(null=True, blank=True)
    UniqueConstraint('org', 'WhsePartType')
    UniqueConstraint('org', 'PartTypePriority')

    def __str__(self) -> str:
        return self.WhsePartType
        # return super().__str__()


class MaterialList(models.Model):
    # oldWICSID = models.IntegerField(null=True, blank=True)      # kill this field once data is tied to new ID in WICS2
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT, blank=True)
    Material = models.CharField(max_length=100)
    Description = models.CharField(max_length=250, blank=True)
    # oldWICSPartType = models.IntegerField(null=True, blank=True)      # kill this field once data is tied to new ID in WICS2
    PartType = models.ForeignKey(WhsePartTypes, null=True, on_delete=models.RESTRICT)
    SAPMaterialType = models.CharField(max_length=100, blank=True)
    SAPMaterialGroup = models.CharField(max_length=100, blank=True)
    Price = models.FloatField(null=True, blank=True)
    PriceUnit = models.PositiveIntegerField(null=True)
    TypicalContainerQty = models.IntegerField(null=True, blank=True)
    TypicalPalletQty = models.IntegerField(null=True, blank=True)
    Notes = models.CharField(max_length=250, blank=True)
    UniqueConstraint('org', 'Material')

    class Meta:
        ordering = ['org','Material']

    def __str__(self) -> str:
        return self.Material
        # return super().__str__()


class CountSchedule(models.Model):
    # oldWICSID = models.IntegerField(null=True, blank=True)      # kill this field once data is tied to new ID in WICS2
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT, blank=True)
    CountDate = models.DateField(null=False)
    # oldWICSMaterial = models.IntegerField(null=True, blank=True)      # kill this field once data is tied to new ID in WICS2
    Material = models.ForeignKey(MaterialList, on_delete=models.RESTRICT)
    Counter = models.CharField(max_length=250, blank=True)
    Priority = models.CharField(max_length=50, blank=True)
    ReasonScheduled = models.CharField(max_length=250, blank=True)
    CMPrintFlag = models.BooleanField(null=True, blank=True)
    Notes = models.CharField(max_length=250, blank=True)
    UniqueConstraint('org', 'CountDate', 'Material')

    class Meta:
        ordering = ['org','CountDate', 'Material']


class ActualCounts(models.Model):
    # oldWICSID = models.IntegerField(null=True, blank=True)      # kill this field once data is tied to new ID in WICS2
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT, blank=True)
    CountDate = models.DateField(null=False)
    CycCtID = models.CharField(max_length=100, blank=True)
    # oldWICSMaterial = models.IntegerField(null=True, blank=True)      # kill this field once data is tied to new ID in WICS2
    Material = models.ForeignKey(MaterialList, on_delete=models.RESTRICT)
    Counter = models.CharField(max_length=250, blank=False)
    LocationOnly = models.BooleanField(null=True, blank=True)
    CTD_QTY_Expr = models.CharField(max_length=500, blank=False)
    BLDG = models.CharField(max_length=100, blank=True)
    LOCATION = models.CharField(max_length=250, blank=True)
    PKGID_Desc = models.CharField(max_length=250, blank=True)
    TAGQTY = models.CharField(max_length=250, blank=True)
    FLAG_PossiblyNotRecieved = models.BooleanField(null=True, blank=True)
    FLAG_MovementDuringCount = models.BooleanField(null=True, blank=True)
    Notes = models.CharField(max_length = 250, blank=True)

    class Meta:
        ordering = ['org', 'CountDate', 'Material']

    def __str__(self) -> str:
        return str(self.pk) + ": " + str(self.CountDate) + " / " + str(self.Material) + " / " + str(self.Counter) + " / " + str(self.BLDG) + "_" + str(self.LOCATION)
        # return super().__str__()


class SAPFiles(models.Model):
    uploaded_at = models.DateTimeField(default=timezone.now)
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT, blank=True)
    SAPFile = models.FileField(upload_to='SAP/')
    Notes = models.CharField(max_length=255, blank=True)
    class Meta:
        get_latest_by = 'uploaded_at'
class SAP(models.Model):
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT, blank=True)
    UpdateDate = models.DateField(null=False)
    Material = models.CharField(max_length=100)
    Description = models.CharField(max_length=250, blank=True)
    Plant = models.CharField(max_length=50, blank=True)
    SAPMaterialType = models.CharField(max_length=100, blank=True)
    StorageLocation = models.CharField(max_length=50, blank=True)
    BaseUnitofMeasure = models.CharField(max_length=50, blank=True)
    Unrestricted = models.FloatField(null=True, blank=True)
    Currency = models.CharField(max_length=50, blank=True)
    ValueUnrestricted = models.FloatField(null=True, blank=True)
    SpecialStock = models.CharField(max_length=50, blank=True)
    Batch = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['org', 'UpdateDate', 'Material']


