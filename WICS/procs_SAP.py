import os, uuid
# from datetime import datetime
# from dateutil import parser
from django import forms
from django.contrib.auth.decorators import login_required
from django.db.models import Max, OuterRef, Subquery
from django.shortcuts import render
from openpyxl import load_workbook
from cMenu.models import getcParm
from cMenu.utils import calvindate
from userprofiles.models import WICSuser
from WICS.models import SAP_SOHRecs, SAPPlants_org, UnitsOfMeasure
from WICS.models import WhsePartTypes, MaterialList, tmpMaterialListUpdate

ExcelWorkbook_fileext = ".XLSX"


@login_required
def fnShowSAP(req, reqDate=calvindate().today()):
    _userorg = WICSuser.objects.get(user=req.user).org

    reqDate = calvindate(reqDate).as_datetime()
    _myDtFmt = '%Y-%m-%d'

    SAP_tbl = fnSAPList(_userorg,for_date=reqDate)
    SAPDatesRaw = choices=SAP_SOHRecs.objects.filter(org=_userorg).order_by('-uploaded_at').values('uploaded_at').distinct()
    SAPDates = []
    for D in SAPDatesRaw:
        SAPDates.append(D['uploaded_at'].strftime(_myDtFmt))


    cntext = {'reqDate': SAP_tbl['reqDate'],
            'SAPDateList': SAPDates,
            'SAPDate': SAP_tbl['SAPDate'].strftime(_myDtFmt),
            'SAPSet': SAP_tbl['SAPTable'],
            'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'show_SAP_table.html'
    return render(req, templt, cntext)


####################################################################################
####################################################################################
####################################################################################


class UploadSAPForm(forms.Form):
    uploaded_at = forms.DateField()
    SAPFile = forms.FileField()

@login_required
def fnUploadSAP(req):

    if req.method == 'POST':
        form = UploadSAPForm(req.POST, req.FILES)
        if form.is_valid():
            # save the file so we can open it as an excel file
            SAPFile = req.FILES['SAPFile']
            svdir = getcParm('SAP-FILELOC')
            fName = svdir+"tmpSAP"+str(uuid.uuid4())+".xlsx"
            with open(fName, "wb") as destination:
                for chunk in SAPFile.chunks():
                    destination.write(chunk)

            wb = load_workbook(filename=fName, read_only=True)
            ws = wb.active

            SAPcolmnNames = ws[1]
            SAPcolmnMap = {'Material': None}
            SAP_SSName_TableName_map = {
                    'Material': 'Material', 
                    'Material description': 'Description', 
                    'Plant': 'Plant',
                    'Material type': 'MaterialType',
                    'Storage location': 'StorageLocation',
                    'Base Unit of Measure': 'BaseUnitofMeasure',
                    'Unrestricted': 'Amount',
                    'Currency': 'Currency',
                    'Value Unrestricted': 'ValueUnrestricted',
                    'Special Stock': 'SpecialStock',
                    'Batch': 'Batch',
                    }
            for col in SAPcolmnNames:
                if col.value in SAP_SSName_TableName_map:
                    SAPcolmnMap[SAP_SSName_TableName_map[col.value]] = col.column - 1
            if (SAPcolmnMap['Material'] == None):   # or SAPcol['StorageLocation'] == None or SAPcol['Amount'] == None):
                raise Exception('SAP Spreadsheet has bad header row.  See Calvin to fix this.')

            # if SAP SOH records exist for this date, kill them; only one set of SAP SOH records per day
            # (this was signed off on by user before coming here)
            UplDate = calvindate(req.POST['uploaded_at']).as_datetime()
            SAP_SOHRecs.objects.filter(uploaded_at=UplDate).delete()

            nRows = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[SAPcolmnMap['Material']]==None: MatNum = ''
                else: MatNum = row[SAPcolmnMap['Material']]
                if len(str(MatNum)):
                    _org = SAPPlants_org.objects.filter(SAPPlant=row[SAPcolmnMap['Plant']])[0].org
                    SRec = SAP_SOHRecs(
                                org = _org,
                                uploaded_at = UplDate
                                )
                    for fldName, colNum in SAPcolmnMap.items():
                        if row[colNum]==None: setval = ''
                        else: setval = row[colNum]
                        setattr(SRec, fldName, setval)
                    SRec.save()
                    nRows += 1

            # close and kill temp files
            wb.close()
            os.remove(fName)

            cntext = {'uploaded_at':UplDate, 'nRows':nRows,
                    'uname':req.user.get_full_name()
                    }
            templt = 'frm_upload_SAP_Success.html'
    else:
        LastSAPUpload = SAP_SOHRecs.objects.all().aggregate(LastSAPDate=Max('uploaded_at'))
        # .first().values('LastSAPDate')['LastSAPDate']

        form = UploadSAPForm()
        cntext = {'form': form, 
                'LastSAPUploadDate': LastSAPUpload['LastSAPDate'],
                'uname':req.user.get_full_name()
                }
        templt = 'frm_upload_SAP.html'
    #endif

    return render(req, templt, cntext)


# read the last SAP list before for_date into a list of SAP_SOHRecs
def fnSAPList(org, for_date = calvindate().today(), matl = None):
    """
    matl is a Material (string, NOT object!), or list, tuple or queryset of Materials to list, or None if all records are to be listed
    the SAPDate returned is the last one prior or equal to for_date
    """
   
    _userorg = org

    _myDtFmt = '%Y-%m-%d %H:%M'

    dateObj = calvindate(for_date) #.as_datetime().date()
    # if isinstance(for_date,str):
    #     dateObj = calvindate(for_date)
    # elif isinstance(for_date,datetime):
    #     dateObj = for_date.date()
    # else:
    #     dateObj = for_date

    if SAP_SOHRecs.objects.filter(org=_userorg, uploaded_at__lte=dateObj).exists():
        SAPDate = SAP_SOHRecs.objects.filter(org=_userorg, uploaded_at__lte=dateObj).latest().uploaded_at
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
    # UOM = UnitsOfMeasure.objects.filter(UOM=OuterRef('BaseUnitofMeasure'))
    STable = STable.annotate(mult=Subquery(UnitsOfMeasure.objects.filter(UOM=OuterRef('BaseUnitofMeasure')).values('Multiplier1')))
    # STb = STable.annotate(mult=Subquery(UnitsOfMeasure.objects.filter(UOM=OuterRef('BaseUnitofMeasure'))))    # nope - can only get a single field

    # yea, building SList is sorta wasteful, but a lot of existing code depends on it
    # won't be changing it until a total revamp of WICS
    SList['SAPDate'] = SAPDate
    SList['SAPTable'] = STable

    return SList


"""
    qs = SAP
    org = _userorg
    Material = Material
    Description = Material description
    PartType = get(UNKNOWN)
    SAPMaterialType = Material type
    SAPMaterialGroup = Material Group
    Price = Price
    PriceUnit = Price unit
"""
@login_required
def fnUpdateMatlListfromSAP(req):
    _userorg = WICSuser.objects.get(user=req.user).org

    if req.method == 'POST':
        if req.POST['NextPhase']=='02-Upl-Sprsht':
            SAPFile = req.FILES['SAPFile']
            svdir = getcParm('SAP-FILELOC')
            fName = svdir+"tmpMatlList"+str(uuid.uuid4())+".xlsx"
            with open(fName, "wb") as destination:
                for chunk in SAPFile.chunks():
                    destination.write(chunk)

            tmpMaterialListUpdate.objects.all().delete()

            wb = load_workbook(filename=fName, read_only=True)
            ws = wb.active
            SAPcolmnNames = ws[1]
            SAPcol = {'Material': None}
            SAP_SSName_TableName_map = {
                    'Material': 'Material', 
                    'Material description': 'Description', 
                    'Material type': 'SAPMaterialType',
                    'Material Group': 'SAPMaterialGroup',
                    'Price': 'Price',
                    'Price unit': 'PriceUnit',
                    }
            for col in SAPcolmnNames:
                if col.value in SAP_SSName_TableName_map:
                    SAPcol[SAP_SSName_TableName_map[col.value]] = col.column - 1
            if (SAPcol['Material'] == None):   # or SAPcol['StorageLocation'] == None or SAPcol['Amount'] == None):
                raise Exception('SAP Spreadsheet has bad header row.  See Calvin to fix this.')

            for row in ws.iter_rows(min_row=2, values_only=True):
                tmpMaterialListUpdate(
                                Material = row[SAPcol['Material']], 
                                Description = row[SAPcol['Description']], 
                                SAPMaterialType = row[SAPcol['SAPMaterialType']],
                                SAPMaterialGroup = row[SAPcol['SAPMaterialGroup']],
                                Price = row[SAPcol['Price']],
                                PriceUnit = row[SAPcol['PriceUnit']]
                                ).save()
            # endfor

            
            # later, save (FileMatList - MaterialList) and (MaterialList - FileMatList)
            # ask permission to correct each to the other
            # that will involve a temp table 
            # almost there now that I've created tmpMaterialListUpdate

            # for now ...
            AddedMatls = tmpMaterialListUpdate.objects.exclude(Material__in=MaterialList.objects.filter(org=_userorg).values('Material'))
            # one day django will implement insert ... select.  Until then ...
            for newRec in AddedMatls:
                MaterialList (
                        org = _userorg,
                        Material = newRec.Material,
                        Description = newRec.Description,
                        PartType = WhsePartTypes.objects.get(WhsePartType='UNKNOWN'),
                        SAPMaterialType = newRec.SAPMaterialType,
                        SAPMaterialGroup = newRec.SAPMaterialGroup,
                        Price = newRec.Price,
                        PriceUnit = newRec.PriceUnit
                        ).save()

            # delete the temporary table and the temporary file
            tmpMaterialListUpdate.objects.all().delete()
            wb.close()
            os.remove(fName)

        # endif req.POST['NextPhase']=='02-Upl-Sprsht'
        cntext = {'AddedMatls':AddedMatls}
        templt = 'frmUpdateMatlListfromSAP_done.html'
    else:
        # (hopefully,) this is the initial phase; all others will be part of a POST request
        cntext = {}
        templt = 'frmUpdateMatlListfromSAP_phase0.html'
    #endif req.method = 'POST'

    cntext['orgname'] = _userorg.orgname
    cntext['uname'] = req.user.get_full_name()
    return render(req, templt, cntext)

