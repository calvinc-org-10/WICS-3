import csv
from imghdr import what
from WICS.models import Organizations, MaterialList


L6OrgKey = Organizations.objects.get(orgname__contains = 'L6')

def load_L6Materials_00():
    # with open('C:\Work\OneDrive - Foxconn Industrial Internet in North America\Inventory\L6 WICS\SAP MatList Updt.csv', newline='') as csvfile:
    with open('//home//calvinc460//WICS-Test//WICS//load_data//SAP MatList Updt.csv', newline='',errors='ignore') as csvfile:

        inReader = csv.reader(csvfile, delimiter=',', quotechar='"')
        csvFlds = next(inReader, None)
        nn = 0

        for row in inReader:
            rowDict = dict(zip(csvFlds,row))
            new_MatRec = MaterialList.objects.create(
                Material=rowDict["Material"],
                oldWICSID=-1,
                org= L6OrgKey,
                Description=rowDict["Material description"],
                SAPMaterialType=rowDict["Material type"],
                SAPMaterialGroup=rowDict["Material Group"],
                Price = float(rowDict["Price"].replace(',','')),
                PriceUnit = float(rowDict["Price unit"].replace(',',''))
                )
            nn = nn + 1
            print('added', nn, ': ',rowDict["Material"])

load_L6Materials_00()
exit()
