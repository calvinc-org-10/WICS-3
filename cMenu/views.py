from django import forms, db
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import formset_factory, modelformset_factory, CharField
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse, resolve
from django.utils.text import slugify
from django.views.generic import ListView
from django.views.generic.edit import FormView
from typing import Any
from cMenu.utils import WrapInQuotes
from cMenu import menucommand_handlers
from cMenu.menucommand_handlers import MENUCOMMAND
from cMenu.models import menuCommands, menuItems, menuGroups, cParameters
from sysver import sysver
from django_support.settings import sysver_key

# imports below are WICS-specific
from userprofiles.models import WICSuser

# Create your views here.

@login_required
def LoadMenu(req, menuGroup, menuNum):
# DOCUMENT THIS!!!   ADD COMMENTS!!!  EXPLAIN IT!!!
    mnItem_qset = menuItems.objects.filter(MenuGroup = menuGroup, MenuID = menuNum).values('OptionNumber','OptionText','Command','Argument')
    mnuName = mnItem_qset.get(OptionNumber=0)['OptionText']

    mnItem_list = ['' for i in range(20)]
    for m in mnItem_qset:
        if m['OptionNumber']==0: continue
        mHTML = "<a href="
        if m['Command'] == MENUCOMMAND.LoadMenu.value:
            mHTML = mHTML + reverse('LoadMenu', kwargs={'menuGroup': menuGroup, 'menuNum':m['Argument']})
        else:
            cmArg = slugify(m['Argument'])
            if not cmArg: cmArg = 'no-arg-no'
            mHTML = mHTML + reverse('HandleCommand', kwargs={'CommandNum':m['Command'], 'CommandArg': cmArg})
            if m['Command'] != MENUCOMMAND.ExitApplication.value:
                mHTML = mHTML + " target=" + WrapInQuotes("_blank")
        # endif
        mHTML = mHTML + " class=" + WrapInQuotes("btn btn-lg bd-btn-lg btn-outline-secondary mx-auto") + ">" + m['OptionText'] + "</a>"
        mnItem_list[m['OptionNumber']-1] = mHTML

    fullMenuHTML = ""

    for i in range(10):
        fullMenuHTML += ("<div class=" + WrapInQuotes("row") + "><div class=" + WrapInQuotes("col m-1") + ">" + mnItem_list[i] + "</div>")
        fullMenuHTML += ("<div class=" + WrapInQuotes("col m-1") + ">" + mnItem_list[i+10] + "</div></div>")
    cntext = {
        'grpNum': menuGroup,
        'menuNum': menuNum,
        'menuName':mnuName , 'menuContents':fullMenuHTML,
        'sysver': sysver[sysver_key],
        }
    templt = "cMenu.html"
    return render(req, templt, context=cntext)


def HandleMenuCommand(req,CommandNum,CommandArg):
    retHTTP = "Command " + menuCommands.objects.get(Command=CommandNum).__str__() + " will be performed with Argument " + CommandArg

    # LoadMenu is handled directly in the menu; it doesn't call HandleMenuCommand
    # if CommandNum == MENUCOMMAND.LoadMenu.value :
    #     WUsrMenuGroup = WICSuser.objects.get(user=req.user).menuGroup_id
    #     retHTTP = LoadMenu(req, WUsrMenuGroup,int(CommandArg))
    # el
    if CommandNum == MENUCOMMAND.FormBrowse.value :
        retHTTP = menucommand_handlers.FormBrowse(req, CommandArg)  # replace this with the url reverse
    elif CommandNum == MENUCOMMAND.OpenTable.value :
        retHTTP = menucommand_handlers.ShowTable(req, CommandArg)
    elif CommandNum == MENUCOMMAND.RunCode.value :
        fn = getattr(menucommand_handlers, CommandArg)
        retHTTP = fn(req)
    elif CommandNum == MENUCOMMAND.RunSQLStatement.value:
        # retHTTP = reverse('RunSQL')
        return HttpResponseRedirect(reverse('RunSQL'))
    elif CommandNum == MENUCOMMAND.ConstructSQLStatement.value:
        pass
    elif CommandNum == MENUCOMMAND.ChangePW.value:
        return HttpResponseRedirect(reverse('change_password'))
    elif CommandNum == MENUCOMMAND.EditMenu.value :
        return HttpResponseRedirect(reverse('EditMenu_init'))
    elif CommandNum == MENUCOMMAND.EditParameters.value :
        return HttpResponseRedirect(reverse('EditParms'))
    elif CommandNum == MENUCOMMAND.EditGreetings.value :
        pass
    elif CommandNum == MENUCOMMAND.ExitApplication.value :
        return HttpResponseRedirect(reverse('WICSlogout'))
    else:
        pass

    return HttpResponse(retHTTP)


@permission_required('SUPERUSER', raise_exception=True)
def EditMenu(req, menuGroup, menuNum):
# DOCUMENT THIS!!!   ADD COMMENTS!!!  EXPLAIN IT!!!

    # things go bonkers if these are strings
    menuGroup = int(menuGroup)
    menuNum = int(menuNum)

    commandchoices = menuCommands.objects.all()
    def commandchoiceHTML(passedcommand):
        commandchoices_html = ""
        for ch in commandchoices:
            commandchoices_html += "<option value=" + str(ch.Command)
            if ch.Command == passedcommand: commandchoices_html += " selected"
            commandchoices_html += ">" + ch.CommandText + "</option>"
        return commandchoices_html

    mnItem_qset = menuItems.objects.filter(MenuGroup = menuGroup, MenuID = menuNum)     #.values('OptionNumber','OptionText','Command','Argument')
    mnuGroupRec = menuGroups.objects.get(id=menuGroup)

    mnItem_list = [{'OptionText':'',
                    'Command':'',
                    'Argument':''}
            for i in range(20)]
    changed_data = ''

    if req.method == 'POST':
        # construct mnItem_list from POST data
        for pdat in req.POST.items():
            if "csrf" in pdat[0]:
                continue
            if "menuName" in pdat[0]:
                mnTitle = mnItem_qset.get(OptionNumber=0)
                if mnTitle.OptionText != pdat[1]:
                    mnTitle.OptionText = pdat[1]
                    mnTitle.save()
                    if changed_data: changed_data += ", "
                    changed_data += "Menu Name changed"
                continue
            if "menugroupName" in pdat[0]:
                # mnuGroupRec is captured above
                if mnuGroupRec.GroupName != pdat[1]:
                    mnuGroupRec.GroupName = pdat[1]
                    mnuGroupRec.save()
                    if changed_data: changed_data += ", "
                    changed_data += "Menu Group Name changed"
                continue
            pdat_line = pdat[0].split('-')
            idx = int(pdat_line[1])-1
            mnItem_list[idx][pdat_line[0]] = pdat[1]

        # compare to mnItem_qset
        # where different, update or add
        # set signal to pass back to form
        for i_0based in range(20):
            i = i_0based + 1
            thisItem = mnItem_list[i_0based]
            thisItem['Command'] = int(thisItem['Command'])      # make the Command a number, not a string
            try:
                mnRec = mnItem_qset.get(OptionNumber=i)
            except:
                mnRec = None

            if thisItem.get('Remove',False):    # later, use makebool since values may be 'on' or 'off'
                if mnRec:
                    mnRec.delete()
                mnItem_list[i_0based] = {'OptionText':'',
                                'Command':'',
                                'Argument':''}
                if changed_data: changed_data += ", "
                changed_data += " Option " + str(i) + " removed"
            if mnRec:
                if mnRec.OptionText != thisItem['OptionText'] \
                or mnRec.Command_id != thisItem['Command'] \
                or mnRec.Argument != thisItem['Argument']:
                    # mnRec exists, and mnItem_list is changed
                    mnRec.OptionText = thisItem['OptionText']
                    mnRec.Command_id = thisItem['Command']
                    mnRec.Argument = thisItem['Argument']
                    mnRec.save()
                    if changed_data: changed_data += ", "
                    changed_data += " Option " + str(i) + " changed"
            else:
                if thisItem['OptionText'] \
                or thisItem['Command'] \
                or thisItem['Argument']:
                    # mnRec does not exist, but mnItem_list is new (has values)
                    mnRec = menuItems(MenuGroup_id = menuGroup,
                        MenuID = menuNum,
                        OptionNumber = i,
                        OptionText = thisItem['OptionText'],
                        Command_id = thisItem['Command'],
                        Argument = thisItem['Argument']
                        )
                    mnRec.save()
                    if changed_data: changed_data += ", "
                    changed_data += " Option " + str(i) + " added"
            #endif mnRec
            if mnRec and thisItem.get('CopyTo',''):
                MoveORCopy = thisItem.get('CopyTo')
                CopyTarget = thisItem.get('CopyTarget').split(',')
                targetGroup = None
                if len(CopyTarget)==2:
                    targetGroup = menuGroup
                    try:
                        targetMenu = int(CopyTarget[0])
                    except:
                        targetMenu = None
                    try:
                        targetOption = int(CopyTarget[1])
                    except:
                        targetOption = None
                elif len(CopyTarget)==3:
                    try:
                        targetGroup = int(CopyTarget[0])
                    except:
                        targetGroup = None
                    try:
                        targetMenu = int(CopyTarget[1])
                    except:
                        targetMenu = None
                    try:
                        targetOption = int(CopyTarget[2])
                    except:
                        targetOption = None
                else:
                    pass    # targetGroup is already None

                if targetGroup==None or targetMenu==None or targetOption==None:
                    if changed_data: changed_data += ", "
                    changed_data += "Could not interpret option " + str(i) + " " + MoveORCopy + " target " + thisItem.get('CopyTarget')
                else:
                    if menuItems.objects.filter(MenuGroup=targetGroup, MenuID=targetMenu, OptionNumber=targetOption).exists():
                        if changed_data: changed_data += ", "
                        changed_data += "Could not " + MoveORCopy + " option " + str(i)
                        changed_data +=  " - target " + thisItem.get('CopyTarget') + " already exists."
                    else:
                        menuItems(
                                MenuGroup_id = targetGroup,
                                MenuID = targetMenu,
                                OptionNumber = targetOption,
                                OptionText = mnRec.OptionText,
                                Command = mnRec.Command,
                                Argument = mnRec.Argument
                            ).save()
                        if MoveORCopy == 'move':
                            mnRec.delete()
                            mnItem_list[i_0based] = {'OptionText':'',
                                'Command':'',
                                'Argument':''}


                        if changed_data: changed_data += ", "
                        changed_data += "Option " + str(i)
                        if MoveORCopy == 'move': changed_data += " moved"
                        else: changed_data += " copied"
                        changed_data +=  " to " + thisItem.get('CopyTarget') + "."

                        # if an item in THIS menu has changed, make mnItem_list reflect it
                        if targetGroup==menuGroup and targetMenu==menuNum:
                            mnItem_list[targetOption-1]['OptionText'] = mnRec.OptionText
                            mnItem_list[targetOption-1]['Command'] = mnRec.Command_id
                            mnItem_list[targetOption-1]['Argument'] = mnRec.Argument
    else:
        for m in mnItem_qset:
            mnItem_list[m.OptionNumber-1]['OptionText'] = m.OptionText
            mnItem_list[m.OptionNumber-1]['Command'] = m.Command_id
            mnItem_list[m.OptionNumber-1]['Argument'] = m.Argument
    # endif request.method = 'POST'

    fullMenuHTML = ""
    for i_0based in range(10):
        i = i_0based + 1
        istr = str(i)
        i2 = i+10
        i2str = str(i2)
        fullMenuHTML += "<div class='row'>"
        fullMenuHTML += "<div class='col m-1'> " + istr + " "
        fullMenuHTML += "<input type='text' size='20' name='OptionText-" + istr + "'"
        if mnItem_list[i_0based]['OptionText']: fullMenuHTML += " value = '" + mnItem_list[i_0based]['OptionText'] + "'"
        fullMenuHTML += "></input></div>"
        fullMenuHTML += "<div class='col m-1'> " + i2str + " "
        fullMenuHTML += "<input type='text' size='20' name='OptionText-" + i2str + "'"
        if mnItem_list[i_0based+10]['OptionText']: fullMenuHTML += " value = '" + mnItem_list[i_0based+10]['OptionText'] + "'"
        fullMenuHTML += "></input></div>"
        fullMenuHTML += "</div>"

        fullMenuHTML += "<div class='row'>"
        fullMenuHTML += "<div class='col m-1'> Command: "
        fullMenuHTML += "<select style='width:15em' name='Command-" + istr + "'>"
        fullMenuHTML += commandchoiceHTML(mnItem_list[i_0based]['Command'])
        fullMenuHTML += "</select>"
        fullMenuHTML += "</div>"
        fullMenuHTML += "<div class='col m-1'> Command: "
        fullMenuHTML += "<select style='width:15em' name='Command-" + i2str + "'>"
        fullMenuHTML += commandchoiceHTML(mnItem_list[i_0based+10]['Command'])
        fullMenuHTML += "</select>"
        fullMenuHTML += "</div>"
        fullMenuHTML += "</div>"

        fullMenuHTML += "<div class='row'>"
        fullMenuHTML += "<div class='col m-1'> Argument: "
        fullMenuHTML += "<input type='text' size='20' name='Argument-" + istr + "'"
        if mnItem_list[i_0based]['Argument']: fullMenuHTML += " value = '" + mnItem_list[i_0based]['Argument'] + "'"
        fullMenuHTML += "></input></div>"
        fullMenuHTML += "<div class='col m-1'> Argument: "
        fullMenuHTML += "<input type='text' size='20' name='Argument-" + i2str + "'"
        if mnItem_list[i_0based+10]['Argument']: fullMenuHTML += " value = '" + mnItem_list[i_0based+10]['Argument'] + "'"
        fullMenuHTML += "></input></div>"
        fullMenuHTML += "</div>"

        fullMenuHTML += "<div class='row'>"
        fullMenuHTML += "<div class='col m-1'>"
        #fullMenuHTML += "----<input type='radio' name='CopyTo-" + istr + "' value=''>"
        fullMenuHTML += " Copy<input type='radio' name='CopyTo-" + istr + "' value='copy'>"
        fullMenuHTML += " Move<input type='radio' name='CopyTo-" + istr + "' value='move'>"
        fullMenuHTML += " to <input type='text' name='CopyTarget-" + istr + "' size='5'>"
        fullMenuHTML += " Remove:<input type='checkbox' name='Remove-" + istr + "'>"
        fullMenuHTML += "</div>"
        fullMenuHTML += "<div class='col m-1'>"
        #fullMenuHTML += "----<input type='radio' name='CopyTo-" + i2str + "' value=''>"
        fullMenuHTML += " Copy<input type='radio' name='CopyTo-" + i2str + "' value='copy'>"
        fullMenuHTML += " Move<input type='radio' name='CopyTo-" + i2str + "' value='move'>"
        fullMenuHTML += " to <input type='text' name='CopyTarget-" + i2str + "' size='5'>"
        fullMenuHTML += " Remove: <input type='checkbox' name='Remove-" + i2str + "'>"
        fullMenuHTML += "</div>"
        fullMenuHTML += "</div>"
        if i<10:
            fullMenuHTML += "<hr>"

    mnuGoto = {'menuGroup':menuGroup,
                'menuGroup_choices': menuGroups.objects.all(),
                'menuID':menuNum,
                'menuID_choices':menuItems.objects.filter(MenuGroup=menuGroup,OptionNumber=0)
                }

    cntext = {
        'menuGroupName': mnuGroupRec.GroupName,
        'menuName':mnItem_qset.get(OptionNumber=0).OptionText,
        'menuGoto':mnuGoto,
        'menuContents':fullMenuHTML,
        'changed_data': changed_data,
        }
    templt = "cMenuEdit.html"
    return render(req, templt, context=cntext)


@permission_required('SUPERUSER', raise_exception=True)
def MenuCreate(req, menuGroup, menuNum, fromGroup=None, fromMenu=None):

    # things go bonkers if these are strings
    menuGroup = int(menuGroup)
    menuNum = int(menuNum)
    if fromGroup: fromGroup = int(fromGroup)
    if fromMenu: fromMenu = int(fromMenu)

    # the new menu must not currently exist
    if menuItems.objects.filter(MenuGroup_id=menuGroup, MenuID=menuNum).exists():
        # nope, cannot create an already existing menu
        messages.add_message(req,
                    messages.ERROR,
                    'menu {},{} exists - it cannot be created'.format(menuGroup,menuNum))
        return HttpResponseRedirect(reverse('EditMenu_init'))
    else:
        # create the new MenuGroup, if need be
        menuGroupObj, isnew = menuGroups.objects.get_or_create(id=menuGroup, defaults={'GroupName':'New Menu Group'})
        if fromMenu:
            if not fromGroup: fromGroup = menuGroup
            for mItm in menuItems.objects.filter(MenuGroup_id=fromGroup, MenuID=fromMenu):
                menuItems(
                    MenuGroup = menuGroupObj,
                    MenuID = menuNum,
                    OptionNumber = mItm.OptionNumber,
                    OptionText = mItm.OptionText,
                    Command = mItm.Command,
                    Argument = mItm.Argument
                ).save()
        else:
            menuItems(
                MenuGroup = menuGroupObj,
                MenuID = menuNum,
                OptionNumber = 0,
                OptionText = 'New Menu'
            ).save()
            menuItems(
                MenuGroup = menuGroupObj,
                MenuID = menuNum,
                OptionNumber = 20,
                OptionText = 'Return to Main Menu',
                Command_id = MENUCOMMAND.LoadMenu.value,
                Argument = 0
            ).save()
            
        return HttpResponseRedirect(reverse('EditMenu', kwargs={'menuGroup':menuGroup, 'menuNum':menuNum}))


@permission_required('SUPERUSER', raise_exception=True)
def MenuRemove(req, menuGroup, menuNum):

    # things go bonkers if these are strings
    menuGroup = int(menuGroup)
    menuNum = int(menuNum)

    # permission was granted to do the delete in the HTML, so just do it
    menuItems.objects.filter(MenuGroup_id=menuGroup, MenuID=menuNum).delete()

    # redirect to url:EditMenu at end
    #return HttpResponseRedirect(reverse('EditMenu', kwargs={'menuGroup':menuGroup, 'menuNum':menuNum}))
    return HttpResponseRedirect(reverse('EditMenu_init'))


from collections import namedtuple

def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]
def namedtuplefetchall(cursor, ResultName = 'Result'):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple(ResultName, [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

class fm_cRawSQL(forms.Form):
    inputSQL = forms.CharField(widget=forms.Textarea(attrs={'cols':120}))


@login_required
def fn_cRawSQL(req):

    cntext = {}

    if req.method == 'POST':
        SForm = fm_cRawSQL(req.POST)

        if not SForm.is_valid(): raise Exception('The SQL is invalid!!')
        sqlerr = None
        with db.connection.cursor() as cursor:
            try:
                cursor.execute(SForm.cleaned_data['inputSQL'])
            except Exception as err:
                sqlerr = err
        if not sqlerr:
            if cursor.description:
                colNames = [col[0] for col in cursor.description]
                #rows = dictfetchall(cursor)
                cntext['colNames'] = colNames
                cntext['nRecs'] = cursor.rowcount
                cntext['SQLresults'] = cursor
            else:
                cntext['colNames'] = 'NO RECORDS RETURNED; ' + str(cursor.rowcount) + ' records affected'
                cntext['nRecs'] = cursor.rowcount
                cntext['SQLresults'] = cursor

            cntext['OrigSQL'] = SForm.cleaned_data['inputSQL']

            templt = "show_raw_SQL.html"                
        else:
            SForm = fm_cRawSQL(req.POST)

            cntext['form'] = SForm
            messages.add_message(req, messages.WARNING,message=sqlerr) 
            templt = "enter_raw_SQL.html"
    else:
        SForm = fm_cRawSQL()

        cntext['form'] = SForm
        templt = "enter_raw_SQL.html"
        

    return render(req, templt, context=cntext)

    

# class cParmFormList(LoginRequiredMixin, ListView):
#     model = cParameters
#     template_name = 'cParameters.html'
#     context_object_name = 'plist'
#     extra_context = {}

#     def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
#         return super().setup(request, *args, **kwargs)

#     def post():
#         pass

# class cParmForm(forms.ModelForm):
#     class Meta:
#         model = cParameters
#         fields = '__all__'
# class cParmForm2(forms.Form):
#     ParmName = forms.CharField()
#     ParmValue = forms.CharField()
#     UserModifiable = forms.BooleanField()
#     Comments = forms.CharField()



@permission_required('SUPERUSER', raise_exception=True)
def fncParmForm(req):
    # mdlForm = cParmForm
    mdlClass = cParameters
    mdlFields = ['ParmName', 'ParmValue', 'UserModifiable', 'Comments']

    initRecs = mdlClass.objects.all()
    initvals = {'UserModifiable':True}


    pFormSet_class = modelformset_factory(mdlClass, fields=mdlFields, can_delete=True)
    changes = {}
    templt = 'cParameters.html'

    if req.method == 'POST':
        pFormSet = pFormSet_class(req.POST, queryset=initRecs)
        if pFormSet.is_valid():
            pFormSet.save()
            changes['changed'] = None
            if pFormSet.changed_objects: changes['changed'] = pFormSet.changed_objects 
            changes['deleted'] = None
            if pFormSet.deleted_objects: changes['deleted'] = pFormSet.deleted_objects 
            changes['added'] = None
            if pFormSet.new_objects: changes['added'] = pFormSet.new_objects 
            templt = 'cParameters-success.html'
        else:
            # reveal the errors and try again
            pass
        #endif
    else:
        pFormSet = pFormSet_class(queryset=initRecs)
    #endif

    cntext = {
        'plist': pFormSet, 
        'Changes': changes, 
        }
    return render(req, templt, cntext)

