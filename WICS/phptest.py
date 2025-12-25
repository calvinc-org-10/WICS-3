from django.http import HttpResponse
from django.shortcuts import render
from WICS.models import MaterialList

def showtestAjax(req):
    cntext = {
            }
    templt = 'phptest.html'

    return render(req, templt, cntext)

def testAjax(req):
    # request should be ajax and method should be GET.
    if req.method == "GET":
        # get the form data
        _org_id = req.GET['org_id']
        _Material = req.GET['Material']
        try:
            id = MaterialList.objects.get(org_id=_org_id, Material=_Material).pk
        except:
            id = None

        #TODO: what can I return aside from a Json?
        return HttpResponse(id)
        # return id
