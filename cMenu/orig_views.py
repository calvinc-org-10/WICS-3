from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse
from django.utils.text import slugify
from WICS.forms import FormBrowse       # later, move this to cMenu
from cMenu.menucommand_handlers import *
from cMenu.models import menuCommands, menuItems

# Create your views here.

def Temporary(req):
    return HttpResponse("Sooner or later I'll figger this out!")

def LoadMenu(req, menuNum):
# DOCUMENT THIS!!!   ADD COMMENTS!!!  EXPLAIN IT!!!
    mnItem_qset = menuItems.objects.filter(MenuID = menuNum).values('OptionNumber','OptionText','Command','Argument')
    mnuName = mnItem_qset.get(OptionNumber=0)['OptionText']

    mnItem_list = ['' for i in range(20)]
    # mnItem_dict = {}
    for m in mnItem_qset:
        if m['OptionNumber']==0: continue
        mHTML = "<button type=""button""><a href="
        if m['Command'] == 1:
            mHTML = mHTML + reverse('LoadMenu', kwargs={'menuNum':m['Argument']})
        else:
            cmArg = slugify(m['Argument'])
            if cmArg == '': cmArg = 'no-arg-no'
            mHTML = mHTML + reverse('HandleCommand', kwargs={'CommandNum':m['Command'], 'CommandArg': cmArg})
            mHTML = mHTML + " target=""_blank"""
        # endif
        mHTML = mHTML + ">" + m['OptionText'] + "</a></button>"
        mnItem_list[m['OptionNumber']-1] = mHTML

    fullMenuHTML = HttpResponse(headers={'title': mnuName})
    fullMenuHTML.write("<h2>Calvin is testing here --- please add coffee!! -- Testing the new menu template</h2>")
    fullMenuHTML.write("<h1>" + mnuName + "</h1>")
    fullMenuHTML.write("<table><caption>" + mnuName + "</caption>")
    for i in range(10):
        fullMenuHTML.write("<tr><td><p>" + mnItem_list[i] + "</p></td>")
        fullMenuHTML.write("<td><p>" + mnItem_list[i+10] + "</p></td></tr>")
    fullMenuHTML.write("</table>")  # </body></html>"

    return fullMenuHTML


def HandleMenuCommand(req,CommandNum,CommandArg):
    tmpst = "Command " + menuCommands.objects.get(Command=CommandNum).__str__() + " will be performed with Argument " + CommandArg
    
    if CommandNum == MENUCOMMAND.LoadMenu.value :
        # work on this case
        LoadMenu(req,int(CommandArg))
        pass
    elif CommandNum == MENUCOMMAND.FormBrowse.value :
        tmpst = FormBrowse(req, CommandArg)
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