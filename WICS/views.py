# import dateutil.utils as dateutils
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from cMenu.utils import calvindate
from userprofiles.models import WICSuser
from WICS.forms import CountEntryForm, CountScheduleRecordForm, RelatedMaterialInfo, RelatedScheduleInfo
from WICS.models import MaterialList
from WICS.procs_CountSchedule import fnCountScheduleRecordExists


@login_required
def fnCountEntryView(req, 
            recNum = 0, MatlNum = None, reqDate = calvindate().today(),
            gotoCommand = None
            ):
    _userorg = WICSuser.objects.get(user=req.user).org

    # the string 'None' is not the same as the value None
    if MatlNum=='None': MatlNum=None
    if gotoCommand=='None': gotoCommand=None

    FormMain = CountEntryForm
    FormSubs = [S for S in [RelatedMaterialInfo, RelatedScheduleInfo]]

    modelMain = FormMain.Meta.model
    modelSubs = [S.Meta.model for S in FormSubs]

    prefixvals = {
        'main': 'counts',
        'matl': 'matl',
        'schedule': 'schedule',
    }
    initialvals = {
        'main': {'CountDate': calvindate(reqDate).as_datetime(),'Counter':req.user.get_short_name()},
        'matl': {},
        'schedule': {'CountDate': calvindate(reqDate).as_datetime()},
    }

    changes_saved = {
        'main': False,
        'matl': False,
        'schedule': False
        }
    chgd_dat = {
        'main':None, 
        'matl': None, 
        'schedule': None
        }

    if req.method == 'POST':
        R = req.POST[prefixvals['main']+'-id']
        recNum = int(R) if R.isnumeric() else 0
        try:
            currRec = modelMain.objects.get(pk=recNum)
        except:
            currRec = modelMain(org=_userorg)
        matlRec = modelSubs[0].objects.get(org=_userorg, Material=req.POST[prefixvals['main']+'-Material'])
        #schedRecs = modelSubs[1].objects.filter(org=_userorg, CountDate=req.POST[prefixvals['main']+'-CountDate'], Material=matlRec)

        # process main form
        if currRec: mainFm = FormMain(_userorg, req.POST, instance=currRec,  prefix=prefixvals['main'])   # do I need to pass in intial?
        else: mainFm = FormMain(_userorg, req.POST, initial=initialvals['main'],  prefix=prefixvals['main']) 
        matlSubFm = FormSubs[0](_userorg, matlRec.pk, req.POST, instance=matlRec, prefix=prefixvals['matl'])
        #schedSet = RelatedScheduleInfo(_userorg, SchedID, req.POST, prefix=prefixvals['schedule'], initial=initialvals['schedule'])

        s = modelMain.objects.none()

        # if mainFm.is_valid() and matlSubFm.is_valid() and schedFm.is_valid():
        if mainFm.is_valid() and matlSubFm.is_valid():
            if mainFm.has_changed():
                s = mainFm.save()
                chgd_dat['main'] = mainFm.changed_data
                changes_saved['main'] = s.id
            # material info subform
            if matlSubFm.has_changed():
                matlSubFm.save()
                chgd_dat['matl'] = matlSubFm.changed_data
                changes_saved['matl'] = True
            # count schedule subform
            # if schedSet.has_changed():
            #      schedSet.save()
            #      chgd_dat['schedule'] = schedSet.changed_data
            #      changes_saved['schedule'] = True

            # prep new record to present
            currRec = modelMain(org=_userorg, CountDate=reqDate,Counter=req.user.get_short_name())
            recNum=0
            MatlNum = None
            matlRec = getattr(currRec,'Material', '')
            # MaterialID = getattr(matlRec, 'pk', None)

            if currRec: 
                mainFm = FormMain(_userorg, instance=currRec, prefix=prefixvals['main'])
            else:       
                mainFm = FormMain(_userorg, initial=initialvals['main'],  prefix=prefixvals['main'])
            if matlRec:
                matlSubFm = FormSubs[0](_userorg, matlRec.pk, instance=matlRec, prefix=prefixvals['matl'])
            else:
                matlSubFm = FormSubs[0](_userorg, None, initial=initialvals['matl'], prefix=prefixvals['matl'])


    else:
        currRec = modelMain(org=_userorg, CountDate=reqDate,Counter=req.user.get_short_name())
        matlRec = modelSubs[0].objects.none()
        # TODO: later, do try..except blocks
        if gotoCommand == 'First':
            # TODO: add protection against no records
            recNum = modelMain.objects.filter(org=_userorg).order_by('id').first().pk
        elif gotoCommand == 'Last':
            # TODO: add protection against no records
            recNum = modelMain.objects.filter(org=_userorg).order_by('id').last().pk
        elif gotoCommand == 'Prev':
            try:
                recNum = modelMain.objects.filter(org=_userorg,pk__lt=recNum).order_by('id').last().pk
            except: # assume it's because we're already at first record.  don't go anywhere
                pass
        elif gotoCommand == 'Next':
            try:
                recNum = modelMain.objects.filter(org=_userorg,pk__gt=recNum).order_by('id').first().pk
            except:
                pass
        else:
            pass

        if recNum:
            currRec = modelMain.objects.get(pk=recNum)
            matlRec = currRec.Material  # subject to change

        if gotoCommand == 'ChgKey':
            currRec.CountDate = reqDate
            matlRec = modelSubs[0].objects.get(org=_userorg, Material=MatlNum)
            currRec.Material = matlRec

        # at this point, currRec and matlRec s/b correct

        if currRec: 
            mainFm = FormMain(_userorg, instance=currRec, prefix=prefixvals['main'])
        else:       
            mainFm = FormMain(_userorg, initial=initialvals['main'],  prefix=prefixvals['main'])
        if matlRec:
            matlSubFm = FormSubs[0](_userorg, matlRec.pk, instance=matlRec, prefix=prefixvals['matl'])
        else:
            matlSubFm = FormSubs[0](_userorg, None, initial=initialvals['matl'], prefix=prefixvals['matl'])

    # all counts for this Material today
    if matlRec:
        matchDate = reqDate
        if currRec: matchDate = currRec.CountDate
        todayscounts = modelMain.objects.filter(CountDate=matchDate,Material=matlRec)
    else: 
        todayscounts = modelMain.objects.none()
    # schedFm
    if currRec:
        getDate = currRec.CountDate
        if matlRec and modelSubs[1].objects.filter(org=_userorg, CountDate=getDate, Material=matlRec).exists():
            schedinfo = modelSubs[1].objects.filter(org=_userorg, CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
        else:
            schedinfo = modelSubs[1].objects.none()
    elif (MatlNum!=None) and (gotoCommand==None):
        # review and clean up this block!
        if MatlNum != None:
            # fill in MatlInfo and CountSchedInfo
            if recNum > 0: getDate = currRec.CountDate 
            else: getDate = reqDate
            if modelSubs[1].objects.filter(org=_userorg, CountDate=getDate, Material=matlRec).exists():
                schedinfo = modelSubs[1].objects.filter(org=_userorg, CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
            else:
                schedinfo = modelSubs[1].objects.none()
        elif recNum > 0:
            # ??????????? shouldn't this already be handled?  Think about it...
            # fill in MatlInfo and CountSchedInfo
            getDate = currRec.CountDate
            if modelSubs[1].objects.filter(org=_userorg, CountDate=getDate, Material=matlRec).exists():
                schedinfo = modelSubs[1].objects.filter(org=_userorg, CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
            else:
                schedinfo = modelSubs[1].objects.none()
    else: schedinfo = modelSubs[1].objects.none()
    if not schedinfo: schedFm = FormSubs[1](_userorg, None, initial=initialvals['schedule'], prefix=prefixvals['schedule'])
    else: schedFm = FormSubs[1](_userorg, schedinfo.pk, instance=schedinfo, prefix=prefixvals['schedule'])

    # CountEntryForm MaterialList dropdown
    matlchoiceForm = {}
    if matlRec:
        matlchoiceForm['gotoItem'] = matlRec        # the template pulls Material from this record
    else:
        if MatlNum==None: MatlNum = ''
        matlchoiceForm['gotoItem'] = {'Material':MatlNum}
    matlchoiceForm['choicelist'] = MaterialList.objects.filter(org=_userorg).values('id','Material')

    # display the form
    cntext = {'frmMain': mainFm,
            'frmMatlInfo': matlSubFm,
            'todayscounts': todayscounts,
            'matlchoiceForm':matlchoiceForm,
            'noSchedInfo':(not schedinfo),
            'frmSchedInfo': schedFm,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            'recNum': recNum,
            'matlnum_changed': MatlNum,
            'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'frm_CountEntry.html'
    return render(req, templt, cntext)


@login_required
def fnCountScheduleRecView(req, 
            recNum = 0, MatlNum = None, reqDate = calvindate().today(),
            gotoCommand = None
            ):
    _userorg = WICSuser.objects.get(user=req.user).org

    # the string 'None' is not the same as the value None
    if MatlNum=='None': MatlNum=None
    if gotoCommand=='None': gotoCommand=None

    FormMain = CountScheduleRecordForm
    FormSubs = [S for S in [RelatedMaterialInfo]]

    modelMain = FormMain.Meta.model
    modelSubs = [S.Meta.model for S in FormSubs]

    prefixvals = {
        'main': 'counts',
        'matl': 'matl',
    }
    initialvals = {
        'main': {'CountDate': calvindate(reqDate).as_datetime()},
        'matl': {},
    }

    changes_saved = {
        'main': False,
        'matl': False,
        }
    chgd_dat = {
        'main':None, 
        'matl': None, 
        }

    msgDupSched = ''

    if req.method == 'POST':
        R = req.POST[prefixvals['main']+'-id']
        recNum = int(R) if R.isnumeric() else 0
        try:
            currRec = modelMain.objects.get(pk=recNum)
        except:
            currRec = modelMain(org=_userorg)
        matlRec = modelSubs[0].objects.get(org=_userorg, Material=req.POST[prefixvals['main']+'-Material'])

        # process main form
        if currRec: mainFm = FormMain(_userorg, req.POST, instance=currRec,  prefix=prefixvals['main'])   # do I need to pass in intial?
        else: mainFm = FormMain(_userorg, req.POST, initial=initialvals['main'],  prefix=prefixvals['main']) 
        matlSubFm = FormSubs[0](_userorg, matlRec.pk, req.POST, instance=matlRec, prefix=prefixvals['matl'])

        s = modelMain.objects.none()

        # if mainFm.is_valid() and matlSubFm.is_valid() and schedFm.is_valid():
        if mainFm.is_valid() and matlSubFm.is_valid():
            if mainFm.has_changed():
                s = mainFm.save()
                chgd_dat['main'] = mainFm.changed_data
                changes_saved['main'] = s.id
            # material info subform
            if matlSubFm.has_changed():
                matlSubFm.save()
                chgd_dat['matl'] = matlSubFm.changed_data
                changes_saved['matl'] = True

            # prep new record to present
            currRec = modelMain(org=_userorg, CountDate=reqDate)
            recNum=0
            MatlNum = None
            matlRec = getattr(currRec,'Material', '')

            if currRec: 
                mainFm = FormMain(_userorg, instance=currRec, prefix=prefixvals['main'])
            else:       
                mainFm = FormMain(_userorg, initial=initialvals['main'],  prefix=prefixvals['main'])
            if matlRec:
                matlSubFm = FormSubs[0](_userorg, matlRec.pk, instance=matlRec, prefix=prefixvals['matl'])
            else:
                matlSubFm = FormSubs[0](_userorg, None, initial=initialvals['matl'], prefix=prefixvals['matl'])

    else:
        currRec = modelMain(org=_userorg, CountDate=reqDate)
        matlRec = modelSubs[0].objects.none()
        # TODO: later, do try..except blocks
        if gotoCommand == 'First':
            # TODO: add protection against no records
            recNum = modelMain.objects.filter(org=_userorg).order_by('id').first().pk
        elif gotoCommand == 'Last':
            # TODO: add protection against no records
            recNum = modelMain.objects.filter(org=_userorg).order_by('id').last().pk
        elif gotoCommand == 'Prev':
            try:
                recNum = modelMain.objects.filter(org=_userorg,pk__lt=recNum).order_by('id').last().pk
            except: # assume it's because we're already at first record.  don't go anywhere
                pass
        elif gotoCommand == 'Next':
            try:
                recNum = modelMain.objects.filter(org=_userorg,pk__gt=recNum).order_by('id').first().pk
            except:
                pass
        else:
            pass
        
        incomingMatlRec = matlRec   # in case it's trying to be changed to an existing scheduled count
        if recNum:
            currRec = modelMain.objects.get(pk=recNum)
            matlRec = currRec.Material  # subject to change

        if gotoCommand == 'ChgKey':
            #finally, if this is a new rec, and a rec already exists for this CountDate and Material, the Material must be rejected
            exstSchdRec = getattr(fnCountScheduleRecordExists(_userorg,reqDate,MatlNum),'id', False)
            if exstSchdRec:
                # if its not THIS record, reject
                if (currRec and currRec.id != exstSchdRec):
                    msgDupSched = 'A count for ' + str(MatlNum) + ' is already scheduled for ' + str(reqDate)
                    matlRec = incomingMatlRec
                    MatlNum = getattr(matlRec,'Material',None)
            else:
                currRec.CountDate = reqDate
                matlRec = modelSubs[0].objects.get(org=_userorg, Material=MatlNum)
                currRec.Material = matlRec

        # at this point, currRec and matlRec s/b correct

        if currRec: 
            mainFm = FormMain(_userorg, instance=currRec, prefix=prefixvals['main'])
        else:       
            mainFm = FormMain(_userorg, initial=initialvals['main'],  prefix=prefixvals['main'])
        if matlRec:
            matlSubFm = FormSubs[0](_userorg, matlRec.pk, instance=matlRec, prefix=prefixvals['matl'])
        else:
            matlSubFm = FormSubs[0](_userorg, None, initial=initialvals['matl'], prefix=prefixvals['matl'])

    # CountEntryForm MaterialList dropdown
    matlchoiceForm = {}
    if matlRec:
        matlchoiceForm['gotoItem'] = matlRec        # the template pulls Material from this record
    else:
        if MatlNum==None: MatlNum = ''
        matlchoiceForm['gotoItem'] = {'Material':MatlNum}
    matlchoiceForm['choicelist'] = MaterialList.objects.filter(org=_userorg).values('id','Material')

    # display the form
    cntext = {'frmMain': mainFm,
            'frmMatlInfo': matlSubFm,
            'matlchoiceForm':matlchoiceForm,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            'recNum': recNum,
            'matlnum_changed': MatlNum,
            'msgDupSched': msgDupSched,
            'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'frm_CountScheduleRec.html'
    return render(req, templt, cntext)

