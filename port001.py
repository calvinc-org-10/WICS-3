from django.db import models
import csv

from cMenu.models import menuItems

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
            continue

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
            continue

    print(str(targetmodel._meta)+' Loaded')
    print()


port_data_002()
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
