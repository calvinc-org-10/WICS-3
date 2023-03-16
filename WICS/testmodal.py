from django.shortcuts import render
from userprofiles.models import WICSuser


def fnTestModal(req):
    _userorg = WICSuser.objects.get(user=req.user).org
    if not _userorg: raise Exception('User is corrupted!!')

    # display the form
    cntext = {
            'orgname':_userorg.orgname, 'uname':req.user.get_full_name()
            }
    templt = 'zzztestmodal.html'
    return render(req, templt, cntext)

