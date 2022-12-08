# later, this will be tied to a user, who will have to log in (see _djangouser, below)

from django.contrib.auth import authenticate, login
# from django.contrib.auth.models import User
from userprofiles.models import WICSuser
from django.shortcuts import HttpResponse, render, redirect
from django.urls import reverse


# start the WICS journey - show the menu!
def loginbegin(req):
    return render(req, 'Uaffirm.html')


def checkuser(req):
    username = req.POST['username']
    password = req.POST['password']
    _djangouser = authenticate(req, username=username, password=password)
    if _djangouser is None:
        return HttpResponse('<h1>You are not an authorized user.</h1>')
    else:
        _authuser = WICSuser.objects.get(user=_djangouser)
        # _userOrgKey = _authuser.org
        _userMenuGroup = _authuser.menuGroup
        _intMenuGroup = _userMenuGroup.pk
        # req.POST['WICSuser'] = _authuser
        login(req,_djangouser)
        return redirect(reverse('LoadMenu',kwargs={'menuGroup':_intMenuGroup, 'menuNum':0}))
        # return HttpResponseRedirect(reverse('LoadMenu',kwargs={'menuGroup':_intMenuGroup, 'menuNum':0}))
    #endif

