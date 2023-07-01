from __future__ import annotations      # to allow calvindate (or any other class) to refer to itself.  See https://stackoverflow.com/questions/40925470/python-how-to-refer-a-class-inside-itself
import datetime
from datetime import date, timedelta
from dateutil.parser import parse
from dateutil.rrule import *
from django.db.models import QuerySet
from collections import namedtuple
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, fills, colors

ExcelWorkbook_fileext = ".XLSX"


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


def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def namedtuplefetchall(cursor, ResultName = 'Result'):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple(ResultName, [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

def rgb_to_int(red,green,blue):
    rgb = red
    rgb = (rgb << 8) + green
    rgb = (rgb << 8) + blue
    return rgb
def int_to_rgb(rgb_int):
    red = (rgb_int >> 16) & 0xFF
    green = (rgb_int >> 8) & 0xFF
    blue = rgb_int & 0xFF
    return (red,green,blue)

def Excelfile_fromqs(qset, flName, freezecols = 0):
    """
    qset: a queryset or list of dictionaries
    flName: the name of the file to be built (WITHOUT extension!).  It's stored on the server.  If it's to be dl'd, the caller does that
    freezecols = 0: the number of columns to freeze to the left
    The top row contains the field names, is always frozen, is bold and is shaded grey

    Returns the name of the Workbook file (with extension).  Once I start building in errorchecking and exceptions, other returns may be possible
    """

    # far easier to process a list of dictionaries, so...
    if isinstance(qset,QuerySet):
        qlist = qset.values()
    else:
        qlist = qset

    # create empty workbook with an empty worksheet
    wb = Workbook()
    ws = wb.active

    # header row is names of columns
    fields = list(qlist[0])
    ws.append(fields)

    # append each row
    for row in qlist:
        ws.append(list(row.values()))

    # make header row bold, shade it grey, freeze it
    # ws.show_gridlines = True  #TODO: Find out how to do this
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(fill_type=fills.FILL_SOLID,
                        start_color=colors.Color("00808080"),
                        end_color=colors.Color("00808080")
                        )
    #TODO: convert row1 and cols:freezecols to an address (A=0, B=1, C=2 etc) for line below
    ws.freeze_panes ='A2'
    #TODO: if freezecols passed, freeze them, too

    # save the workbook
    wb.save(flName+ExcelWorkbook_fileext)

    # close the workbook
    wb.close()

    # and return success code to the caller
    return flName+ExcelWorkbook_fileext

