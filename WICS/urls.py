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
from WICS import forms, reports, userinit
from userprofiles import logout

# should this be in cMenu? 12/24/2022 - I'm thinking no
urlpatterns = [
    path('', lambda request: redirect(reverse('login'),permanent=False), name='WICSlogin'),       # this is actually the entry point to WICS
    path('inituser', userinit.inituser , name='initWICSuser'),
    path('MaterialForm2/<int:recNum>',forms.fnMaterialForm, {'formname': 'frmmaterialform','gotoRec':True}, name='ReloadMatlForm'),
    path('CountEntryForm/<int:recNum>/<str:passedCountDate>/<str:loadMatlInfo>',forms.fnCountEntryForm, {'formname': 'frmcountentry'}, name='CountEntryForm'),
    path('CountEntryForm/<int:recNum>/<str:passedCountDate>/<str:loadMatlInfo>/<str:gotoCommand>',forms.fnCountEntryForm, {'formname': 'frmcountentry'}, name='CountEntryFormGoto'),
    path('CountSummaryRpt/<str:passedCountDate>',reports.fnCountSummaryRptPreview, name='CountSummaryReport'),
    path('logout',logout.WICSlogout, name='WICSlogout'),
]
