# "global" var used by a WICS session
# later, this will be tied to a user, who will have to log in

from WICS.models import Organizations

WICSOrgKey = Organizations.objects.get(orgname__contains = 'L6')
