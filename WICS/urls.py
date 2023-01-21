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
from WICS import forms, userinit, \
        procs_SAP, procs_CountSchedule, procs_ActualCounts, procs_Material, \
        SAPMatlUpdt
from userprofiles import logout

urlpatterns = [
    path('', lambda request: redirect(reverse('login'),permanent=False), name='WICSlogin'),       # this is actually the entry point to WICS
    path('inituser', userinit.inituser , name='initWICSuser'),
    path('logout',logout.WICSlogout, name='WICSlogout'),
    path('ActualCountList',
            procs_ActualCounts.ActualCountListForm.as_view(), name='ActualCountList'),
    path('CountEntryForm',
            procs_ActualCounts.fnCountEntryForm, name='CountEntryForm'),
    path('CountEntryForm/<int:recNum>',
            procs_ActualCounts.fnCountEntryForm, name='CountEntryForm'),
    path('CountEntryForm/<int:recNum>/<str:passedCountDate>/<str:loadMatlInfo>',
            procs_ActualCounts.fnCountEntryForm, name='CountEntryForm'),
    path('CountEntryForm/<int:recNum>/<str:passedCountDate>/<str:loadMatlInfo>/<str:gotoCommand>',
            procs_ActualCounts.fnCountEntryForm, name='CountEntryFormGoto'),
    path('CountScheduleList',
            procs_CountSchedule.CountScheduleListForm.as_view(),name='CountScheduleList'),
    path('CountScheduleForm',
            procs_CountSchedule.fnCountScheduleRecordForm,name='CountScheduleForm'),
    path('CountScheduleForm/<int:recNum>/<str:passedMatlNum>/<str:passedCountDate>/<str:gotoCommand>',
            procs_CountSchedule.fnCountScheduleRecordForm,name='CountScheduleForm'),
    path('CountSummaryRpt',
            procs_ActualCounts.fnCountSummaryRpt, name='CountSummaryReport'),
    path('CountSummaryRpt/<str:passedCountDate>',
            procs_ActualCounts.fnCountSummaryRpt, name='CountSummaryReport'),
    path('CountWorksheet',
            procs_CountSchedule.CountWorksheetReport.as_view(),name='CountWorksheet'),
    path('CountWorksheet/<CountDate>',
            procs_CountSchedule.CountWorksheetReport.as_view(),name='CountWorksheet'),
    path('MaterialForm',
            forms.fnMaterialForm, name='MatlForm'),
    path('MaterialForm/<int:recNum>',
            forms.fnMaterialForm, {'gotoRec':True}, name='ReloadMatlForm'),
    path('MatlByPartType',forms.MaterialByPartType.as_view(), name='MatlByPartType'),
    path('MaterialLocations',
            procs_Material.MaterialLocationsList.as_view(),name='MaterialLocations'),
    path('SAP',procs_SAP.fnShowSAP,name='showtable-SAP'),
    path('SAP/<str:reqDate>',procs_SAP.fnShowSAP,name='showtable-SAP'),
    path('UpldActCtSprsht', procs_ActualCounts.fnUploadActCountSprsht, name='UploadActualCountSprsht'),
    path('UpdateMatlListfromSAP',SAPMatlUpdt.fnUpdateMatlListfromSAP, name='UpdateMatlListfromSAP'),
    path('UpldSAPSprsht',forms.fnUploadSAP, name='UploadSAPSprSht'),
]
