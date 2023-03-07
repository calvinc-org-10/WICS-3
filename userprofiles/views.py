### later - consider custom User Manager: WICSUser_objects

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
from django.forms import formset_factory

from userprofiles.models import WICSuser
from userprofiles.globals import _defaultPW
from cMenu.models import menuGroups
from django.contrib.auth.models import User

# Create your views here.

#class User_plus_WICS:

class WICSUfrm(forms.Form):
    uid = forms.IntegerField(disabled = True, required=False)   # later, make hideden : u.user.pk
    WICSuid = forms.IntegerField(disabled = True, required=False)   # later, make hideden : u.pk
    showuid = forms.CharField(disabled = True, required=False, initial="* NEW *")
    menuGroup = forms.ModelChoiceField(queryset=menuGroups.objects.all(), empty_label=None)   #: u.menuGroup
    uname = forms.CharField()   # : u.user.username
    fname = forms.CharField()   # : u.user.first_name
    lname = forms.CharField()   # : u.user.last_name
    email = forms.EmailField(required=False)   # : u.user.email
    superuser = forms.BooleanField(required=False)   # : u.user.is_superuser
    admin = forms.BooleanField(required=False)   # : u.user.is_staff
    active = forms.BooleanField(required=False)   # : u.user.is_active
    last_login = forms.DateTimeField(disabled = True, required=False)   # ,u.user.last_login


@permission_required('SUPERUSER', raise_exception=True)
def fnWICSuserForm(req):
    _userorg = req.user.WICSuser.org
    uFormSet_class = formset_factory(WICSUfrm,max_num=100,extra=0)      # , initial={'menuGroup':menuGroup for org}
    templt = 'Uadmin.html'
    nChangedRecs = 0
    initdata = []
    qset = WICSuser.objects.filter(org=_userorg)
    for u in qset:
        initdata.append({
        'uid': u.user.pk,
        'WICSuid': u.pk,
        'showuid': str(u.user.pk) + "/" + str(u.pk),
        'menuGroup': u.menuGroup,
        'uname': u.user.username,
        'fname': u.user.first_name,
        'lname': u.user.last_name,
        'email': u.user.email,
        'superuser': u.user.is_superuser,
        'admin': u.user.is_staff,
        'active': u.user.is_active,
        'last_login': u.user.last_login,
        })
    if req.method == 'POST':
        uFormSet = uFormSet_class(req.POST, initial=initdata)
        if uFormSet.is_valid():
            for f in uFormSet:
                if f.has_changed():
                    nChangedRecs += 1
                    if f.cleaned_data['uid'] is not None:
                        # raise Exception("uid = " + str(f.cleaned_data['uid']) + " and f.fields = " + str(f.fields['uid']))
                        uRec = User.objects.get(pk=f.cleaned_data['uid'])
                        uFldMap =  {
                            "uname": "username",
                            "fname": "first_name",
                            "lname": "last_name",
                            "email": "email",
                            "superuser": "is_superuser",
                            "admin": "is_staff",
                            "active": "is_active"
                            }
                        for fld in f.changed_data:
                            if fld == "uid": pass # raise error!!!  N E V E R change the uid or WICSuid!
                            if fld in uFldMap: setattr(uRec, uFldMap[fld], f.cleaned_data[fld])
                        #endfor
                    else:   # we need a new User record
                        # raise Exception("OK, I'm trying to create a new urec")
                        uRec = User.objects.create_user(
                            username=f.cleaned_data['uname'],
                            email=f.cleaned_data['email'],
                            first_name=f.cleaned_data['fname'],
                            last_name=f.cleaned_data['lname'],
                            is_superuser=f.cleaned_data['superuser'],
                            is_staff=f.cleaned_data['admin'],
                            is_active=f.cleaned_data['active']
                            )
                    #endif
                    uRec.set_password(_defaultPW)
                    uRec.save()
                    if f.cleaned_data['WICSuid'] is not None:
                        WuRec = WICSuser.objects.get(pk=f.cleaned_data['WICSuid'])
                        uFldMap =  {
                            "menuGroup": "menuGroup"
                            }
                        for fld in f.changed_data:
                            if fld == "WICSuid": pass # raise error!!!  N E V E R change the uid or WICSuid!
                            if fld in uFldMap: setattr(WuRec, uFldMap[fld], f.cleaned_data[fld])
                        #endfor
                        # guarantee the org and user are correctly set
                        WuRec.org = _userorg
                        WuRec.user = uRec
                    else:
                        WuRec = WICSuser(
                            org=_userorg,
                            menuGroup=f.cleaned_data['menuGroup'],
                            user=uRec
                            )
                    #endif
                    WuRec.save()
                #endif
            #endfor
            # close the window
            templt = 'Uadmin.html'
            pass
        else:
            # reveal the errors and try again
            pass
        #endif
        pass
    else:
        uFormSet = uFormSet_class(initial=initdata)
    #endif

    cntext = {
        'ulist': uFormSet, 
        'orgname':_userorg.orgname, 
        'uname':req.user.get_full_name(), 
        'nChangedRecs': nChangedRecs, 
        'PW':_defaultPW
        }
    return render(req, templt, cntext)

