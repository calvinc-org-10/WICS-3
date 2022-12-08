from django.shortcuts import render # HttpResponse, render, redirect
#from django.urls import reverse
#from django.utils.html import escape
from userprofiles.views import fnWICSuserForm
from userprofiles.models import WICSuser
from WICS.forms import fnUploadSAP, fnMaterialForm, fnCountEntryForm
from WICS.SAPLists import fnSAPList #, SAProw


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
    if formname == 'frmcount-schedulehistory-by-counterdate': pass
    elif formname == 'l10-wics-uadmin':
        theForm = fnWICSuserForm(req)
    elif formname == 'l6-wics-uadmin':
        theForm = fnWICSuserForm(req)
    elif formname == 'frmcountentry':
        theForm = fnCountEntryForm(req, formname)
    elif formname == 'frmCountSummaryPreview': pass
    elif formname == 'frmExportCMCounts': pass
    elif formname == 'frmimportsap':
        theForm = fnUploadSAP(req, formname)
    elif formname == 'frmmaterial':
        theForm = fnMaterialForm(req, formname, recNum)
    elif formname == 'frmPartTypes with CountInfo': pass
    elif formname == 'frmPrintAgendas': pass
    elif formname == 'frmRandCountScheduler': pass
    elif formname == 'frmSchedule AddPicks': pass
    elif formname == 'zutilShowColor': pass
    else: pass

    return theForm


def ShowTable(req, tblname):
    _userorg = WICSuser.objects.get(user=req.user).org

    # hopefully, this will be straightforward, except for SAP, which is a pseudotable - it's actually an excel file
    # guess what - SAP is the first one I'm implementing!
    thetable = 'working on presenting table ' + tblname + '. Calvin still needs more coffee, and maybe for material to stay put sometimes!'
    if tblname == 'sap':
        SAP_tbl = fnSAPList(req)
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

def f00test00(req):
    r = render(req,"00test00.html")

    # r = HttpResponse(escape(req))
    # r.write('the test works')
    # r.write('I hope the test works')
    return r

