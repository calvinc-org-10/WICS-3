_base_ver_major=3
_base_ver_minor=2
_base_ver_patch=4
_ver_date='2023-09-06'
_base_ver = str(_base_ver_major) +'.'+ str(_base_ver_minor) +'.'+ str(_base_ver_patch)
sysver = {
    'DEV': 'DEV'+_base_ver, 
    'PROD':_base_ver,
    } 

# 3.2.4 - 2023-09-06 Button to output Material Listings to spreadsheet
# 3.2.3 - 2023-09-05 First draft of Remove User 
# 3.2.2 - 2023-09-02 Put Copy Count button on Matl Form and Actual Count List.  Added Del Count button to Actual Count List
# 3.2.1 - 2023-08-27 Bug fixes with MM52 - revert to semi-manual process for now
    # set null=True on most Model fields where it's OK
# 3.2.0 - 2023-08-18 Update Materials (MM60), Update SAP (MB52), and CountEntry Upload done async with status updates
# 3.1.4 - 2023-08-07 WICSignore field in Count Spreadsheet, use db VIEW_materials