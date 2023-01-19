#import os, uuid
from datetime import timedelta, date, MINYEAR
import dateutil.utils
#from django import forms
#from django.db import models
from django.db.models import Value, Max, Q
from django.db.models.query import QuerySet
#from django.contrib.auth.decorators import login_required
#from django.forms import inlineformset_factory, formset_factory
from django.http import HttpResponse, HttpRequest
#from django.shortcuts import render
#from django.urls import reverse
#from django.utils import timezone
from django.views.generic import ListView
#from openpyxl import load_workbook
#from cMenu.models import getcParm
from userprofiles.models import WICSuser
from WICS.models import MaterialList, LastFoundAt
from WICS.SAPLists import fnSAPList
from typing import Any, Dict

# used in MaterialLocationsList.get_queryset.  Replace with a cParameter later
p_countwindow = 120

class MaterialLocationsList(ListView):
    ordering = ['Material']
    context_object_name = 'MatlList'
    template_name = 'rpt_PartLocations.html'
    SAPSums = {}
    
    def setup(self, req: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self._user = req.user
        self._userorg = WICSuser.objects.get(user=self._user).org
        # get last count date (incl LocationOnly) for each Material (prefetch_related?)
        qs = MaterialList.objects.filter(org=self._userorg).order_by('Material').annotate(LFADate=Value(0), LFALocation=Value(''), SAPList=Value(0), DoNotShow=Value(False))   # figure out how to pass in self.ordering
        
        # it's more efficient to pull this all now and store it for the upcoming qs request
        SAP = fnSAPList(self._userorg)
        self.SAPDate = SAP['SAPDate']
        self.SAPTable = SAP['SAPTable']
        

        self.queryset = qs
        return super().setup(req, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()
        for rec in qs:
            L = LastFoundAt(rec)
            rec.LFADate = L['lastCountDate']
            rec.LFALocation = L['lastFoundAt']
            rec.SAPList = self.SAPTable.filter(Material=rec.Material)
            # filter Material in SAP_SOH for date OR last count date within 30d
            testdate = rec.LFADate
            if testdate == None: testdate = date(MINYEAR, 1, 1)
            rec.DoNotShow = (not rec.SAPList.exists()) and (testdate < (dateutil.utils.today()-timedelta(days=p_countwindow)).date())

        return qs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctxt = super().get_context_data(**kwargs)
        # ctxt['SAPDate'] = self.SAPDate
        return ctxt

    # def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    #     return super().get(request, *args, **kwargs)

    def render_to_response(self, context: Dict[str, Any], **response_kwargs: Any) -> HttpResponse:
        context.update({'orgname': self._userorg.orgname,  'uname':self._user.get_full_name()})
        return super().render_to_response(context, **response_kwargs)


