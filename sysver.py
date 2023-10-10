_base_ver_major=3
_base_ver_minor=3
_base_ver_patch=1
_ver_date='2023-10-09'
_base_ver = str(_base_ver_major) +'.'+ str(_base_ver_minor) +'.'+ str(_base_ver_patch)
sysver = {
    'DEV': 'DEV'+_base_ver, 
    'PROD':_base_ver,
    } 

# 3.3.1 - 2023-10-09 Voice announcement of lengthy process completions
# 3.3.0 - 2023-10-07 Attach Photos (1-many) to Material
# 3.2.9 - 2023-10-02 Show id's on Requested Count Listing.  Fixed editing.
# 3.2.8 - 2023-09-30 RunSQL - make textarea autofocus; print barcodes on Count Worksheet Material summary; Matl Form: don't include LocOnly records in summary counts
# 3.2.7 - 2023-09-24 Make Count Worksheet rpt async
# 3.2.6 - 2023-09-16 Put hints to structure of major WICS tables on RunSQL
# 3.2.5 - 2023-09-13 Attempt to make MaterialList Update a self-transitioning process, with no need for intervention
# 3.2.4 - 2023-09-06 Button to output Material Listings to spreadsheet
# 3.2.3 - 2023-09-05 First draft of Remove User 
# 3.2.2 - 2023-09-02 Put Copy Count button on Matl Form and Actual Count List.  Added Del Count button to Actual Count List
# 3.2.1 - 2023-08-27 Bug fixes with MM52 - revert to semi-manual process for now
    # set null=True on most Model fields where it's OK
# 3.2.0 - 2023-08-18 Update Materials (MM60), Update SAP (MB52), and CountEntry Upload done async with status updates
# 3.1.4 - 2023-08-07 WICSignore field in Count Spreadsheet, use db VIEW_materials