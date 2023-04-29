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
from WICS import userinit
from WICS import procs_ActualCounts, procs_CountSchedule, procs_Material, procs_SAP, views
from WICS import adhoc_2023_02_01_001
from userprofiles import logout

urlpatterns = [
    path('', lambda request: redirect(reverse('login'),permanent=False), name='WICSlogin'),       # this is actually the entry point to WICS
    # path('test00', testmodal.fnTestModal, name='test00'),
    path('inituser', userinit.inituser , name='initWICSuser'),
    path('logout',logout.WICSlogout, name='WICSlogout'),

    path('ActualCountList',
            procs_ActualCounts.ActualCountListForm.as_view(), name='ActualCountList'),

    path('CountScheduleList',
            procs_CountSchedule.CountScheduleListForm.as_view(),name='CountScheduleList'),

    path('CountEntryForm',
            views.fnCountEntryView, name='CountEntryForm'),
    path('CountEntryForm/Go/<int:recNum>',
            views.fnCountEntryView, name='CountEntryFormGo'),
    path('CountEntryForm/Go/<int:recNum>/<str:gotoCommand>',
            views.fnCountEntryView,
            name='CountEntryFormGo'),    
    path('CountEntryForm/<int:recNum>/<str:reqDate>/<str:MatlNum>',
            views.fnCountEntryView, {'gotoCommand':'ChgKey'},
            name='CountEntryForm'),

    path('CountScheduleForm',
            views.fnCountScheduleRecView, name='CountScheduleForm'),
    path('CountScheduleForm/Go/<int:recNum>',
            views.fnCountScheduleRecView, name='CountScheduleFormGo'),
    path('CountScheduleForm/Go/<int:recNum>/<str:gotoCommand>',
            views.fnCountScheduleRecView,
            name='CountScheduleFormGo'),    
    path('CountScheduleForm/<int:recNum>/<str:reqDate>/<str:MatlNum>',
            views.fnCountScheduleRecView, {'gotoCommand':'ChgKey'},
            name='CountScheduleForm'),

    path('RequestCountScheduleForm',
            views.fnRequestCountScheduleRecView, name='RequestCountScheduleForm'),
    path('RequestCountScheduleForm/<int:recNum>/<str:reqDate>/<str:MatlNum>',
            views.fnRequestCountScheduleRecView, {'gotoCommand':'ChgKey'},
            name='RequestCountScheduleForm'),
    path('RequestedCountListEdit',
            views.fnRequestedCountEditListView, name='RequestCountListEdit'),

    path('CountSummaryRpt/v/REQ',
            procs_ActualCounts.fnCountSummaryReqRpt, name='CountSummaryReport-v-init'),
    path('CountSummaryRpt/v/<str:Rptvariation>',
            procs_ActualCounts.fnCountSummaryRpt, name='CountSummaryReport-v'),
    path('CountSummaryRpt/v/<str:Rptvariation>/<str:passedCountDate>',
            procs_ActualCounts.fnCountSummaryRpt, name='CountSummaryReport-v'),
    path('CountSummaryRpt',
            procs_ActualCounts.fnCountSummaryRpt, name='CountSummaryReport'),
    path('CountSummaryRpt/<str:passedCountDate>',
            procs_ActualCounts.fnCountSummaryRpt, name='CountSummaryReport'),

    path('CountWorksheet',
            procs_CountSchedule.CountWorksheetReport.as_view(),name='CountWorksheet'),
    path('CountWorksheet/<CountDate>',
            procs_CountSchedule.CountWorksheetReport.as_view(),name='CountWorksheet'),

    path('MaterialForm',
            procs_Material.fnMaterialForm, name='MatlForm'),
    path('MaterialForm/newRec',
            procs_Material.fnMaterialForm, {'gotoRec':False, 'newRec':True}, name='NewMatlForm'),       #this MUST occur before name='ReloadMatlForm'
    path('MaterialForm/<str:gotoMatl>',
            procs_Material.fnMaterialForm, {'gotoRec':True}, name='ReloadMatlForm'),
    path('MaterialForm/recnum/<int:recNum>',
            procs_Material.fnMaterialForm, name='MatlFormRecNum'),

    path('MatlByPartType',
            procs_Material.MaterialByPartType.as_view(), name='MatlByPartType'),

    path('MatlByLastCountDate',
            procs_Material.MaterialByLastCountDate.as_view(), name='MatlByLastCountDate'),

    path('MatlByDESCValue',
            procs_Material.MaterialByDESCValue.as_view(), name='MatlByDESCValue'),

    path('MaterialLocations',
            procs_Material.MaterialLocationsList.as_view(),name='MaterialLocations'),

    path('LocationList',
            procs_Material.fnLocationList,name='LocationList'),

    path('PartTypeForm',
            procs_Material.fnPartTypesForm, {'recNum':-999}, name='PartTypeForm'),
    path('PartTypeForm/<int:recNum>',
            procs_Material.fnPartTypesForm, {'gotoRec':True}, name='ReloadPTypForm'),
    path('DeltePartType/<int:recNum>',
            procs_Material.fnDeletPartTypes, name='DeletePTyp'),

    path('SAP',procs_SAP.fnShowSAP,name='showtable-SAP'),
    path('SAP/<str:reqDate>',procs_SAP.fnShowSAP,name='showtable-SAP'),

    path('UpldActCtSprsht', procs_ActualCounts.fnUploadActCountSprsht, name='UploadActualCountSprsht'),

    path('UpdateMatlListfromSAP',procs_SAP.fnUpdateMatlListfromSAP, name='UpdateMatlListfromSAP'),

    path('UpldSAPSprsht',procs_SAP.fnUploadSAP, name='UploadSAPSprSht'),

    path('adhoc-2023-02-01-001',adhoc_2023_02_01_001.adhoc001,name='adhoc-2023-02-01-001'),

]

oldpatterns = [

]
newpatterns = [

]