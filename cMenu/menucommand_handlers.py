from re import L
from django.shortcuts import render, HttpResponse, redirect
from django.urls import reverse, resolve
from userprofiles.views import fnWICSuserForm
from userprofiles.models import WICSuser
from WICS.forms import fnUploadSAP, fnMaterialForm, fnCountEntryForm, CountScheduleForm
from WICS.reports import fnCountSummaryRptPreview
from WICS.SAPLists import fnSAPList, SAProw
from WICS.SAPMatlUpdt import fnUpdateMatlListfromSAP


# Menu Command Constants
from enum import Enum
class MENUCOMMAND(Enum):
    LoadMenu = 1
    FormBrowse = 11
    FormAdd = 12
    ReportView = 13
    ReportPrint = 14
    OpenTable = 15
    OpenQuery = 16
    RunCode = 21
    RunSQLStatement = 31
    ConstructSQLStatement = 32
    EditMenu = 91
    EditParameters = 92
    EditGreetings = 93
    EditPasswords = 94
    ExitApplication = 200


# should this be handled via urls?
def FormBrowse(req, formname, recNum = -1):
    theForm = 'Form ' + formname + ' is not built yet.  Calvin needs more coffee.'
    if formname.lower() == 'frmcount-schedulehistory-by-counterdate'.lower(): 
        theView = CountScheduleForm.as_view()
        theForm = theView(req).render()
    elif formname.lower() == 'l10-wics-uadmin'.lower():
        theForm = fnWICSuserForm(req)
    elif formname.lower() == 'l6-wics-uadmin'.lower():
        theForm = fnWICSuserForm(req)
    elif formname.lower() == 'frmcountentry'.lower():
        theForm = fnCountEntryForm(req, formname)
    elif formname.lower() == 'frmcountsummarypreview'.lower(): 
        theForm = fnCountSummaryRptPreview(req)
    elif formname.lower() == 'frmExportCMCounts': pass
    elif formname.lower() == 'frmimportsap'.lower():
        theForm = fnUploadSAP(req, formname)
    elif formname.lower() == 'frmmaterial'.lower():
        theForm = fnMaterialForm(req, formname, recNum)
    elif formname.lower() == 'frmPartTypes with CountInfo'.lower(): pass
    elif formname.lower() == 'frmParts-By-Type-with-LastCounts'.lower():
        theForm = resolve(reverse('MatlByPartType')).func(req).render()
    elif formname.lower() == 'frmPrintAgendas'.lower(): pass
    elif formname.lower() == 'frmRandCountScheduler'.lower(): pass
    elif formname.lower() == 'frmSchedule AddPicks'.lower(): pass
    elif formname.lower() == 'matllistupdt'.lower(): 
        theForm = fnUpdateMatlListfromSAP(req)
    elif formname.lower() == 'zutilShowColor'.lower(): pass
    else: pass

    return theForm


def ShowTable(req, tblname):
    _userorg = WICSuser.objects.get(user=req.user).org

    # hopefully, this will be straightforward, except for SAP, which is a pseudotable - it's actually an excel file
    # guess what - SAP is the first one I'm implementing!
    thetable = 'working on presenting table ' + tblname + '. Calvin still needs more coffee, and maybe for material to stay put sometimes!'
    if tblname == 'sap':
        SAP_tbl = fnSAPList(_userorg)
        cntext = {'reqDate': SAP_tbl['reqDate'],
                'SAPDate': SAP_tbl['SAPDate'],
                'SAPSet': SAP_tbl['SAPTable'],
                'formID':tblname, 'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
                }
        tmplt = 'show_SAP_table.html'
        thetable = render(req, tmplt, cntext)
        pass
    else:
        pass
    #endif

    return thetable

# functions called directly by the menu by RunCode
# Calvin is lazy - these should take no arguments except req - the HttpRequest, but should return a redirect (to preserve HttpRequest)

def f00test00_orig(req):
    r = render(req,"00test00.html")

    # r = HttpResponse(escape(req))
    # r.write('the test works')
    # r.write('I hope the test works')
    return r

import csv, os
from WICS.models import ActualCounts, CountSchedule,  MaterialList

# this could be generally useful...
def makebool(strngN, numtype = bool):
    # the built-in bool function is good with one set of exceptions
    if (strngN.upper()=='FALSE' or strngN.upper()=='NO' or strngN.upper()=='0'):
        strngN = False
    else:
        strngN = numtype(strngN)
    return strngN
def iif(cond, ifTrue, ifFalse=None):
    if (cond):
        return ifTrue
    else:
        return ifFalse

def f00test00_act():
    ExportOutFile = 'ActCounts.csv'
    ExportModel = ActualCounts
    fieldnames = ['org_id',
            'CountDate',
            'CycCtID',
            'Material',
            'Counter',
            'LocationOnly',
            'CTD_QTY_Expr',
            'BLDG',
            'LOCATION',
            'PKGID_Desc',
            'TAGQTY',
            'FLAG_PossiblyNotRecieved',
            'FLAG_MovementDuringCount',
            'Notes']

    print('=======================================')
    print (ExportOutFile)
    print('=======================================')

    with open(ExportOutFile, 'r', newline='') as csvfile:
        CSVreader = csv.DictReader(csvfile)

        for inrec in CSVreader:
            # transform the booleans, so they don't cause problems
            # for next time - I might have gotten lucky - don't modify the for var!!
            inrec['LocationOnly'] = makebool(inrec['LocationOnly'])
            inrec['FLAG_MovementDuringCount'] = makebool(inrec['FLAG_MovementDuringCount'])
            inrec['FLAG_PossiblyNotRecieved'] = makebool(inrec['FLAG_PossiblyNotRecieved'])
            
            ExportModel.objects.create(
                org_id = inrec['org_id'],
                CountDate = inrec['CountDate'],
                CycCtID = inrec['CycCtID'],
                Material = MaterialList.objects.get(org_id=inrec['org_id'], Material=inrec['Material']),
                Counter = inrec['Counter'],
                LocationOnly = inrec['LocationOnly'],
                CTD_QTY_Expr = inrec['CTD_QTY_Expr'],
                BLDG = inrec['BLDG'],
                LOCATION = inrec['LOCATION'],
                PKGID_Desc = inrec['PKGID_Desc'],
                TAGQTY = inrec['TAGQTY'],
                FLAG_PossiblyNotRecieved = inrec['FLAG_PossiblyNotRecieved'],
                FLAG_MovementDuringCount = inrec['FLAG_MovementDuringCount'],
                Notes = inrec['Notes'] 
            )
            print(
                inrec['org_id'], '|',
                inrec['CountDate'], '|',
                inrec['CycCtID'], '|',
                inrec['Material'], '|',
                inrec['Counter'],
                inrec['BLDG']+'_'+inrec['LOCATION']
            )
    print('\n\n')
def f00test00_sch():
    ExportOutFile = 'CountSched.csv'
    ExportModel = CountSchedule
    fieldnames = ['org_id',
            'CountDate',
            'Material',
            'Counter',
            'Priority',
            'ReasonScheduled',
            'CMPrintFlag',
            'Notes']

    print('=======================================')
    print (ExportOutFile)
    print('=======================================')

    with open(ExportOutFile, 'r', newline='') as csvfile:
        CSVreader = csv.DictReader(csvfile)

        for inrec in CSVreader:
            # transform the booleans, so they don't cause problems
            CMPrintFlag_bool = makebool(inrec['CMPrintFlag'])


            isdup = ExportModel.objects.filter(
                org_id = inrec['org_id'],
                CountDate = inrec['CountDate'],
                Material = MaterialList.objects.get(org_id=inrec['org_id'], Material=inrec['Material'])
                ).exists()
            if not isdup:
                ExportModel.objects.create(
                    org_id = inrec['org_id'],
                    CountDate = inrec['CountDate'],
                    Material = MaterialList.objects.get(org_id=inrec['org_id'], Material=inrec['Material']),
                    Counter = inrec['Counter'],
                    Priority = inrec['Priority'],
                    ReasonScheduled = inrec['ReasonScheduled'],
                    CMPrintFlag = CMPrintFlag_bool,
                    Notes = inrec['Notes'] 
                    )

            print(
                inrec['org_id'], '|',
                inrec['CountDate'], '|',
                inrec['Material'], '|',
                inrec['Counter'], '|',
                iif(isdup,'*** DUP REC ***','')
                )

            continue

    print('\n\n')



def f00test00(req):
    # r = render(req,"00test00.html")
    r = HttpResponse()
    r.write('no current test fn!')
    return r

