from dateutil.parser import parse
from dateutil.rrule import *
import dateutil.utils


def WrapInQuotes(strg, openquotechar = chr(34), closequotechar = chr(34)):
    return openquotechar + strg + closequotechar


def makebool(strngN, numtype = bool):
    # res = bool(strngN)
    # the built-in bool function is good with one set of exceptions
    if isinstance(strngN,str):
        FalsieList = ['FALSE','NO','0','OFF','']
        if  (strngN.strip().upper() in FalsieList) or len(strngN)<1:
            strngN = False
    else:
        strngN = numtype(strngN)
    return strngN
def iif(cond, ifTrue, ifFalse=None):
    if makebool(cond):
        return ifTrue
    else:
        return ifFalse


def isDate(testdate):
    try:
        td = parse(testdate)
    except:
        td = False
    return td


def nextWorkdayAfter(afterdate=dateutil.utils.today(), nonWorkdays={SA,SU}, extraNonWorkdayList={}, include_afterdate=False):
    excRule = rrule(WEEKLY,dtstart=afterdate,byweekday=nonWorkdays)
    afterdaysRule = rrule(DAILY,dtstart=afterdate)

    exclSet = rruleset()
    exclSet.rrule(afterdaysRule)
    exclSet.exrule(excRule)
    # loop extraNonWorkdays into exclSet.exdate
    for xDate in extraNonWorkdayList:
        exclSet.exdate(xDate)

    return exclSet.after(afterdate,include_afterdate)
