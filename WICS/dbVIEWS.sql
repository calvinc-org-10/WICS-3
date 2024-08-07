-- define first - most other views derive from this
-- `demo01`.VIEW_materials source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_materials` AS
select
    `MATL`.`id` AS `id`,
    `MATL`.`Material` AS `Material`,
    `MATL`.`Description` AS `Description`,
    `MATL`.`SAPMaterialType` AS `SAPMaterialType`,
    `MATL`.`SAPMaterialGroup` AS `SAPMaterialGroup`,
    `MATL`.`SAPABC` AS `SAPABC`,
    `MATL`.`SAPMPN` AS `SAPMPN`,
    `MATL`.`SAPManuf` AS `SAPManuf`,
    `MATL`.`Price` AS `Price`,
    `MATL`.`PriceUnit` AS `PriceUnit`,
    `MATL`.`Notes` AS `Notes`,
    `MATL`.`PartType_id` AS `PartType_id`,
    `MATL`.`org_id` AS `org_id`,
    `MATL`.`TypicalContainerQty` AS `TypicalContainerQty`,
    `MATL`.`TypicalPalletQty` AS `TypicalPalletQty`,
    `MATL`.`Currency` AS `Currency`,
    `MATL`.`Plant` AS `Plant`,
    `PTYPE`.`WhsePartType` AS `PartType`,
    `PTYPE`.`PartTypePriority` AS `PartTypePriority`,
    `ORG`.`orgname` AS `OrgName`,
    `ACTCOUNT`.`CountDate` AS `LastCountDate`,
    `ACTCOUNT`.`LastFoundAt` AS `LastFoundAt`,
    if(((
    select
        count(0)
    from
        `WICS_materiallist` `numdups`
    where
        ((`numdups`.`Material` = `MATL`.`Material`)
            and (`numdups`.`org_id` <> `MATL`.`org_id`))) > 0),
    concat(`MATL`.`Material`, ' (', `ORG`.`orgname`, ')'),
    `MATL`.`Material`) AS `Material_org`,
    `SCHD`.`NextScheduledCount` AS `NextScheduledCount`,
    exists(
    select
        1
    from
        `WICS_countschedule` `U1`
    where
        ((`U1`.`Material_id` = `MATL`.`id`)
            and (`U1`.`CountDate` = curdate()))) AS `ScheduledForToday`
from
    ((((`WICS_materiallist` `MATL`
join `WICS_organizations` `ORG` on
    ((`MATL`.`org_id` = `ORG`.`id`)))
left join `WICS_whseparttypes` `PTYPE` on
    ((`MATL`.`PartType_id` = `PTYPE`.`id`)))
left join (
    select
        min(`WICS_countschedule`.`CountDate`) AS `NextScheduledCount`,
        `WICS_countschedule`.`Material_id` AS `Material_id`
    from
        `WICS_countschedule`
    where
        (`WICS_countschedule`.`CountDate` > curdate())
    group by
        `WICS_countschedule`.`Material_id`) `SCHD` on
    (((`SCHD`.`Material_id` = `MATL`.`id`)
        or isnull(`SCHD`.`Material_id`))))
left join (
    select
        `AC`.`Material_id` AS `Material_id`,
        `AC`.`CountDate` AS `CountDate`,
        group_concat(distinct `AC`.`LOCATION` order by `AC`.`LOCATION` ASC separator ', ') AS `LastFoundAt`
    from
        (`WICS_actualcounts` `AC`
    join (
        select
            max(`WICS_actualcounts`.`CountDate`) AS `MaxCountDate`,
            `WICS_actualcounts`.`Material_id` AS `Material_id`
        from
            `WICS_actualcounts`
        group by
            `WICS_actualcounts`.`Material_id`) `MAXAC` on
        (((`AC`.`Material_id` = `MAXAC`.`Material_id`)
            and (`AC`.`CountDate` = `MAXAC`.`MaxCountDate`))))
    group by
        `AC`.`Material_id`,
        `AC`.`CountDate`) `ACTCOUNT` on
    (((`ACTCOUNT`.`Material_id` = `MATL`.`id`)
        or isnull(`ACTCOUNT`.`Material_id`))));


-- `calvinc460$default`.VIEW_SAP source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_SAP` AS
select
    `SAP`.`id` AS `id`,
    `SAP`.`uploaded_at` AS `uploaded_at`,
    `MATL`.`id` AS `Material_id`,
    `MATL`.`Material` AS `Material`,
    `MATL`.`Material_org` AS `Material_org`,
    `SAP`.`Plant` AS `Plant`,
    `SAP`.`StorageLocation` AS `StorageLocation`,
    `SAP`.`BaseUnitofMeasure` AS `BaseUnitofMeasure`,
    `SAP`.`Amount` AS `Amount`,
    `SAP`.`Currency` AS `Currency`,
    `SAP`.`ValueUnrestricted` AS `ValueUnrestricted`,
    `SAP`.`Blocked` AS `BlockedAmount`,
    `SAP`.`ValueBlocked` AS `ValueBlocked`,
    `UOMTable`.`UOM` AS `UOM`,
    `UOMTable`.`UOMText` AS `UOMText`,
    `UOMTable`.`DimensionText` AS `DimensionText`,
    `UOMTable`.`Multiplier1` AS `mult`,
    `SAP`.`SpecialStock` AS `SpecialStock`,
    `SAP`.`Batch` AS `Batch`,
    `SAP`.`Vendor` AS `Vendor`,
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
    (`SAP`.`Material_id` = `MATL`.`id`))
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
    `MATL`.`Material_org` AS `Material_org`,
    AC.LOCATION as LOCATION,
    `AC`.`CycCtID` AS `CycCtID`,
    `AC`.`Counter` AS `Counter`,
    `AC`.`CTD_QTY_Expr` AS `CTD_QTY_Expr`,
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
    `MATL`.`PartTypePriority` AS `PartTypePriority`
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
    `MATL`.`Material_org` AS `Material_org`,
    `SCHD`.`Requestor` AS `Requestor`,
    `SCHD`.`RequestFilled` AS `RequestFilled`,
    `SCHD`.`Requestor_userid_id` AS `Requestor_userid_id`,
    `SCHD`.`Counter` AS `Counter`,
    `SCHD`.`Priority` AS `Priority`,
    `SCHD`.`ReasonScheduled` AS `ReasonScheduled`,
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
    `MATL`.`PartTypePriority` AS `PartTypePriority`
from
    `WICS_countschedule` `SCHD`
join `VIEW_materials` `MATL` on
    (`SCHD`.`Material_id` = `MATL`.`id`);


-- `calvinc460$default`.VIEW_FoundAt source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_FoundAt` AS
select DISTINCT
    0 AS `id`,
    `AC`.`Material_id` AS `Material_id`,
    `AC`.`Material` AS `Material`,
    `AC`.`Material_org` AS `Material_org`,
    `AC`.`CountDate` AS `CountDate`,
    group_concat(distinct `AC`.`LOCATION` order by `AC`.`LOCATION` ASC separator ', ') AS `FoundAt`
from
    `VIEW_actualcounts` `AC`
group by
    `AC`.`Material_id`,
    `AC`.`CountDate`
order by
    `AC`.`Material`,
    `AC`.`CountDate` desc;


-- `calvinc460$default`.VIEW_LastFoundAt source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_LastFoundAt` AS
select
    0 AS `id`,
    `VIEW_FoundAt`.`Material_id` AS `Material_id`,
    `VIEW_FoundAt`.`Material` AS `Material`,
    `VIEW_FoundAt`.`Material_org` AS `Material_org`,
    `VIEW_FoundAt`.`CountDate` AS `CountDate`,
    `VIEW_FoundAt`.`FoundAt` AS `FoundAt`
from
    `VIEW_FoundAt`
group by
    `VIEW_FoundAt`.`Material_id`
having
    (`VIEW_FoundAt`.`CountDate` = max(`VIEW_FoundAt`.`CountDate`));


-- `calvinc460$default`.VIEW_LastFoundAtList source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_LastFoundAtList` AS
select distinct 
    0 AS `id`,
    `AC`.`Material_id` AS `Material_id`,
    `AC`.`Material` AS `Material`,
    `AC`.`Material_org` AS `Material_org`,
    `AC`.`CountDate` AS `CountDate`,
    `AC`.`LOCATION` AS `LOCATION`,
    `AC`.`LOCATION` AS `FoundAt`
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
    `AC`.`Material`,
    `AC`.`LOCATION`;


-- `calvinc460$default`.VIEW_LastSAP source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_LastSAP` AS
select
    `SAP`.`id` AS `id`,
    `SAP`.`uploaded_at` AS `uploaded_at`,
    `SAP`.`org_id` AS `org_id`,
    `SAP`.`OrgName` AS `OrgName`,
    `SAP`.`Material_id` AS `Material_id`,
    `SAP`.`Material` AS `Material`,
    `SAP`.`Material_org` AS `Material_org`,
    `SAP`.`Plant` AS `Plant`,
    `SAP`.`StorageLocation` AS `StorageLocation`,
    `SAP`.`BaseUnitofMeasure` AS `BaseUnitofMeasure`,
    `SAP`.`Amount` AS `Amount`,
    `SAP`.`Currency` AS `Currency`,
    `SAP`.`ValueUnrestricted` AS `ValueUnrestricted`,
    `SAP`.`BlockedAmount` AS `BlockedAmount`,
    `SAP`.`ValueBlocked` AS `ValueBlocked`,
    `SAP`.`UOM` AS `UOM`,
    `SAP`.`UOMText` AS `UOMText`,
    `SAP`.`DimensionText` AS `DimensionText`,
    `SAP`.`mult` AS `mult`,
    `SAP`.`SpecialStock` AS `SpecialStock`,
    `SAP`.`Batch` AS `Batch`,
    `SAP`.`Vendor` AS `Vendor`,
    `SAP`.`Description` AS `Description`,
    `SAP`.`SAPMaterialType` AS `SAPMaterialType`,
    `SAP`.`SAPMaterialGroup` AS `SAPMaterialGroup`,
    `SAP`.`Price` AS `Price`,
    `SAP`.`PriceUnit` AS `PriceUnit`,
    `SAP`.`Notes` AS `Notes`,
    `SAP`.`TypicalContainerQty` AS `TypicalContainerQty`,
    `SAP`.`TypicalPalletQty` AS `TypicalPalletQty`,
    `SAP`.`PartType_id` AS `PartType_id`,
    `SAP`.`PartType` AS `PartType`,
    `SAP`.`PartTypePriority` AS `PartTypePriority`
from
    (`VIEW_SAP` `SAP`
join (
    select
        `WICS_sap_sohrecs`.`org_id` AS `org_id`,
        max(`WICS_sap_sohrecs`.`uploaded_at`) AS `MaxUploadedDate`
    from
        `WICS_sap_sohrecs`
    group by
        `WICS_sap_sohrecs`.`org_id`
        ) `MaxRecs` 
  on
    ((`SAP`.`uploaded_at` = `MaxRecs`.`MaxUploadedDate`)
        and (`SAP`.`org_id` = `MaxRecs`.`org_id`)))
order by
    `SAP`.`org_id`,
    `SAP`.`Material`,
    `SAP`.`StorageLocation`;

   
-- `calvinc460$default`.VIEW_MaterialLocationListWithSAP source

CREATE OR REPLACE
ALGORITHM = UNDEFINED VIEW `VIEW_MaterialLocationListWithSAP` AS
select
    `MATL`.`id` AS `id`,
    `matl`.`org_id` as `org_id`,
    `MATL`.`Material` AS `Material`,
    `MATL`.`Material_org` AS `Material_org`,
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
    `SAP`.`BlockedAmount` AS `BlockedAmount`,
    `SAP`.`ValueBlocked` AS `ValueBlocked`,
    `SAP`.`Currency` AS `Currency`,
    `SAP`.`SpecialStock` AS `SpecialStock`,
    `SAP`.`Batch` AS `Batch`,
    `SAP`.`Vendor` AS `Vendor`,
    (isnull(`SAP`.`id`)
    and (ifnull(`LFA`.`CountDate`, 0) < (curdate() - interval cast((select `PARM`.`ParmValue` from `cMenu_cparameters` `PARM` where (`PARM`.`ParmName` = 'LOCRPT-COUNTDAYS-IFNOSAP')) as unsigned) day))) AS `DoNotShow`
from
    ((`VIEW_materials` `MATL`
left join `VIEW_LastFoundAt` `LFA` on
    ((`MATL`.`id` = `LFA`.`Material_id`)))
left join `VIEW_SAP` `SAP` on
    ((`MATL`.`id` = `SAP`.`Material_id`)));
    
-- wicsv3dev.view_materiallocationlistwithlastsap source

create or replace
algorithm = UNDEFINED view `VIEW_MaterialLocationListWithLastSAP` as
select
    `matl`.`id` as `id`,
    `matl`.`org_id` as `org_id`,
    `matl`.`Material` as `Material`,
    `matl`.`Material_org` as `Material_org`,
    `matl`.`Description` as `Description`,
    `matl`.`SAPMaterialType` as `SAPMaterialType`,
    `matl`.`SAPMaterialGroup` as `SAPMaterialGroup`,
    `matl`.`Price` as `Price`,
    `matl`.`PriceUnit` as `PriceUnit`,
    `matl`.`Notes` as `Notes`,
    `matl`.`PartType_id` as `PartType_id`,
    `matl`.`PartType` as `PartType`,
    `matl`.`PartTypePriority` as `PartTypePriority`,
    `matl`.`TypicalContainerQty` as `TypicalContainerQty`,
    `matl`.`TypicalPalletQty` as `TypicalPalletQty`,
    `matl`.`OrgName` as `OrgName`,
    `lfa`.`CountDate` as `CountDate`,
    `lfa`.`FoundAt` as `FoundAt`,
    `sap`.`id` as `SAP_id`,
    `sap`.`uploaded_at` as `SAPDate`,
    `sap`.`Plant` as `Plant`,
    `sap`.`StorageLocation` as `StorageLocation`,
    `sap`.`Amount` as `Amount`,
    `sap`.`BaseUnitofMeasure` as `BaseUnitofMeasure`,
    `sap`.`UOM` as `UOM`,
    `sap`.`UOMText` as `UOMText`,
    `sap`.`DimensionText` as `DimensionText`,
    `sap`.`mult` as `mult`,
    `sap`.`ValueUnrestricted` as `ValueUnrestricted`,
    `SAP`.`BlockedAmount` AS `BlockedAmount`,
    `SAP`.`ValueBlocked` AS `ValueBlocked`,
    `SAP`.`Currency` AS `Currency`,
    `SAP`.`SpecialStock` AS `SpecialStock`,
    `SAP`.`Batch` AS `Batch`,
    `SAP`.`Vendor` AS `Vendor`,
    `sap`.`id` is null
    and ifnull(`lfa`.`CountDate`, 0) < curdate() - interval cast((select `parm`.`ParmValue` from `cMenu_cparameters` `parm` where `parm`.`ParmName` = 'LOCRPT-COUNTDAYS-IFNOSAP') as unsigned) day as `DoNotShow`
from
    ((`VIEW_materials` `matl`
left join `VIEW_lastfoundat` `lfa` on
    (`matl`.`id` = `lfa`.`Material_id`))
left join `VIEW_lastsap` `sap` on
    (`matl`.`id` = `sap`.`Material_id`));

