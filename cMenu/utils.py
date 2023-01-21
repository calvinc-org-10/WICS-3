from dateutil.parser import parse


def WrapInQuotes(str, openquotechar = chr(34), closequotechar = chr(34)):
    return openquotechar + str + closequotechar


def makebool(strngN, numtype = bool):
    res = bool(strngN)
    # the built-in bool function is good with one set of exceptions
    if isinstance(strngN,str):
        FalsieList = ['FALSE','NO','0','OFF','']
        if  (strngN.strip().upper() in FalsieList) or len(strngN)<1:
            strngN = False
    else:
        strngN = numtype(strngN)
    return strngN
def iif(cond, ifTrue, ifFalse=None):
    if (makebool(cond)):
        return ifTrue
    else:
        return ifFalse


def isDate(testdate):
    try:
        td = parse(testdate)
    except:
        td = False
    return td


