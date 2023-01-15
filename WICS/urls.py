"""django_support URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, reverse
from django.shortcuts import redirect
from WICS import forms, reports, userinit, procs_SAP, procs_CountSchedule, procs_ActualCounts, procs_Material
from userprofiles import logout

urlpatterns = [
    path('', lambda request: redirect(reverse('login'),permanent=False), name='WICSlogin'),       # this is actually the entry point to WICS
    path('inituser', userinit.inituser , name='initWICSuser'),
    path('MaterialForm2/<int:recNum>',
            forms.fnMaterialForm, {'formname': 'frmmaterialform','gotoRec':True}, name='ReloadMatlForm'),
    path('CountEntryForm/<int:recNum>/<str:passedCountDate>/<str:loadMatlInfo>',
            procs_ActualCounts.fnCountEntryForm, {'formname': 'frmcountentry'}, name='CountEntryForm'),
    path('CountEntryForm/<int:recNum>/<str:passedCountDate>/<str:loadMatlInfo>/<str:gotoCommand>',
            procs_ActualCounts.fnCountEntryForm, {'formname': 'frmcountentry'}, name='CountEntryFormGoto'),
    path('CountSummaryRpt/<str:passedCountDate>',
            reports.fnCountSummaryRptPreview, name='CountSummaryReport'),
    path('CountScheduleList/',
            procs_CountSchedule.CountScheduleListForm.as_view(),name='CountScheduleList'),
    path('CountScheduleForm/',
            procs_CountSchedule.fnCountScheduleRecordForm,name='CountScheduleForm'),
    path('CountScheduleForm/<int:recNum>/<str:passedMatlNum>/<str:passedCountDate>/<str:gotoCommand>',
            procs_CountSchedule.fnCountScheduleRecordForm,name='CountScheduleForm'),
    path('CountWorksheet',
            procs_CountSchedule.CountWorksheetReport.as_view(),name='CountWorksheet'),
    path('CountWorksheet/<CountDate>',
            procs_CountSchedule.CountWorksheetReport.as_view(),name='CountWorksheet'),
    path('MatlByPartType',forms.MaterialByPartType.as_view(), name='MatlByPartType'),
    path('SAP/<str:reqDate>',procs_SAP.fnShowSAP,name='showtable-SAP'),
    path('logout',logout.WICSlogout, name='WICSlogout'),
]
