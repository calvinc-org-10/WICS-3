from django.shortcuts import render
from django.http import HttpResponse
from tomlkit import array
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
    match CommandNum:
        case MENUCOMMAND.LoadMenu :
            pass
        case MENUCOMMAND.FormBrowse :
            pass
        case MENUCOMMAND.FormAdd :
            pass
        case MENUCOMMAND.ReportView :
            pass
        case MENUCOMMAND.ReportPrint :
            pass
        case MENUCOMMAND.OpenTable :
            pass
        case MENUCOMMAND.OpenQuery :
            pass
        case MENUCOMMAND.RunCode :
            pass
        case MENUCOMMAND.EditMenu :
            pass
        case MENUCOMMAND.EditParameters :
            pass
        case MENUCOMMAND.EditGreetings :
            pass
        case MENUCOMMAND.EditPasswords :
            pass
        case MENUCOMMAND.ExitApplication :
            pass
        case _:
            pass

    tmpst = "Command " + CommandNum.__str__() + " will be performed with Argument " + CommandArg
    return HttpResponse(tmpst)