import datetime
from dateutil import parser
from openpyxl import load_workbook
from userprofiles.models import WICSuser
from WICS.models import SAP_SOHRecs


class SAProw:
    def __init__(self, Material, StorageLocation, Amount):
        self.Material = Material
        self.StorageLocation = StorageLocation
        self.Amount = Amount
    def __str__(self):
        return self.Material + ", " + self.StorageLocation + ", " + str(self.Amount)


# read the last SAP list before for_date into a list of SAProw
def fnSAPList(org, for_date = datetime.datetime.today(), matl = None):
    """
    matl is a Material (string, NOT object!), or list, tuple or queryset of Materials to list, or None if all records are to be listed
    the SAPDate returned is the last one prior or equal to for_date
    """
   
    _userorg = org

    _myDtFmt = '%Y-%m-%d %H:%M'

    if isinstance(for_date,str):
        dateObj = parser.parse(for_date)
    elif isinstance(for_date,datetime.datetime):
        dateObj = for_date.date()
    else:
        dateObj = for_date

    if SAP_SOHRecs.objects.filter(org=_userorg, uploaded_at__date__lte=dateObj).exists():
        SAPDate = SAP_SOHRecs.objects.filter(org=_userorg, uploaded_at__date__lte=dateObj).latest().uploaded_at
    else:
        SAPDate = SAP_SOHRecs.objects.filter(org=_userorg).order_by('uploaded_at').first().uploaded_at

    SList = {'reqDate': for_date, 'SAPDate': SAPDate, 'SAPTable':[]}

    if not matl:
        STable = SAP_SOHRecs.objects.filter(org=_userorg, uploaded_at=SAPDate).order_by('Material')
    else:
        if isinstance(matl,str):
            STable = SAP_SOHRecs.objects.filter(org=_userorg, uploaded_at=SAPDate, Material=matl).order_by('Material')
        else:   # it better be an iterable!
            STable = SAP_SOHRecs.objects.filter(org=_userorg, uploaded_at=SAPDate, Material__in=matl).order_by('Material')
    
    # yea, building SList is sorta wasteful, but a lot of existing code depends on it
    # won't be changing it until a total revamp of WICS
    SList['SAPDate'] = SAPDate
    SList['SAPTable'] = STable

    return SList

