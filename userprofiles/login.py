import random
from django.conf import settings as django_settings
from django.contrib.auth import authenticate, login, views as auth_views
from django.shortcuts import HttpResponse
from typing import *
from userprofiles.models import WICSuser
from cMenu.models import cGreetings
from sysver import sysver
from django_support.settings import sysver_key


# start the WICS journey!
class WICSLoginView(auth_views.LoginView):
    template_name = "Uaffirm.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        cntext = super().get_context_data(**kwargs)

        grts = cGreetings.objects.all().values('Greeting')
        Greeting = random.choice(grts)['Greeting'] if grts.count() else ''

        cntext.update({
            'Greeting':Greeting,
            'sysver_key': sysver_key,
            'sysver':sysver[sysver_key],
            })

        return cntext

    def post(self, request, *args: str, **kwargs: Any) -> HttpResponse:
        if sysver_key == 'DEV':
            if 'dev_bypass' in request.POST and request.POST['dev_bypass'] != '':
                usr = authenticate(request,username='DEV',password='devpassword')
                if usr != None:
                    login(request,usr)
                    return self.form_valid(self.get_form())

        django_settings.TIME_ZONE = request.POST['localTZ'] # set the time zone from wherever the user's at 

        return super().post(request, *args, **kwargs)


class WICSDemoLoginView(auth_views.LoginView):
    template_name = "DemoLogin.html"
    svK = 'DEMO'
    uName = 'demo'
    uPW = '12345678demo'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        cntext = super().get_context_data(**kwargs)

        grts = cGreetings.objects.all().values('Greeting')
        Greeting = random.choice(grts)['Greeting'] if grts.count() else ''

        cntext.update({
            'Greeting':Greeting,
            'sysver_key': self.svK,
            'sysver':sysver[self.svK],
            'DEMOuName': self.uName,
            'DEMOuPW': self.uPW,
            })

        return cntext

    def post(self, request, *args: str, **kwargs: Any) -> HttpResponse:

        usr = authenticate(request,username=self.uName,password=self.uPW)
        if usr != None:
            login(request,usr)
            return self.form_valid(self.get_form())

        django_settings.TIME_ZONE = request.POST['localTZ'] # set the time zone from wherever the user's at 

        return super().post(request, *args, **kwargs)

