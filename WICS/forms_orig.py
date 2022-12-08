import time
from django.contrib.auth.decorators import login_required
from django import forms
from django.db import models
from django.forms import inlineformset_factory, formset_factory
from django.shortcuts import render
from django.db.models import Value
from WICS.models import MaterialList, ActualCounts, CountSchedule, SAPFiles
from WICS.SAPLists import fnSAPList
from userprofiles.models import WICSuser
from django.http import HttpResponseRedirect


ExcelWorkbook_fileext = ".XLSX"


class MaterialFormGoTo(forms.Form):
    gotoItem = forms.ModelChoiceField(queryset=MaterialList.objects.none(), empty_label=None, required=False)


class MaterialForm(forms.ModelForm):
    showPK = forms.IntegerField(label='ID', disabled=True, required=False)
    class Meta:
        model = MaterialList
        fields = ['id', 'org', 'Material', 'Description','PartType',
                'SAPMaterialType', 'SAPMaterialGroup', 'Price',
                'TypicalContainerQty', 'TypicalPalletQty', 'PriceUnit', 'Notes']
        # fields = '__all__'

class MaterialCountSummary(forms.Form):
    Material = forms.CharField(max_length=100, disabled=True)
    CountDate = forms.DateField(required=False, disabled=True)
    CountQTY_Eval = forms.IntegerField(required=False, disabled=True)


@login_required
def fnMaterialForm(req, formname, recNum = -1):
    _userorg = WICSuser.objects.get(user=req.user).org

    # get current record
    if recNum <= 0:
        currRec = MaterialList.objects.filter(org=_userorg).first()
    else:
        currRec = MaterialList.objects.filter(org=_userorg).get(pk=recNum)   # later, handle record not found
    # endif
    SAP_SOH = fnSAPList(req, matl=currRec)

    gotoForm = MaterialFormGoTo({'gotoItem':currRec})
    gotoForm.fields['gotoItem'].queryset=MaterialList.objects.filter(org=_userorg)

    changes_saved = {
        'main': False,
        'counts': False,
        'schedule': False
        }
    chgd_dat = {'main':None, 'counts': None, 'schedule': None}

    if req.method == 'POST':
        # changed data is being submitted.  process and save it
        # process mtlFm AND subforms.

        # process main form
        mtlFm = MaterialForm(req.POST, instance=currRec,  initial={'gotoItem': currRec.pk, 'showPK': currRec.pk, 'org':_userorg},  prefix='material')
        if mtlFm.is_valid():
            if mtlFm.has_changed():
                mtlFm.save()
                chgd_dat['main'] = mtlFm.changed_data
                changes_saved['main'] = True
                #raise Exception('main saved')

        # count detail subform
        countSubFm_class = inlineformset_factory(MaterialList,ActualCounts,
                    fields=('id', 'CountDate', 'CycCtID', 'Counter', 'CTD_QTY_Expr', 'BLDG', 'LOCATION', 'PKGID_Desc', 'TAGQTY', 'FLAG_PossiblyNotRecieved', 'FLAG_MovementDuringCount', 'Notes',),
                    extra=0,can_delete=False)
        countSet = countSubFm_class(req.POST, instance=currRec, prefix='countset', initial={'org': _userorg})
        if countSet.is_valid():
            if countSet.has_changed():
                countSet.save()
                chgd_dat['counts'] = countSet.changed_objects
                changes_saved['counts'] = True
                #raise Exception('counts saved')

        # count schedule subform
        SchedSubFm_class = inlineformset_factory(MaterialList,CountSchedule,
                    fields=('id', 'CountDate','Counter', 'Priority', 'ReasonScheduled', 'CMPrintFlag', 'Notes',),
                    extra=0,can_delete=False)
        schedSet = SchedSubFm_class(req.POST, instance=currRec, prefix='schedset', initial={'org': _userorg})
        if schedSet.is_valid():
            if schedSet.has_changed():
                schedSet.save()
                chgd_dat['schedule'] = schedSet.changed_objects
                changes_saved['schedule'] = True
                #raise Exception('sched saved')

        # count summary form is r/o.  It will not be changed

    else: # request.method == 'GET' or something else
        mtlFm = MaterialForm(instance=currRec, initial={'gotoItem': currRec.pk, 'showPK': currRec.pk, 'org':_userorg}, prefix='material')

        CountSubFm_class = inlineformset_factory(MaterialList,ActualCounts,
                    fields=('id', 'CountDate', 'CycCtID', 'Counter', 'CTD_QTY_Expr', 'BLDG', 'LOCATION', 'PKGID_Desc', 'TAGQTY', 'FLAG_PossiblyNotRecieved', 'FLAG_MovementDuringCount', 'Notes',),
                    extra=0,can_delete=False)
        countSet = CountSubFm_class(instance=currRec, prefix='countset', initial={'org':_userorg})

        SchedSubFm_class = inlineformset_factory(MaterialList,CountSchedule,
                    fields=('id','CountDate','Counter', 'Priority', 'ReasonScheduled', 'CMPrintFlag', 'Notes',),
                    extra=0,can_delete=False)
        schedSet = SchedSubFm_class(instance=currRec, prefix='schedset', initial={'org':_userorg})

    # endif

    # count summary subform
    raw_countdata = ActualCounts.objects.filter(Material=currRec).order_by('Material','CountDate').annotate(QtyEval=Value(0, output_field=models.IntegerField()))
    LastMaterial = None ; LastCountDate = None
    initdata = []
    for r in raw_countdata:
        try:
            r.QtyEval = eval(r.CTD_QTY_Expr)    # later, use ast.literal_eval
        # except (ValueError, SyntaxError):
        except:
            r.QtyEval = 0
        if (r.Material != LastMaterial or r.CountDate != LastCountDate):
            LastMaterial = r.Material ; LastCountDate = r.CountDate
            initdata.append({
                'Material': r.Material,
                'CountDate': r.CountDate,
                'CountQTY_Eval': 0,
            })
        n = initdata[-1]['CountQTY_Eval'] + r.QtyEval
        initdata[-1]['CountQTY_Eval'] = n
    subFm_class = formset_factory(MaterialCountSummary,extra=0)
    summarySet = subFm_class(initial=initdata, prefix='summaryset')

    #countSet['org'].is_hidden = True
    #schedSet['org'].is_hidden = True

    # display the form
    cntext = {'frmMain': mtlFm,
            'gotoForm': gotoForm,
            'countset': countSet,
            'scheduleset': schedSet,
            'countsummset': summarySet,
            'SAPSet': SAP_SOH,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            'recNum': recNum,
            'formID':formname, 'orgname':currRec.org.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'frm_Material.html'
    return render(req, templt, cntext)

#####################################################################################################
#####################################################################################################
#####################################################################################################

class UploadSAPForm(forms.ModelForm):
    class Meta:
        model = SAPFiles
        fields = ('org', 'uploaded_at', 'SAPFile', 'Notes', )

@login_required
def fnUploadSAP(req, formname):
    _userorg = WICSuser.objects.get(user=req.user).org
    timetogo = False

    if req.method == 'POST':
        form = UploadSAPForm(req.POST, req.FILES, initial={'org':_userorg})
        if form.is_valid():
            instance = SAPFiles(SAPFile=req.FILES['SAPFile'])
            instance.org = _userorg
            instance.uploaded_at = req.POST['uploaded_at']
            instance.SAPFile.upload_to="SAP/SAP" + str(time.ctime(time.time())).replace(":","-").strip() + ExcelWorkbook_fileext
            instance.save()
            timetogo = True
            return HttpResponseRedirect('/success/url/')    #fixmefixmefixme - set up templt to handle timetogo
    else:
        form = UploadSAPForm(initial={'org':_userorg})
    #endif

    cntext = {'form': form, 'timetogo': timetogo,
            'formID':formname, 'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'frm_upload_SAP.html'
    return render(req, templt, cntext)

#####################################################################################################
#####################################################################################################
#####################################################################################################

