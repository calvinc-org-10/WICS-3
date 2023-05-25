import django
from django import forms
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from userprofiles.models import WICSuser


class GodRightsPasswordChangeForm(forms.Form):
    """
    A form used to change the password of another user
    """

    required_css_class = "required"
    password1 = forms.CharField(
        label= "Password",
        widget=forms.TextInput(
            attrs={"autocomplete": "off", "autofocus": True}
        ),
        strip=False,
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)


    def save(self, commit=True):
        """Save the new password."""
        password = self.cleaned_data["password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user

    @property
    def changed_data(self):
        data = super().changed_data
        for name in self.fields:
            if name not in data:
                return []
        return ["password"]


@login_required
def change_password(req, usNm=None):
    if not usNm: 
        usr=req.user
    else:
        usr = User.objects.get_by_natural_key(usNm)
    thisisme = (usr==req.user)

    if not req.user.is_staff and not thisisme:
        # non-staff user trying to change a PW not his own.  Don't do it!
        return redirect('change_password_deny')
    else:
        if thisisme: fmClass = PasswordChangeForm 
        else: fmClass = GodRightsPasswordChangeForm

    if req.method == 'POST':
        form = fmClass(usr, req.POST)
        if form.is_valid():
            usr = form.save()
            if thisisme: update_session_auth_hash(req, usr)  # Important!
            messages.success(req, 'Your password was successfully updated!')
            return redirect('change_password_done',usr)
        else:
            messages.error(req, 'Please correct the error below.')
    else:
        form = fmClass(usr)

    cntext = {'form': form, 
        }
    templt = 'Uchgpw.html'
    return render(req, templt, cntext)

def change_password_done(req,usNm=None):
    if not usNm: 
        usr=req.user
    else:
        usr = User.objects.get_by_natural_key(usNm)
    cntext = { 'usr': usr,
        }
    templt = 'UchgpwX.html'
    return render(req, templt, cntext)

def change_password_deny(req):
    cntext = { 
        }
    templt = 'UchgpwDN.html'
    return render(req, templt, cntext)
    

