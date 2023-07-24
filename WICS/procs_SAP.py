import os, uuid, re as regex
from django import forms
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Max, OuterRef, Subquery
from django.shortcuts import render
from openpyxl import load_workbook
from cMenu.models import getcParm
from cMenu.utils import calvindate, dictfetchall, ExcelWorkbook_fileext
from userprofiles.models import WICSuser
import WICS.globals
from WICS.models import ActualCounts, CountSchedule
from WICS.models import SAP_SOHRecs, SAPPlants_org, UnitsOfMeasure  #, VIEW_SAP
from WICS.models import WhsePartTypes, MaterialList, tmpMaterialListUpdate


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
    uploaded_at = forms.DateField(widget=forms.widgets.DateInput())
    SAPFile = forms.FileField()

@login_required
def fnUploadSAP(req):

    if req.method == 'POST':
        UplResults = []
        nRowsAdded = 0
        SprshtRowNum = 0

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

            _SStName_Material = 'Material'
            _TblName_Material = 'MaterialPartNum'
            _SStName_Plant = 'Plant'
            _TblName_Plant = 'Plant'
            SAPcolmnNames = ws[1]
            SAPcolmnMap = {_TblName_Material: None, _TblName_Plant: None}
            SAP_SSName_TableName_map = {
                    _SStName_Material: _TblName_Material,  # Material+org will translate to a Material_id
                    _SStName_Plant: _TblName_Plant,
                    'Material description': 'Description', 
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
                    colkey = SAP_SSName_TableName_map[col.value]
                    # has this col.value already been mapped?
                    if (colkey in SAPcolmnMap and SAPcolmnMap[colkey] is not None):
                        # yes, that's a problem
                        raise Exception(f'SAP Spreadsheet has bad header row - More than one column named {col.value}.  See Calvin to fix this.')
                    else:
                        SAPcolmnMap[colkey] = col.column - 1
                    # endif previously mapped
            if (SAPcolmnMap[_TblName_Material] is None) or (SAPcolmnMap[_TblName_Plant] is None):   # or SAPcol['StorageLocation'] == None or SAPcol['Amount'] == None):
                raise Exception(f'SAP Spreadsheet has bad header row - no {_SStName_Material} column or no {_SStName_Plant} column.  See Calvin to fix this.')

            # if SAP SOH records exist for this date, kill them; only one set of SAP SOH records per day
            # (this was signed off on by user before coming here)
            UplDate = calvindate(req.POST['uploaded_at']).as_datetime()
            SAP_SOHRecs.objects.filter(uploaded_at=UplDate).delete()

            SprshtRowNum = 1
            for row in ws.iter_rows(min_row=SprshtRowNum+1, values_only=True):
                SprshtRowNum += 1
                if row[SAPcolmnMap[_TblName_Material]]==None: MatlNum = ''
                else: MatlNum = row[SAPcolmnMap[_TblName_Material]]
                if len(str(MatlNum)):
                    _org = SAPPlants_org.objects.filter(SAPPlant=row[SAPcolmnMap[_TblName_Plant]])[0].org
                    try:
                        MatlRec = MaterialList.objects.get(org=_org,Material=MatlNum)
                    except:
                        MatlRec = None
                    if not MatlRec:
                        UplResults.append({'error':'either ' + MatlNum + ' does not exist in MaterialList or incorrect Plant (' + str(row[SAPcolmnMap['Plant']]) + ') given', 'rowNum':SprshtRowNum})
                    else:
                        SRec = SAP_SOHRecs(
                                org = _org,     # will be going away
                                uploaded_at = UplDate,
                                Material = MatlRec
                                )
                        for fldName, colNum in SAPcolmnMap.items():
                            if fldName == _TblName_Material:
                                pass    # not continue - we are preserving the incoming MaterialPartNum string
                            if row[colNum]==None: setval = ''
                            else: setval = row[colNum]
                            setattr(SRec, fldName, setval)
                        SRec.save()
                        nRowsAdded += 1
                    # endif MatlRec
                # endif len(str(MatlNum))

            # close and kill temp files
            wb.close()
            os.remove(fName)

            cntext = {
                'uploaded_at':UplDate, 
                'nRows':nRowsAdded,
                'UplProblems': UplResults,
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
    finally done!: allow matl to be a MaterialList object or an id
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
    SAPLatest = SAP_SOHRecs.objects\
        .filter(uploaded_at=LatestSAPDate)\
        .annotate(mult=Subquery(UnitsOfMeasure.objects.filter(UOM=OuterRef('BaseUnitofMeasure')).values('Multiplier1')[:1]))\
        .order_by('Material__org', 'Material__Material', 'StorageLocation')

    SList = {'reqDate': for_date, 'SAPDate': LatestSAPDate, 'SAPTable':[]}

    if not matl:
        STable = SAPLatest
    else:
        if isinstance(matl,str):
            raise Exception('fnSAPList by Matl string is deprecated')
        elif isinstance(matl,MaterialList):  # handle case matl is a MaterialList instance here
            STable = SAPLatest.filter(Material=matl)
        elif isinstance(matl,int):  # handle case matl is a MaterialList id here
            STable = SAPLatest.filter(Material_id=matl)
        else:   # it better be an iterable!
            STable = SAPLatest.filter(Material__in=matl)

    # yea, building SList is sorta wasteful, but a lot of existing code depends on it
    # won't be changing it until a total revamp of WICS
    if not STable:
        SList['SAPDate'] = None
    SList['SAPTable'] = STable

    return SList


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

            MustKeepMatlsCond = " (id NOT IN (SELECT DISTINCT MaterialLink_id AS Material_id FROM WICS_tmpmateriallistupdate WHERE MaterialLink_id IS NOT NULL))"
            MustKeepMatlsCond += " AND (id NOT IN (SELECT DISTINCT Material_id FROM WICS_actualcounts))"
            MustKeepMatlsCond += " AND (id NOT IN (SELECT DISTINCT Material_id FROM WICS_countschedule))"

            DeleteMatlsSelectSQL = "SELECT id, (SELECT orgname FROM WICS_organizations WHERE id=org_id) AS org, Material, Description, Plant FROM WICS_materiallist"
            DeleteMatlsSelectSQL += " WHERE (" + MustKeepMatlsCond + ")"
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

            UnknownTypeID = WhsePartTypes.objects.get(WhsePartType=WICS.globals._PartTypeName_UNKNOWN)
            # first pass, for presentation in results - orgname rather than org
            AddMatlsSelectSQL = "SELECT"
            AddMatlsSelectSQL += " org_id, (SELECT orgname FROM WICS_organizations WHERE id=org_id) AS orgname,"
            AddMatlsSelectSQL += " Material, Description,"
            AddMatlsSelectSQL += " Plant, " + str(UnknownTypeID.pk) + " AS PartType_id,"
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

            #TODO: (issue #53) update AddedMatlsList field new_MaterialLink_id with the new MaterialLink_id
            NewMatl_idListSQL = "SELECT id, org_id, Material"
            NewMatl_idListSQL += " FROM WICS_materiallist"
            NewMatl_idListSQL += f" WHERE (org_id, Material) IN {tuple(((x['org_id'], x['Material']) for x in AddedMatlsList))}"
            with connection.cursor() as cursor:
                cursor.execute(NewMatl_idListSQL)
                NewMatl_idDict = {(x['org_id'], x['Material']): x['id'] for x in dictfetchall(cursor)}
            for newRec in AddedMatlsList:
                newRec['id'] = NewMatl_idDict[(newRec['org_id'], newRec['Material'])]

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
