from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse
from django.utils.text import slugify
from WICS.forms import FormBrowse       # later, move this to cMenu
from cMenu.menucommand_handlers import *
from cMenu.models import menuCommands, menuItems

# Create your views here.

# move this to (or find it in) a utility package
def WrapInQuotes(str):
    quotechar = chr(34)
    return quotechar + str + quotechar

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
        mHTML = "<button type=" + WrapInQuotes("button") + " class=" + WrapInQuotes("btn btn-outline-primary col-6 mx-auto") + "><a href="
        if m['Command'] == 1:
            mHTML = mHTML + reverse('LoadMenu', kwargs={'menuNum':m['Argument']})
        else:
            cmArg = slugify(m['Argument'])
            if cmArg == '': cmArg = 'no-arg-no'
            mHTML = mHTML + reverse('HandleCommand', kwargs={'CommandNum':m['Command'], 'CommandArg': cmArg})
            mHTML = mHTML + " target=" + WrapInQuotes("_blank")
        # endif
        mHTML = mHTML + ">" + m['OptionText'] + "</a></button>"
        mnItem_list[m['OptionNumber']-1] = mHTML

    fullMenuHTML = ""
    #fullMenuHTML = HttpResponse(headers={'title': mnuName,
    #                                'meta':'name=""viewport"" content=""width=device-width, initial-scale=1""',
    #                                'link':'href=""https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.css"" rel=""sytlesheet"" crossorigin=""anonymous""'
    #                                })
    #fullMenuHTML.write("<script src=""https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js"" integrity=""sha384-OERcA2EqjJCMA+/3y+gxIOqMEjwtxJY7qPCqsdltbNJuaOe923+mo//f6V8Qbsw3"" crossorigin=""anonymous""></script>")
    #fullMenuHTML.write("<h2>Calvin is testing here --- please add coffee!!</h2>")
    #fullMenuHTML.write("<h1>" + mnuName + "</h1>")

    for i in range(10):
        fullMenuHTML += ("<div class=" + WrapInQuotes("row") + "><div class=" + WrapInQuotes("col m-1") + ">" + mnItem_list[i] + "</div>")
        fullMenuHTML += ("<div class=" + WrapInQuotes("col m-1") + ">" + mnItem_list[i+10] + "</div></div>")
    # fullMenuHTML.write("</div>")  # </body></html>"
    ctxt = {'menuName':mnuName , 'menuContents':fullMenuHTML}
    return render(req, "cMenu.html", context=ctxt)


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