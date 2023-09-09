from django.contrib.auth.decorators import login_required
from django.db.models import Value
from django.forms import modelformset_factory
from django import http # for the various HttpResponses
from django.shortcuts import render
from cMenu.utils import calvindate
from userprofiles.models import WICSuser
from WICS.forms import CountEntryForm, CountScheduleRecordForm, RequestCountScheduleRecordForm
from WICS.forms import RelatedMaterialInfo, RelatedScheduleInfo
from WICS.procs_misc import HolidayList
from WICS.models import VIEW_materials, ActualCounts
from WICS.procs_CountSchedule import fnCountScheduleRecordExists


@login_required
def fnCountEntryView(req, 
            recNum = None, MatlNum = None, reqDate = None,
            gotoCommand = None
            ):

    # defauls parms
    if recNum is None: recNum = 0
    if reqDate is None: reqDate = calvindate().today()

    # the string 'None' is not the same as the value None
    if MatlNum=='None' or MatlNum is None: MatlNum=0
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
            currRec = modelMain()
        matlRec = modelSubs[0].objects.get(id=req.POST['MatlPK'])
        #schedRecs = modelSubs[1].objects.filter(org=_userorg, CountDate=req.POST[prefixvals['main']+'-CountDate'], Material=matlRec)

        # process main form
        if currRec: mainFm = FormMain(req.POST, instance=currRec,  prefix=prefixvals['main'])   # do I need to pass in intial?
        else: mainFm = FormMain(req.POST, initial=initialvals['main'],  prefix=prefixvals['main']) 
        matlSubFm = FormSubs[0](matlRec.pk, req.POST, instance=matlRec, prefix=prefixvals['matl'])
        #schedSet = RelatedScheduleInfo(_userorg, SchedID, req.POST, prefix=prefixvals['schedule'], initial=initialvals['schedule'])

        s = modelMain.objects.none()

        # if mainFm.is_valid() and matlSubFm.is_valid() and schedFm.is_valid():
        if mainFm.is_valid() and matlSubFm.is_valid():
            if mainFm.has_changed():
                s = mainFm.save()
                chgd_dat['main'] = []
                for chgdfld in mainFm.changed_data:
                    chgd_dat['main'].append(chgdfld+'='+str(mainFm.cleaned_data[chgdfld]))
                changes_saved['main'] = s.id
            # material info subform
            if matlSubFm.has_changed():
                matlSubFm.save()
                chgd_dat['matl'] = []
                for chgdfld in matlSubFm.changed_data:
                    chgd_dat['matl'].append(chgdfld+'='+str(matlSubFm.cleaned_data[chgdfld]))
                changes_saved['matl'] = True
            # count schedule subform
            # if schedSet.has_changed():
            #      schedSet.save()
            #      chgd_dat['schedule'] = schedSet.changed_data
            #      changes_saved['schedule'] = True

            # prep new record to present
            currRec = modelMain(CountDate=reqDate,Counter=req.user.get_short_name())
            recNum=0
            MatlNum = 0
            matlRec = getattr(currRec,'Material', '')
            # MaterialID = getattr(matlRec, 'pk', None)

            if currRec: 
                mainFm = FormMain(instance=currRec, prefix=prefixvals['main'])
            else:       
                mainFm = FormMain(initial=initialvals['main'],  prefix=prefixvals['main'])
            if matlRec:
                matlSubFm = FormSubs[0](matlRec.pk, instance=matlRec, prefix=prefixvals['matl'])
            else:
                matlSubFm = FormSubs[0](None, initial=initialvals['matl'], prefix=prefixvals['matl'])
    else:
        currRec = modelMain(CountDate=reqDate,Counter=req.user.get_short_name())
        matlRec = modelSubs[0].objects.none()

        # TODO: add protection against no records
        recFirstPK = modelMain.objects.order_by('id').first().pk
        recLastPK = modelMain.objects.order_by('id').last().pk
        
        if gotoCommand == 'New':
            recNum = 0
        if gotoCommand == 'First':
            try:
                recNum = recFirstPK
            except:
                recNum = 0
        elif gotoCommand == 'Last':
            try:
                recNum = recLastPK
            except:
                recNum = 0
        elif gotoCommand == 'Prev':
            try:
                if recNum <= 0:
                    recNum = recLastPK
                elif recNum <= recFirstPK:
                    recNum = recFirstPK
                else:
                    recNum = modelMain.objects.filter(pk__lt=recNum).order_by('id').last().pk
            except:
                recNum = 0
        elif gotoCommand == 'Next':
            try:
                if recNum <= 0:
                    recNum = recFirstPK
                elif recNum >= recLastPK:
                    recNum = recLastPK
                else:
                    recNum = modelMain.objects.filter(pk__gt=recNum).order_by('id').first().pk
            except:
                recNum = 0
        else:
            pass

        if recNum:
            currRec = modelMain.objects.get(pk=recNum)
            matlRec = currRec.Material  # subject to change

        if gotoCommand == 'ChgKey':
            currRec.CountDate = reqDate
            matlRec = modelSubs[0].objects.get(pk=MatlNum)
            currRec.Material = matlRec
            currRec.Material_id = MatlNum

        # at this point, currRec and matlRec s/b correct

        if currRec: 
            mainFm = FormMain(instance=currRec, prefix=prefixvals['main'])
        else:       
            mainFm = FormMain(initial=initialvals['main'],  prefix=prefixvals['main'])
        if matlRec:
            matlSubFm = FormSubs[0](matlRec.pk, instance=matlRec, prefix=prefixvals['matl'])
        else:
            matlSubFm = FormSubs[0](None, initial=initialvals['matl'], prefix=prefixvals['matl'])

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
        if matlRec and modelSubs[1].objects.filter(CountDate=getDate, Material=matlRec).exists():
            schedinfo = modelSubs[1].objects.filter(CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
        else:
            schedinfo = modelSubs[1].objects.none()
    elif (MatlNum!=0) and (gotoCommand==None):
        # review and clean up this block!
        if MatlNum != 0:
            # fill in MatlInfo and CountSchedInfo
            if recNum > 0: getDate = currRec.CountDate 
            else: getDate = reqDate
            if modelSubs[1].objects.filter(CountDate=getDate, Material=matlRec).exists():
                schedinfo = modelSubs[1].objects.filter(CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
            else:
                schedinfo = modelSubs[1].objects.none()
        elif recNum > 0:
            # ??????????? shouldn't this already be handled?  Think about it...
            # fill in MatlInfo and CountSchedInfo
            getDate = currRec.CountDate
            if modelSubs[1].objects.filter(CountDate=getDate, Material=matlRec).exists():
                schedinfo = modelSubs[1].objects.filter(CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
            else:
                schedinfo = modelSubs[1].objects.none()
    else: schedinfo = modelSubs[1].objects.none()
    if not schedinfo: schedFm = FormSubs[1](None, initial=initialvals['schedule'], prefix=prefixvals['schedule'])
    else: schedFm = FormSubs[1](schedinfo.pk, instance=schedinfo, prefix=prefixvals['schedule'])

    # CountEntryForm MaterialList dropdown
    matlchoiceForm = {}
    if matlRec:
        matlchoiceForm['gotoItem'] = matlRec        # the template pulls Material from this record
    else:
        if MatlNum==None: MatlNum = 0
        ## matlchoiceForm['gotoItem'] = {'Material':MatlNum}
        matlchoiceForm['gotoItem'] = ''
    matlchoiceForm['choicelist'] = VIEW_materials.objects.all().values('id','Material_org')

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
            }
    templt = 'frm_CountEntry.html'
    return render(req, templt, cntext)

############################################################################

def _fnCountSchedRecViewCommon(req, variation,
            recNum = 0, MatlNum = 0, reqDate = None,
            gotoCommand = None, **kwargs
            ):
    requser = WICSuser.objects.get(user=req.user)

    # defauls parms
    if recNum is None: recNum = 0
    if reqDate is None: 
        skipdates = HolidayList()
        reqDate = calvindate().nextWorkdayAfter(extraNonWorkdayList=skipdates)

    # the string 'None' is not the same as the value None
    if MatlNum=='None' or MatlNum is None: MatlNum=0
    if gotoCommand=='None': gotoCommand=None

    if variation=='REQ':
        FormMain = RequestCountScheduleRecordForm
    else:
        FormMain = CountScheduleRecordForm
    FormSubs = [S for S in [RelatedMaterialInfo]]

    modelMain = FormMain.Meta.model
    modelSubs = [S.Meta.model for S in FormSubs]

    prefixvals = {
        'main': 'counts',
        'matl': 'matl',
    }
    initialvals = {
        'main': {'CountDate': calvindate(reqDate).as_datetime(), 'RequestFilled': None},
        'matl': {},
    }
    if variation == 'REQ':
        initialvals['main']['Requestor'] = req.user.get_short_name()
    else:
        initialvals['main']['Requestor'] = None

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
            currRec = modelMain()
        matlRec = modelSubs[0].objects.get(pk=req.POST['MatlPK'])

        # process main form
        if currRec: mainFm = FormMain(req.POST, instance=currRec,  prefix=prefixvals['main'])
        else: mainFm = FormMain(req.POST, initial=initialvals['main'],  prefix=prefixvals['main']) 
        matlSubFm = FormSubs[0](matlRec.pk, req.POST, instance=matlRec, prefix=prefixvals['matl'])

        s = modelMain.objects.none()

        # if mainFm.is_valid() and matlSubFm.is_valid() and schedFm.is_valid():
        if mainFm.is_valid() and matlSubFm.is_valid():
            if mainFm.has_changed():
                if variation=='REQ':
                    s = mainFm.save(requser)    #pylint: disable=E1120
                else:
                    s = mainFm.save()    #pylint: disable=E1120
                chgd_dat['main'] = []
                for chgdfld in mainFm.changed_data:
                    chgd_dat['main'].append(chgdfld+'='+str(mainFm.cleaned_data[chgdfld]))
                changes_saved['main'] = s.id
            # material info subform
            if matlSubFm.has_changed():
                matlSubFm.save()
                chgd_dat['matl'] = []
                for chgdfld in matlSubFm.changed_data:
                    chgd_dat['matl'].append(chgdfld+'='+str(matlSubFm.cleaned_data[chgdfld]))
                changes_saved['matl'] = True

            # prep new record to present
            currRec = modelMain(
                CountDate=reqDate, 
                Requestor=req.user.get_short_name() if variation=='REQ' else None,
                RequestFilled=None
                )
            recNum=0
            MatlNum = 0
            matlRec = getattr(currRec,'Material', '')

            if currRec: 
                mainFm = FormMain(instance=currRec, prefix=prefixvals['main'])
            else:       
                mainFm = FormMain(initial=initialvals['main'],  prefix=prefixvals['main'])
            if matlRec:
                matlSubFm = FormSubs[0](matlRec.pk, instance=matlRec, prefix=prefixvals['matl'])
            else:
                matlSubFm = FormSubs[0](None, initial=initialvals['matl'], prefix=prefixvals['matl'])

    else:
        currRec = modelMain(
            CountDate=reqDate, 
            Requestor=req.user.get_short_name() if variation=='REQ' else None,
            RequestFilled=None
            )
        matlRec = modelSubs[0].objects.none()

        # TODO: add protection against no records
        recFirstPK = modelMain.objects.order_by('id').first().pk
        recLastPK = modelMain.objects.order_by('id').last().pk
        
        if gotoCommand == 'New':
            recNum = 0
        if gotoCommand == 'First':
            try:
                recNum = recFirstPK
            except:
                recNum = 0
        elif gotoCommand == 'Last':
            try:
                recNum = recLastPK
            except:
                recNum = 0
        elif gotoCommand == 'Prev':
            try:
                if recNum <= 0:
                    recNum = recLastPK
                elif recNum <= recFirstPK:
                    recNum = recFirstPK
                else:
                    recNum = modelMain.objects.filter(pk__lt=recNum).order_by('id').last().pk
            except:
                recNum = 0
        elif gotoCommand == 'Next':
            try:
                if recNum <= 0:
                    recNum = recFirstPK
                elif recNum >= recLastPK:
                    recNum = recLastPK
                else:
                    recNum = modelMain.objects.filter(pk__gt=recNum).order_by('id').first().pk
            except:
                recNum = 0
        else:
            pass

        incomingMatlRec = matlRec   # in case it's trying to be changed to an existing scheduled count
        if recNum:
            currRec = modelMain.objects.get(pk=recNum)
            matlRec = currRec.Material  # subject to change

        if gotoCommand == 'ChgKey':
            #finally, if this is a new rec, and a rec already exists for this CountDate and Material, the Material must be rejected
            MatlNum = int(MatlNum)
            exstSchdRec = getattr(fnCountScheduleRecordExists(reqDate,MatlNum),'id', False)
            if exstSchdRec:
                # if its not THIS record, reject
                if (currRec and currRec.id != exstSchdRec):
                    matlRec = VIEW_materials.objects.get(id=MatlNum)
                    msgDupSched = 'A count for ' + str(matlRec.Material) + ' is already scheduled for ' + str(reqDate)
                    matlRec = incomingMatlRec
                    MatlNum = getattr(matlRec,'Material',None)
            else:
                currRec.CountDate = reqDate
                matlRec = modelSubs[0].objects.get(pk=MatlNum)
                currRec.Material = matlRec

        # at this point, currRec and matlRec s/b correct

        if currRec: 
            mainFm = FormMain(instance=currRec, prefix=prefixvals['main'])
        else:       
            mainFm = FormMain(initial=initialvals['main'],  prefix=prefixvals['main'])
        if matlRec:
            matlSubFm = FormSubs[0](matlRec.pk, instance=matlRec, prefix=prefixvals['matl'])
        else:
            matlSubFm = FormSubs[0](None, initial=initialvals['matl'], prefix=prefixvals['matl'])

    # CountEntryForm MaterialList dropdown
    matlchoiceForm = {}
    if matlRec:
        matlchoiceForm['gotoItem'] = matlRec        # the template pulls Material from this record
    else:
        if MatlNum==None: MatlNum = 0
        ## matlchoiceForm['gotoItem'] = {'Material':MatlNum}
        matlchoiceForm['gotoItem'] = ''
    matlchoiceForm['choicelist'] = VIEW_materials.objects.all().values('id','Material_org')

    # display the form
    cntext = {'frmMain': mainFm,
            'frmMatlInfo': matlSubFm,
            'matlchoiceForm':matlchoiceForm,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            'recNum': recNum,
            'matlnum_changed': MatlNum,
            'msgDupSched': msgDupSched,
            }
    if variation == 'REQ':
        templt = 'frm_RequestCountScheduleRec.html'
    else:
        templt = 'frm_CountScheduleRec.html'
    return render(req, templt, cntext)

@login_required
def fnRequestCountScheduleRecView(req, 
            recNum = 0, MatlNum = 0, reqDate = None,
            gotoCommand = None
            ):
    return _fnCountSchedRecViewCommon(req, 'REQ',
            recNum, MatlNum, reqDate,
            gotoCommand
            )

@login_required
def fnCountScheduleRecView(req, 
            recNum = 0, MatlNum = 0, reqDate = None,
            gotoCommand = None
            ):

    return _fnCountSchedRecViewCommon(req, None,
            recNum, MatlNum, reqDate,
            gotoCommand
            )

##########################################################################

def fnRequestedCountEditListView(req, ShowFilledRequests = True):
    requser = WICSuser.objects.get(user=req.user)

    FormMain = RequestCountScheduleRecordForm
    FormSubs = [S for S in []]

    modelMain = FormMain.Meta.model
    modelSubs = [S.Meta.model for S in FormSubs]

    prefixvals = {
        'main': 'counts',
    }
    initialvals = {
        'main': {'CountDate': calvindate().as_datetime(),'Requestor':req.user.get_short_name()},
    }
    fieldlist = {
        'main':  ('id', 'CountDate', 'Material', 'Requestor', 'RequestFilled', 'Counter', 'Priority', 'ReasonScheduled', 'Notes',)
    }
    excludelist = {
        'main': ()            # ('Requestor_userid',)
    }

    changes_saved = {
        'main': False,
        }
    chgd_dat = {
        'main':None, 
        }

    mainFm_class = modelformset_factory(modelMain,
                fields=fieldlist['main'],
                exclude=excludelist['main'],
                # form=FormMain,
                extra=0,can_delete=False)
    qs_RequestsToShow = modelMain.objects.filter(Requestor_userid__isnull=False).annotate(hascounts=Value(False))
    if not ShowFilledRequests:
        qs_RequestsToShow = qs_RequestsToShow.filter(RequestFilled=False)

    if req.method == 'POST':
        # process main form
        mainFm = mainFm_class(req.POST, prefix=prefixvals['main'], initial=initialvals['main'],
                    queryset=qs_RequestsToShow)

        if mainFm.is_valid():
            if mainFm.has_changed():
                s = mainFm.save()
                chgd_dat['main'] = mainFm.changed_objects
                changes_saved['main'] = s
    else:
        mainFm = mainFm_class(prefix=prefixvals['main'], initial=initialvals['main'],
                    queryset=qs_RequestsToShow)

    # show if the request has counts or not
    for rec in qs_RequestsToShow:
        rec.hascounts = ActualCounts.objects.filter(Material=rec.Material,CountDate=rec.CountDate).exists()

    # display the form
    cntext = {
            'frmMain': mainFm,
            'ShowFilled': ShowFilledRequests,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            }
    templt = 'frm_RequestCountScheduleEditList.html'
    return render(req, templt, cntext)


