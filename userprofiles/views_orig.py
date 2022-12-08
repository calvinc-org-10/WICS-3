from django.shortcuts import render
# from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory

from userprofiles.models import WICSuser, WICSuser_with_User
from django.contrib.auth.models import User

# Create your views here.


@login_required
def fnWICSuserForm(req):
    # uOrg = WICSuser.objects.get(user=req.user).org
    uOrg = req.user.WICSuser.org
    qset0 = WICSuser.objects.filter(org=uOrg)
    qset1 = User.objects.filter(pk__in=qset0)
    uFormSet_full = inlineformset_factory(User,WICSuser,fields='__all__',max_num=100,extra=0)
    uFormSet = uFormSet_full(instance=qset1)

    # create formset from uQS
    cntext = {'ulist': uFormSet, 'orgname':uOrg.orgname, 'uname':req.user.get_full_name()}
    return render(req, 'Uadmin.html', cntext)

