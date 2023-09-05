from django.shortcuts import render, HttpResponse #, redirect
from cMenu import utils


# Menu Command Constants
from enum import Enum
class MENUCOMMAND(Enum):
    LoadMenu = 1
    FormBrowse = 11
    OpenTable = 15
    RunCode = 21
    RunSQLStatement = 31
    ConstructSQLStatement = 32
    ChangePW = 51
    EditMenu = 91
    EditParameters = 92
    EditGreetings = 93
    ExitApplication = 200



# functions called directly by the menu by RunCode
# Calvin is lazy - these should take no arguments except req - the HttpRequest, but should return a redirect (to preserve HttpRequest)

# def f00test00_orig(req):
#     r = render(req,"00test00.html")

#     # r = HttpResponse(escape(req))
#     # r.write('the test works')
#     # r.write('I hope the test works')
#     return r

# def f00test00(req):
#     # r = render(req,"00test00.html")
#     r = HttpResponse()
#     r.write('no current test fn!')
#     return r

