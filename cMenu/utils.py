from __future__ import annotations      # to allow calvindate (or any other class) to refer to itself.  See https://stackoverflow.com/questions/40925470/python-how-to-refer-a-class-inside-itself
import datetime
from datetime import date, timedelta
from dateutil.parser import parse
from dateutil.rrule import *


class calvindate(date):
    def __new__(cls, *args):
        D = datetime.date.today()        # set default to datetime.date.today()
        if len(args) == 3:  # year, month, day was passed in
            return super().__new__(cls, int(args[0]), int(args[1]), int(args[2]))
        elif len(args) == 2:    # month, day passed in , year should be current year
            yrr = datetime.date.today().year
            return super().__new__(cls, int(yrr), int(args[0]), int(args[1]))
        elif len(args) == 1:    # either a date string or date object passed in
            if isinstance(args[0],(datetime.date, datetime.datetime)):
                DStr = str(args[0])
            else:
                DStr = args[0]
            try:
                D = parse(DStr)
                D = D.date()
            except:
                pass
        else:
            # invalid number of args.  Do nothing; let the default stand
            pass
        return super().__new__(cls, D.year, D.month, D.day)
    # def __init__(self) -> None:
    #     super().__init__()
# testarg = datetime.datetime.now()
# while testarg != 'stop':
#     R = calvindate(testarg)
#     print(type(R),R)
#     testarg = input('Next testarg:')
    def as_datetime(self):
        return datetime.datetime(self.year,self.month,self.day)

    def today(self):
        return self.__class__()
    def daysfrom(self,delta:int) -> calvindate:
        R_dt = self.as_datetime() + timedelta(days=delta)
        return calvindate(R_dt)
    def tomorrow(self):
        return self.daysfrom(1)
    def yesterday(self):
        return self.daysfrom(-1)
    
    def nextWorkdayAfter(self, nonWorkdays={SA,SU}, extraNonWorkdayList={}, include_afterdate=False):
        afterdate = self.as_datetime()
        
        excRule = rrule(WEEKLY,dtstart=afterdate,byweekday=nonWorkdays)
        afterdaysRule = rrule(DAILY,dtstart=afterdate)

        exclSet = rruleset()
        exclSet.rrule(afterdaysRule)
        exclSet.exrule(excRule)
        # loop extraNonWorkdays into exclSet.exdate
        for xDate in extraNonWorkdayList:
            exclSet.exdate(xDate)

        return self.__class__( exclSet.after(afterdate,include_afterdate) )
    
    # operators
    def __comparison_workhorse__(self, RHE, compOpr):
        LHExpr = calvindate(self).as_datetime()
        RHExpr = calvindate(RHE).as_datetime()
        if compOpr == 'lt':
            return LHExpr < RHExpr
        if compOpr == 'le':
            return LHExpr <= RHExpr
        if compOpr == 'eq':
            return LHExpr == RHExpr
        if compOpr == 'ne':
            return LHExpr != RHExpr
        if compOpr == 'gt':
            return LHExpr > RHExpr
        if compOpr == 'ge':
            return LHExpr >= RHExpr
        return False
    def __lt__(self, other):
        return self.__comparison_workhorse__(other,'lt')
    def __le__(self, other):
        return self.__comparison_workhorse__(other,'le')
    def __eq__(self, other):
        return self.__comparison_workhorse__(other,'eq')
    def __ne__(self, other):
        return self.__comparison_workhorse__(other,'ne')
    def __gt__(self, other):
        return self.__comparison_workhorse__(other,'gt')
    def __ge__(self, other):
        return self.__comparison_workhorse__(other,'ge')
    def __add__(self, other):
        if isinstance(other, int):
            return self.daysfrom(other)
        else:
            return NotImplemented
    def __sub__(self, other):
        if isinstance(other, int):
            return self.daysfrom(-other)
        else:
            return NotImplemented


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


