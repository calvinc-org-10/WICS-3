from userprofiles.models import WICSuser
from WICS.models import SAPFiles
from openpyxl import load_workbook
from django.db.models import Model
import datetime


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
    matl is a MaterialList object to list, or None if all records are to be listed
    """
    #TODO: Allow matl to be a set or list
    #TODO  Sort SList['SAPTable'] by Material
    
    _userorg = org

    try:
        SAPObj = SAPFiles.objects.filter(org=_userorg, uploaded_at__date__lte=for_date).latest()
    except (SAPFiles.DoesNotExist):
        SAPObj = SAPFiles.objects.filter(org=_userorg).order_by('uploaded_at').first()

    SList = {'reqDate': for_date, 'SAPDate': for_date, 'SAPTable':[]}
    if SAPObj == None:
        # return an empty SAPList
        pass
    else:
        SList['SAPDate'] = SAPObj.uploaded_at
        wb = load_workbook(filename=SAPObj.SAPFile, read_only=True)
        ws = wb.active
        SAPcolmnNames = ws[1]
        SAPcol = {'Material': None, 'StorageLocation': None, 'Amount': None,}
        for col in SAPcolmnNames:
            if col.value == 'Material':
                SAPcol['Material'] = col.column - 1
            if col.value == 'Storage location':
                SAPcol['StorageLocation'] = col.column - 1
            if col.value == 'Unrestricted':
                SAPcol['Amount'] = col.column - 1
        if (SAPcol['Material'] == None or SAPcol['StorageLocation'] == None or SAPcol['Amount'] == None):
            raise Exception('SAP Spreadsheet has bad header row.  See Calvin to fix this.')

        for row in ws.iter_rows(min_row=2, values_only=True):
            if (matl == None or matl.Material == row[SAPcol['Material']]):
                x = SAProw(row[SAPcol['Material']], row[SAPcol['StorageLocation']], row[SAPcol['Amount']])
                SList['SAPTable'].append(x)
            #endif
        #endfor
    #endif

    return SList

