# later, this will be tied to a user, who will have to log in (see _djangouser, below)
import random
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
        Greeting = random.choice(grts)['Greeting']

        cntext.update({
            'Greeting':Greeting,
            'sysver_key': sysver_key,
            'sysver':sysver[sysver_key],
            })

        return cntext

    def post(self, request, *args: str, **kwargs: Any) -> HttpResponse:
        if sysver_key == 'DEV':
            if 'dev_bypass' in request.POST:
                usr = authenticate(request,username='DEV',password='devpassword')
                if usr != None:
                    login(request,usr)
                    return self.form_valid(self.get_form())

        return super().post(request, *args, **kwargs)

