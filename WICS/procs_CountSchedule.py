# import datetime
import re as regex
#from dateutil import parser
#from dateutil.utils import today
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Value
from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from django.views.generic import ListView
from barcode import Code128
from userprofiles.models import WICSuser
from WICS.forms import CountScheduleRecordForm, RelatedMaterialInfo
from WICS.models import MaterialList, CountSchedule, \
                        WhsePartTypes, LastFoundAt, WorksheetZones, Location_WorksheetZone, org_queryset
from WICS.procs_SAP import fnSAPList
from typing import *
# below: skip Sat, Sun using dateutil, dateutil.rrule, dateutil.rruleset
# implement skipping holidays
from cMenu.utils import calvindate
from WICS.procs_misc import HolidayList



def fnCountScheduleRecordExists(org, CtDate, Matl):
    """
    used to check if a CountSchedule redcord exists for the given CtDate and Material
    (only one such record is allowed).
    If the record exists, it is the return value, else a None CountSchedule rec
    """
    if isinstance(Matl,MaterialList):
        MatObj = Matl 
    elif isinstance(Matl,str):
        try:
            MatObj = org_queryset(MaterialList, org=org).get(Material=Matl)
        except:
            MatObj = MaterialList.objects.none()
    elif isinstance(Matl,int):
        try:
            MatObj = org_queryset(MaterialList, org=org).get(pk=Matl)
        except:
            MatObj = MaterialList.objects.none()
    else:
        MatObj = MaterialList.objects.none()
        
    try:
        rec = CountSchedule.objects.get(org=org, CountDate=CtDate, Material=MatObj)
    except:
        rec = CountSchedule.objects.none()

    return rec

#####################################################################
#####################################################################
#####################################################################

class CountScheduleListForm(LoginRequiredMixin, ListView):
    ordering = ['-CountDate', 'Material']
    context_object_name = 'CtSchdList'
    template_name = 'frm_CountScheduleList.html'
    
    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self._user = req.user
        self._userorg = WICSuser.objects.get(user=req.user).org
        self.queryset = CountSchedule.objects.filter(org=self._userorg).order_by('-CountDate', 'Material')   # figure out how to pass in self.ordering
        return super().setup(req, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset()

    # def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    #     return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return HttpResponse('Stop rushing me!!')

    def render_to_response(self, context: Dict[str, Any], **response_kwargs: Any) -> HttpResponse:
        context.update({'orgname': self._userorg.orgname,  'uname':self._user.get_full_name()})
        return super().render_to_response(context, **response_kwargs)


#####################################################################
#####################################################################
#####################################################################

class CountWorksheetReport(LoginRequiredMixin, ListView):
    ordering = ['Counter', 'Material']
    context_object_name = 'CtSchd'
    template_name = 'rpt_CountWksht.html'
    
    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self._user = req.user
        self._userorg = WICSuser.objects.get(user=req.user).org
        if 'CountDate' in kwargs: self.CountDate = kwargs['CountDate']
        else: self.CountDate = calvindate().today().as_datetime()
        if isinstance(self.CountDate,str): self.CountDate = calvindate(self.CountDate).as_datetime()
        return super().setup(req, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        SAP_SOH = fnSAPList(self._userorg,self.CountDate)
        self.SAPDate = SAP_SOH['SAPDate']
        qs = CountSchedule.objects.filter(org=self._userorg, CountDate=self.CountDate).order_by('Counter', 'Material').select_related('Material','Material__PartType')   # figure out how to pass in self.ordering
        qs = qs.annotate(LastFoundAt=Value(''), SAPQty=Value(0), MaterialBarCode=Value(''))
        Mat3char = None
        lastCtr = None
        for rec in qs:
            strMatlNum = rec.Material.Material
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

        # collect the list of Counters to that tabs can be built in the html
        CounterList = CountSchedule.objects.filter(org=self._userorg, CountDate=self.CountDate).order_by('Counter').values('Counter').distinct()

        context.update({
                'zoneList': zoneList,
                'CounterList': CounterList,
                'CountDate': self.CountDate,     # .as_datetime(), -- this was done in setup()
                'SAP_Updated_at': self.SAPDate,
                'orgname': self._userorg.orgname, 'uname':self._user.get_full_name()
                })

        ## is this block a leftover from when this DIDN'T work??
        # collect the list of Counters to that tabs can be built in the html
        # self.CounterList = self.get_queryset().values('Counter').distinct()

        return super().render_to_response(context, **response_kwargs)

