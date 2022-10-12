import csv
from imghdr import what
from WICS.models import Organizations, MaterialList


L6OrgKey = Organizations.objects.get(orgname__contains = 'L6')

def load_L6Materials_00():
    with open('C:\Work\OneDrive - Foxconn Industrial Internet in North America\Inventory\L6 WICS\SAP MatList Updt.csv', newline='') as csvfile:
        inReader = csv.reader(csvfile, delimiter=',', quotechar='"')
        csvFlds = next(inReader, None)
        nn = 0

        for row in inReader:
            rowDict = dict(zip(csvFlds,row))
            new_MatRec = MaterialList.objects.create(
                Material=rowDict["Material"], 
                oldID=-1, 
                org= L6OrgKey,
                Description=rowDict["Material description"],
                SAPMaterialType=rowDict["Material type"],
                SAPMaterialGroup=rowDict["Material Group"]
                )
            nn = nn + 1
            print('added', nn, ': ',rowDict["Material"])
            #if nn>=3: break

def load_L6Materials_01_Load_Prices():
    with open('C:\Work\OneDrive - Foxconn Industrial Internet in North America\Inventory\L6 WICS\SAP MatList Updt.csv', newline='') as csvfile:
        inReader = csv.reader(csvfile, delimiter=',', quotechar='"')
        csvFlds = next(inReader, None)
        nn = 0

        for row in inReader:
            rowDict = dict(zip(csvFlds,row))
 
            mtlrec = MaterialList.objects.get(org=L6OrgKey, Material=rowDict["Material"])
            mtlrec.Price = float(rowDict["Price"].replace(',',''))
            mtlrec.PriceUnit = float(rowDict["Price unit"].replace(',',''))
            mtlrec.save()

            print('added Price for ',rowDict["Material"])

# testing proc - how do I catch a null in the db?
def whatdoesnulllooklike():
    mtlrec = MaterialList.objects.filter(Price__isnull=True)
    print(mtlrec.count())

whatdoesnulllooklike()
exit()
