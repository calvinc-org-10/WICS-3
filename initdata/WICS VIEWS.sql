-- define first - most other views derive from this
-- `calvinc460$default`.VIEW_materials source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_materials` AS
select
    `MATL`.`id` AS `id`,
    `MATL`.`Material` AS `Material`,
    `MATL`.`Description` AS `Description`,
    `MATL`.`SAPMaterialType` AS `SAPMaterialType`,
    `MATL`.`SAPMaterialGroup` AS `SAPMaterialGroup`,
    `MATL`.`Price` AS `Price`,
    `MATL`.`PriceUnit` AS `PriceUnit`,
    `MATL`.`Notes` AS `Notes`,
    `MATL`.`PartType_id` AS `PartType_id`,
    `MATL`.`org_id` AS `org_id`,
    `MATL`.`TypicalContainerQty` AS `TypicalContainerQty`,
    `MATL`.`TypicalPalletQty` AS `TypicalPalletQty`,
    `PTYPE`.`WhsePartType` AS `PartType`,
    `PTYPE`.`PartTypePriority` AS `PartTypePriority`,
    `ORG`.`orgname` AS `OrgName`
from
    ((`WICS_materiallist` `MATL`
join `WICS_organizations` `ORG` on
    ((`MATL`.`org_id` = `ORG`.`id`)))
left join `WICS_whseparttypes` `PTYPE` on
    ((`MATL`.`PartType_id` = `PTYPE`.`id`)));


-- `calvinc460$default`.VIEW_SAP source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_SAP` AS
select
    `SAP`.`id` AS `id`,
    `SAP`.`uploaded_at` AS `uploaded_at`,
    `MATL`.`Material` AS `Material`,
    `MATL`.`id` AS `Material_id`,
    `SAP`.`Plant` AS `Plant`,
    `SAP`.`StorageLocation` AS `StorageLocation`,
    `SAP`.`BaseUnitofMeasure` AS `BaseUnitofMeasure`,
    `SAP`.`Amount` AS `Amount`,
    `SAP`.`Currency` AS `Currency`,
    `SAP`.`ValueUnrestricted` AS `ValueUnrestricted`,
    `UOMTable`.`UOM` AS `UOM`,
    `UOMTable`.`UOMText` AS `UOMText`,
    `UOMTable`.`DimensionText` AS `DimensionText`,
    `UOMTable`.`Multiplier1` AS `mult`,
    `SAP`.`SpecialStock` AS `SpecialStock`,
    `SAP`.`Batch` AS `Batch`,
    `MATL`.`Description` AS `Description`,
    `MATL`.`SAPMaterialType` AS `SAPMaterialType`,
    `MATL`.`SAPMaterialGroup` AS `SAPMaterialGroup`,
    `MATL`.`Price` AS `Price`,
    `MATL`.`PriceUnit` AS `PriceUnit`,
    `MATL`.`Notes` AS `Notes`,
    `MATL`.`TypicalContainerQty` AS `TypicalContainerQty`,
    `MATL`.`TypicalPalletQty` AS `TypicalPalletQty`,
    `MATL`.`PartType_id` AS `PartType_id`,
    `MATL`.`PartType` AS `PartType`,
    `MATL`.`PartTypePriority` AS `PartTypePriority`,
    `MATL`.`org_id` AS `org_id`,
    `MATL`.`OrgName` AS `OrgName`
from
    ((`WICS_sap_sohrecs` `SAP`
left join `VIEW_materials` `MATL` on
    (((`SAP`.`Material` = `MATL`.`Material`)
        and (`SAP`.`org_id` = `MATL`.`org_id`))))
left join `WICS_unitsofmeasure` `UOMTable` on
    ((`UOMTable`.`UOM` = `SAP`.`BaseUnitofMeasure`)));

 
 -- `calvinc460$default`.VIEW_actualcounts source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_actualcounts` AS
select
    `AC`.`id` AS `id`,
    `AC`.`CountDate` AS `CountDate`,
    `AC`.`Material_id` AS `Material_id`,
    `MATL`.`Material` AS `Material`,
    `AC`.`CycCtID` AS `CycCtID`,
    `AC`.`Counter` AS `Counter`,
    `AC`.`CTD_QTY_Expr` AS `CTD_QTY_Expr`,
    `AC`.`BLDG` AS `BLDG`,
    `AC`.`LOCATION` AS `LOCATION`,
    `AC`.`FLAG_PossiblyNotRecieved` AS `FLAG_PossiblyNotRecieved`,
    `AC`.`FLAG_MovementDuringCount` AS `FLAG_MovementDuringCount`,
    `AC`.`Notes` AS `CountNotes`,
    `AC`.`LocationOnly` AS `LocationOnly`,
    `MATL`.`Description` AS `Description`,
    `MATL`.`SAPMaterialType` AS `SAPMaterialType`,
    `MATL`.`SAPMaterialGroup` AS `SAPMaterialGroup`,
    `MATL`.`Price` AS `Price`,
    `MATL`.`PriceUnit` AS `PriceUnit`,
    `MATL`.`Notes` AS `MaterialNotes`,
    `MATL`.`PartType_id` AS `PartType_id`,
    `MATL`.`TypicalContainerQty` AS `TypicalContainerQty`,
    `MATL`.`TypicalPalletQty` AS `TypicalPalletQty`,
    `MATL`.`PartType` AS `PartType`,
    `MATL`.`PartTypePriority` AS `PartTypePriority`,
    `AC`.`org_id` AS `org_id`,
    `MATL`.`OrgName` AS `OrgName`
from
    (`WICS_actualcounts` `AC`
join `VIEW_materials` `MATL` on
    ((`AC`.`Material_id` = `MATL`.`id`)));
    
   
-- `calvinc460$default`.VIEW_countschedule source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_countschedule` AS
select
    `SCHD`.`id` AS `id`,
    `SCHD`.`CountDate` AS `CountDate`,
    `SCHD`.`Material_id` AS `Material_id`,
    `MATL`.`Material` AS `Material`,
    `SCHD`.`Counter` AS `Counter`,
    `SCHD`.`Priority` AS `Priority`,
    `SCHD`.`ReasonScheduled` AS `ReasonScheduled`,
    `SCHD`.`CMPrintFlag` AS `CMPrintFlag`,
    `SCHD`.`Notes` AS `ScheduleNotes`,
    `MATL`.`Description` AS `Description`,
    `MATL`.`SAPMaterialType` AS `SAPMaterialType`,
    `MATL`.`SAPMaterialGroup` AS `SAPMaterialGroup`,
    `MATL`.`Price` AS `Price`,
    `MATL`.`PriceUnit` AS `PriceUnit`,
    `MATL`.`Notes` AS `MaterialNotes`,
    `MATL`.`PartType_id` AS `PartType_id`,
    `MATL`.`TypicalContainerQty` AS `TypicalContainerQty`,
    `MATL`.`TypicalPalletQty` AS `TypicalPalletQty`,
    `MATL`.`PartType` AS `PartType`,
    `MATL`.`PartTypePriority` AS `PartTypePriority`,
    `SCHD`.`org_id` AS `org_id`,
    `MATL`.`OrgName` AS `OrgName`
from
    (`WICS_countschedule` `SCHD`
join `VIEW_materials` `MATL` on
    ((`SCHD`.`Material_id` = `MATL`.`id`)));


-- `calvinc460$default`.VIEW_FoundAt source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_FoundAt` AS
select
    `AC`.`org_id` AS `org_id`,
    `AC`.`OrgName` AS `OrgName`,
    `AC`.`Material_id` AS `Material_id`,
    `AC`.`Material` AS `Material`,
    `AC`.`CountDate` AS `CountDate`,
    group_concat(distinct concat_ws('_', `AC`.`BLDG`, `AC`.`LOCATION`) order by `AC`.`BLDG` ASC, `AC`.`LOCATION` ASC separator ', ') AS `FoundAt`
from
    `VIEW_actualcounts` `AC`
group by
    `AC`.`org_id`,
    `AC`.`Material_id`,
    `AC`.`CountDate`
order by
    `AC`.`org_id`,
    `AC`.`Material`,
    `AC`.`CountDate` desc;


-- `calvinc460$default`.VIEW_LastFoundAt source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_LastFoundAt` AS
select
    `VIEW_FoundAt`.`org_id` AS `org_id`,
    `VIEW_FoundAt`.`OrgName` AS `OrgName`,
    `VIEW_FoundAt`.`Material_id` AS `Material_id`,
    `VIEW_FoundAt`.`Material` AS `Material`,
    `VIEW_FoundAt`.`CountDate` AS `CountDate`,
    `VIEW_FoundAt`.`FoundAt` AS `FoundAt`
from
    `VIEW_FoundAt`
group by
    `VIEW_FoundAt`.`org_id`,
    `VIEW_FoundAt`.`Material_id`
having
    (`VIEW_FoundAt`.`CountDate` = max(`VIEW_FoundAt`.`CountDate`));


-- `calvinc460$default`.VIEW_LastFoundAtList source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_LastFoundAtList` AS
select
    distinct `AC`.`org_id` AS `org_id`,
    `AC`.`OrgName` AS `OrgName`,
    `AC`.`Material_id` AS `Material_id`,
    `AC`.`Material` AS `Material`,
    `AC`.`CountDate` AS `CountDate`,
    `AC`.`BLDG` AS `BLDG`,
    `AC`.`LOCATION` AS `LOCATION`,
    concat_ws('_', `AC`.`BLDG`, `AC`.`LOCATION`) AS `FoundAt`
from
    `VIEW_actualcounts` `AC`
where
    (`AC`.`CountDate` = (
    select
        max(`A2`.`CountDate`)
    from
        `VIEW_actualcounts` `A2`
    where
        (`A2`.`Material_id` = `AC`.`Material_id`)))
order by
    `AC`.`org_id`,
    `AC`.`Material`,
    `AC`.`BLDG`,
    `AC`.`LOCATION`;

   
-- `calvinc460$default`.VIEW_MaterialLocationListWithSAP source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_MaterialLocationListWithSAP` AS
select
    `MATL`.`id` AS `id`,
    `MATL`.`org_id` AS `org_id`,
    `MATL`.`Material` AS `Material`,
    `MATL`.`Description` AS `Description`,
    `MATL`.`SAPMaterialType` AS `SAPMaterialType`,
    `MATL`.`SAPMaterialGroup` AS `SAPMaterialGroup`,
    `MATL`.`Price` AS `Price`,
    `MATL`.`PriceUnit` AS `PriceUnit`,
    `MATL`.`Notes` AS `Notes`,
    `MATL`.`PartType_id` AS `PartType_id`,
    `MATL`.`PartType` AS `PartType`,
    `MATL`.`PartTypePriority` AS `PartTypePriority`,
    `MATL`.`TypicalContainerQty` AS `TypicalContainerQty`,
    `MATL`.`TypicalPalletQty` AS `TypicalPalletQty`,
    `MATL`.`OrgName` AS `OrgName`,
    `LFA`.`CountDate` AS `CountDate`,
    `LFA`.`FoundAt` AS `FoundAt`,
    `SAP`.`id` AS `SAP_id`,
    `SAP`.`uploaded_at` AS `SAPDate`,
    `SAP`.`Plant` AS `Plant`,
    `SAP`.`StorageLocation` AS `StorageLocation`,
    `SAP`.`Amount` AS `Amount`,
    `SAP`.`BaseUnitofMeasure` AS `BaseUnitofMeasure`,
    `SAP`.`UOM` AS `UOM`,
    `SAP`.`UOMText` AS `UOMText`,
    `SAP`.`DimensionText` AS `DimensionText`,
    `SAP`.`mult` AS `mult`,
    `SAP`.`ValueUnrestricted` AS `ValueUnrestricted`,
    `SAP`.`Currency` AS `Currency`,
    `SAP`.`SpecialStock` AS `SpecialStock`,
    `SAP`.`Batch` AS `Batch`,
    (isnull(`SAP`.`id`)
    and (ifnull(`LFA`.`CountDate`, 0) < (curdate() - interval cast((select `PARM`.`ParmValue` from `cMenu_cparameters` `PARM` where (`PARM`.`ParmName` = 'LOCRPT-COUNTDAYS-IFNOSAP')) as unsigned) day))) AS `DoNotShow`
from
    ((`VIEW_materials` `MATL`
left join `VIEW_LastFoundAt` `LFA` on
    ((`MATL`.`id` = `LFA`.`Material_id`)))
left join `VIEW_SAP` `SAP` on
    ((`MATL`.`id` = `SAP`.`Material_id`)));
    
   
