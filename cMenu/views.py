from ast import Load
from django.shortcuts import render
from django.http import HttpResponse
from django.template import Context, Template
from tomlkit import array
from WICS.forms import FormBrowse
from cMenu.menucommand_handlers import *

from cMenu.models import menuItems

# Create your views here.

def Temporary(req):
    return HttpResponse("Sooner or later I'll figger this out!")

def LoadMenu(req, menuNum):
    mnItem_qset = menuItems.objects.filter(MenuID = menuNum).values('OptionNumber','OptionText','Command','Argument')
    # tmplt = Engine.get_template(template_name="cMenu.html")

    mnItem_dict = {}
    for m in mnItem_qset:
        mnItem_dict[m['OptionNumber']] = m

    mnContxt = dict(mnInfo=mnItem_dict)
    return render(None,template_name="cMenu.html",context=mnContxt)

def HandleMenuCommand(req,CommandNum,CommandArg):
    tmpst = "Command " + CommandNum.__str__() + " will be performed with Argument " + CommandArg

    if CommandNum == MENUCOMMAND.LoadMenu.value :
        # work on this case
        LoadMenu(req,int(CommandArg))
        pass
    elif CommandNum == MENUCOMMAND.FormBrowse.value :
        tmpst = FormBrowse(CommandArg)
        pass
    elif CommandNum == MENUCOMMAND.FormAdd.value :
        pass
    elif CommandNum == MENUCOMMAND.ReportView.value :
        pass
    elif CommandNum == MENUCOMMAND.ReportPrint.value :
        pass
    elif CommandNum == MENUCOMMAND.OpenTable.value :
        pass
    elif CommandNum == MENUCOMMAND.OpenQuery.value :
        pass
    elif CommandNum == MENUCOMMAND.RunCode.value :
        pass
    elif CommandNum == MENUCOMMAND.EditMenu.value :
        pass
    elif CommandNum == MENUCOMMAND.EditParameters.value :
        pass
    elif CommandNum == MENUCOMMAND.EditGreetings.value :
        pass
    elif CommandNum == MENUCOMMAND.EditPasswords.value :
        pass
    elif CommandNum == MENUCOMMAND.ExitApplication.value :
        pass
    else:
        pass

    return HttpResponse(tmpst)