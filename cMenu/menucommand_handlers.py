from django.shortcuts import render, HttpResponse #, redirect
from django.urls import reverse, resolve
from userprofiles.views import fnWICSuserForm


# Menu Command Constants
from enum import Enum
class MENUCOMMAND(Enum):
    LoadMenu = 1
    FormBrowse = 11
    OpenTable = 15
    RunCode = 21
    RunSQLStatement = 31
    ConstructSQLStatement = 32
    ChangePW = 51
    EditMenu = 91
    EditParameters = 92
    EditGreetings = 93
    ExitApplication = 200


# should the url be the Argument rather than the formname?
def FormBrowse(req, formname, recNum = -1):
    theForm = 'Form ' + formname + ' is not built yet.  Calvin needs more coffee.'
    theForm = None
    if formname.lower() == 'l10-wics-uadmin'.lower():
        theForm = fnWICSuserForm(req)
    elif formname.lower() == 'l6-wics-uadmin'.lower():
        theForm = fnWICSuserForm(req)
    elif formname.lower() == 'frmcount-schedulehistory-by-counterdate'.lower(): 
        url = 'CountScheduleList'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'frmcountentry'.lower():
        url = 'CountEntryForm'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'frmUploadCountEntry'.lower():
        url = 'UploadActualCountSprsht'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'frmcountsummarypreview'.lower(): 
        url = 'CountSummaryReport'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'frmExportCMCounts': pass
    elif formname.lower() == 'frmimportsap'.lower():
        url = 'UploadSAPSprSht'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'frmmaterial'.lower():
        url = 'MatlForm'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'frmParts-By-Type-with-LastCounts'.lower():
        url = 'MatlByPartType'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'frmPrintAgendas'.lower(): pass
    elif formname.lower() == 'frmRandCountScheduler'.lower(): pass
    elif formname.lower() == 'frmSchedule AddPicks'.lower(): pass
    elif formname.lower() == 'matllistupdt'.lower(): 
        url = 'UpdateMatlListfromSAP'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'frmCountScheduleEntry'.lower():
        url = 'CountScheduleForm'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'rptCountWorksheet'.lower():
        url = 'CountWorksheet'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'rptMaterialLocations'.lower():
        url = 'MaterialLocations'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'LocationList'.lower():
        url = 'LocationList'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'zutilShowColor'.lower(): pass
    elif formname.lower() == 'sap'.lower():
        url = 'showtable-SAP'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'tblActualCounts'.lower():
        url = 'ActualCountList'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'adhoc2023-02-01-001'.lower():
        url = 'adhoc-2023-02-01-001'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'PartTypeFm'.lower():
        url = 'PartTypeForm'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    else: pass

    if not theForm:
        templt = "UnderConstruction.html"
        cntext = {
            'formname': formname, 
            #'orgname':_userorg.orgname, 
            'uname':req.user.get_full_name(), 
            }
        theForm = render(req, templt, cntext)


    # must be rendered if theForm came from a class-based-view
    if hasattr(theForm,'render'): theForm = theForm.render()
    return theForm


def ShowTable(req, tblname):
    # showing a table is nothing more than another form
    return FormBrowse(req,tblname)


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

