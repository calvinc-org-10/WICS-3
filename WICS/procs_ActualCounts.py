import datetime
import os, uuid
from tkinter import NO
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import render
from django.views.generic import ListView
from typing import *
from cMenu.models import getcParm
from cMenu.utils import makebool, isDate, WrapInQuotes, calvindate
from mathematical_expressions_parser.eval import evaluate
from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel, WINDOWS_EPOCH
from WICS.models import ActualCounts, MaterialList, CountSchedule, Organizations
from WICS.procs_SAP import fnSAPList


##############################################################
##############################################################
##############################################################

@login_required
def fnUploadActCountSprsht(req):

    CountSprshtDateEpoch = WINDOWS_EPOCH

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
                cleanval = from_excel(val,CountSprshtDateEpoch)
            else:
                usefld = isDate(val) 
                if (usefld != False):
                    cleanval = calvindate(usefld).as_datetime()
                    usefld = True
        elif fld in \
            ['CTD_QTY_Expr', 
             ]:
            if isinstance(val,str):
                if val[0] == '=':
                    val = val[1:]
            try:
                v = evaluate(str(val))
            except (SyntaxError, NameError, TypeError, ZeroDivisionError):
                v = "-- INVALID --"
            usefld = (v!="-- INVALID --")
            cleanval = str(val) if (v != "--INVALID--") else None
        elif fld in \
            ['org_id', 
             'LocationOnly',
             'FLAG_PossiblyNotRecieved', 
             'FLAG_MovementDuringCount',
             ]:
            try:
                cleanval = int(val)
                usefld = True
            except:
                usefld = False
        elif fld in \
            ['Material', 
             'Counter', 
             'BLDG', 
             'LOCATION', 
             'Notes', 
             'TypicalContainerQty', 
             'TypicalPalletQty',
             'PKGID_Desc',	
             'TAGQTY',
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
        CountSprshtFile = req.FILES['CEFile']
        svdir = getcParm('SAP-FILELOC')
        fName = svdir+"tmpCE"+str(uuid.uuid4())+".xlsx"
        with open(fName, "wb") as destination:
            for chunk in CountSprshtFile.chunks():
                destination.write(chunk)

        wb = load_workbook(filename=fName, read_only=True)
        CountSprshtDateEpoch = wb.epoch
        if 'Counts' in wb:
            ws = wb['Counts']
        else:
            UplResults.append({'error':'This workbook does not contain a sheet named Counts in the correct format'})
            ws = None

        if ws:
            CountSprshtcolmnNames = ws[1]
            CountSprshtREQUIREDFLDS = ['Material','CountDate','Counter','BLDG']     
                # LocationOnly/CTD_QTY_Expr handled separately since at least one must be present and both can be
            CountSprshtcolmnMap = {}
            CountSprsht_SSName_TableName_map = {
                    'CountDate': 'CountDate',
                    'Counter': 'Counter',
                    'BLDG': 'BLDG',
                    'LOCATION': 'LOCATION',
                    'org_id': 'org_id',
                    'Material': 'Material',
                    'LocationOnly': 'LocationOnly',
                    'CTD_QTY_Expr': 'CTD_QTY_Expr',
                    'Typ Cntner Qty': 'TypicalContainerQty',
                    'Typ Plt Qty': 'TypicalPalletQty',
                    'Notes': 'Notes',
                    'PKGID_Desc': 'PKGID_Desc',
                    'TAGQTY': 'TAGQTY',
                    'Poss Not Rcvd': 'FLAG_PossiblyNotRecieved',
                    'Mvmt Dur Ct': 'FLAG_MovementDuringCount',
                    }
            for col in CountSprshtcolmnNames:
                if col.value in CountSprsht_SSName_TableName_map:
                    CountSprshtcolmnMap[CountSprsht_SSName_TableName_map[col.value]] = col.column - 1
            
            HeaderGood = True
            for reqFld in CountSprshtREQUIREDFLDS:
                HeaderGood = HeaderGood and (reqFld in CountSprshtcolmnMap)
            if not HeaderGood:
                UplResults.append({'error':'The Counts worksheet in this workbook has bad header row'})
                ws = None

        if ws:
            SprshtRowNum=1
            # SprshtRowNum = 2  # skip row 2 because it holds hints for the kids, not a count - nope, let old spreadsheet work, too
            MAX_COUNT_ROWS = 5000
            for row in ws.iter_rows(min_row=SprshtRowNum+1, max_row=MAX_COUNT_ROWS, values_only=True):
                SprshtRowNum += 1

                # if no org given, check that Material unique.
                if 'org_id' not in CountSprshtcolmnMap:
                    spshtorg = None
                else:
                    spshtorg = cleanupfld('org_id', row[CountSprshtcolmnMap['org_id']])['cleanval']
                matlnum = cleanupfld('Material', row[CountSprshtcolmnMap['Material']])['cleanval']
                MatlKount =  MaterialList.objects.filter(Material=matlnum).count() 
                MatObj = None
                err_already_handled = False
                if spshtorg is None:
                    if MatlKount > 1:
                        UplResults.append({'error':matlnum+" in in multiple org_id's, but no org_id given ", 'rowNum':SprshtRowNum})
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
                    requiredFields = {reqFld: False for reqFld in CountSprshtREQUIREDFLDS}
                    requiredFields['Both LocationOnly and CTD_QTY'] = False

                    MatChanged = False
                    SRec = ActualCounts()
                    for fldName, colNum in CountSprshtcolmnMap.items():
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
                                elif fldName == 'BLDG': 
                                    setattr(SRec, fldName, V)
                                    requiredFields['BLDG'] = True
                                elif fldName == 'LocationOnly': 
                                    setattr(SRec, fldName, makebool(V))
                                    requiredFields['Both LocationOnly and CTD_QTY'] = True
                                elif fldName == 'CTD_QTY_Expr': 
                                    setattr(SRec, fldName, V)
                                    requiredFields['Both LocationOnly and CTD_QTY'] = True
                                elif fldName == 'TypicalContainerQty' \
                                or fldName == 'TypicalPalletQty':
                                    if V == '' or V == None: V = 0
                                    if V != 0 and V != getattr(MatObj,fldName,0): 
                                        setattr(MatObj, fldName, V)
                                        MatChanged = True
                                else:
                                    if hasattr(SRec, fldName): setattr(SRec, fldName, V)
                            else:
                                UplResults.append({'error':str(V)+' is invalid for '+fldName, 'rowNum':SprshtRowNum})
                                

                    # are all required fields present?
                    AllRequiredPresent = True
                    for keyname, Prsnt in requiredFields.items():
                        AllRequiredPresent = AllRequiredPresent and Prsnt
                        if not Prsnt:
                            UplResults.append({'error':keyname+' missing', 'rowNum':SprshtRowNum})

                    if AllRequiredPresent:
                        SRec.save()
                        if MatChanged: MatObj.save()
                        qs = type(SRec).objects.filter(pk=SRec.pk).values().first()
                        res = {'error': False, 'rowNum':SprshtRowNum, 'TypicalQty':MatChanged, 'MaterialNum': str(MatObj) }
                        res.update(qs)      # tack the new record (along with its new pk) onto res
                            #QUESTION:  can I do this directly with SRec??
                        UplResults.append(res)
                        nRowsAdded += 1

            if SprshtRowNum >= MAX_COUNT_ROWS:
                UplResults.insert(0,{'error':f'Data in spreadsheet rows {MAX_COUNT_ROWS+1} and beyond are being ignored.'})

        # close and kill temp files
        wb.close()
        os.remove(fName)

        cntext = {'UplResults':UplResults, 'nRowsRead':SprshtRowNum, 'nRowsAdded':nRowsAdded,
                }
        templt = 'frm_uploadCountEntry_Success.html'
    else:
        cntext = {
                }
        templt = 'frm_UploadCountEntrySprdsht.html'
    #endif

    return render(req, templt, cntext)

#####################################################################
#####################################################################
#####################################################################

class ActualCountListForm(LoginRequiredMixin, ListView):
    ordering = ['-CountDate', 'Material']
    context_object_name = 'ActCtList'
    template_name = 'frm_ActualCountList.html'
    
    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self._user = req.user
        return super().setup(req, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        return ActualCounts.objects.all().order_by(*self.ordering)
        # return super().get_queryset()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        cntext = super().get_context_data(**kwargs)

        return cntext

    # def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    #     return super().get(request, *args, **kwargs)

    # def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    #     return HttpResponse('Not needed!!')


#####################################################################
#####################################################################
#####################################################################

@login_required
def fnCountSummaryReqRpt(req, passedCountDate='CURRENT_DATE'):
    return fnCountSummaryRpt(req, passedCountDate, Rptvariation='REQ')
@login_required
def fnCountSummaryRpt (req, passedCountDate='CURRENT_DATE', Rptvariation=None):

    # get the SAP data
    dtobj_pDate = isDate(passedCountDate)
    if not dtobj_pDate: dtobj_pDate = calvindate().as_datetime()
    SAP_SOH = fnSAPList(dtobj_pDate)
    
    def CreateOutputRows(raw_qs, Eval_CTDQTY=True):
        def SummaryLine(lastrow):
            # summarize last Matl
            # total SAP Numbers
            SAPTot = 0
            outputline = dict()
            outputline['type'] = 'Summary'
            outputline['SAPNum'] = []
            for SAProw in SAP_SOH['SAPTable'].filter(Material=lastrow['Material']): 
                outputline['SAPNum'].append((SAProw.StorageLocation, SAProw.Amount, SAProw.BaseUnitofMeasure))
                SAPTot += SAProw.Amount*SAProw.mult
            outputline['TypicalContainerQty'] = lastrow['TypicalContainerQty']
            outputline['TypicalPalletQty'] = lastrow['TypicalPalletQty']
            outputline['Material'] = lastrow['Material']
            outputline['Material_id'] = lastrow['Material_id']
            outputline['SchedCounter'] = lastrow['SchedCounter']
            outputline['Requestor'] = lastrow['Requestor']
            outputline['RequestFilled'] = lastrow['RequestFilled']
            outputline['PartType'] = lastrow['PartType']
            outputline['CountTotal'] = lastrow['TotalCounted']
            outputline['SAPTotal'] = SAPTot
            outputline['Diff'] = lastrow['TotalCounted'] - SAPTot
            divsr = 1
            if lastrow['TotalCounted']!=0 or SAPTot!=0: divsr = max(lastrow['TotalCounted'], SAPTot)
            outputline['Accuracy'] = min(lastrow['TotalCounted'], SAPTot) / divsr * 100
            outputline['ReasonScheduled'] = lastrow['ReasonScheduled']
            outputline['SchedNotes'] = lastrow['SchedNotes']
            outputline['MatlNotes'] = lastrow['MatlNotes']
            #outputrows.append(outputline)

            return outputline
        # end def SummaryLine

        def CreateLastrow(rawrow):
            lastrow = dict()
            lastrow['Material'] = rawrow.Matl_PartNum
            lastrow['Material_id'] = rawrow.matl_id
            lastrow['SchedCounter'] = rawrow.cs_Counter
            lastrow['Requestor'] = rawrow.Requestor
            lastrow['RequestFilled'] = rawrow.RequestFilled
            lastrow['PartType'] = rawrow.PartType
            lastrow['TotalCounted'] = 0
            lastrow['SchedNotes'] = rawrow.cs_Notes
            lastrow['TypicalContainerQty'] = rawrow.TypicalContainerQty
            lastrow['TypicalPalletQty'] = rawrow.TypicalPalletQty
            lastrow['MatlNotes'] = rawrow.mtl_Notes
            lastrow['ReasonScheduled'] = rawrow.cs_ReasonScheduled

            return lastrow
        # end def CreateLastRow

        def DetailLine(rawrow, Eval_CTDQTY=True):
            outputline = dict()
            outputline['type'] = 'Detail'
            outputline['CycCtID'] = rawrow.ac_CycCtID
            outputline['Material'] = rawrow.Matl_PartNum
            outputline['Material_id'] = rawrow.matl_id
            outputline['org_id'] = rawrow.org_id
            outputline['orgName'] = rawrow.OrgName
            outputline['ActCounter'] = rawrow.ac_Counter
            outputline['BLDG'] = rawrow.ac_BLDG
            outputline['LOCATION'] = rawrow.ac_LOCATION
            outputline['PKGID'] = rawrow.ac_PKGID_Desc
            outputline['TAGQTY'] = rawrow.ac_TAGQTY
            outputline['PossNotRec'] = rawrow.FLAG_PossiblyNotRecieved
            outputline['MovDurCt'] = rawrow.FLAG_MovementDuringCount
            outputline['CTD_QTY_Expr'] = rawrow.ac_CTD_QTY_Expr
            if Eval_CTDQTY:
                try:
                    outputline['CTD_QTY_Eval'] = evaluate(rawrow.ac_CTD_QTY_Expr)
                    # do next line at caller
                    # lastrow['TotalCounted'] += outputline['CTD_QTY_Eval']
                except:
                    # Exception('bad expression:'+rawrow.ac_CTD_QTY_Expr)
                    outputline['CTD_QTY_Eval'] = "????"
            else:
                outputline['CTD_QTY_Eval'] = "----"
            outputline['ActCountNotes'] = rawrow.ac_Notes
            # outputrows.append(outputline)

            return outputline
        #end def DetailLine
        
        outputrows = []
        lastrow = {'Material_id': None}
        for rawrow in raw_qs:
            if rawrow.matl_id != lastrow['Material_id']:     # new Matl
                if outputrows:
                    outputrows.append(SummaryLine(lastrow))
                # no else -  if outputrows is empty, this is the first row, so keep going

                # this new material is now the "old" one; save values for when it switches, and we do the above block
                # this whole block becomes
                lastrow = CreateLastrow(rawrow)
            #endif

            # process this row
            outputline = DetailLine(rawrow, Eval_CTDQTY)
            outputrows.append(outputline)
            if isinstance(outputline['CTD_QTY_Eval'],(int,float)): lastrow['TotalCounted'] += outputline['CTD_QTY_Eval']
        # endfor
        # need to do the summary on the last row
        if outputrows:
            # summarize last Matl
            outputrows.append(SummaryLine(lastrow))
        
        return outputrows
    #end def CreateOutputRows
        
    ### main body of fnCountSummaryRpt

    SummaryReport = []

    for org in Organizations.objects.all():
        # group by org_id
        fldlist = "0 as id, cs.id as cs_id, cs.CountDate as cs_CountDate , cs.Counter as cs_Counter" \
            ", cs.Priority as cs_Priority, cs.ReasonScheduled as cs_ReasonScheduled" \
            ", cs.Requestor, cs.RequestFilled" \
            ", cs.Notes as cs_Notes" \
            ", ac.id as ac_id, ac.CountDate as ac_CountDate, ac.CycCtID as ac_CycCtID, ac.Counter as ac_Counter" \
            ", ac.LocationOnly as ac_LocationOnly, ac.CTD_QTY_Expr as ac_CTD_QTY_Expr, ac.BLDG as ac_BLDG" \
            ", ac.LOCATION as ac_LOCATION, ac.PKGID_Desc as ac_PKGID_Desc, ac.TAGQTY as ac_TAGQTY" \
            ", ac.FLAG_PossiblyNotRecieved, ac.FLAG_MovementDuringCount, ac.Notes as ac_Notes" \
            ", mtl.id as matl_id, mtl.org_id, mtl.OrgName" \
            ", mtl.Material_org as Matl_PartNum, mtl.PartType as PartType" \
            ", mtl.Description, mtl.TypicalContainerQty, mtl.TypicalPalletQty, mtl.Notes as mtl_Notes"
        if isDate(passedCountDate): datestr = WrapInQuotes(passedCountDate,"'","'")
        else: datestr = passedCountDate
        org_condition = '(mtl.org_id = ' + str(org.pk) + ')'
        date_condition = '(ac.CountDate = ' + datestr + ' OR cs.CountDate = ' + datestr + ') '
        order_by = 'Matl_PartNum'

        A_Sched_Ctd_from = 'WICS_countschedule cs INNER JOIN VIEW_materials mtl INNER JOIN WICS_actualcounts ac'    
        A_Sched_Ctd_joinon = 'cs.CountDate=ac.CountDate AND cs.Material_id=ac.Material_id AND ac.Material_id=mtl.id'    
        A_Sched_Ctd_where = ''
        if Rptvariation == 'REQ':
            if A_Sched_Ctd_where:  A_Sched_Ctd_where += ' AND ' 
            A_Sched_Ctd_where += 'Requestor IS NOT NULL'
        A_Sched_Ctd_sql = 'SELECT ' + fldlist + \
            ' FROM ' + A_Sched_Ctd_from + \
            ' ON ' + A_Sched_Ctd_joinon + \
            ' WHERE NOT ac.LocationOnly AND ' + date_condition + ' AND ' + org_condition
        if A_Sched_Ctd_where:
            A_Sched_Ctd_sql += ' AND ' + A_Sched_Ctd_where
        A_Sched_Ctd_sql += ' ORDER BY ' + order_by
        A_Sched_Ctd_qs = CountSchedule.objects.raw(A_Sched_Ctd_sql)
        # build display lines
        ttl = 'Scheduled and Counted'
        if Rptvariation == 'REQ':
            ttl = 'Requested and Counted'            
        SummaryReport.append({
                    'org':org,
                    'Title':ttl,
                    'outputrows': CreateOutputRows(A_Sched_Ctd_qs)
                    })

        if Rptvariation is None:
            B_UnSched_Ctd_from = 'WICS_countschedule cs RIGHT JOIN' \
                ' (WICS_actualcounts ac INNER JOIN VIEW_materials mtl ON ac.Material_id=mtl.id)'
            B_UnSched_Ctd_joinon = 'cs.CountDate=ac.CountDate AND cs.Material_id=ac.Material_id'
            B_UnSched_Ctd_where = '(cs.id IS NULL)'
            B_UnSched_Ctd_sql = 'SELECT ' + fldlist + ' ' + \
                ' FROM ' + B_UnSched_Ctd_from + \
                ' ON ' + B_UnSched_Ctd_joinon + \
                ' WHERE NOT ac.LocationOnly AND ' + date_condition + ' AND ' + org_condition + \
                ' AND ' + B_UnSched_Ctd_where + \
                ' ORDER BY ' + order_by
            B_UnSched_Ctd_qs = CountSchedule.objects.raw(B_UnSched_Ctd_sql)
            SummaryReport.append({
                        'org':org,
                        'Title':'UnScheduled',
                        'outputrows': CreateOutputRows(B_UnSched_Ctd_qs)
                        })
        
        C_Sched_NotCtd_Ctd_from = '(WICS_countschedule cs INNER JOIN VIEW_materials mtl ON cs.Material_id=mtl.id)' \
            ' LEFT JOIN WICS_actualcounts ac'
        C_Sched_NotCtd_Ctd_joinon = 'cs.CountDate=ac.CountDate AND cs.Material_id=ac.Material_id'
        C_Sched_NotCtd_Ctd_where = '(ac.id IS NULL)'
        if Rptvariation == 'REQ':
            if C_Sched_NotCtd_Ctd_where:  C_Sched_NotCtd_Ctd_where += ' AND ' 
            C_Sched_NotCtd_Ctd_where += '(Requestor IS NOT NULL)'
        C_Sched_NotCtd_Ctd_sql = 'SELECT ' + fldlist + ' ' + \
            ' FROM ' + C_Sched_NotCtd_Ctd_from + \
            ' ON ' + C_Sched_NotCtd_Ctd_joinon + \
            ' WHERE ' + date_condition + ' AND ' + org_condition
        if C_Sched_NotCtd_Ctd_where:
            C_Sched_NotCtd_Ctd_sql += ' AND ' + C_Sched_NotCtd_Ctd_where
        C_Sched_NotCtd_Ctd_sql += ' ORDER BY ' + order_by
        C_Sched_NotCtd_Ctd_qs = CountSchedule.objects.raw(C_Sched_NotCtd_Ctd_sql)
        ttl = 'Scheduled but Not Counted'
        if Rptvariation == 'REQ':
            ttl = 'Requested but Not Counted'            
        SummaryReport.append({
                    'org':org,
                    'Title':ttl,
                    'outputrows': CreateOutputRows(C_Sched_NotCtd_Ctd_qs, Eval_CTDQTY=False)
                    })
    
    AccuracyCutoff = { 
                'DANGER': float(getcParm('ACCURACY-DANGER')),
                'SUCCESS': float(getcParm('ACCURACY-SUCCESS')),
                'WARNING': float(getcParm('ACCURACY-WARNING')),
                }

    # display the form
    cntext = {
            'variation': Rptvariation,
            'CountDate': dtobj_pDate,
            'SAPDate': SAP_SOH['SAPDate'],
            'AccuracyCutoff': AccuracyCutoff,
            'SummaryReport': SummaryReport,
            }
    templt = 'rpt_CountSummary.html'
    return render(req, templt, cntext)


