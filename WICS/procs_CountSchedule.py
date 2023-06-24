import datetime
import os, uuid
import re as regex
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Value
from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from django.views.generic import ListView
from barcode import Code128
from userprofiles.models import WICSuser
from cMenu.models import getcParm
from cMenu.utils import makebool, isDate, WrapInQuotes, calvindate
from WICS.models import MaterialList, CountSchedule, VIEW_countschedule
from WICS.models import LastFoundAt, WorksheetZones, Location_WorksheetZone
from WICS.procs_SAP import fnSAPList
from typing import *
from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel, WINDOWS_EPOCH
# below: skip Sat, Sun using dateutil, dateutil.rrule, dateutil.rruleset
# implement skipping holidays
from cMenu.utils import calvindate
# from WICS.procs_misc import HolidayList


# ====================================================
# ====================================================
# ====================================================


def fnCountScheduleRecordExists(CtDate, Matl):
    """
    used to check if a CountSchedule record exists for the given CtDate and Material
    (only one such record is allowed).
    If the record exists, it is the return value, else a None CountSchedule rec
    """
    if isinstance(Matl,MaterialList):
        MatObj = Matl 
    elif isinstance(Matl,str):
        try:
            MatObj = MaterialList.objects.get(Material=Matl)
        except:
            MatObj = MaterialList.objects.none()
    elif isinstance(Matl,int):
        try:
            MatObj = MaterialList.objects.get(pk=Matl)
        except:
            MatObj = MaterialList.objects.none()
    else:
        MatObj = MaterialList.objects.none()
        
    try:
        rec = CountSchedule.objects.get(CountDate=CtDate, Material=MatObj)
    except:
        rec = CountSchedule.objects.none()

    return rec

#####################################################################
#####################################################################
#####################################################################

@login_required
def fnUploadCountSchedSprsht(req):

    SprshtDateEpoch = WINDOWS_EPOCH

    def cleanupfld(fld, val):
        """
        fld is the name of the field in the ActualCount or MaterialList table
        val is the value to be cleaned for insertion into the fld
        Returns  {'usefld':usefld, 'cleanval': cleanval}
            usefld is a boolean indicating that val could/not be cleaned to the correct type
            cleanval is val in the correct type (if usefld==True)
        """
        cleanval = None

        if   fld == 'CountDate': 
            if isinstance(val,(calvindate, datetime.date, datetime.datetime)):
                usefld = True
                cleanval = calvindate(val).as_datetime()
            elif isinstance(val,int):
                usefld = True
                cleanval = from_excel(val,SprshtDateEpoch)
            else:
                usefld = isDate(val) 
                if (usefld != False):
                    cleanval = calvindate(usefld).as_datetime()
                    usefld = True
        elif fld in \
            ['org_id', 
            ]:
            try:
                cleanval = int(val)
                usefld = True
            except:
                usefld = False
        elif fld in \
            ['Material', 
             'Counter', 
             'Notes', 
             'Priority'
             'ReasonScheduled',
            ]:
            usefld = (val is not None)
            if usefld: cleanval = str(val)
        else:
            usefld = True
            cleanval = val
        
        return {'usefld':usefld, 'cleanval': cleanval}
    #end def cleanupfld

    if req.method == 'POST':
        UplResults = []
        nRowsAdded = 0
        SprshtRowNum = 0

        # save the file so we can open it as an excel file
        SprshtFile = req.FILES['SchdFile']
        svdir = getcParm('SAP-FILELOC')
        fName = svdir+"tmpSchd"+str(uuid.uuid4())+".xlsx"
        with open(fName, "wb") as destination:
            for chunk in SprshtFile.chunks():
                destination.write(chunk)

        wb = load_workbook(filename=fName, read_only=True)
        SprshtDateEpoch = wb.epoch
        if 'Schedule' in wb:
            ws = wb['Schedule']
        else:
            UplResults.append({'error':'This workbook does not contain a sheet named Schedule in the correct format'})
            ws = None

        if ws:
            SprshtcolmnNames = ws[1]
            SprshtREQUIREDFLDS = ['org_id','Material','CountDate']     
            SprshtcolmnMap = {}
            Sprsht_SSName_TableName_map = {
                    'org_id': 'org_id',         # org_id and Material will be converted to a Material_id
                    'Material': 'Material',     # org_id and Material will be converted to a Material_id
                    
                    'CountDate': 'CountDate',
                    'Counter': 'Counter',
                    'Priority': 'Priority',
                    'ReasonScheduled': 'ReasonScheduled',
                    'Notes': 'Notes',
                    }
            for col in SprshtcolmnNames:
                if col.value in Sprsht_SSName_TableName_map:
                    SprshtcolmnMap[Sprsht_SSName_TableName_map[col.value]] = col.column - 1
            
            HeaderGood = True
            for reqFld in SprshtREQUIREDFLDS:
                HeaderGood = HeaderGood and (reqFld in SprshtcolmnMap)
            if not HeaderGood:
                UplResults.append({'error':'The Schedule worksheet in this workbook has bad header row'})
                ws = None

        if ws:
            SprshtRowNum=1
            MAX_COUNT_ROWS = 5000
            for row in ws.iter_rows(min_row=SprshtRowNum+1, max_row=MAX_COUNT_ROWS, values_only=True):
                SprshtRowNum += 1

                # if no org given, check that Material unique.
                if 'org_id' not in SprshtcolmnMap:
                    spshtorg = None
                else:
                    spshtorg = cleanupfld('org_id', row[SprshtcolmnMap['org_id']])['cleanval']
                matlnum = cleanupfld('Material', row[SprshtcolmnMap['Material']])['cleanval']
                MatlKount =  MaterialList.objects.filter(Material=matlnum).count() 
                MatObj = None
                err_already_handled = False
                if spshtorg is None:
                    if MatlKount > 1:
                        UplResults.append({'error':matlnum+" is in multiple org_id's, but no org_id given ", 'rowNum':SprshtRowNum})
                        err_already_handled = True
                if MatlKount == 1:
                    MatObj = MaterialList.objects.get(Material=matlnum)
                    spshtorg = MatObj.org_id
                if MatlKount > 1:
                    MatObj = MaterialList.objects.get(org_id=spshtorg, Material=matlnum)

                if matlnum and not MatObj:
                    if not err_already_handled:
                        UplResults.append({'error':'either ' + matlnum + ' does not exist in MaterialList or incorrect org_id (' + str(spshtorg) + ') given', 'rowNum':SprshtRowNum})
                elif matlnum and MatObj:
                    requiredFields = {reqFld: False for reqFld in SprshtREQUIREDFLDS}

                    SRec = CountSchedule()
                    for fldName, colNum in SprshtcolmnMap.items():
                        # check/correct problematic data types
                        usefld, V = cleanupfld(fldName, row[colNum]).values()
                        if (V is not None):
                            if usefld:
                                if   fldName == 'CountDate': 
                                    setattr(SRec, fldName, V) 
                                    requiredFields['CountDate'] = True
                                elif fldName == 'Material': 
                                    setattr(SRec, fldName, MatObj)
                                    requiredFields['Material'] = True
                                elif fldName == 'Counter': 
                                    setattr(SRec, fldName, V)
                                    requiredFields['Counter'] = True
                                else:
                                    if hasattr(SRec, fldName): setattr(SRec, fldName, V)
                                #endif fldName == ...
                            else:
                                UplResults.append({'error':str(V)+' is invalid for '+fldName, 'rowNum':SprshtRowNum})
                            #endif usefld
                        #endif (V is not None)
                    #endfor fldName, colNum

                    # are all required fields present?
                    AllRequiredPresent = True
                    for keyname, Prsnt in requiredFields.items():
                        AllRequiredPresent = AllRequiredPresent and Prsnt
                        if not Prsnt:
                            UplResults.append({'error':keyname+' missing', 'rowNum':SprshtRowNum})

                    if AllRequiredPresent:
                        if fnCountScheduleRecordExists(SRec.CountDate, MatObj):
                            UplResults.append({'error':'Count alreaqdy scheduled for ' + str(MatObj) +' on '+ str(SRec.CountDate), 'rowNum':SprshtRowNum})
                        else:
                            SRec.save()
                            qs = type(SRec).objects.filter(pk=SRec.pk).values().first()
                            res = {'error': False, 'rowNum':SprshtRowNum, 'MaterialNum': str(MatObj) }
                            res.update(qs)      # tack the new record (along with its new pk) onto res
                                #QUESTION:  can I do this directly with SRec??
                            UplResults.append(res)
                            nRowsAdded += 1
                #endif matlnum and MatObj/not MatObj

            if SprshtRowNum >= MAX_COUNT_ROWS:
                UplResults.insert(0,{'error':f'Data in spreadsheet rows {MAX_COUNT_ROWS+1} and beyond are being ignored.'})
        #endif ws

        # close and kill temp files
        wb.close()
        os.remove(fName)

        cntext = {
            'UplResults':UplResults, 
            'nRowsRead':SprshtRowNum, 
            'nRowsAdded':nRowsAdded,
                }
        templt = 'frm_uploadSchedCount_Success.html'
    else:
        cntext = {
                }
        templt = 'frm_UploadSchedCountSprdsht.html'
    #endif

    return render(req, templt, cntext)


#####################################################################
#####################################################################
#####################################################################

class CountScheduleListForm(LoginRequiredMixin, ListView):
    ordering = ['-CountDate', 'Material']
    context_object_name = 'CtSchdList'
    template_name = 'frm_CountScheduleList.html'
    
    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self._user = req.user
        return super().setup(req, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        return VIEW_countschedule.objects.all().order_by(*self.ordering)

    # def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    #     return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return HttpResponse('Stop rushing me!!')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        cntext = super().get_context_data(**kwargs)

        return cntext


#####################################################################
#####################################################################
#####################################################################

class CountWorksheetReport(LoginRequiredMixin, ListView):
    ordering = ['Counter', 'Material__Material']
    context_object_name = 'CtSchd'
    template_name = 'rpt_CountWksht.html'
    
    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self._user = req.user
        if 'CountDate' in kwargs: self.CountDate = kwargs['CountDate']
        else: self.CountDate = calvindate().today().as_datetime()
        if isinstance(self.CountDate,str): self.CountDate = calvindate(self.CountDate).as_datetime()
        return super().setup(req, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        SAP_SOH = fnSAPList(self.CountDate)
        self.SAPDate = SAP_SOH['SAPDate']
        qs = CountSchedule.objects.filter(CountDate=self.CountDate).order_by(*self.ordering).select_related('Material','Material__PartType')
        qs = qs.annotate(LastFoundAt=Value(''), SAPQty=Value(0), MaterialBarCode=Value(''), Material_org=Value(''))
        Mat3char = None
        lastCtr = None
        for rec in qs:
            strMatlNum = rec.Material.Material
            if MaterialList.objects.filter(Material=rec.Material.Material).exclude(pk=rec.Material.pk).exists():
                 strMatlNum += ' (' + str(rec.Material.org) + ')'
            rec.Material_org = strMatlNum
            if strMatlNum[0:3] != Mat3char:
                rec.NewMat3char = True
                Mat3char = strMatlNum[0:3]
            else:
                rec.NewMat3char = False
            if lastCtr != rec.Counter:
                rec.NewCounter = True
                lastCtr = rec.Counter
            else:
                rec.NewCounter = False
            bcstr = Code128(str(strMatlNum)).render(writer_options={'module_height':7.0,'module_width':0.25,'quiet_zone':0.1,'write_text':True,'text_distance':3.5})
            bcstr = str(bcstr).replace("b'","").replace('\\r','').replace('\\n','').replace("'","")
            rec.MaterialBarCode = bcstr
            rec.LastFoundAt = LastFoundAt(rec.Material)
            zoneList = []
            for lz in Location_WorksheetZone.objects.all().values('location','zone'):
                if regex.search(lz['location'],rec.LastFoundAt['lastFoundAt']):    #if lz['location'] in rec.LastFoundAt['lastFoundAt']: 
                    zoneList.append(lz['zone'])
            rec.Zones = zoneList
            for SAProw in SAP_SOH['SAPTable'].filter(Material=rec.Material): 
                rec.SAPQty += SAProw.Amount*SAProw.mult

        return qs

    # def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    #     return super().get(request, *args, **kwargs)

    # there is no POST processing; it's a r/o report
    # def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    #     return HttpResponse('Stop rushing me!!')

    def render_to_response(self, context: Dict[str, Any], **response_kwargs: Any) -> HttpResponse:
        zoneListqs = WorksheetZones.objects.order_by('zone')
        numZones = zoneListqs.last().zone
        # oops -- I need zoneList to be an array with '' if there's no zone
        zoneList = [''] * numZones
        for Z in zoneListqs:
            zoneList[Z.zone-1] = Z.zoneName

        # collect the list of Counters so that tabs can be built in the html
        CounterList = CountSchedule.objects.filter(CountDate=self.CountDate).order_by('Counter').values('Counter').distinct()

        context.update({
                'zoneList': zoneList,
                'CounterList': CounterList,
                'CountDate': self.CountDate,     # .as_datetime(), -- this was done in setup()
                'SAP_Updated_at': self.SAPDate,
                })

        return super().render_to_response(context, **response_kwargs)

