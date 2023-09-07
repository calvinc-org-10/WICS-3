import os, uuid, re as regex
import random
import subprocess, signal
import json
from functools import partial
from django import forms
from django.contrib.auth.decorators import login_required
from django.conf import settings as django_settings
from django.db import connection, transaction
from django.db.models import Max, OuterRef, Subquery
from django.http import HttpResponse, HttpResponseNotModified
from django.shortcuts import render
from django_q.tasks import async_task
from openpyxl import load_workbook
from cMenu.models import getcParm
from cMenu.utils import calvindate, ExcelWorkbook_fileext
import WICS.globals
from WICS.models import SAP_SOHRecs, SAPPlants_org, UnitsOfMeasure, UploadSAPResults  #, VIEW_SAP
from WICS.models import WhsePartTypes, MaterialList, tmpMaterialListUpdate
from WICS.models_async_comm import async_comm, set_async_comm_state


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

##### the suite of procs to support fnUploadSAP


class UploadSAPForm(forms.Form):
    uploaded_at = forms.DateField(widget=forms.widgets.DateInput())
    SAPFile = forms.FileField()

def proc_UpSAPSpreadsheet_00InitUpSAP(reqid):
    acomm = set_async_comm_state(
        reqid,
        processname = 'Upload SAP MM52',
        statecode = 'reading-spreadsht-init',
        statetext = 'Initializing',
        new_async=True,
        )
    UploadSAPResults.objects.all().delete()

def proc_UpSAPSpreadsheet_00CopyUpSAPSpreadsheet(req, reqid):
    acomm = set_async_comm_state(
        reqid,
        statecode = 'uploading-sprsht',
        statetext = 'Uploading Spreadsheet',
        )

    SAPFile = req.FILES['SAPFile']
    svdir = getcParm('SAP-FILELOC')
    fName = svdir+"tmpSAP"+str(uuid.uuid4())+ExcelWorkbook_fileext
    with open(fName, "wb") as destination:
        for chunk in SAPFile.chunks():
            destination.write(chunk)

    return fName

def proc_UpSAPSpreadsheet_01ReadSheet(reqid, fName, UplDate):
    acomm = set_async_comm_state(
        reqid,
        statecode = 'rdng-sprsht',
        statetext = 'Reading Spreadsheet',
        )

    nRowsAdded = 0
    SprshtRowNum = 0

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
                set_async_comm_state(
                    reqid,
                    statecode = 'fatalerr',
                    statetext = f'SAP Spreadsheet has bad header row - More than one column named {col.value}.  See Calvin to fix this.',
                    result = 'FAIL - bad spreadsheet',
                    )
                wb.close()
                os.remove(fName)
                return
            else:
                SAPcolmnMap[colkey] = col.column - 1
            # endif previously mapped
        #endif col.value in SAP_SSName_TableName_map
    #endfor col in SAPcolmnNames
    if (SAPcolmnMap[_TblName_Material] is None) or (SAPcolmnMap[_TblName_Plant] is None):   # or SAPcol['StorageLocation'] == None or SAPcol['Amount'] == None):
        set_async_comm_state(
            reqid,
            statecode = 'fatalerr',
            statetext = f'SAP Spreadsheet has bad header row - no {_SStName_Material} column or no {_SStName_Plant} column.  See Calvin to fix this.',
            result = 'FAIL - bad spreadsheet',
            )
        wb.close()
        os.remove(fName)
        return

    # if SAP SOH records exist for this date, kill them; only one set of SAP SOH records per day
    # (this was signed off on by user before coming here)
    SAP_SOHRecs.objects.filter(uploaded_at=UplDate).delete()

    numrows = ws.max_row
    SprshtRowNum = 1
    for row in ws.iter_rows(min_row=SprshtRowNum+1, values_only=True):
        SprshtRowNum += 1
        if SprshtRowNum % 100 == 0:
            set_async_comm_state(
                reqid,
                statecode = 'rdng-sprsht',
                statetext = f'Reading Spreadsheet ... record {SprshtRowNum} of {numrows}',
                )

        if row[SAPcolmnMap[_TblName_Material]]==None: MatlNum = ''
        else: MatlNum = row[SAPcolmnMap[_TblName_Material]]
        if len(str(MatlNum)):
            _org = SAPPlants_org.objects.filter(SAPPlant=row[SAPcolmnMap[_TblName_Plant]])[0].org
            try:
                MatlRec = MaterialList.objects.get(org=_org,Material=MatlNum)
            except:
                MatlRec = None
            if not MatlRec:
                UploadSAPResults(
                    errState = 'error',
                    errmsg = f'either {MatlNum}  does not exist in MaterialList or incorrect Plant ({str(row[SAPcolmnMap[_TblName_Plant]])}) given',
                    rowNum = SprshtRowNum
                    ).save()
            else:
                SRec = SAP_SOHRecs(
                        org = _org,     # will be going away - or will it???
                        uploaded_at = UplDate,
                        Material = MatlRec
                        )
                for fldName, colNum in SAPcolmnMap.items():
                    if fldName == _TblName_Material:
                        pass    # not continue - we are preserving the incoming MaterialPartNum string
                    if row[colNum] is None: setval = ''
                    else: setval = row[colNum]
                    setattr(SRec, fldName, setval)
                SRec.save()
                nRowsAdded += 1
            # endif MatlRec
        # endif len(str(MatlNum))
    #endfor row in ws.iter_rows

    UploadSAPResults(
        errState = 'nRowsTotal',
        errmsg = '',
        rowNum = SprshtRowNum
        ).save()
    UploadSAPResults(
        errState = 'nRowsAdded',
        errmsg = '',
        rowNum = nRowsAdded
        ).save()

    # close and kill temp files
    wb.close()
    os.remove(fName)
def done_UpSAPSpreadsheet_01ReadSheet(t):
    reqid = t.args[0]
    statecode = async_comm.objects.get(pk=reqid).statecode
    if statecode != 'fatalerr':
        set_async_comm_state(
            reqid,
            statecode = 'done-rdng-sprsht',
            statetext = f'Finished Reading Spreadsheet',
            )
        proc_UpSAPSpreadsheet_99_FinalProc(reqid)
    #endif stateocde != 'fatalerr'

def proc_UpSAPSpreadsheet_99_FinalProc(reqid):
    set_async_comm_state(
        reqid,
        statecode = 'done',
        statetext = 'Finished Processing Spreadsheet',
        )

def proc_UpSAPSpreadsheet_99_Cleanup(reqid):
    # also kill reqid, acomm, qcluster process
    async_comm.objects.filter(pk=reqid).delete()
    os.kill(int(reqid), signal.SIGTERM)
    os.kill(int(reqid), signal.SIGKILL)

    # delete the temporary table
    UploadSAPResults.objects.all().delete()

@login_required
def fnUploadSAP(req):

    client_phase = req.POST['phase'] if 'phase' in req.POST else None
    reqid = req.COOKIES['reqid'] if 'reqid' in req.COOKIES else None
    UplDate = calvindate(req.POST['uploaded_at']).isoformat() if 'uploaded_at' in req.POST else calvindate()

    if req.method == 'POST':
        # check any mandatory commits here and change status code

        if client_phase=='init-upl':
            retinfo = HttpResponse()

            # start django_q broker
            reqid = subprocess.Popen(
                ['python', f'{django_settings.BASE_DIR}/manage.py', 'qcluster']
            ).pid
            retinfo.set_cookie('reqid',str(reqid))
            proc_UpSAPSpreadsheet_00InitUpSAP(reqid)

            # save the file so we can open it as an excel file
            fName = proc_UpSAPSpreadsheet_00CopyUpSAPSpreadsheet(req, reqid)

            task01 = async_task(proc_UpSAPSpreadsheet_01ReadSheet, reqid, fName, UplDate, hook=done_UpSAPSpreadsheet_01ReadSheet)

            acomm_fake = {
                'statecode': 'starting',
                'statetext': 'SAP MM60 Update Starting',
                }
            retinfo.write(json.dumps(acomm_fake))
            return retinfo
        elif client_phase=='waiting':
            retinfo = HttpResponse()

            acomm = async_comm.objects.values().get(pk=reqid)    # something's very wrong if this doesn't exist
            stcode = acomm['statecode']
            if stcode == 'fatalerr':
                pass
            retinfo.write(json.dumps(acomm))
            return retinfo
        elif client_phase=='wantresults':
            if UploadSAPResults.objects.filter(errState = 'nRowsAdded').exists():
                nRowsAdded = UploadSAPResults.objects.filter(errState = 'nRowsAdded')[0].rowNum
            else:
                nRowsAdded = 0
            if UploadSAPResults.objects.filter(errState = 'nRowsTotal').exists():
                nRowsTotal = UploadSAPResults.objects.filter(errState = 'nRowsTotal')[0].rowNum
            else:
                nRowsTotal = 0
            UplResults = UploadSAPResults.objects.exclude(errState__in = ['nRowsAdded','nRowsTotal'])
            cntext = {
                'uploaded_at':UplDate,
                'nRows':nRowsAdded,
                'nRowsRead':nRowsTotal,
                'UplProblems': UplResults,
                    }
            templt = 'frm_upload_SAP_Success.html'
            return render(req, templt, cntext)
        elif client_phase=='resultspresented':
            proc_UpSAPSpreadsheet_99_Cleanup(reqid)
            retinfo = HttpResponse()
            retinfo.delete_cookie('reqid')

            return retinfo
        else:
            return
        #endif client_phase

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


####################################################################################
####################################################################################
####################################################################################


# read the last SAP list before for_date into a list of SAP_SOHRecs
def fnSAPList(for_date = calvindate().today(), matl = None):
    """
    finally done!: allow matl to be a MaterialList object or an id
    matl is a Material (string, NOT object!), or list, tuple or queryset of Materials to list, or None if all records are to be listed
    the SAPDate returned is the last one prior or equal to for_date
    """
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


####################################################################################
####################################################################################
####################################################################################

##### the suite of procs to support fnUpdateMatlListfromSAP

def proc_MatlListSAPSprsheet_00InitUMLasync_comm(reqid):
    acomm = set_async_comm_state(
        reqid,
        statecode = 'rdng-sprsht-init',
        statetext = 'Initializing ...',
        new_async=True
        )

def proc_MatlListSAPSprsheet_00CopyUMLSpreadsheet(req, reqid):
    acomm = set_async_comm_state(
        reqid,
        statecode = 'uploading-sprsht',
        statetext = 'Uploading Spreadsheet',
        )

    SAPFile = req.FILES['SAPFile']
    svdir = getcParm('SAP-FILELOC')
    fName = svdir+"tmpMatlList"+str(uuid.uuid4())+ExcelWorkbook_fileext
    with open(fName, "wb") as destination:
        for chunk in SAPFile.chunks():
            destination.write(chunk)

    return fName

def proc_MatlListSAPSprsheet_01ReadSpreadsheet(reqid, fName):
    acomm = set_async_comm_state(
        reqid,
        statecode = 'rdng-sprsht',
        statetext = 'Reading Spreadsheet',
        )

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
    if (SAPcol['Material'] == None or SAPcol['Plant'] == None):
        set_async_comm_state(
            reqid,
            statecode = 'fatalerr',
            statetext = 'SAP Spreadsheet has bad header row. Plant and/or Material is missing.  See Calvin to fix this.',
            result = 'FAIL - bad spreadsheet',
            )

        wb.close()
        os.remove(fName)
        return

    numrows = ws.max_row
    nRows = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        nRows += 1
        if nRows % 100 == 0:
            set_async_comm_state(
                reqid,
                statecode = 'rdng-sprsht',
                statetext = f'Reading Spreadsheet ... record {nRows} of {numrows}',
                )

        if row[SAPcol['Material']]==None: MatNum = ''
        else: MatNum = row[SAPcol['Material']]
        ## refuse to work with special chars embedded in the MatNum
        if regex.match(".*[\n\t\xA0].*",MatNum):
            tmpMaterialListUpdate(
                recStatus = 'err-MatlNum',
                errmsg = f'error: {MatNum!a} is an unusable part number. It contains invalid characters and cannot be added to WICS',
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
            continue
        elif len(str(MatNum)):
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
        # endif invalid Material
    # endfor
    wb.close()
    os.remove(fName)
def done_MatlListSAPSprsheet_01ReadSpreadsheet(t):
    reqid = t.args[0]
    statecode = async_comm.objects.get(pk=reqid).statecode
    # print(f't.success= {t.success}')
    # print(f'tresult (type {type(t.result)}) = {t.result}')
    #DOITNOW!!! handle not t.success, t.result
    if statecode != 'fatalerr':
        set_async_comm_state(
            reqid,
            statecode = 'done-rdng-sprsht',
            statetext = f'Finished Reading Spreadsheet',
            )

def proc_MatlListSAPSprsheet_02_identifyexistingMaterial(reqid):
    set_async_comm_state(
        reqid,
        statecode = 'get-matl-link',
        statetext = f'Finding SAP MM60 Materials already in WICS Material List',
        )
    UpdMaterialLinkSQL = 'UPDATE WICS_tmpmateriallistupdate, (select id, org_id, Material from WICS_materiallist) as MasterMaterials'
    UpdMaterialLinkSQL += ' set WICS_tmpmateriallistupdate.MaterialLink_id = MasterMaterials.id, '
    UpdMaterialLinkSQL += "     WICS_tmpmateriallistupdate.recStatus = 'FOUND' "
    UpdMaterialLinkSQL += ' where WICS_tmpmateriallistupdate.org_id = MasterMaterials.org_id '
    UpdMaterialLinkSQL += '   and WICS_tmpmateriallistupdate.Material = MasterMaterials.Material '
    with connection.cursor() as cursor:
        cursor.execute(UpdMaterialLinkSQL)

    set_async_comm_state(
        reqid,
        statecode = 'id-del-matl',
        statetext = f'Identifying WICS Materials no longer in SAP MM60 Materials',
        )
    MustKeepMatlsSelCond = ''
    if MustKeepMatlsSelCond: MustKeepMatlsSelCond += ' AND '
    MustKeepMatlsSelCond += 'id NOT IN (SELECT DISTINCT tmucopy.MaterialLink_id AS Material_id FROM WICS_tmpmateriallistupdate tmucopy WHERE tmucopy.MaterialLink_id IS NOT NULL)'
    if MustKeepMatlsSelCond: MustKeepMatlsSelCond += ' AND '
    MustKeepMatlsSelCond += 'id NOT IN (SELECT DISTINCT Material_id FROM WICS_actualcounts)'
    if MustKeepMatlsSelCond: MustKeepMatlsSelCond += ' AND '
    MustKeepMatlsSelCond += 'id NOT IN (SELECT DISTINCT Material_id FROM WICS_countschedule)'
    if MustKeepMatlsSelCond: MustKeepMatlsSelCond += ' AND '
    MustKeepMatlsSelCond += 'id NOT IN (SELECT DISTINCT Material_id FROM WICS_sap_sohrecs)'

    DeleteMatlsSelectSQL = "INSERT INTO WICS_tmpmateriallistupdate (recStatus, delMaterialLink, MaterialLink_id, org_id, Material, Description, Plant "
    DeleteMatlsSelectSQL += ", SAPMaterialType, SAPMaterialGroup, Currency  ) "    # these can go once I set null=True on these fields
    DeleteMatlsSelectSQL += " SELECT  concat('DEL ',FORMAT(id,0)), id, NULL, org_id, Material, Description, Plant "
    DeleteMatlsSelectSQL += ", SAPMaterialType, SAPMaterialGroup, Currency  "    # these can go once I set null=True on these fields
    DeleteMatlsSelectSQL += " FROM WICS_materiallist"
    DeleteMatlsSelectSQL += f" WHERE ({MustKeepMatlsSelCond})"
    with connection.cursor() as cursor:
        cursor.execute(DeleteMatlsSelectSQL)

    set_async_comm_state(
        reqid,
        statecode = 'id-add-matl',
        statetext = f'Identifying SAP MM60 Materials new to WICS',
        )
    MarkAddMatlsSelectSQL = "UPDATE WICS_tmpmateriallistupdate"
    MarkAddMatlsSelectSQL += " SET recStatus = 'ADD'"
    MarkAddMatlsSelectSQL += " WHERE (MaterialLink_id IS NULL) AND (recStatus is NULL)"
    with connection.cursor() as cursor:
        cursor.execute(MarkAddMatlsSelectSQL)
        transaction.on_commit(partial(done_MatlListSAPSprsheet_02_identifyexistingMaterial,reqid))
def done_MatlListSAPSprsheet_02_identifyexistingMaterial(reqid):
    set_async_comm_state(
        reqid,
        statecode = 'get-matl-link-done',
        statetext = f'Finished linking SAP MM60 list to existing WICS Materials',
        )

def proc_MatlListSAPSprsheet_03_Remove(reqid):
    MustKeepMatlsDelCond = ''
    if MustKeepMatlsDelCond: MustKeepMatlsDelCond += ' AND '
    MustKeepMatlsDelCond += 'id IN (SELECT DISTINCT delMaterialLink FROM WICS_tmpmateriallistupdate WHERE recStatus like "DEL%")'

    set_async_comm_state(
        reqid,
        statecode = 'del-matl',
        statetext = f'Removing WICS Materials no longer in SAP MM60 Materials',
        )
    # do the Removals
    DeleteMatlsDoitSQL = "DELETE FROM WICS_materiallist"
    DeleteMatlsDoitSQL += f" WHERE ({MustKeepMatlsDelCond})"
    with connection.cursor() as cursor:
        cursor.execute(DeleteMatlsDoitSQL)
        transaction.on_commit(partial(done_MatlListSAPSprsheet_03_Remove,reqid))
def done_MatlListSAPSprsheet_03_Remove(reqid):
    mandatorytaskdonekey = f'MatlX{reqid}'
    statecodeVal = ".03D."
    existingstatecode = ''
    if async_comm.objects.filter(pk=mandatorytaskdonekey).exists(): existingstatecode = async_comm.objects.get(pk=mandatorytaskdonekey).statecode
    MatlXval = existingstatecode + statecodeVal
    set_async_comm_state(
        mandatorytaskdonekey,
        statecode = MatlXval,
        statetext = '',
        new_async = True
        )
    set_async_comm_state(
        reqid,
        statecode = 'done-del-matl',
        statetext = f'Finished Removing WICS Materials no longer in SAP MM60 Materials',
        )
    proc_MatlListSAPSprsheet_03_Add(reqid)

def proc_MatlListSAPSprsheet_03_Add(reqid):
    set_async_comm_state(
        reqid,
        statecode = 'add-matl',
        statetext = f'Adding SAP MM60 Materials new to WICS',
        )
    UnknownTypeID = WhsePartTypes.objects.get(WhsePartType=WICS.globals._PartTypeName_UNKNOWN)
    # do the adds
    # one day django will implement insert ... select.  Until then ...
    AddMatlsSelectSQL = "SELECT"
    AddMatlsSelectSQL += " org_id, Material, Description, Plant, " + str(UnknownTypeID.pk) + " AS PartType_id,"
    AddMatlsSelectSQL += " SAPMaterialType, SAPMaterialGroup, Price, PriceUnit, Currency,"
    AddMatlsSelectSQL += " '' AS TypicalContainerQty, '' AS TypicalPalletQty, '' AS Notes"
    AddMatlsSelectSQL += " FROM WICS_tmpmateriallistupdate"
    AddMatlsSelectSQL += " WHERE (MaterialLink_id IS NULL) AND (recStatus = 'ADD') "

    AddMatlsDoitSQL = "INSERT INTO WICS_materiallist"
    AddMatlsDoitSQL += " (org_id, Material, Description, Plant, PartType_id,"
    AddMatlsDoitSQL += " SAPMaterialType, SAPMaterialGroup, Price, PriceUnit, Currency,"
    AddMatlsDoitSQL += " TypicalContainerQty, TypicalPalletQty, Notes)"
    AddMatlsDoitSQL += " " + AddMatlsSelectSQL
    with connection.cursor() as cursor:
        cursor.execute(AddMatlsDoitSQL)

    set_async_comm_state(
        reqid,
        statecode = 'add-matl-get-recid',
        statetext = f'Getting Record ids of SAP MM60 Materials new to WICS',
        )
    UpdMaterialLinkSQL = 'UPDATE WICS_tmpmateriallistupdate, (select id, org_id, Material from WICS_materiallist) as MasterMaterials'
    UpdMaterialLinkSQL += ' set WICS_tmpmateriallistupdate.MaterialLink_id = MasterMaterials.id '
    UpdMaterialLinkSQL += ' where WICS_tmpmateriallistupdate.org_id = MasterMaterials.org_id '
    UpdMaterialLinkSQL += '   and WICS_tmpmateriallistupdate.Material = MasterMaterials.Material '
    UpdMaterialLinkSQL += "   and (MaterialLink_id IS NULL) AND (recStatus = 'ADD')"
    with connection.cursor() as cursor:
        cursor.execute(UpdMaterialLinkSQL)
        transaction.on_commit(partial(done_MatlListSAPSprsheet_03_Add,reqid))
def done_MatlListSAPSprsheet_03_Add(reqid):
    mandatorytaskdonekey = f'MatlX{reqid}'
    statecodeVal = ".03A."
    existingstatecode = ''
    if async_comm.objects.filter(pk=mandatorytaskdonekey).exists(): existingstatecode = async_comm.objects.get(pk=mandatorytaskdonekey).statecode
    MatlXval = existingstatecode + statecodeVal
    set_async_comm_state(
        mandatorytaskdonekey,
        statecode = MatlXval,
        statetext = '',
        new_async = True
        )
    set_async_comm_state(
        reqid,
        statecode = 'done-add-matl',
        statetext = f'Finished Adding SAP MM60 Materials new to WICS',
        )

def proc_MatlListSAPSprsheet_99_FinalProc(reqid):
    set_async_comm_state(
        reqid,
        statecode = 'done',
        statetext = 'Finished Processing Spreadsheet',
        )

def proc_MatlListSAPSprsheet_99_Cleanup(reqid):
    # also kill reqid, acomm, qcluster process
    async_comm.objects.filter(pk=reqid).delete()

    # when we can start django-q programmatically, this is where we kill that process
    # os.kill(int(reqid), signal.SIGTERM)
    # os.kill(int(reqid), signal.SIGKILL)

    # delete the temporary table
    tmpMaterialListUpdate.objects.all().delete()

@login_required
def fnUpdateMatlListfromSAP(req):

    client_phase = req.POST['phase'] if 'phase' in req.POST else None
    reqid = req.COOKIES['reqid'] if 'reqid' in req.COOKIES else None

    if req.method == 'POST':
        # check if the mandatory commits have been done and change the status code if so
        if reqid is not None:
            mandatory_commit_key = f'MatlX{reqid}'
            mandatory_commit_list = ['03A', '03D']
            if async_comm.objects.filter(pk=mandatory_commit_key).exists():
                mandatory_commits_recorded = async_comm.objects.get(pk=mandatory_commit_key).statecode
                if all((c in mandatory_commits_recorded) for c in mandatory_commit_list):
                    proc_MatlListSAPSprsheet_99_FinalProc(reqid)
                    async_comm.objects.filter(pk=mandatory_commit_key).delete()

        retinfo = HttpResponse()
        if client_phase=='init-upl':
            # start django_q broker
            # reqid = subprocess.Popen(
            #     ['python', f'{django_settings.BASE_DIR}/manage.py', 'qcluster']
            # ).pid
            reqid = random.randint(1, 100000000000)
            retinfo.set_cookie('reqid',str(reqid))

            proc_MatlListSAPSprsheet_00InitUMLasync_comm(reqid)

            UMLSSName = proc_MatlListSAPSprsheet_00CopyUMLSpreadsheet(req, reqid)
            async_task(proc_MatlListSAPSprsheet_01ReadSpreadsheet, reqid, UMLSSName, hook=done_MatlListSAPSprsheet_01ReadSpreadsheet)

            acomm = async_comm.objects.values().get(pk=reqid)    # something's very wrong if this doesn't exist
            retinfo.write(json.dumps(acomm))
            return retinfo
        elif client_phase=='waiting':
            acomm = async_comm.objects.values().get(pk=reqid)    # something's very wrong if this doesn't exist
            retinfo.write(json.dumps(acomm))
            return retinfo
        elif client_phase=='need-ident-exist-matl':
            async_task(proc_MatlListSAPSprsheet_02_identifyexistingMaterial, reqid, )

            acomm = async_comm.objects.values().get(pk=reqid)    # something's very wrong if this doesn't exist
            retinfo.write(json.dumps(acomm))
            return retinfo
        elif client_phase=='need-add-del':
            async_task(proc_MatlListSAPSprsheet_03_Remove, reqid, )

            acomm = async_comm.objects.values().get(pk=reqid)    # something's very wrong if this doesn't exist
            retinfo.write(json.dumps(acomm))
            return retinfo
            pass
        elif client_phase=='wantresults':
            ImpErrList = tmpMaterialListUpdate.objects.filter(recStatus__startswith='err')
            AddedMatlsList = tmpMaterialListUpdate.objects.filter(recStatus='ADD')
            RemvdMatlsList = tmpMaterialListUpdate.objects.filter(recStatus__startswith='DEL')
            cntext = {
                'ImpErrList':ImpErrList,
                'AddedMatls':AddedMatlsList,
                'RemvdMatls':RemvdMatlsList,
                }
            templt = 'frmUpdateMatlListfromSAP_done.html'
            return render(req, templt, cntext)
        elif client_phase=='cleanup-after-failure':
            pass
        elif client_phase=='resultspresented':
            proc_MatlListSAPSprsheet_99_Cleanup(reqid)
            retinfo.delete_cookie('reqid')

            return retinfo
        else:
            return
        #endif client_phase
    else:
        # (hopefully,) this is the initial phase; all others will be part of a POST request

        cntext = {
            'reqid': -1,
            }
        templt = 'frmUpdateMatlListfromSAP_phase0.html'
    #endif req.method = 'POST'

    return render(req, templt, cntext)
