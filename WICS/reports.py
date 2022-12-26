import datetime
from userprofiles.models import WICSuser
from cMenu.utils import WrapInQuotes
from WICS.models import ActualCounts, CountSchedule, MaterialList
from WICS.SAPLists import fnSAPList
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q


@login_required
def fnCountSummaryRptPreview (req, passedCountDate=None):
    _userorg = WICSuser.objects.get(user=req.user).org

    #TODO:  Incorporate SAP, summary calculations

    fldlist = "0 as id, cs.id as cs_id, cs.CountDate as cs_CountDate , cs.Counter as cs_Counter" \
        ", cs.Priority as cs_Priority, cs.ReasonScheduled as cs_ReasonScheduled, cs.CMPrintFlag as cs_CMPrintFlag" \
        ", cs.Notes as cs_Notes" \
        ", ac.id as ac_id, ac.CountDate as ac_CountDate, ac.CycCtID as ac_CycCtID, ac.Counter as ac_Counter" \
        ", ac.LocationOnly as ac_LocationOnly, ac.CTD_QTY_Expr as ac_CTD_QTY_Expr, ac.BLDG as ac_BLDG" \
        ", ac.LOCATION as ac_LOCATION, ac.PKGID_Desc as ac_PKGID_Desc, ac.TAGQTY as ac_TAGQTY" \
        ", ac.FLAG_PossiblyNotRecieved, ac.FLAG_MovementDuringCount, ac.Notes as ac_Notes" \
        ", mtl.Material as Matl_PartNum, (SELECT WhsePartType FROM WICS_WhsePartTypes WHERE id=mtl.PartType_id) as PartType" \
        ", mtl.Description, mtl.Notes as mtl_Notes"
    org_condition = '(ac.org_id = ' + str(_userorg.pk) + ' OR cs.org_id = ' + str(_userorg.pk) + ') '
    #datestr = 'CURRENT_DATE'
    datestrM = "2022-10-07"
    datestr = WrapInQuotes(datestrM)
    if passedCountDate: datestr = WrapInQuotes(passedCountDate,"'","'")
    date_condition = '(ac.CountDate = ' + datestr + ' OR cs.CountDate = ' + datestr + ') '
    order_by = 'Matl_PartNum'

    # get the SAP data
    SAP_SOH = fnSAPList(_userorg)
    
    A_Sched_Ctd_from = 'WICS_countschedule cs INNER JOIN WICS_materiallist mtl INNER JOIN WICS_actualcounts ac'    
    A_Sched_Ctd_joinon = 'cs.CountDate=ac.CountDate AND cs.Material_id=ac.Material_id AND ac.Material_id=mtl.id'    
    A_Sched_Ctd_where = ''
    A_Sched_Ctd_sql = 'SELECT ' + fldlist + \
        ' FROM ' + A_Sched_Ctd_from + \
        ' ON ' + A_Sched_Ctd_joinon + \
        ' WHERE NOT ac.LocationOnly AND ' + org_condition + ' AND ' + date_condition + \
        ' ORDER BY ' + order_by
        # + ' AND ' + A_Sched_Ctd_where
    A_Sched_Ctd_qs = CountSchedule.objects.raw(A_Sched_Ctd_sql)
    # build display lines
    raw_qs = A_Sched_Ctd_qs
    outputrows = []
    lastrow = {'Material': None}
    for rawrow in raw_qs:
        if rawrow.Matl_PartNum != lastrow['Material']:     # new Matl
            if outputrows:
                # summarize last Matl
                # total SAP Numbers
                SAPTot = 0
                outputline = dict()
                outputline['type'] = 'Summary'
                outputline['SAPNum'] = []
                for SAProw in SAP_SOH['SAPTable']:  # change this to a loop until SAProw.Material > rawrow.Matl_PartNum or SAPRow exhausted
                    if SAProw.Material == lastrow['Material']:
                        outputline['SAPNum'].append((SAProw.StorageLocation, SAProw.Amount))
                        SAPTot += SAProw.Amount
                
                outputline['Material'] = lastrow['Material']
                outputline['PartType'] = lastrow['PartType']
                outputline['CountTotal'] = lastrow['TotalCounted']
                outputline['SAPTotal'] = SAPTot
                outputline['Diff'] = lastrow['TotalCounted'] - SAPTot
                divsr = 1
                if lastrow['TotalCounted']!=0 or SAPTot!=0: divsr = max(lastrow['TotalCounted'], SAPTot)
                outputline['Accuracy'] = min(lastrow['TotalCounted'], SAPTot) / divsr * 100
                outputline['CMFlag'] = lastrow['CMFlag']
                outputline['ReasonScheduled'] = lastrow['ReasonScheduled']
                outputline['SchedNotes'] = lastrow['SchedNotes']
                outputline['MatlNotes'] = lastrow['MatlNotes']
                outputrows.append(outputline)
            # no else -  if outputrows is empty, this is the first row, so keep going

            # this new material is now the "old" one; save values for when it switches, and we do the above block
            lastrow['Material'] = rawrow.Matl_PartNum
            lastrow['PartType'] = rawrow.PartType
            lastrow['TotalCounted'] = 0
            lastrow['CMFlag'] = rawrow.cs_CMPrintFlag
            lastrow['SchedNotes'] = rawrow.cs_Notes
            lastrow['MatlNotes'] = rawrow.mtl_Notes
            lastrow['ReasonScheduled'] = rawrow.cs_ReasonScheduled
        #endif

        # process this row
        outputline = {}
        outputline['type'] = 'Detail'
        outputline['CycCtID'] = rawrow.ac_CycCtID
        outputline['Material'] = rawrow.Matl_PartNum
        outputline['SchedCounter'] = rawrow.cs_Counter
        outputline['ActCounter'] = rawrow.ac_Counter
        outputline['BLDG'] = rawrow.ac_BLDG
        outputline['LOCATION'] = rawrow.ac_LOCATION
        outputline['PKGID'] = rawrow.ac_PKGID_Desc
        outputline['TAGQTY'] = rawrow.ac_TAGQTY
        outputline['PossNotRec'] = rawrow.FLAG_PossiblyNotRecieved
        outputline['MovDurCt'] = rawrow.FLAG_MovementDuringCount
        outputline['CTD_QTY_Expr'] = rawrow.ac_CTD_QTY_Expr
        outputline['CTD_QTY_Eval'] = eval(rawrow.ac_CTD_QTY_Expr)   # yes, I know the risks - I'll write my own parser later ...
        lastrow['TotalCounted'] += outputline['CTD_QTY_Eval']
        outputline['ActCountNotes'] = rawrow.ac_Notes
        outputrows.append(outputline)
    # endfor
    # need to do the summary on the last row
    if outputrows:
        # summarize last Matl
        # total SAP Numbers
        SAPTot = 0
        outputline = dict()
        outputline['type'] = 'Summary'
        outputline['SAPNum'] = []
        for SAProw in SAP_SOH['SAPTable']:  # change this to a loop until SAProw.Material > rawrow.Matl_PartNum or SAPRow exhausted
            if SAProw.Material == lastrow['Material']:
                outputline['SAPNum'].append((SAProw.StorageLocation, SAProw.Amount))
                SAPTot += SAProw.Amount
        
        outputline['Material'] = lastrow['Material']
        outputline['PartType'] = lastrow['PartType']
        outputline['CountTotal'] = lastrow['TotalCounted']
        outputline['SAPTotal'] = SAPTot
        outputline['Diff'] = lastrow['TotalCounted'] - SAPTot
        divsr = 1
        if lastrow['TotalCounted']!=0 or SAPTot!=0: divsr = max(lastrow['TotalCounted'], SAPTot)
        outputline['Accuracy'] = min(lastrow['TotalCounted'], SAPTot) / divsr * 100
        outputline['CMFlag'] = lastrow['CMFlag']
        outputline['ReasonScheduled'] = lastrow['ReasonScheduled']
        outputline['SchedNotes'] = lastrow['SchedNotes']
        outputline['MatlNotes'] = lastrow['MatlNotes']
        outputrows.append(outputline)
    A_Sched_Ctd_outputrows = outputrows

    B_UnSched_Ctd_from = 'WICS_countschedule cs RIGHT JOIN' \
        ' (WICS_actualcounts ac INNER JOIN WICS_materiallist mtl ON ac.Material_id=mtl.id)'
    B_UnSched_Ctd_joinon = 'cs.CountDate=ac.CountDate AND cs.Material_id=ac.Material_id'
    B_UnSched_Ctd_where = '(cs.id IS NULL)'
    B_UnSched_Ctd_sql = 'SELECT ' + fldlist + ' ' + \
        ' FROM ' + B_UnSched_Ctd_from + \
        ' ON ' + B_UnSched_Ctd_joinon + \
        ' WHERE NOT ac.LocationOnly AND ' + org_condition + ' AND ' + date_condition + \
        ' AND ' + B_UnSched_Ctd_where + \
        ' ORDER BY ' + order_by
    B_UnSched_Ctd_qs = CountSchedule.objects.raw(B_UnSched_Ctd_sql)
    # build display lines
    raw_qs = B_UnSched_Ctd_qs
    outputrows = []
    lastrow = {'Material': None}
    for rawrow in raw_qs:
        if rawrow.Matl_PartNum != lastrow['Material']:     # new Matl
            if outputrows:
                # summarize last Matl
                # total SAP Numbers
                SAPTot = 0
                outputline = dict()
                outputline['type'] = 'Summary'
                outputline['SAPNum'] = []
                for SAProw in SAP_SOH['SAPTable']:  # change this to a loop until SAProw.Material > rawrow.Matl_PartNum or SAPRow exhausted
                    if SAProw.Material == lastrow['Material']:
                        outputline['SAPNum'].append((SAProw.StorageLocation, SAProw.Amount))
                        SAPTot += SAProw.Amount
                
                outputline['Material'] = lastrow['Material']
                outputline['PartType'] = lastrow['PartType']
                outputline['CountTotal'] = lastrow['TotalCounted']
                outputline['SAPTotal'] = SAPTot
                outputline['Diff'] = lastrow['TotalCounted'] - SAPTot
                divsr = 1
                if lastrow['TotalCounted']!=0 or SAPTot!=0: divsr = max(lastrow['TotalCounted'], SAPTot)
                outputline['Accuracy'] = min(lastrow['TotalCounted'], SAPTot) / divsr * 100
                outputline['CMFlag'] = lastrow['CMFlag']
                outputline['ReasonScheduled'] = lastrow['ReasonScheduled']
                outputline['SchedNotes'] = lastrow['SchedNotes']
                outputline['MatlNotes'] = lastrow['MatlNotes']
                outputrows.append(outputline)
            # no else -  if outputrows is empty, this is the first row, so keep going

            # this new material is now the "old" one; save values for when it switches, and we do the above block
            lastrow['Material'] = rawrow.Matl_PartNum
            lastrow['PartType'] = rawrow.PartType
            lastrow['TotalCounted'] = 0
            lastrow['CMFlag'] = rawrow.cs_CMPrintFlag
            lastrow['SchedNotes'] = rawrow.cs_Notes
            lastrow['MatlNotes'] = rawrow.mtl_Notes
            lastrow['ReasonScheduled'] = rawrow.cs_ReasonScheduled
        #endif

        # process this row
        outputline = {}
        outputline['type'] = 'Detail'
        outputline['CycCtID'] = rawrow.ac_CycCtID
        outputline['Material'] = rawrow.Matl_PartNum
        outputline['SchedCounter'] = rawrow.cs_Counter
        outputline['ActCounter'] = rawrow.ac_Counter
        outputline['BLDG'] = rawrow.ac_BLDG
        outputline['LOCATION'] = rawrow.ac_LOCATION
        outputline['PKGID'] = rawrow.ac_PKGID_Desc
        outputline['TAGQTY'] = rawrow.ac_TAGQTY
        outputline['PossNotRec'] = rawrow.FLAG_PossiblyNotRecieved
        outputline['MovDurCt'] = rawrow.FLAG_MovementDuringCount
        outputline['CTD_QTY_Expr'] = rawrow.ac_CTD_QTY_Expr
        outputline['CTD_QTY_Eval'] = eval(rawrow.ac_CTD_QTY_Expr)   # yes, I know the risks - I'll write my own parser later ...
        lastrow['TotalCounted'] += outputline['CTD_QTY_Eval']
        outputline['ActCountNotes'] = rawrow.ac_Notes
        outputrows.append(outputline)
    # endfor
    # need to do the summary on the last row
    if outputrows:
        # summarize last Matl
        # total SAP Numbers
        SAPTot = 0
        outputline = dict()
        outputline['type'] = 'Summary'
        outputline['SAPNum'] = []
        for SAProw in SAP_SOH['SAPTable']:  # change this to a loop until SAProw.Material > rawrow.Matl_PartNum or SAPRow exhausted
            if SAProw.Material == lastrow['Material']:
                outputline['SAPNum'].append((SAProw.StorageLocation, SAProw.Amount))
                SAPTot += SAProw.Amount
        
        outputline['Material'] = lastrow['Material']
        outputline['PartType'] = lastrow['PartType']
        outputline['CountTotal'] = lastrow['TotalCounted']
        outputline['SAPTotal'] = SAPTot
        outputline['Diff'] = lastrow['TotalCounted'] - SAPTot
        divsr = 1
        if lastrow['TotalCounted']!=0 or SAPTot!=0: divsr = max(lastrow['TotalCounted'], SAPTot)
        outputline['Accuracy'] = min(lastrow['TotalCounted'], SAPTot) / divsr * 100
        outputline['CMFlag'] = lastrow['CMFlag']
        outputline['ReasonScheduled'] = lastrow['ReasonScheduled']
        outputline['SchedNotes'] = lastrow['SchedNotes']
        outputline['MatlNotes'] = lastrow['MatlNotes']
        outputrows.append(outputline)
    B_UnSched_Ctd_outputrows = outputrows
    
    C_Sched_NotCtd_Ctd_from = '(WICS_countschedule cs INNER JOIN WICS_materiallist mtl ON cs.Material_id=mtl.id)' \
        ' LEFT JOIN WICS_actualcounts ac'
    C_Sched_NotCtd_Ctd_joinon = 'cs.CountDate=ac.CountDate AND cs.Material_id=ac.Material_id'
    C_Sched_NotCtd_Ctd_where = '(ac.id IS NULL)'
    C_Sched_NotCtd_Ctd_sql = 'SELECT ' + fldlist + ' ' + \
        ' FROM ' + C_Sched_NotCtd_Ctd_from + \
        ' ON ' + C_Sched_NotCtd_Ctd_joinon + \
        ' WHERE ' + org_condition + ' AND ' + date_condition + \
        ' AND ' + C_Sched_NotCtd_Ctd_where + \
        ' ORDER BY ' + order_by
    C_Sched_NotCtd_Ctd_qs = CountSchedule.objects.raw(C_Sched_NotCtd_Ctd_sql)
    # build display lines
    raw_qs = C_Sched_NotCtd_Ctd_qs
    outputrows = []
    lastrow = {'Material': None}
    for rawrow in raw_qs:
        if rawrow.Matl_PartNum != lastrow['Material']:     # new Matl
            if outputrows:
                # summarize last Matl
                # total SAP Numbers
                SAPTot = 0
                outputline = dict()
                outputline['type'] = 'Summary'
                outputline['SAPNum'] = []
                for SAProw in SAP_SOH['SAPTable']:  # change this to a loop until SAProw.Material > rawrow.Matl_PartNum or SAPRow exhausted
                    if SAProw.Material == lastrow['Material']:
                        outputline['SAPNum'].append((SAProw.StorageLocation, SAProw.Amount))
                        SAPTot += SAProw.Amount
                
                outputline['Material'] = lastrow['Material']
                outputline['PartType'] = lastrow['PartType']
                outputline['CountTotal'] = lastrow['TotalCounted']
                outputline['SAPTotal'] = SAPTot
                outputline['Diff'] = lastrow['TotalCounted'] - SAPTot
                divsr = 1
                if lastrow['TotalCounted']!=0 or SAPTot!=0: divsr = max(lastrow['TotalCounted'], SAPTot)
                outputline['Accuracy'] = min(lastrow['TotalCounted'], SAPTot) / divsr * 100
                outputline['CMFlag'] = lastrow['CMFlag']
                outputline['ReasonScheduled'] = lastrow['ReasonScheduled']
                outputline['SchedNotes'] = lastrow['SchedNotes']
                outputline['MatlNotes'] = lastrow['MatlNotes']
                outputrows.append(outputline)
            # no else -  if outputrows is empty, this is the first row, so keep going

            # this new material is now the "old" one; save values for when it switches, and we do the above block
            lastrow['Material'] = rawrow.Matl_PartNum
            lastrow['PartType'] = rawrow.PartType
            lastrow['TotalCounted'] = 0
            lastrow['CMFlag'] = rawrow.cs_CMPrintFlag
            lastrow['SchedNotes'] = rawrow.cs_Notes
            lastrow['MatlNotes'] = rawrow.mtl_Notes
            lastrow['ReasonScheduled'] = rawrow.cs_ReasonScheduled
        #endif

        # process this row
        outputline = {}
        outputline['type'] = 'Detail'
        outputline['CycCtID'] = rawrow.ac_CycCtID
        outputline['Material'] = rawrow.Matl_PartNum
        outputline['SchedCounter'] = rawrow.cs_Counter
        outputline['ActCounter'] = rawrow.ac_Counter
        outputline['BLDG'] = rawrow.ac_BLDG
        outputline['LOCATION'] = rawrow.ac_LOCATION
        outputline['PKGID'] = rawrow.ac_PKGID_Desc
        outputline['TAGQTY'] = rawrow.ac_TAGQTY
        outputline['PossNotRec'] = rawrow.FLAG_PossiblyNotRecieved
        outputline['MovDurCt'] = rawrow.FLAG_MovementDuringCount
        outputline['CTD_QTY_Expr'] = rawrow.ac_CTD_QTY_Expr
        outputline['CTD_QTY_Eval'] = 0  # change this if it ever becomes possible for CTD_QTY_Expr to be nonnull   # yes, I know the risks - I'll write my own parser later ...
        lastrow['TotalCounted'] += outputline['CTD_QTY_Eval']
        outputline['ActCountNotes'] = rawrow.ac_Notes
        outputrows.append(outputline)
    # endfor
    # need to do the summary on the last row
    if outputrows:
        # summarize last Matl
        # total SAP Numbers
        SAPTot = 0
        outputline = dict()
        outputline['type'] = 'Summary'
        outputline['SAPNum'] = []
        for SAProw in SAP_SOH['SAPTable']:  # change this to a loop until SAProw.Material > rawrow.Matl_PartNum or SAPRow exhausted
            if SAProw.Material == lastrow['Material']:
                outputline['SAPNum'].append((SAProw.StorageLocation, SAProw.Amount))
                SAPTot += SAProw.Amount
        
        outputline['Material'] = lastrow['Material']
        outputline['PartType'] = lastrow['PartType']
        outputline['CountTotal'] = lastrow['TotalCounted']
        outputline['SAPTotal'] = SAPTot
        outputline['Diff'] = lastrow['TotalCounted'] - SAPTot
        divsr = 1
        if lastrow['TotalCounted']!=0 or SAPTot!=0: divsr = max(lastrow['TotalCounted'], SAPTot)
        outputline['Accuracy'] = min(lastrow['TotalCounted'], SAPTot) / divsr * 100
        outputline['CMFlag'] = lastrow['CMFlag']
        outputline['ReasonScheduled'] = lastrow['ReasonScheduled']
        outputline['SchedNotes'] = lastrow['SchedNotes']
        outputline['MatlNotes'] = lastrow['MatlNotes']
        outputrows.append(outputline)
    C_Sched_NotCtd_Ctd_outputrows = outputrows

    # display the form
    cntext = {
            'CountDate': datestrM,
            'SAPDate': SAP_SOH['SAPDate'],
            'Sched_Ctd': A_Sched_Ctd_outputrows,
            'UnSched_Ctd': B_UnSched_Ctd_outputrows,
            'Sched_NotCtd':C_Sched_NotCtd_Ctd_outputrows,
            'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'rpt_CountSummary.html'
    return render(req, templt, cntext)

#########################################
#########################################
#########################################

def fnCountSummaryRptPreview_firsttry (req, passedCountDate=None):
    _userorg = WICSuser.objects.get(user=req.user).org

    #TODO:  Incorporate SAP, summary calculations

    fldlist = "0 as id, cs.id as cs_id, cs.CountDate as cs_CountDate , cs.Counter as cs_Counter" \
        ", cs.Priority, cs.ReasonScheduled, cs.CMPrintFlag, cs.Notes as cs_Notes" \
        ", ac.id as ac_id, ac.CountDate as ac_CountDate, ac.CycCtID, ac.Counter as ac_Counter" \
        ", ac.LocationOnly, ac.CTD_QTY_Expr, ac.BLDG, ac.LOCATION, ac.PKGID_Desc, ac.TAGQTY" \
        ", ac.FLAG_PossiblyNotRecieved, ac.FLAG_MovementDuringCount, ac.Notes as ac_Notes" \
        ", mtl.Material as Matl_PartNum, (SELECT WhsePartType FROM WICS_WhsePartTypes WHERE id=mtl.PartType_id) as PartType" \
        ", mtl.Description, mtl.Notes as mtl_Notes"
    org_condition = '(ac.org_id = ' + str(_userorg.pk) + ' OR cs.org_id = ' + str(_userorg.pk) + ') '
    #datestr = 'CURRENT_DATE'
    datestr = WrapInQuotes('2022-04-06',"'","'")  
    if passedCountDate: datestr = WrapInQuotes(passedCountDate,"'","'")
    date_condition = '(ac.CountDate = ' + datestr + ' OR cs.CountDate = ' + datestr + ') '
    order_by = 'Matl_PartNum'
    
    A_Sched_Ctd_from = 'WICS_countschedule cs INNER JOIN WICS_materiallist mtl INNER JOIN WICS_actualcounts ac'    
    A_Sched_Ctd_joinon = 'cs.CountDate=ac.CountDate AND cs.Material_id=ac.Material_id AND ac.Material_id=mtl.id'    
    A_Sched_Ctd_where = ''
    A_Sched_Ctd_sql = 'SELECT ' + fldlist + \
        ' FROM ' + A_Sched_Ctd_from + \
        ' ON ' + A_Sched_Ctd_joinon + \
        ' WHERE NOT ac.LocationOnly AND ' + org_condition + ' AND ' + date_condition \
        # + ' AND ' + A_Sched_Ctd_where 
    A_Sched_Ctd_qs = CountSchedule.objects.raw(A_Sched_Ctd_sql)

    B_UnSched_Ctd_from = 'WICS_countschedule cs RIGHT JOIN' \
        ' (WICS_actualcounts ac INNER JOIN WICS_materiallist mtl ON ac.Material_id=mtl.id)'
    B_UnSched_Ctd_joinon = 'cs.CountDate=ac.CountDate AND cs.Material_id=ac.Material_id'
    B_UnSched_Ctd_where = '(cs.id IS NULL)'
    B_UnSched_Ctd_sql = 'SELECT ' + fldlist + ' ' + \
        ' FROM ' + B_UnSched_Ctd_from + \
        ' ON ' + B_UnSched_Ctd_joinon + \
        ' WHERE NOT ac.LocationOnly AND ' + org_condition + ' AND ' + date_condition + \
        ' AND ' + B_UnSched_Ctd_where
    B_UnSched_Ctd_qs = CountSchedule.objects.raw(B_UnSched_Ctd_sql)
    
    C_Sched_NotCtd_Ctd_from = '(WICS_countschedule cs INNER JOIN WICS_materiallist mtl ON cs.Material_id=mtl.id)' \
        ' LEFT JOIN WICS_actualcounts ac'
    C_Sched_NotCtd_Ctd_joinon = 'cs.CountDate=ac.CountDate AND cs.Material_id=ac.Material_id'
    C_Sched_NotCtd_Ctd_where = '(ac.id IS NULL)'
    C_Sched_NotCtd_Ctd_sql = 'SELECT ' + fldlist + ' ' + \
        ' FROM ' + C_Sched_NotCtd_Ctd_from + \
        ' ON ' + C_Sched_NotCtd_Ctd_joinon + \
        ' WHERE ' + org_condition + ' AND ' + date_condition + \
        ' AND ' + C_Sched_NotCtd_Ctd_where
    C_Sched_NotCtd_Ctd_qs = CountSchedule.objects.raw(C_Sched_NotCtd_Ctd_sql)

    # display the form
    cntext = {'Sched_Ctd': A_Sched_Ctd_qs,
            'UnSched_Ctd': B_UnSched_Ctd_qs,
            'Sched_NotCtd':C_Sched_NotCtd_Ctd_qs,
            'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'rpt_CountSummary.html'
    return render(req, templt, cntext)

    