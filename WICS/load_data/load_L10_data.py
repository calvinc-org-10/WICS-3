import csv
from WICS.models import *


L6OrgKey = Organizations.objects.get(orgname__contains = 'L6')
L10OrgKey = Organizations.objects.get(orgname__contains = 'L10')
userOrgKey = L10OrgKey

def load_L10Data_00():
    # first, fix links MaterialList -> WhsePartTypes
    rs_materl = MaterialList.objects.filter(org=L10OrgKey)
    nn = 0

    for mtl in rs_materl:
        mtl.PartType = WhsePartTypes.objects.get(oldWICSID=mtl.oldWICSPartType)
        mtl.save()

    print('updated Part Types in Materials')
    print()


def load_L10Data_01():
    print('------------------------------------------------')
    print('--------------Loading CountSchedule-------------')
    print('------------------------------------------------')
    # insert CountSched records
    # file_ToImp = '//home//calvinc460//WICS-Test//WICS//load_data//CountSched.csv'
    file_ToImp = '//home//calvinc460//WICS-Test//WICS//load_data//ARCHV_Count Schedule+History.csv'

    with open(file_ToImp, newline='',errors='ignore') as csvfile:

        inReader = csv.reader(csvfile, delimiter=',', quotechar='"')
        csvFlds = next(inReader, None)
        nn = 0

        for row in inReader:
            rowDict = dict(zip(csvFlds,row))
            cDate = rowDict["CountDate"]
            cDateX = cDate[6:10] + '-' + cDate[0:2] + '-' + cDate[3:5]
            try:
                mtl_obj = MaterialList.objects.get(oldWICSID=rowDict["MaterialID"])
            except MaterialList.DoesNotExist:
                print ('***** no Material Record for ',rowDict["MaterialID"])
            else:
                new_Rec = CountSchedule.objects.create(
                    org= L10OrgKey,
                    oldWICSID= rowDict["ID"],
                    CountDate = cDateX,  # rowDict["CountDate"],
                    Material = mtl_obj,
                    Counter = rowDict["Counter"],
                    Priority = rowDict["Priority"],
                    ReasonScheduled = rowDict["Reason Scheduled"],
                    CMPrintFlag = False,
                    Notes = rowDict["Notes"]
                    )
                nn = nn + 1
                print('added', nn, ': ',new_Rec.CountDate, "," , new_Rec.Material.Material)
            continue

    print('CountSchedule Loaded')
    print()


def load_L10Data_02():
    print('------------------------------------------------')
    print('--------------Loading ActualCounts--------------')
    print('------------------------------------------------')
    # insert CountActual records
    # file_ToImp = '//home//calvinc460//WICS-Test//WICS//load_data//Counts.csv'
    file_ToImp = '//home//calvinc460//WICS-Test//WICS//load_data//ARCHV_Counts.csv'
    with open(file_ToImp, newline='',errors='ignore') as csvfile:

        inReader = csv.reader(csvfile, delimiter=',', quotechar='"')
        csvFlds = next(inReader, None)
        nn = 0

        for row in inReader:
            rowDict = dict(zip(csvFlds,row))
            cDate = rowDict["CountDate"]
            cDateX = cDate[6:10] + '-' + cDate[0:2] + '-' + cDate[3:5]
            try:
                mtl_obj = MaterialList.objects.get(oldWICSID=rowDict["MaterialID"])
            except MaterialList.DoesNotExist:
                print ('***** no Material Record for ',rowDict["MaterialID"])
            else:
                new_Rec = ActualCounts.objects.create(
                    org= L10OrgKey,
                    oldWICSID= rowDict["ID"],
                    CountDate = cDateX,  # rowDict["CountDate"],
                    Material = mtl_obj,
                    Counter = rowDict["Counter"],
                    CTD_QTY_Expr = rowDict["CTD QTY Expr"],
                    BLDG = rowDict["BIN/LOC"],
                    LOCATION = rowDict["PLT/POS"],
                    PKGID_Desc = rowDict["PKG ID/Desc"],
                    TAGQTY = rowDict["TAG QTY"],
                    FLAG_PossiblyNotRecieved = False,
                    FLAG_MovementDuringCount = False,
                    Notes = rowDict["NOTES"]
                    )
                nn = nn + 1
                print('added', nn, ': ',new_Rec.CountDate, "," , new_Rec.Material.Material)
            continue

    print('ActualCounts Loaded')
    print()


#load_L10Data_00()  # run successfully
#load_L10Data_01()  # run successfully
#load_L10Data_02()  # run successfully
print ('\n\nDONE!')
exit()