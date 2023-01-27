import os, uuid
from datetime import datetime
from dateutil import parser
from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from openpyxl import load_workbook
from cMenu.models import getcParm
from userprofiles.models import WICSuser
from WICS.models import SAP_SOHRecs
from WICS.models import WhsePartTypes, MaterialList, tmpMaterialListUpdate

ExcelWorkbook_fileext = ".XLSX"


@login_required
def fnShowSAP(req, reqDate=datetime.today()):
    _userorg = WICSuser.objects.get(user=req.user).org

    _myDtFmt = '%Y-%m-%d %H:%M'

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
    tmplt = 'show_SAP_table.html'
    return render(req, tmplt, cntext)


####################################################################################
####################################################################################
####################################################################################


class UploadSAPForm(forms.Form):
    uploaded_at = forms.DateTimeField()
    SAPFile = forms.FileField()

@login_required
def fnUploadSAP(req):
    _userorg = WICSuser.objects.get(user=req.user).org

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

            # I map Table Fields directly to spreadsheet columns because the SOH spreadsheets
            # are fairly stable.  If that changes, see fnUpdateMatlListfromSAP
            # for an alternative way of handling this mapping
            SAPcolmnMap = {
                        'Material': 0,
                        'Description': 1,
                        'Plant': 2,
                        'MaterialType': 3,
                        'StorageLocation': 4,
                        'BaseUnitofMeasure': 5,
                        'Amount': 6,
                        'Currency': 7,
                        'ValueUnrestricted': 8,
                        'SpecialStock': 9,
                        'Batch': 10,
                        }

            nRows = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[SAPcolmnMap['Material']]==None: MatNum = ''
                else: MatNum = row[SAPcolmnMap['Material']]
                if len(str(MatNum)):
                    SRec = SAP_SOHRecs(
                                org = _userorg,
                                uploaded_at = req.POST['uploaded_at']
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

            cntext = {'uploaded_at':req.POST['uploaded_at'], 'nRows':nRows,
                    'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
                    }
            templt = 'frm_upload_SAP_Success.html'
    else:
        form = UploadSAPForm()
        cntext = {'form': form, 
                'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
                }
        templt = 'frm_upload_SAP.html'
    #endif

    return render(req, templt, cntext)


# read the last SAP list before for_date into a list of SAP_SOHRecs
def fnSAPList(org, for_date = datetime.today(), matl = None):
    """
    matl is a Material (string, NOT object!), or list, tuple or queryset of Materials to list, or None if all records are to be listed
    the SAPDate returned is the last one prior or equal to for_date
    """
   
    _userorg = org

    _myDtFmt = '%Y-%m-%d %H:%M'

    if isinstance(for_date,str):
        dateObj = parser.parse(for_date)
    elif isinstance(for_date,datetime):
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

