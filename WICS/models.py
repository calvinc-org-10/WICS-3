from django.db import models
from sqlalchemy import UniqueConstraint
from django.utils import timezone
from cMenu.models import getcParm

# Create your models here.
# I'm quite happy with automaintained pk fields, so I don't specify any

class Organizations(models.Model):
    orgname = models.CharField(max_length=250)

    class Meta:
        ordering = ['orgname']

    def __str__(self) -> str:
        return self.orgname
        # return super().__str__()


class orgObjects(models.Manager):
    def __init__(self, org_in) -> None:
        super().__init__()
        self.org = org_in
    def get_queryset(self):
        return super().get_queryset().filter(org=self.org)


class WhsePartTypes(models.Model):
    # oldWICSID = models.IntegerField(null=True, blank=True)      # kill this field once data is tied to new ID in WICS2
    org = models.ForeignKey(Organizations, on_delete=models.CASCADE, blank=True)
    WhsePartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()
    InactivePartType = models.BooleanField(blank=True, default=False)
    objects = models.Manager()
    orgobjects = orgObjects(org)
    UniqueConstraint('org', 'WhsePartType')
    UniqueConstraint('org', 'PartTypePriority')

    def __str__(self) -> str:
        return self.WhsePartType
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
    objects = models.Manager()
    orgobjects = orgObjects(org)
    UniqueConstraint('org', 'Material')

    class Meta:
        ordering = ['org','Material']

    def __str__(self) -> str:
        return self.Material
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
    objects = models.Manager()
    orgobjects = orgObjects(org)
    UniqueConstraint('org', 'CountDate', 'Material')

    class Meta:
        ordering = ['org','CountDate', 'Material']
    def __str__(self) -> str:
        return str(self.pk) + ": " + str(self.CountDate) + " / " + str(self.Material) + " / " + str(self.Counter)
        # return super().__str__()


class ActualCounts(models.Model):
    # oldWICSID = models.IntegerField(null=True, blank=True)      # kill this field once data is tied to new ID in WICS2
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT, blank=False)
    CountDate = models.DateField(null=False)
    CycCtID = models.CharField(max_length=100, blank=True)
    # oldWICSMaterial = models.IntegerField(null=True, blank=True)      # kill this field once data is tied to new ID in WICS2
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
    objects = models.Manager()
    orgobjects = orgObjects(org)

    class Meta:
        ordering = ['org', 'CountDate', 'Material']

    def __str__(self) -> str:
        return str(self.pk) + ": " + str(self.CountDate) + " / " + str(self.Material) + " / " + str(self.Counter) + " / " + str(self.BLDG) + "_" + str(self.LOCATION)
        # return super().__str__()

def LastFoundAt(matl):
    try:
        lastCountDate = ActualCounts.objects.filter(Material=matl).latest('CountDate').CountDate
    except:
        lastCountDate = None
    LFAString = ''
    if lastCountDate:
        countrecs = ActualCounts.objects.filter(Material=matl,CountDate=lastCountDate)\
                    .order_by('BLDG','LOCATION')\
                    .values('BLDG','LOCATION')\
                    .distinct()
        for rec in countrecs:
            if LFAString: LFAString += ', '
            LFAString += rec['BLDG'] + '_' + rec['LOCATION']
    
    return {'lastCountDate': lastCountDate, 'lastFoundAt': LFAString}


class SAP_SOHRecs(models.Model):
    uploaded_at = models.DateTimeField(default=timezone.now)
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



