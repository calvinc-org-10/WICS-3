from userprofiles.views import fnWICSuserForm
from django.shortcuts import render, redirect

def LoadAdmin(req):
    return redirect('/admin/')

#########################################################################
#########################################################################


ExternalWebPageURL_Map = {}
# FormNameToURL_Map['menu Argument'.lower()] = 'URL of external page'
ExternalWebPageURL_Map['calvin00'.lower()] = 'https://calvinc440.great-site.net/'
