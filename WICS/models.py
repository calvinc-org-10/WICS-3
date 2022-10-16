from django.db import models
import uuid
from sqlalchemy import UniqueConstraint

# Create your models here.


class Organizations(models.Model):
    ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    orgname = models.CharField(max_length=250)

    class Meta:
        db_table = 'organizations'
        ordering = ['orgname']

    def __str__(self) -> str:
        return self.orgname
        # return super().__str__()


class org_SAPPlant(models.Model):
    ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey(Organizations, on_delete=models.CASCADE)
    SAPPlant = models.CharField(max_length=50)
    SAPStorLoc = models.CharField(max_length=50)
    UniqueConstraint('SAPPlant', 'SAPStorLoc')


class WhsePartTypes(models.Model):
    ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    oldID = models.IntegerField()
    org = models.ForeignKey(Organizations, on_delete=models.CASCADE)
    WhsePartType = models.CharField(max_length=50)
    PartTypePriority = models.SmallIntegerField()
    InactivePartType = models.BooleanField()
    UniqueConstraint('org', 'WhsePartType')


class MaterialList(models.Model):
    ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    oldID = models.IntegerField()
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT)
    Material = models.CharField(max_length=100)
    Description = models.CharField(max_length=250, blank=True)
    PartType = models.ForeignKey(WhsePartTypes, null=True, on_delete=models.RESTRICT)
    SAPMaterialType = models.CharField(max_length=100, blank=True)
    SAPMaterialGroup = models.CharField(max_length=100, blank=True)
    Price = models.FloatField(null=True)
    PriceUnit = models.PositiveIntegerField(null=True)
    Notes = models.CharField(max_length=250, blank=True)
    UniqueConstraint('org', 'Material')

    class Meta:
        ordering = ['org','Material']

    def __str__(self) -> str:
        return self.Material
        # return super().__str__()

class Count_Schedule_History(models.Model):
    ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    oldID = models.IntegerField()
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT)
    CountDate = models.DateField()
    Material = models.ForeignKey(MaterialList, on_delete=models.RESTRICT)
    Counter = models.CharField(max_length=250)
    Priority = models.CharField(max_length=50)
    ReasonScheduled = models.CharField(max_length=250)
    CMPrintFlag = models.BooleanField()
    Notes = models.CharField(max_length=250)
    UniqueConstraint('org', 'CountDate', 'Material')

class ActualCounts(models.Model):
    ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    oldID = models.IntegerField()
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT)
    CountDate = models.DateField()
    CycCtID = models.CharField(max_length=100)
    Material = models.ForeignKey(MaterialList, on_delete=models.RESTRICT)
    Counter = models.CharField(max_length=250, blank=False)
    CTD_QTY_Expr = models.CharField(max_length=500, blank=False)
    BLDG = models.CharField(max_length=100, blank=True)
    LOCATION = models.CharField(max_length=250, blank=True)
    PKGID_Desc = models.CharField(max_length=250, blank=True)
    TAGQTY = models.CharField(max_length=250, blank=True)
    FLAG_PossiblyNotRecieved = models.BooleanField()
    FLAG_MovementDuringCount = models.BooleanField()
    Notes = models.CharField(max_length = 250, blank=True)

