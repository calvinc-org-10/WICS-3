from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from userprofiles.models import WICSuser

def change_password(req):
    _userorg = WICSuser.objects.get(user=req.user).org
    if req.method == 'POST':
        form = PasswordChangeForm(req.user, req.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(req, user)  # Important!
            messages.success(req, 'Your password was successfully updated!')
            return redirect('change_password_done')
        else:
            messages.error(req, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(req.user)

    cntext = {'form': form,
        'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
        }
    templt = 'Uchgpw.html'
    return render(req, templt, cntext)

def change_password_done(req):
    _userorg = WICSuser.objects.get(user=req.user).org
    cntext = {
        'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
        }
    templt = 'UchgpwX.html'
    return render(req, templt, cntext)

