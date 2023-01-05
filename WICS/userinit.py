from userprofiles.models import WICSuser
from django.shortcuts import redirect
from django.urls import reverse


def inituser(req):
    _authuser = WICSuser.objects.get(user=req.user)
    _userMenuGroup = _authuser.menuGroup
    _intMenuGroup = _userMenuGroup.pk
    return redirect(reverse('LoadMenu',kwargs={'menuGroup':_intMenuGroup, 'menuNum':0}))
