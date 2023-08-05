_base_ver_major=3
_base_ver_minor=1
_base_ver_patch=4
_ver_date='2023-08-07'
_base_ver = str(_base_ver_major) +'.'+ str(_base_ver_minor) +'.'+ str(_base_ver_patch)
sysver = {
    'DEV': 'DEV'+_base_ver, 
    'PROD':_base_ver,
    } 

# 3.1.4 - 2023-08-07 WICSignore field in Count Spreadsheet, use db VIEW_materials