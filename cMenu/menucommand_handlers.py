from django.shortcuts import render, HttpResponse, redirect
from django.urls import reverse, resolve
from userprofiles.views import fnWICSuserForm
from userprofiles.models import WICSuser
from WICS.forms import fnUploadSAP, fnMaterialForm
from WICS.reports import fnCountSummaryRptPreview
from WICS.SAPLists import fnSAPList
from WICS.SAPMatlUpdt import fnUpdateMatlListfromSAP
from WICS.procs_ActualCounts import fnUploadActCountSprsht, fnCountEntryForm
from WICS.procs_SAP import fnShowSAP
from cMenu.utils import makebool, iif


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
    ChangePW = 51
    EditMenu = 91
    EditParameters = 92
    EditGreetings = 93
    EditPasswords = 94
    ExitApplication = 200


# should this be handled via urls?
def FormBrowse(req, formname, recNum = -1):
    theForm = 'Form ' + formname + ' is not built yet.  Calvin needs more coffee.'
    if formname.lower() == 'frmcount-schedulehistory-by-counterdate'.lower(): 
        theView = resolve(reverse('CountScheduleList')).func
        theForm = theView(req).render()     # must be rendered because this calls a class-based-view
    elif formname.lower() == 'l10-wics-uadmin'.lower():
        theForm = fnWICSuserForm(req)
    elif formname.lower() == 'l6-wics-uadmin'.lower():
        theForm = fnWICSuserForm(req)
    elif formname.lower() == 'frmcountentry'.lower():
        theForm = fnCountEntryForm(req, formname)
    elif formname.lower() == 'frmUploadCountEntry'.lower():
        theForm = fnUploadActCountSprsht(req)
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
    elif formname.lower() == 'frmCountScheduleEntry'.lower():
        theView = resolve(reverse('CountScheduleForm')).func
        theForm = theView(req)
    elif formname.lower() == 'rptCountWorksheet'.lower():
        theView = resolve(reverse('CountWorksheet')).func
        theForm = theView(req).render()
    elif formname.lower() == 'zutilShowColor'.lower(): pass
    else: pass

    return theForm


def ShowTable(req, tblname):
    _userorg = WICSuser.objects.get(user=req.user).org

    # hopefully, this will be straightforward, except for SAP, which is a pseudotable - it's actually an excel file
    # guess what - SAP is the first one I'm implementing!
    thetable = 'working on presenting table ' + tblname + '. Calvin still needs more coffee, and maybe for material to stay put sometimes!'
    if tblname == 'sap':
        thetable = fnShowSAP(req)
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

def f00test00(req):
    # r = render(req,"00test00.html")
    r = HttpResponse()
    r.write('no current test fn!')
    return r

