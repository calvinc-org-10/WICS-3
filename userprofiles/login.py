# later, this will be tied to a user, who will have to log in (see _djangouser, below)
import random
from django.contrib.auth import views as auth_views
from userprofiles.models import WICSuser
from django.shortcuts import HttpResponse, render, redirect
from django.urls import reverse
from cMenu.models import cGreetings, getcParm
from typing import *


# start the WICS journey!
class WICSLoginView(auth_views.LoginView):
    template_name = "Uaffirm.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        cntext = super().get_context_data(**kwargs)

        grts = cGreetings.objects.all().values('Greeting')
        # Greeting = 'Greeting will go here'        # this line needed, comment next line until cGreetings exists and is filled
        Greeting = random.choice(grts)['Greeting']

        # Get News for WICS users
        fildir = getcParm('MISC-FILELOC')
        fName = fildir+"WICSNews.html"
        News = ''
        with open(fName,"r") as infile: 
            News = infile.read()

        cntext.update({'Greeting':Greeting,'News':News})

        return cntext


