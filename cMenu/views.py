from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse
from django.utils.text import slugify
from cMenu import menucommand_handlers
from cMenu.menucommand_handlers import MENUCOMMAND
from cMenu.models import menuCommands, menuItems
# imports below are WICS-specific
from userprofiles.models import WICSuser

# Create your views here.

# move this to (or find it in) a utility package
def WrapInQuotes(str, quotechar = chr(34)):
    return quotechar + str + quotechar


@login_required
def LoadMenu(req, menuGroup, menuNum):
# DOCUMENT THIS!!!   ADD COMMENTS!!!  EXPLAIN IT!!!
    # next few lines (and their uses) is WICS-specific, not generic cMenu
    _userorg = WICSuser.objects.get(user=req.user).org

    mnItem_qset = menuItems.objects.filter(MenuGroup = menuGroup, MenuID = menuNum).values('OptionNumber','OptionText','Command','Argument')
    mnuName = mnItem_qset.get(OptionNumber=0)['OptionText']

    mnItem_list = ['' for i in range(20)]
    for m in mnItem_qset:
        if m['OptionNumber']==0: continue
        mHTML = "<a href="
        if m['Command'] == 1:
            mHTML = mHTML + reverse('LoadMenu', kwargs={'menuGroup': menuGroup, 'menuNum':m['Argument']})
        else:
            cmArg = slugify(m['Argument'])
            if cmArg == '': cmArg = 'no-arg-no'
            mHTML = mHTML + reverse('HandleCommand', kwargs={'CommandNum':m['Command'], 'CommandArg': cmArg})
            mHTML = mHTML + " target=" + WrapInQuotes("_blank")
        # endif
        mHTML = mHTML + " class=" + WrapInQuotes("btn btn-lg bd-btn-lg btn-outline-secondary mx-auto") + ">" + m['OptionText'] + "</a>"
        mnItem_list[m['OptionNumber']-1] = mHTML

    fullMenuHTML = ""

    for i in range(10):
        fullMenuHTML += ("<div class=" + WrapInQuotes("row") + "><div class=" + WrapInQuotes("col m-1") + ">" + mnItem_list[i] + "</div>")
        fullMenuHTML += ("<div class=" + WrapInQuotes("col m-1") + ">" + mnItem_list[i+10] + "</div></div>")
    ctxt = {'menuName':mnuName , 'menuContents':fullMenuHTML, 'orgname':_userorg.orgname, 'uname':req.user.get_full_name()}
    return render(req, "cMenu.html", context=ctxt)


def HandleMenuCommand(req,CommandNum,CommandArg):
    tmpst = "Command " + menuCommands.objects.get(Command=CommandNum).__str__() + " will be performed with Argument " + CommandArg

    if CommandNum == MENUCOMMAND.LoadMenu.value :
        # work on this case
        LoadMenu(req,int(CommandArg))
        pass
    elif CommandNum == MENUCOMMAND.FormBrowse.value :
        tmpst = menucommand_handlers.FormBrowse(req, CommandArg)
        pass
    elif CommandNum == MENUCOMMAND.FormAdd.value :
        pass
    elif CommandNum == MENUCOMMAND.ReportView.value :
        pass
    elif CommandNum == MENUCOMMAND.ReportPrint.value :
        pass
    elif CommandNum == MENUCOMMAND.OpenTable.value :
        tmpst = menucommand_handlers.ShowTable(req, CommandArg)
        pass
    elif CommandNum == MENUCOMMAND.OpenQuery.value :
        pass
    elif CommandNum == MENUCOMMAND.RunCode.value :
        fn = getattr(menucommand_handlers, CommandArg)
        return fn(req)
    elif CommandNum == MENUCOMMAND.RunSQLStatement.value:
        pass
    elif CommandNum == MENUCOMMAND.ConstructSQLStatement.value:
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