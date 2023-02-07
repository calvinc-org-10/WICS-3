#import datetime
#import os, uuid
#from django import forms
from django.contrib.auth.decorators import login_required
#from django.contrib.auth.mixins import LoginRequiredMixin
#from django.db.models.query import QuerySet
#from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
#from django.utils import timezone
#from django.urls import reverse
from django.shortcuts import render
#from django.views.generic import ListView
#from typing import *
#from cMenu.models import getcParm
from cMenu.utils import isDate, WrapInQuotes
from userprofiles.models import WICSuser
from WICS.models import ActualCounts, SAP_SOHRecs



@login_required
def adhoc001(req):
    _userorg = WICSuser.objects.get(user=req.user).org

    def CreateOutputRows(raw_qs, Eval_CTDQTY=True):
        def SummaryLine(lastrow):
            # summarize last Matl
            # total SAP Numbers
            if SAPRecs.filter(uploaded_at__date__lte=lastrow['CountDate']).exists():
                SAPDate = SAPRecs.filter(org=_userorg, uploaded_at__date__lte=lastrow['CountDate']).latest().uploaded_at
            else:
                SAPDate = SAPRecs.filter(org=_userorg).order_by('uploaded_at').first().uploaded_at

            SAPTot = 0
            outputline = dict()
            outputline['type'] = 'Summary'
            outputline['CountDate'] = lastrow['CountDate']
            outputline['SAPDate'] = SAPDate
            outputline['SAPNum'] = []
            for SAProw in SAPRecs.filter(uploaded_at=SAPDate,Material=lastrow['Material']): 
                outputline['SAPNum'].append((SAProw.StorageLocation, SAProw.Amount))
                SAPTot += SAProw.Amount
            outputline['TypicalContainerQty'] = lastrow['TypicalContainerQty']
            outputline['TypicalPalletQty'] = lastrow['TypicalPalletQty']
            outputline['Material'] = lastrow['Material']
            outputline['PartType'] = lastrow['PartType']
            outputline['CountTotal'] = lastrow['TotalCounted']
            outputline['SAPTotal'] = SAPTot
            outputline['Diff'] = lastrow['TotalCounted'] - SAPTot
            divsr = 1
            if lastrow['TotalCounted']!=0 or SAPTot!=0: divsr = max(lastrow['TotalCounted'], SAPTot)
            outputline['Accuracy'] = min(lastrow['TotalCounted'], SAPTot) / divsr * 100
            outputline['MatlNotes'] = lastrow['MatlNotes']
            #outputrows.append(outputline)

            return outputline

        def CreateLastrow(rawrow):
            lastrow = dict()
            lastrow['CountDate'] = rawrow.ac_CountDate
            lastrow['Material'] = rawrow.Matl_PartNum
            lastrow['PartType'] = rawrow.PartType
            lastrow['TotalCounted'] = 0
            lastrow['TypicalContainerQty'] = rawrow.TypicalContainerQty
            lastrow['TypicalPalletQty'] = rawrow.TypicalPalletQty
            lastrow['MatlNotes'] = rawrow.mtl_Notes

            return lastrow

        def DetailLine(rawrow, Eval_CTDQTY=True):
            outputline = dict()
            outputline['type'] = 'Detail'
            outputline['CountDate'] = rawrow.ac_CountDate
            outputline['CycCtID'] = rawrow.ac_CycCtID
            outputline['Material'] = rawrow.Matl_PartNum
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
                    outputline['CTD_QTY_Eval'] = eval(rawrow.ac_CTD_QTY_Expr)   # yes, I know the risks - Ill write my own parser later ...
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
        
        outputrows = []
        lastrow = {'Material': None, 'CountDate':None}
        for rawrow in raw_qs:
            if rawrow.Matl_PartNum != lastrow['Material'] or rawrow.ac_CountDate != lastrow['CountDate']:     # new Matl
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
        
    ### main body of fnCountSummaryRpt

    cutoff_date = '2023-01-25'
    matl = {
        '1021801-02','1036578-07','1036580-07','1038012-07','1038019-06',    
        '1041332-01','1048738-01','1048740-01','1053031-01','1055235-01','1068789-01','1073489-01',
        '1093751','1098743-03','1098744-04','1098745-03','1098746-04','1103745-01','1106221-01',
        '1106919-01','1106920-02','1106934-04','1107200-01','1107202-01','1107204-02','1107242-01',
        '1111596-01','1111598-01','1111603-01','1111604-01','1111669-01','1111728-02','1111738-01',
        '1111739-01','1112233-01','1112236-01','1112237-01','1112238-01' ,'1112244-01' ,'1112401-01',  
        '1112402-01' ,'1112433-01' ,'1114156-01' ,'1116885-01' ,'1116886-01' ,'1119679-01' ,'1120159-01' ,
        '1120160-01','1120161-01' ,'1120166-01','1125366-04' ,'1125366-05' ,'1125367-01' ,'1125367-02' ,
        '1125367-04' ,'1125367-05' ,'1135528','1139339-03' ,'1139708-01' ,'1142853-01' ,'1142972-01' ,
        '42000834-12' ,'42000839-14'
        }
    matl_as_string = ''
    for MM in matl:
        if matl_as_string: matl_as_string += ", "
        matl_as_string += WrapInQuotes(MM,"'","'")
    
    # get the SAP data
    SAPRecs = SAP_SOHRecs.objects.filter(org=_userorg,Material__in=matl).order_by('uploaded_at','Material')

    fldlist = "0 as id" \
        ", ac.id as ac_id, ac.CountDate as ac_CountDate, ac.CycCtID as ac_CycCtID, ac.Counter as ac_Counter" \
        ", ac.LocationOnly as ac_LocationOnly, ac.CTD_QTY_Expr as ac_CTD_QTY_Expr, ac.BLDG as ac_BLDG" \
        ", ac.LOCATION as ac_LOCATION, ac.PKGID_Desc as ac_PKGID_Desc, ac.TAGQTY as ac_TAGQTY" \
        ", ac.FLAG_PossiblyNotRecieved, ac.FLAG_MovementDuringCount, ac.Notes as ac_Notes" \
        ", mtl.Material as Matl_PartNum, (SELECT WhsePartType FROM WICS_whseparttypes WHERE id=mtl.PartType_id) as PartType" \
        ", mtl.Description, mtl.TypicalContainerQty, mtl.TypicalPalletQty, mtl.Notes as mtl_Notes"
    org_condition = '(ac.org_id = ' + str(_userorg.pk) +  ') '
    if isDate(cutoff_date): datestr = WrapInQuotes(cutoff_date,"'","'")
    else: datestr = cutoff_date
    datecutoff_relation = ">="
    date_condition = '(ac.CountDate ' + datecutoff_relation + ' ' + datestr + ') '
    order_by = 'Matl_PartNum, ac_CountDate'

    SummaryReport = []

    A_Sched_Ctd_from = 'WICS_materiallist mtl LEFT JOIN WICS_actualcounts ac'    
    A_Sched_Ctd_joinon = 'ac.Material_id=mtl.id'    
    A_Sched_Ctd_where = 'mtl.Material in (' + matl_as_string + ")"
    A_Sched_Ctd_sql = 'SELECT ' + fldlist + \
        ' FROM ' + A_Sched_Ctd_from + \
        ' ON ' + A_Sched_Ctd_joinon + \
        ' WHERE NOT ac.LocationOnly AND ' + org_condition + ' AND ' + date_condition + \
        ' AND ' + A_Sched_Ctd_where + \
        ' ORDER BY ' + order_by
    A_Sched_Ctd_qs = ActualCounts.objects.raw(A_Sched_Ctd_sql)
    # build display lines
    SummaryReport.append({
                'Title':'Counted',
                'outputrows': CreateOutputRows(A_Sched_Ctd_qs)
                })

    # display the form
    cntext = {
            'SummaryReport': SummaryReport,
            'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
            #'Sched_Ctd': A_Sched_Ctd_outputrows,
            #'UnSched_Ctd': B_UnSched_Ctd_outputrows,
            #'Sched_NotCtd':C_Sched_NotCtd_Ctd_outputrows,
    templt = 'rpt_adhoc-2023-02-01-001.html'
    return render(req, templt, cntext)

