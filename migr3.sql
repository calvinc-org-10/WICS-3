--
-- Create model Organizations
--
CREATE TABLE `WICS_organizations` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `orgname` varchar(250) NOT NULL);
--
-- Create model WhsePartTypes
--
CREATE TABLE `WICS_whseparttypes` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `oldWICSID` integer NULL, `WhsePartType` varchar(50) NOT NULL, `PartTypePriority` smallint NOT NULL, `InactivePartType` bool NOT NULL, `org_id` bigint NOT NULL);
--
-- Create model org_SAPPlant
--
CREATE TABLE `WICS_org_sapplant` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `SAPPlant` varchar(50) NOT NULL, `SAPStorLoc` varchar(50) NOT NULL, `org_id` bigint NOT NULL);
--
-- Create model MaterialList
--
CREATE TABLE `WICS_materiallist` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `oldWICSID` integer NULL, `Material` varchar(100) NOT NULL, `Description` varchar(250) NOT NULL, `oldWICSPartType` integer NULL, `SAPMaterialType` varchar(100) NOT NULL, `SAPMaterialGroup` varchar(100) NOT NULL, `Price` double precision NULL, `PriceUnit` integer UNSIGNED NULL, `Notes` varchar(250) NOT NULL, `PartType_id` bigint NULL, `org_id` bigint NOT NULL);
--
-- Create model Count_Schedule_History
--
CREATE TABLE `WICS_count_schedule_history` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `oldWICSID` integer NULL, `CountDate` date NOT NULL, `oldWICSMaterial` integer NULL, `Counter` varchar(250) NOT NULL, `Priority` varchar(50) NOT NULL, `ReasonScheduled` varchar(250) NOT NULL, `CMPrintFlag` bool NOT NULL, `Notes` varchar(250) NOT NULL, `Material_id` bigint NOT NULL, `org_id` bigint NOT NULL);
--
-- Create model ActualCounts
--
CREATE TABLE `WICS_actualcounts` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `oldWICSID` integer NOT NULL, `CountDate` date NOT NULL, `CycCtID` varchar(100) NOT NULL, `oldWICSMaterial` integer NULL, `Counter` varchar(250) NOT NULL, `CTD_QTY_Expr` varchar(500) NOT NULL, `BLDG` varchar(100) NOT NULL, `LOCATION` varchar(250) NOT NULL, `PKGID_Desc` varchar(250) NOT NULL, `TAGQTY` varchar(250) NOT NULL, `FLAG_PossiblyNotRecieved` bool NOT NULL, `FLAG_MovementDuringCount` bool NOT NULL, `Notes` varchar(250) NOT NULL, `Material_id` bigint NOT NULL, `org_id` bigint NOT NULL);
ALTER TABLE `WICS_whseparttypes` ADD CONSTRAINT `WICS_whseparttypes_org_id_52165ceb_fk_WICS_organizations_id` FOREIGN KEY (`org_id`) REFERENCES `WICS_organizations` (`id`);
ALTER TABLE `WICS_org_sapplant` ADD CONSTRAINT `WICS_org_sapplant_org_id_3fa52364_fk_WICS_organizations_id` FOREIGN KEY (`org_id`) REFERENCES `WICS_organizations` (`id`);
ALTER TABLE `WICS_materiallist` ADD CONSTRAINT `WICS_materiallist_PartType_id_86058a4a_fk_WICS_whseparttypes_id` FOREIGN KEY (`PartType_id`) REFERENCES `WICS_whseparttypes` (`id`);
ALTER TABLE `WICS_materiallist` ADD CONSTRAINT `WICS_materiallist_org_id_6c7bdf21_fk_WICS_organizations_id` FOREIGN KEY (`org_id`) REFERENCES `WICS_organizations` (`id`);
ALTER TABLE `WICS_count_schedule_history` ADD CONSTRAINT `WICS_count_schedule__Material_id_625a3c03_fk_WICS_mate` FOREIGN KEY (`Material_id`) REFERENCES `WICS_materiallist` (`id`);
ALTER TABLE `WICS_count_schedule_history` ADD CONSTRAINT `WICS_count_schedule__org_id_259f3b8d_fk_WICS_orga` FOREIGN KEY (`org_id`) REFERENCES `WICS_organizations` (`id`);
ALTER TABLE `WICS_actualcounts` ADD CONSTRAINT `WICS_actualcounts_Material_id_6f114fcf_fk_WICS_materiallist_id` FOREIGN KEY (`Material_id`) REFERENCES `WICS_materiallist` (`id`);
ALTER TABLE `WICS_actualcounts` ADD CONSTRAINT `WICS_actualcounts_org_id_f7b33a95_fk_WICS_organizations_id` FOREIGN KEY (`org_id`) REFERENCES `WICS_organizations` (`id`);
