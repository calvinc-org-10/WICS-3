_base_ver_major=3
_base_ver_minor=2
_base_ver_patch=0
_ver_date='2023-08-18'
_base_ver = str(_base_ver_major) +'.'+ str(_base_ver_minor) +'.'+ str(_base_ver_patch)
sysver = {
    'DEV': 'DEV'+_base_ver, 
    'PROD':_base_ver,
    } 

# 3.2.0 - 2023-08-18 Update Materials (MM60), Update SAP (MB52), and CountEntry Upload done async with status updates
# 3.1.4 - 2023-08-07 WICSignore field in Count Spreadsheet, use db VIEW_materials