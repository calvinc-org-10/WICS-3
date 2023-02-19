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
from django.urls import path
from cMenu import views, menucommand_handlers

urlpatterns = [
    path('loadmenu/<int:menuGroup>/<int:menuNum>/',views.LoadMenu,name='LoadMenu'),
    path('editmenu', 
            views.EditMenu,kwargs={'menuGroup':1, 'menuNum':0},
            name='EditMenu_init'),
    path('editmenu/<menuGroup>/<menuNum>',
            views.EditMenu,
            name='EditMenu'),
    path('ProcessMenuCommand/<int:CommandNum>/<slug:CommandArg>',
            views.HandleMenuCommand,
            name='HandleCommand'),
    path('FormBrowse/<slug:formname>/<int:recNum>',
            menucommand_handlers.FormBrowse,
            name='FormBrowse'),
    path('MenuCreate/<menuGroup>/<menuNum>',
            views.MenuCreate,
            name='MenuCreate'),
    path('MenuCreate/<menuGroup>/<menuNum>/<fromGroup>/<fromMenu>',
            views.MenuCreate,
            name='MenuCreate'),
    path('MenuRemove/<menuGroup>/<menuNum>',
            views.MenuRemove,
            name='MenuRemove'),
    path('cUtil/ParmEdit', 
            #views.cParmFormList.as_view(),   
            views.fncParmForm,
            name='EditParms'),
]
