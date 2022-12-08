import csv
from cMenu.models import *



def load_Commands():
    with open('/home/calvinc460/WICS-Test/cMenu/load_data/MenuCommands.csv', newline='') as csvfile:
        inReader = csv.reader(csvfile, delimiter=',', quotechar='"')
        csvFlds = next(inReader, None)
        nn   = 0

        for row in inReader:
            rowDict = dict(zip(csvFlds,row))
            new_Rec = menuCommands.objects.create(
                Command = rowDict["Command"],
                CommandText = rowDict["CommandText"]
                )
            nn = nn + 1

def load_MenuItems():
    # menuCommands.objects.create(Command = 0, CommandText = "Null Command")

    with open('/home/calvinc460/WICS-Test/cMenu/load_data/MenuItems.csv', newline='') as csvfile:
        inReader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        csvFlds = next(inReader, None)
        nn = 0

        for row in inReader:
            rowDict = dict(zip(csvFlds,row))
            if rowDict["Command"] == '': rowDict["Command"] = '0'
            new_Rec = menuItems.objects.create(
                MenuID = rowDict["MenuID"],
                OptionNumber = rowDict["OptionNumber"],
                OptionText = rowDict["OptionText"],
                Command = menuCommands.objects.get(Command=int(rowDict["Command"])),
                Argument = rowDict["Argument"],
                PWord = rowDict["PWord"],
                TopLine = bool(rowDict["TopLine"]),
                BottomLine = bool(rowDict["BottomLine"])
                )

# load_Commands()
# load_MenuItems()
exit()