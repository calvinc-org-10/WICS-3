from datetime import datetime
from django.shortcuts import render
from userprofiles.models import WICSuser
from WICS.models import SAP_SOHRecs
from WICS.SAPLists import fnSAPList


def fnShowSAP(req, reqDate=datetime.today()):
    _userorg = WICSuser.objects.get(user=req.user).org

    _myDtFmt = '%Y-%m-%d %H:%M'

    SAP_tbl = fnSAPList(_userorg,for_date=reqDate)
    SAPDatesRaw = choices=SAP_SOHRecs.objects.filter(org=_userorg).order_by('-uploaded_at').values('uploaded_at').distinct()
    SAPDates = []
    for D in SAPDatesRaw:
        SAPDates.append(D['uploaded_at'].strftime(_myDtFmt))


    cntext = {'reqDate': SAP_tbl['reqDate'],
            'SAPDateList': SAPDates,
            'SAPDate': SAP_tbl['SAPDate'].strftime(_myDtFmt),
            'SAPSet': SAP_tbl['SAPTable'],
            'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    tmplt = 'show_SAP_table.html'
    return render(req, tmplt, cntext)

    