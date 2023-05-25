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
def FormBrowse_orig(req, formname, recNum = -1):
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
    elif formname.lower() == 'frmrequestedcountsummary'.lower(): 
        url = 'CountSummaryReport-v-init'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'frmExportCMCounts': 
        pass
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
    elif formname.lower() == 'rptMaterialByLastCount'.lower():
        url = 'MatlByLastCountDate'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'rptMaterialByDESCValue'.lower():
        url = 'MatlByDESCValue'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'frmRandCountScheduler'.lower(): 
        pass
    elif formname.lower() == 'matllistupdt'.lower(): 
        url = 'UpdateMatlListfromSAP'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'frmCountScheduleEntry'.lower():
        url = 'CountScheduleForm'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'frmRequestCountScheduleEntry'.lower():
        url = 'RequestCountScheduleForm'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'frmRequestedCountListEdit'.lower():
        url = 'RequestCountListEdit'
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
    elif formname.lower() == 'zutilShowColor'.lower(): 
        pass
    elif formname.lower() == 'sap'.lower():
        url = 'showtable-SAP'
        theView = resolve(reverse(url)).func
        theForm = theView(req)
    elif formname.lower() == 'tblActualCounts'.lower():
        url = 'ActualCountList'
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
            }
        theForm = render(req, templt, cntext)


    # must be rendered if theForm came from a class-based-view
    if hasattr(theForm,'render'): theForm = theForm.render()
    return theForm

def FormBrowse(req, formname):
    FormNameToURL_Map = {}
    urlIndex = 0
    viewIndex = 1

    FormNameToURL_Map['l10-wics-uadmin'.lower()] = (None, fnWICSuserForm)
    FormNameToURL_Map['l6-wics-uadmin'.lower()] = FormNameToURL_Map['l10-wics-uadmin']
    FormNameToURL_Map['frmcount-schedulehistory-by-counterdate'.lower()] = ('CountScheduleList', None)
    FormNameToURL_Map['frmcountentry'.lower()] = ('CountEntryForm', None)
    FormNameToURL_Map['frmUploadCountEntry'.lower()] = ('UploadActualCountSprsht', None)
    FormNameToURL_Map['frmcountsummarypreview'.lower()] = ('CountSummaryReport', None)
    FormNameToURL_Map['frmrequestedcountsummary'.lower()] = ('CountSummaryReport-v-init', None)
    FormNameToURL_Map['frmimportsap'.lower()] = ('UploadSAPSprSht', None)
    FormNameToURL_Map['frmmaterial'.lower()] = ('MatlForm', None)
    FormNameToURL_Map['frmParts-By-Type-with-LastCounts'.lower()] = ('MatlByPartType', None)
    FormNameToURL_Map['rptMaterialByLastCount'.lower()] = ('MatlByLastCountDate', None)
    FormNameToURL_Map['rptMaterialByDESCValue'.lower()] = ('MatlByDESCValue', None)
    FormNameToURL_Map['frmRandCountScheduler'.lower()] = (None, None)
    FormNameToURL_Map['matllistupdt'.lower()] = ('UpdateMatlListfromSAP', None)
    FormNameToURL_Map['frmCountScheduleEntry'.lower()] = ('CountScheduleForm', None)
    FormNameToURL_Map['frmRequestCountScheduleEntry'.lower()] = ('RequestCountScheduleForm', None)
    FormNameToURL_Map['frmRequestedCountListEdit'.lower()] = ('RequestCountListEdit', None)
    FormNameToURL_Map['rptCountWorksheet'.lower()] = ('CountWorksheet', None)
    FormNameToURL_Map['rptMaterialLocations'.lower()] = ('MaterialLocations', None)
    FormNameToURL_Map['LocationList'.lower()] = ('LocationList', None)
    FormNameToURL_Map['sap'.lower()] = ('showtable-SAP', None)
    FormNameToURL_Map['tblActualCounts'.lower()] = ('ActualCountList', None)
    FormNameToURL_Map['PartTypeFm'.lower()] = ('PartTypeForm', None)

    # theForm = 'Form ' + formname + ' is not built yet.  Calvin needs more coffee.'
    theForm = None
    formname = formname.lower()
    if formname in FormNameToURL_Map:
        if FormNameToURL_Map[formname][urlIndex]:
            url = FormNameToURL_Map[formname][urlIndex]
            theView = resolve(reverse(url)).func
            theForm = theView(req)
        elif FormNameToURL_Map[formname][viewIndex]:
            fn = FormNameToURL_Map[formname][viewIndex]
            theForm = fn(req)

    if not theForm:
        templt = "UnderConstruction.html"
        cntext = {
            'formname': formname, 
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

