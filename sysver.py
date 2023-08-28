_base_ver_major=3
_base_ver_minor=2
_base_ver_patch=1
_ver_date='2023-08-27'
_base_ver = str(_base_ver_major) +'.'+ str(_base_ver_minor) +'.'+ str(_base_ver_patch)
sysver = {
    'DEV': 'DEV'+_base_ver, 
    'PROD':_base_ver,
    } 

# 3.2.1 - 2023-08-27 Bug fixes with MM52 - revert to semi-manual process for now
    # set null=True on most Model fields where it's OK
# 3.2.0 - 2023-08-18 Update Materials (MM60), Update SAP (MB52), and CountEntry Upload done async with status updates
# 3.1.4 - 2023-08-07 WICSignore field in Count Spreadsheet, use db VIEW_materials