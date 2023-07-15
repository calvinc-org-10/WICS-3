WICS = Warehouse Inventory Control System

WICS3 is a Major rewrite of WICS.  Goals:
Users are not tied to an organization.  The org they're in will be default, but they can switch without logout/login
Optimize queries, construct/use some SQL views (sorry, Django)
Other stuff as outlined in the WICS3 project

WICS uses Semantic Versioning - documented at https://semver.org/

The main objects/tables in WICS are
 - Materials
 - Count Schedule
 - Actual Counts
 - SAP table

 