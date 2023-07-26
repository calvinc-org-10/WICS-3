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

    def load_initial_WICSuserForm():
        initd = []
        qset = WICSuser.objects.all()
        for u in qset:
            initd.append({
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
        return initd
    # enddef  load_initial_WICSuserForm():
        
    uFormSet_class = formset_factory(WICSUfrm,max_num=300,extra=0)
    
    templt = 'Uadmin.html'
    nChangedRecs = 0
    
    if req.method == 'POST':
        initdata = load_initial_WICSuserForm()
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
                        # guarantee the user is correctly set
                        WuRec.user = uRec
                    else:
                        WuRec = WICSuser(
                            menuGroup=f.cleaned_data['menuGroup'],
                            user=uRec
                            )
                    #endif
                    WuRec.save()
                #endif
            #endfor
            # reload the form so that changes may be seen
            initdata = load_initial_WICSuserForm()
            uFormSet = uFormSet_class(initial=initdata)
        else:
            # reveal the errors and try again
            pass
        #endif uFormSet.is_valid():
    else:
        initdata = load_initial_WICSuserForm()
        uFormSet = uFormSet_class(initial=initdata)
    #endif req.method = 'POST'

    cntext = {
        'ulist': uFormSet, 
        'nChangedRecs': nChangedRecs, 
        'PW':_defaultPW
        }
    return render(req, templt, cntext)

