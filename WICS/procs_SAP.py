import os, uuid, re as regex
from django import forms
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Max, OuterRef, Subquery
from django.shortcuts import render
from openpyxl import load_workbook
from cMenu.models import getcParm
from cMenu.utils import calvindate
from userprofiles.models import WICSuser
from WICS.models import ActualCounts, CountSchedule
from WICS.models import VIEW_SAP, SAP_SOHRecs, SAPPlants_org
from WICS.models import WhsePartTypes, MaterialList, tmpMaterialListUpdate

ExcelWorkbook_fileext = ".XLSX"


@login_required
def fnShowSAP(req, reqDate=calvindate().today()):

    reqDate = calvindate(reqDate).as_datetime()
    _myDtFmt = '%Y-%m-%d'

    SAP_tbl = fnSAPList(for_date=reqDate)
    SAPDatesRaw = SAP_SOHRecs.objects.all().order_by('-uploaded_at').values('uploaded_at').distinct()
    SAPDates = []
    for D in SAPDatesRaw:
        SAPDates.append(D['uploaded_at'].strftime(_myDtFmt))


    cntext = {'reqDate': SAP_tbl['reqDate'],
            'SAPDateList': SAPDates,
            'SAPDate': SAP_tbl['SAPDate'].strftime(_myDtFmt),
            'SAPSet': SAP_tbl['SAPTable'],
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
            fName = svdir+"tmpSAP"+str(uuid.uuid4())+ExcelWorkbook_fileext
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
                    'Blocked':'Blocked',
                    'Value BlockedStock':'ValueBlocked',
                    'Vendor':'Vendor',
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
                    }
            templt = 'frm_upload_SAP_Success.html'
    else:
        LastSAPUpload = SAP_SOHRecs.objects.all().aggregate(LastSAPDate=Max('uploaded_at'))
        # .first().values('LastSAPDate')['LastSAPDate']

        form = UploadSAPForm()
        cntext = {'form': form, 
                'LastSAPUploadDate': LastSAPUpload['LastSAPDate'],
                }
        templt = 'frm_upload_SAP.html'
    #endif

    return render(req, templt, cntext)


# read the last SAP list before for_date into a list of SAP_SOHRecs
def fnSAPList(for_date = calvindate().today(), matl = None):
    """
    coming: allow matl to be a MaterialList object or an id
    matl is a Material (string, NOT object!), or list, tuple or queryset of Materials to list, or None if all records are to be listed
    the SAPDate returned is the last one prior or equal to for_date
    """
   
    # _userorg = org

    _myDtFmt = '%Y-%m-%d %H:%M'

    dateObj = calvindate(for_date) #.as_datetime().date()

    if SAP_SOHRecs.objects.filter(uploaded_at__lte=dateObj).exists():
        LatestSAPDate = SAP_SOHRecs.objects.filter(uploaded_at__lte=dateObj).latest().uploaded_at
    else:
        LatestSAPDate = SAP_SOHRecs.objects.earliest().uploaded_at
    SAPLatest = VIEW_SAP.objects.filter(uploaded_at=LatestSAPDate).order_by('org_id', 'Material', 'StorageLocation')

    # if SAP_SOHRecs.objects.filter(org=_userorg, uploaded_at__lte=dateObj).exists():
    #     SAPDate = SAP_SOHRecs.objects.filter(org=_userorg, uploaded_at__lte=dateObj).latest().uploaded_at
    # else:
    #     SAPDate = SAP_SOHRecs.objects.filter(org=_userorg).order_by('uploaded_at').first().uploaded_at

    SList = {'reqDate': for_date, 'SAPDate': SAPLatest[0].uploaded_at, 'SAPTable':[]}

    if not matl:
        # STable = SAP_SOHRecs.objects.filter(org=_userorg, uploaded_at=SAPDate).order_by('Material')
        STable = SAPLatest
    else:
        if isinstance(matl,str):
            # STable = SAP_SOHRecs.objects.filter(org=_userorg, uploaded_at=SAPDate, Material=matl).order_by('Material')
            STable = SAPLatest.filter(Material=matl)
        elif isinstance(matl,MaterialList):  # handle case matl is a MaterialList instance here
            STable = SAPLatest.filter(Material_id=matl.id)
        elif isinstance(matl,str):  # handle case matl is a MaterialList id here
            STable = SAPLatest.filter(Material_id=matl)
        else:   # it better be an iterable!
            STable = SAPLatest.filter(Material__in=matl)

    # yea, building SList is sorta wasteful, but a lot of existing code depends on it
    # won't be changing it until a total revamp of WICS
    if STable:
        SList['SAPDate'] = STable[0].uploaded_at
    else:
        SList['SAPDate'] = None
    SList['SAPTable'] = STable

    return SList


#TODO: promote this to a utility
def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

@login_required
def fnUpdateMatlListfromSAP(req):
    if req.method == 'POST':
        if req.POST['NextPhase']=='02-Upl-Sprsht':
            SAPFile = req.FILES['SAPFile']
            svdir = getcParm('SAP-FILELOC')
            fName = svdir+"tmpMatlList"+str(uuid.uuid4())+ExcelWorkbook_fileext
            with open(fName, "wb") as destination:
                for chunk in SAPFile.chunks():
                    destination.write(chunk)

            tmpMaterialListUpdate.objects.all().delete()

            wb = load_workbook(filename=fName, read_only=True)
            ws = wb.active
            SAPcolmnNames = ws[1]
            SAPcol = {'Plant':None,'Material': None}
            SAP_SSName_TableName_map = {
                    'Material': 'Material', 
                    'Material description': 'Description', 
                    'Plant': 'Plant',
                    'Material type': 'SAPMaterialType',
                    'Material Group': 'SAPMaterialGroup',
                    'Price': 'Price',
                    'Price unit': 'PriceUnit',
                    'Currency':'Currency',
                    }
            for col in SAPcolmnNames:
                if col.value in SAP_SSName_TableName_map:
                    SAPcol[SAP_SSName_TableName_map[col.value]] = col.column - 1
            if (SAPcol['Material'] == None or SAPcol['Plant'] == None):   # or SAPcol['StorageLocation'] == None or SAPcol['Amount'] == None):
                raise Exception('SAP Spreadsheet has bad header row. Plant and/or Material is missing.  See Calvin to fix this.')

            ImpErrList = []
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[SAPcol['Material']]==None: MatNum = ''
                else: MatNum = row[SAPcol['Material']]
                ## refuse to work with special chars embedded in the MatNum
                if regex.match(".*[\n\t\xA0].*",MatNum):
                    ImpErrList.append('error: '+MatNum+' is an unusable part number. It contains an invalid character and cannot be added to WICS')
                    continue

                if len(str(MatNum)):
                    _org = SAPPlants_org.objects.filter(SAPPlant=row[SAPcol['Plant']])[0].org
                    tmpMaterialListUpdate(
                        org = _org,
                        Material = row[SAPcol['Material']], 
                        # MaterialLink = MaterialLink,
                        Description = row[SAPcol['Description']], 
                        Plant = row[SAPcol['Plant']],
                        SAPMaterialType = row[SAPcol['SAPMaterialType']],
                        SAPMaterialGroup = row[SAPcol['SAPMaterialGroup']],
                        Price = row[SAPcol['Price']],
                        PriceUnit = row[SAPcol['PriceUnit']],
                        Currency = row[SAPcol['Currency']]
                        ).save()
            # endfor
            wb.close()
            os.remove(fName)

            UpdMaterialLinkSQL = 'UPDATE WICS_tmpmateriallistupdate, (select id, org_id, Material from WICS_materiallist) as MasterMaterials'
            UpdMaterialLinkSQL += ' set WICS_tmpmateriallistupdate.MaterialLink_id = MasterMaterials.id '
            UpdMaterialLinkSQL += ' where WICS_tmpmateriallistupdate.org_id = MasterMaterials.org_id '
            UpdMaterialLinkSQL += '   and WICS_tmpmateriallistupdate.Material = MasterMaterials.Material '
            # tmpMaterialListUpdate.objects.all().update(MaterialLink=Subquery(MaterialList.objects.filter(org=OuterRef('org'), Material=OuterRef('Material'))[0]))
            with connection.cursor() as cursor:
                cursor.execute(UpdMaterialLinkSQL)

            # later, save (FileMatList - MaterialList) and (MaterialList - FileMatList)
            # TODO: ??ask permission to correct each to the other

            MustKeepMatlsSQL = "(SELECT MaterialLink_id AS Material_id FROM WICS_tmpmateriallistupdate WHERE MaterialLink_id IS NOT NULL)"
            MustKeepMatlsSQL += " UNION (SELECT Material_id FROM WICS_actualcounts)"
            MustKeepMatlsSQL += " UNION (SELECT Material_id FROM WICS_countschedule)"

            DeleteMatlsSelectSQL = "SELECT id, (SELECT orgname FROM WICS_organizations WHERE id=org_id) AS org, Material, Description, Plant FROM WICS_materiallist WHERE id NOT IN"
            DeleteMatlsSelectSQL += " (" + MustKeepMatlsSQL + ")"
            with connection.cursor() as cursor:
                cursor.execute(DeleteMatlsSelectSQL)
                RemvdMatlsList = dictfetchall(cursor)

            # do the Removals
            RemoveIDSQLList = "(-1"
            for rmvRec in RemvdMatlsList:
                RemoveIDSQLList += ", " + str(rmvRec['id'])
            RemoveIDSQLList += ")"
            DeleteMatlsDoitSQL = "DELETE FROM WICS_materiallist"
            DeleteMatlsDoitSQL += " WHERE id IN " + RemoveIDSQLList
            with connection.cursor() as cursor:
                cursor.execute(DeleteMatlsDoitSQL)

            UnknownTypeID = WhsePartTypes.objects.get(WhsePartType='UNKNOWN')
            # first pass, for presentation in results - orgname rather than org
            AddMatlsSelectSQL = "SELECT"
            AddMatlsSelectSQL += " (SELECT orgname FROM WICS_organizations WHERE id=org_id) AS orgname, Material,"
            AddMatlsSelectSQL += " Description, Plant, " + str(UnknownTypeID.pk) + " AS PartType_id,"
            AddMatlsSelectSQL += " SAPMaterialType, SAPMaterialGroup, Price, PriceUnit, Currency,"
            AddMatlsSelectSQL += " '' AS TypicalContainerQty, '' AS TypicalPalletQty, '' AS Notes"
            AddMatlsSelectSQL += " FROM WICS_tmpmateriallistupdate WHERE MaterialLink_id IS NULL"
            with connection.cursor() as cursor:
                cursor.execute(AddMatlsSelectSQL)
                AddedMatlsList = dictfetchall(cursor)

            # do the adds
            # one day django will implement insert ... select.  Until then ...
            AddMatlsSelectSQL = "SELECT"
            AddMatlsSelectSQL += " org_id, Material, Description, Plant, " + str(UnknownTypeID.pk) + " AS PartType_id,"
            AddMatlsSelectSQL += " SAPMaterialType, SAPMaterialGroup, Price, PriceUnit, Currency,"
            AddMatlsSelectSQL += " '' AS TypicalContainerQty, '' AS TypicalPalletQty, '' AS Notes"
            AddMatlsSelectSQL += " FROM WICS_tmpmateriallistupdate WHERE MaterialLink_id IS NULL"

            AddMatlsDoitSQL = "INSERT INTO WICS_materiallist"
            AddMatlsDoitSQL += " (org_id, Material, Description, Plant, PartType_id,"
            AddMatlsDoitSQL += " SAPMaterialType, SAPMaterialGroup, Price, PriceUnit, Currency,"
            AddMatlsDoitSQL += " TypicalContainerQty, TypicalPalletQty, Notes)"
            AddMatlsDoitSQL += " " + AddMatlsSelectSQL
            with connection.cursor() as cursor:
                cursor.execute(AddMatlsDoitSQL)

            # delete the temporary table and the temporary file
            tmpMaterialListUpdate.objects.all().delete()

        # endif req.POST['NextPhase']=='02-Upl-Sprsht'
        cntext = {
            'ImpErrList':ImpErrList,
            'AddedMatls':AddedMatlsList,
            'RemvdMatls':RemvdMatlsList,
            }
        templt = 'frmUpdateMatlListfromSAP_done.html'
    else:
        # (hopefully,) this is the initial phase; all others will be part of a POST request
        cntext = {}
        templt = 'frmUpdateMatlListfromSAP_phase0.html'
    #endif req.method = 'POST'

    return render(req, templt, cntext)
