from django.db import models
import csv

from cMenu.models import menuCommands, menuItems
from WICS.models import WhsePartTypes, MaterialList

delim = '|'


def port_data_000():
    file_ToImp = 'portdata.txt'    
    with open(file_ToImp, newline='',errors='ignore') as infile:
        inReader = csv.DictReader(infile, delimiter=delim)
        for indx, fldn in enumerate(inReader.fieldnames):  # strip out all that stupid whitespace!!
            inReader.fieldnames[indx] = fldn.strip()
        nn = 0

        for rowDict in inReader:
            new_Rec = menuCommands.objects.create(
                Command = int( rowDict['Command'].strip() ),
                CommandText = rowDict['CommandText'].strip()
            )
            nn = nn + 1
            print('added', nn, ': ',new_Rec.Command, "," , new_Rec.CommandText)

    print('MenuCommands Loaded')
    print()


def port_data_001():
    file_ToImp = 'portdata.txt'
    targetmodel = menuItems
    with open(file_ToImp, newline='',errors='ignore') as infile:
        inReader = csv.DictReader(infile, delimiter=delim)
        for indx, fldn in enumerate(inReader.fieldnames):  # strip out all that stupid whitespace!!
            inReader.fieldnames[indx] = fldn.strip()
        nn = 0

        for rowDict in inReader:
            cid = rowDict['Command_id'].strip()
            if (cid.isnumeric()):
                cid = int(cid)
            else:
                cid = None
            new_Rec = targetmodel.objects.create(
                MenuID = int( rowDict['MenuID'].strip() ),
                OptionNumber = int( rowDict['OptionNumber'].strip() ),
                OptionText = rowDict['OptionText'].strip(),
                Argument = rowDict['Argument'].strip(),
                Command_id = cid,
                MenuGroup_id = int( rowDict['MenuGroup_id'].strip() )
            )

            nn = nn + 1
            print('added', nn, ': ',new_Rec.MenuID, "," , new_Rec.OptionNumber)

    print(str(targetmodel._meta)+' Loaded')
    print()


def port_data_002():
    file_ToImp = 'portdata.txt'
    targetmodel = WhsePartTypes

    file_ToExp = 'whse_id_map.txt'
    outfile = open(file_ToExp,'w',newline='')
    outflds = ['oldID','newID']
    outWriter = csv.DictWriter(outfile, outflds)
    outWriter.writeheader()

    redirectmap = {}    # oldID -> id of redirectmap
    with open(file_ToImp, newline='',errors='ignore') as infile:
        inReader = csv.DictReader(infile, delimiter=delim)
        for indx, fldn in enumerate(inReader.fieldnames):  # strip out all that stupid whitespace!!
            inReader.fieldnames[indx] = fldn.strip()
        nn = 0

        for rowDict in inReader:
            oldid = int(rowDict['id'].strip())
            new_map = int(rowDict['new_map'].strip())

            if oldid == new_map:
                new_Rec = targetmodel.objects.create(
                    WhsePartType = rowDict['WhsePartType'].strip(),
                    PartTypePriority = int(rowDict['PartTypePriority'].strip()),
                    InactivePartType = bool(int(rowDict['InactivePartType'].strip())),
                    org_id = int(rowDict['org_id'].strip())
                )
                redirectmap[oldid] = new_Rec.id

            outWriter.writerow({'oldID': oldid ,'newID': redirectmap[new_map] })
            nn = nn + 1
            print('added', nn, ': ',oldid, ' --> ' , redirectmap[new_map])

    print(str(targetmodel._meta)+' Loaded')
    outfile.close()
    print(file_ToExp+' created')
    print()

def port_data_test3():
    file_ToImp = 'portdata.txt'
    targetmodel = WhsePartTypes

    file_ToExp = 'TESTwhse_id_map.txt'
    outfile = open(file_ToExp,'w',newline='')
    outfile.write('old, new\n')

    redirectmap = {}    # oldID -> id of redirectmap
    with open(file_ToImp, newline='',errors='ignore') as infile:
        inReader = csv.DictReader(infile, delimiter=delim)
        for indx, fldn in enumerate(inReader.fieldnames):  # strip out all that stupid whitespace!!
            inReader.fieldnames[indx] = fldn.strip()
        nn = 0

        for rowDict in inReader:
            oldid = int(rowDict['id'].strip())
            new_map = int(rowDict['new_map'].strip())

            if oldid == new_map:
                nn = nn + 1
                redirectmap[oldid] = nn

            outfile.write(str(oldid) + ', ' + str(redirectmap[new_map]) + '\n')
            # nn = nn + 1
            print('added', nn, ': ',oldid, ' --> ' , redirectmap[new_map])

    print(str(targetmodel._meta)+' Loaded')
    outfile.close()
    print(file_ToExp+' created')
    print()

# this could be generally useful...
def makenum(strngN, numtype = int, defNonNum = 0):
    if (strngN.isnumeric()):
        strngN = numtype(strngN)
    else:
        strngN = defNonNum
    return strngN

def port_data_004():
    file_ToImp = 'portdata.txt'
    targetmodel = MaterialList

    # read WhsePartTypes translation map
    file_xMap = 'whse_id_map.txt'
    xMap = {}
    with open(file_xMap, newline='',errors='ignore') as infile:
        inReader = csv.DictReader(infile, delimiter=',')
        for rowDict in inReader:
            idx = makenum(rowDict['old'])
            xMap[idx] = makenum(rowDict['new'])

    file_ToExp = 'matl_map.txt'
    outfile = open(file_ToExp,'w',newline='')
    # outflds = ['oldID','newID']
    outfile.write('old, new\n')

    with open(file_ToImp, newline='',errors='ignore') as infile:
        inReader = csv.DictReader(infile, delimiter=delim)
        for indx, fldn in enumerate(inReader.fieldnames):  # strip out all that stupid whitespace!!
            inReader.fieldnames[indx] = fldn.strip()
        nn = 0

        for rowDict in inReader:
            oldid = makenum(rowDict['id'].strip(),int,None)
            ptid = makenum(rowDict['PartType_id'].strip(), int, None)
            if ptid:
                ptid = xMap[ptid]

            new_Rec = targetmodel.objects.create(
                org_id = makenum(rowDict['org_id'].strip(),int,None),
                Material = rowDict['Material'].strip(),
                Description = rowDict['Description'].strip(),
                PartType_id = ptid,
                SAPMaterialType = rowDict['SAPMaterialType'].strip(),
                SAPMaterialGroup = rowDict['SAPMaterialGroup'].strip(),
                Price = makenum(rowDict['Price'].strip(), numtype=float, defNonNum=None),
                PriceUnit = makenum(rowDict['PriceUnit'].strip(), numtype=int, defNonNum=None),
                TypicalContainerQty = makenum(rowDict['TypicalContainerQty'].strip()),
                TypicalPalletQty = makenum(rowDict['TypicalPalletQty'].strip()),
                Notes = rowDict['Notes'].strip()
            )

            outfile.write(str(oldid) + ', ' + str(new_Rec.id) + '\n')
            nn = nn + 1
            print('added', nn, ': ', new_Rec.Material,', ', oldid, ' --> ' , new_Rec.id)

    print(str(targetmodel._meta)+' Loaded')
    outfile.close()
    print(file_ToExp+' created')
    print()

    return


def port_data_005():
    file_ToImp = 'portdata1.txt'
    targetmodel = MaterialList

    with open(file_ToImp, newline='',errors='ignore') as infile:
        inReader = csv.DictReader(infile, delimiter=delim)
        for indx, fldn in enumerate(inReader.fieldnames):  # strip out all that stupid whitespace!!
            inReader.fieldnames[indx] = fldn.strip()
        nn = 0

        for rowDict in inReader:
            oldid = makenum(rowDict['id'].strip(),int,None)
            ptid = makenum(rowDict['PartType_id'].strip(), int, None)

            new_Rec = targetmodel.objects.create(
                org_id = makenum(rowDict['org_id'].strip(),int,None),
                Material = rowDict['Material'].strip(),
                Description = rowDict['Description'].strip(),
                PartType_id = ptid,
                SAPMaterialType = rowDict['SAPMaterialType'].strip(),
                SAPMaterialGroup = rowDict['SAPMaterialGroup'].strip(),
                Price = makenum(rowDict['Price'].strip(), numtype=float, defNonNum=None),
                PriceUnit = makenum(rowDict['PriceUnit'].strip(), numtype=int, defNonNum=None),
                TypicalContainerQty = makenum(rowDict['TypicalContainerQty'].strip()),
                TypicalPalletQty = makenum(rowDict['TypicalPalletQty'].strip()),
                Notes = rowDict['Notes'].strip()
            )

            nn = nn + 1
            print('added', nn, ': ', new_Rec.Material,', ', oldid, ' --> ' , new_Rec.id)

    print(str(targetmodel._meta)+' Loaded')
    print()

    return

###############################################################
port_data_005()
print("done!")
exit()


##### save for later
#            cDate = rowDict["CountDate"]
#            cDateX = cDate[6:10] + '-' + cDate[0:2] + '-' + cDate[3:5]
#            try:
#                mtl_obj = MaterialList.objects.get(oldWICSID=rowDict["MaterialID"])
#            except MaterialList.DoesNotExist:
#                print ('***** no Material Record for ',rowDict["MaterialID"])
#            else:
#                new_Rec = CountSchedule.objects.create(
#                    org= L10OrgKey,
#                    oldWICSID= rowDict["ID"],
#                    CountDate = cDateX,  # rowDict["CountDate"],
#                    Material = mtl_obj,
#                    Counter = rowDict["Counter"],
#                    Priority = rowDict["Priority"],
#                    ReasonScheduled = rowDict["Reason Scheduled"],
#                    CMPrintFlag = False,
#                    Notes = rowDict["Notes"]
#                    )
