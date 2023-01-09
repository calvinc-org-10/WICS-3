

# move this to (or find it in) a utility package
from types import NoneType


def WrapInQuotes(str, openquotechar = chr(34), closequotechar = chr(34)):
    return openquotechar + str + closequotechar

# this could be generally useful...
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

