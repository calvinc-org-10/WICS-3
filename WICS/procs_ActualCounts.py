import time, datetime
import os, uuid
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.urls import reverse
from django import forms
from django.shortcuts import render
from cMenu.models import getcParm
from cMenu.utils import makebool
from userprofiles.models import WICSuser
#from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from openpyxl import load_workbook
from userprofiles.models import WICSuser
from WICS.models import ActualCounts, MaterialList
import datetime


@login_required
def fnUploadActCountSprsht(req):
    _userorg = WICSuser.objects.get(user=req.user).org

    if req.method == 'POST':
        # save the file so we can open it as an excel file
        SAPFile = req.FILES['CEFile']
        svdir = getcParm('SAP-FILELOC')
        fName = svdir+"tmpCE"+str(uuid.uuid4())+".xlsx"
        with open(fName, "wb") as destination:
            for chunk in SAPFile.chunks():
                destination.write(chunk)

        wb = load_workbook(filename=fName, read_only=True)
        ws = wb.active

        # I map Table Fields directly to spreadsheet columns because it's MY spreadsxheet and 
        # I have defin ed the format.  If that changes, see fnUpdateMatlListfromSAP in SAPMatlUpdt.py
        # for an alternative way of handling this mapping
        SAPcolmnMap = {
                    'CountDate': 0,
                    'Counter': 1,
                    'BLDG': 2,
                    'LOCATION': 3,
                    'Material': 4,
                    'LocationOnly': 5,
                    'CTD_QTY_Expr': 6,
                    'TypicalContainerQty': 7,
                    'TypicalPalletQty': 8,
                    'Notes':9,
                    }
        
        UplResults = []
        nRows = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            try:
                MatObj = MaterialList.objects.get(org=_userorg, Material=row[SAPcolmnMap['Material']])
            except:
                MatObj = None

            if MatObj:
                MatChanged = False
                SRec = ActualCounts(org = _userorg)
                for fldName, colNum in SAPcolmnMap.items():
                    V = row[colNum]
                    if V==None: V = ''

                    if   fldName == 'CountDate': setattr(SRec, fldName, V)
                    elif fldName == 'Counter': setattr(SRec, fldName, V)
                    elif fldName == 'BLDG': 
                        # later, make sure BLDG not blank
                        setattr(SRec, fldName, V)
                    elif fldName == 'LOCATION': setattr(SRec, fldName, V)
                    elif fldName == 'Material': setattr(SRec, fldName, MatObj)
                    elif fldName == 'LocationOnly': setattr(SRec, fldName, makebool(V))
                    elif fldName == 'CTD_QTY_Expr': setattr(SRec, fldName, V)
                    elif fldName == 'Notes': setattr(SRec, fldName, V)
                    elif fldName == 'TypicalContainerQty' \
                      or fldName == 'TypicalPalletQty':
                        if V == '' or V == None: V = 0
                        if row[colNum] != getattr(MatObj,fldName,0): 
                            setattr(MatObj, fldName, V)
                            MatChanged = True
                    
                SRec.save()
                if MatChanged: MatObj.save()
                res = {'error': False, 'TypicalQty':MatChanged}.update(type(SRec).objects.filter(pk=SRec.pk).values().first())
                UplResults.append(res)
                nRows += 1
            else:
                UplResults.append({'error':row[SAPcolmnMap['Material']]+' does not exist in MaterialList'})

        # close and kill temp files
        wb.close()
        os.remove(fName)

        cntext = {'UplResults':UplResults, 'nRowsAdded':nRows,
                'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
                }
        templt = 'frm_uploadCountEntry_Success.html'
    else:
        cntext = {'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
                }
        templt = 'frm_UploadCountEntrySprdsht.html'
    #endif

    return render(req, templt, cntext)

