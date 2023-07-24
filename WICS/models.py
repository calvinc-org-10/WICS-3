from typing import Any
from django.db import connection, models
from django.db.models import F, Exists, OuterRef, Value, Case, When, Subquery, Max
from django.db.models.functions import Concat
from userprofiles.models import WICSuser
from cMenu.utils import GroupConcat, dictfetchall


# I'm quite happy with automaintained pk fields, so I don't specify any

class Organizations(models.Model):
    orgname = models.CharField(max_length=250)

    class Meta:
        ordering = ['orgname']

    def __str__(self) -> str:
        return str(self.orgname)
        # return super().__str__()

###########################################################
###########################################################

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

###########################################################
###########################################################

##### Material_org prototype construction code cannot be
##### fn.  It involves an OuterRef, which anchors to its
##### Subquery.  Do not actually call this fn.  Use it as
##### a prototype for each instance.

def fnMaterial_org_constr(fld_matlName, fld_org, fld_orgname):
    return Case(
        When(Exists(MaterialList.objects.filter(Material=OuterRef(fld_matlName)).exclude(org=OuterRef(fld_org))),
            then=Concat(F(fld_matlName), Value(' ('), F(fld_orgname), Value(')'), output_field=models.CharField())
            ),
        default=F(fld_matlName)
        )

###########################################################
###########################################################

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

def fnMaterial_id(org_id:int,Material:str) -> str | None:
    try:
        return MaterialList.objects.get(org_id=org_id, Material=Material).pk
    except:
        return None

def VIEW_materials():
    return MaterialList.objects.all()\
        .annotate(
            PrtType=F('PartType__WhsePartType'),
            OrgName=F('org__orgname'),
            Material_org=Case(
                When(Exists(MaterialList.objects.filter(Material=OuterRef('Material')).exclude(org=OuterRef('org'))),
                    then=Concat(F('Material'), Value(' ('), F('org__orgname'), Value(')'), output_field=models.CharField())
                    ),
                default=F('Material')
                )
            )

###########################################################
###########################################################

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

def VIEW_countschedule():
    qs = CountSchedule.objects.all()
    qs = qs.annotate(
            Material_org = Case(
                When(Exists(MaterialList.objects.filter(Material=OuterRef('Material__Material')).exclude(org=OuterRef('Material__org'))),
                    then=Concat(F('Material__Material'), Value(' ('), F('Material__org__orgname'), Value(')'), output_field=models.CharField())
                    ),
                default=F('Material__Material')
                )
            )
    qs = qs.annotate(Description = F('Material__Description'),
                    MaterialNotes = F('Material__Notes'),
                    ScheduleNotes = F('Notes')
            )

    return qs

###########################################################
###########################################################

class ActualCounts(models.Model):
    CountDate = models.DateField(null=False)
    CycCtID = models.CharField(max_length=100, blank=True)
    Material = models.ForeignKey(MaterialList, on_delete=models.RESTRICT)
    Counter = models.CharField(max_length=250, blank=False, null=False)
    LocationOnly = models.BooleanField(blank=True, default=False)
    CTD_QTY_Expr = models.CharField(max_length=500, blank=True)
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
            models.Index(fields=['LOCATION']),
        ]

    def __str__(self) -> str:
        return str(self.pk) + ": " + str(self.CountDate) + " / " + str(self.Material) + " / " + str(self.Counter) + " / " + str(self.LOCATION)
        # return super().__str__()


def VIEW_actualcounts():
    qs = ActualCounts.objects.all()
    qs = qs.annotate(
            Material_org=Case(
                When(Exists(MaterialList.objects.filter(Material=OuterRef('Material__Material')).exclude(org=OuterRef('Material__org'))),
                    then=Concat(F('Material__Material'), Value(' ('), F('Material__org__orgname'), Value(')'), output_field=models.CharField())
                    ),
                default=F('Material__Material')
                )
            )
    qs = qs.annotate(Description = F('Material__Description'))
    qs = qs.annotate(MaterialNotes = F('Material__Notes'))
    qs = qs.annotate(CountNotes = F('Notes'))

    return qs

def FoundAt(matl = None):
    # Django's generated SQL takes longer than I'd like.  I can do better, so...

    if matl is None:
        Totalqs = VIEW_actualcounts().all()
    else:
        Totalqs = VIEW_actualcounts().filter(Material=matl)

    FA_qs = Totalqs.values('Material', 'Material_org', 'CountDate').annotate(FoundAt=GroupConcat('LOCATION',distinct=True, ordering='LOCATION'))
    return FA_qs


def VIEW_LastFoundAt(matl = None):
    """NOTE:  This returns a list of dictionaries, **NOT** a QuerySet!!! """
    if matl is None:
        RecordRestrict_sql = ''
    else:
        RecordRestrict_sql = f'ACT.Material_id = {matl.pk}'

    LFAsql = ""
    LFAsql += "SELECT ACT.`Material_id`,"
    LFAsql += "	    CASE WHEN EXISTS(SELECT (1) AS `a` FROM `WICS_materiallist` U0 WHERE (U0.`Material` = (MATL.`Material`) AND NOT (U0.`org_id` = (MATL.`org_id`))) LIMIT 1)"
    LFAsql += "		    THEN CONCAT_WS('', MATL.`Material`, ' (', ORG.`orgname`, ')')"
    LFAsql += "		    ELSE MATL.`Material`"
    LFAsql += "	        END AS `Material_org`,"
    LFAsql += "	    ACT.`CountDate`,"
    LFAsql += "	    GROUP_CONCAT(DISTINCT ACT.`LOCATION` ORDER BY LOCATION) AS `FoundAt`"
    LFAsql += " FROM `WICS_actualcounts` ACT"
    LFAsql += " INNER JOIN `WICS_materiallist` MATL ON (ACT.`Material_id` = MATL.`id`)"
    LFAsql += " INNER JOIN `WICS_organizations` ORG ON (MATL.`org_id` = ORG.`id`)"
    LFAsql += " INNER JOIN (SELECT U0.Material_id, MAX(U0.`CountDate`) AS `MaxCtDt` FROM `WICS_actualcounts` U0 GROUP BY U0.`Material_id`) V1"
    LFAsql += " ON ACT.`CountDate` = V1.MaxCtDt AND ACT.Material_id = V1.Material_id"
    if RecordRestrict_sql: LFAsql += f" WHERE {RecordRestrict_sql}"
    LFAsql += " GROUP BY ACT.`Material_id`, ACT.`CountDate`"
    LFAsql += " ORDER BY Material_org"

    with connection.cursor() as cursor:
        cursor.execute(LFAsql)
        LFAList = dictfetchall(cursor)
    
    return LFAList

def LastFoundAt(matl):
    lastCountDate = None
    LFAString = ''

    if isinstance(matl,(int, MaterialList)):
        LFAqs = VIEW_LastFoundAt(matl)
        if LFAqs:
            lastCountDate = LFAqs[0]['CountDate']
            LFAString = LFAqs[0]['FoundAt']

    return {'lastCountDate': lastCountDate, 'lastFoundAt': LFAString,}

def VIEW_LastFoundAtList(matl=None):

    if matl is None:
        MaxDates = ActualCounts.objects.all().values('Material').annotate(MaxCtDt=Max('CountDate'))
        FA_qs = VIEW_actualcounts()\
                    .filter(CountDate = Subquery(MaxDates.filter(Material=OuterRef('Material')).values('MaxCtDt')[:1]))
    else:
        MaxDates = ActualCounts.objects.filter(Material=matl).values('Material').annotate(MaxCtDt=Max('CountDate'))
        FA_qs = VIEW_actualcounts()\
                    .filter(Material=matl,
                            CountDate = Subquery(MaxDates.filter(Material=OuterRef('Material')).values('MaxCtDt')[:1]))

    LFAqs = FA_qs.order_by('Material__Material', 'Material__org', 'FoundAt')

    return LFAqs

###########################################################
###########################################################

class SAP_SOHRecs(models.Model):
    uploaded_at = models.DateField()
    org = models.ForeignKey(Organizations, on_delete=models.RESTRICT, blank=True)
    MaterialPartNum = models.CharField(max_length=100)
    Material = models.ForeignKey(MaterialList,on_delete=models.SET_NULL,null=True)
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
        ordering = ['uploaded_at', 'org', 'MaterialPartNum']
        indexes = [
            models.Index(fields=['uploaded_at', 'org', 'MaterialPartNum']),
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

def VIEW_SAP():
    return SAP_SOHRecs.objects.all()\
        .annotate(
            Material_org=Case(
                When(Exists(MaterialList.objects.filter(Material=OuterRef('MaterialPartNum')).exclude(org=OuterRef('org'))),
                    then=Concat(F('MaterialPartNum'), Value(' ('), F('org__orgname'), Value(')'), output_field=models.CharField())
                    ),
                default=F('MaterialPartNum')
                ),
            Description = F('Material__Description'),
            Notes = F('Material__Notes'),
            mult = Subquery(UnitsOfMeasure.objects.filter(UOM=OuterRef('BaseUnitofMeasure')).values('Multiplier1')[:1])
            )
            # do I need to annotate OrgName?

###########################################################
###########################################################

class WorksheetZones(models.Model):
    zone = models.IntegerField(primary_key=True)
    zoneName = models.CharField(max_length=10,blank=True)


class Location_WorksheetZone(models.Model):
    location = models.CharField(max_length=50,blank=False)
    zone = models.ForeignKey('WorksheetZones', on_delete=models.RESTRICT)

###########################################################
###########################################################

class WICSPermissions(models.Model):
    class Meta:
        managed = False  # No database table creation or deletion  \
                         # operations will be performed for this model.
        default_permissions = () # disable "add", "change", "delete"
                                 # and "view" default permissions
        permissions = [
            ('Material_onlyview', 'For restricting Material Form to view only'),
        ]

###########################################################
###########################################################
