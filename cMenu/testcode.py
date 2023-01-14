import csv, os
from WICS.models import ActualCounts, CountSchedule,  MaterialList
from cMenu.utils import makebool, iif

def f00test00_act():
    ExportOutFile = 'ActCounts.csv'
    ExportModel = ActualCounts
    fieldnames = ['org_id',
            'CountDate',
            'CycCtID',
            'Material',
            'Counter',
            'LocationOnly',
            'CTD_QTY_Expr',
            'BLDG',
            'LOCATION',
            'PKGID_Desc',
            'TAGQTY',
            'FLAG_PossiblyNotRecieved',
            'FLAG_MovementDuringCount',
            'Notes']

    print('=======================================')
    print (ExportOutFile)
    print('=======================================')

    with open(ExportOutFile, 'r', newline='') as csvfile:
        CSVreader = csv.DictReader(csvfile)

        for inrec in CSVreader:
            # transform the booleans, so they don't cause problems
            # for next time - I might have gotten lucky - don't modify the for var!!
            inrec['LocationOnly'] = makebool(inrec['LocationOnly'])
            inrec['FLAG_MovementDuringCount'] = makebool(inrec['FLAG_MovementDuringCount'])
            inrec['FLAG_PossiblyNotRecieved'] = makebool(inrec['FLAG_PossiblyNotRecieved'])
            
            ExportModel.objects.create(
                org_id = inrec['org_id'],
                CountDate = inrec['CountDate'],
                CycCtID = inrec['CycCtID'],
                Material = MaterialList.objects.get(org_id=inrec['org_id'], Material=inrec['Material']),
                Counter = inrec['Counter'],
                LocationOnly = inrec['LocationOnly'],
                CTD_QTY_Expr = inrec['CTD_QTY_Expr'],
                BLDG = inrec['BLDG'],
                LOCATION = inrec['LOCATION'],
                PKGID_Desc = inrec['PKGID_Desc'],
                TAGQTY = inrec['TAGQTY'],
                FLAG_PossiblyNotRecieved = inrec['FLAG_PossiblyNotRecieved'],
                FLAG_MovementDuringCount = inrec['FLAG_MovementDuringCount'],
                Notes = inrec['Notes'] 
            )
            print(
                inrec['org_id'], '|',
                inrec['CountDate'], '|',
                inrec['CycCtID'], '|',
                inrec['Material'], '|',
                inrec['Counter'],
                inrec['BLDG']+'_'+inrec['LOCATION']
            )
    print('\n\n')
def f00test00_sch():
    ExportOutFile = 'CountSched.csv'
    ExportModel = CountSchedule
    fieldnames = ['org_id',
            'CountDate',
            'Material',
            'Counter',
            'Priority',
            'ReasonScheduled',
            'CMPrintFlag',
            'Notes']

    print('=======================================')
    print (ExportOutFile)
    print('=======================================')

    with open(ExportOutFile, 'r', newline='') as csvfile:
        CSVreader = csv.DictReader(csvfile)

        for inrec in CSVreader:
            # transform the booleans, so they don't cause problems
            CMPrintFlag_bool = makebool(inrec['CMPrintFlag'])


            isdup = ExportModel.objects.filter(
                org_id = inrec['org_id'],
                CountDate = inrec['CountDate'],
                Material = MaterialList.objects.get(org_id=inrec['org_id'], Material=inrec['Material'])
                ).exists()
            if not isdup:
                ExportModel.objects.create(
                    org_id = inrec['org_id'],
                    CountDate = inrec['CountDate'],
                    Material = MaterialList.objects.get(org_id=inrec['org_id'], Material=inrec['Material']),
                    Counter = inrec['Counter'],
                    Priority = inrec['Priority'],
                    ReasonScheduled = inrec['ReasonScheduled'],
                    CMPrintFlag = CMPrintFlag_bool,
                    Notes = inrec['Notes'] 
                    )

            print(
                inrec['org_id'], '|',
                inrec['CountDate'], '|',
                inrec['Material'], '|',
                inrec['Counter'], '|',
                iif(isdup,'*** DUP REC ***','')
                )

            continue

    print('\n\n')

