from userprofiles.models import WICSuser
from django.conf import settings as django_settings
from django.shortcuts import redirect
from django.urls import reverse
from cMenu.views import user_db


def inituser(req):
    _authuser = WICSuser.objects.get(user=req.user)
    _userMenuGroup = _authuser.menuGroup
    _intMenuGroup = _userMenuGroup.pk

    # django_settings.DATABASES['default'] = django_settings.DATABASES[user_db(req)]

    return redirect(reverse('LoadMenu',kwargs={'menuGroup':_intMenuGroup, 'menuNum':0}))
