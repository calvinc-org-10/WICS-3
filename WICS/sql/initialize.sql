-- python manage.py sqlmigrate WICS 0001_initial  
--
--
-- Create model Organizations
--
CREATE TABLE "organizations" ("ID" uuid NOT NULL PRIMARY KEY, "orgname" varchar(250) NOT NULL);
--
-- Create model WhsePartTypes
--
CREATE TABLE "WICS_whseparttypes" ("ID" uuid NOT NULL PRIMARY KEY, "oldID" integer NOT NULL, "WhsePartType" varchar(50) NOT NULL, "PartTypePriority" smallint NOT NULL, "InactivePartType" boolean NOT NULL, "org_id" uuid NOT NULL);
--
-- Create model org_SAPPlant
--
CREATE TABLE "WICS_org_sapplant" ("ID" uuid NOT NULL PRIMARY KEY, "SAPPlant" varchar(50) NOT NULL, "SAPStorLoc" varchar(50) NOT NULL, "org_id" uuid NOT NULL);
--
-- Create model MaterialList
--
CREATE TABLE "WICS_materiallist" ("ID" uuid NOT NULL PRIMARY KEY, "oldID" integer NOT NULL, "Material" varchar(100) NOT NULL, "Description" varchar(250) NOT NULL, "SAPMaterialType" varchar(100) NOT NULL, "SAPMaterialGroup" varchar(100) NOT NULL, "PossibleLocations" varchar(250) NOT NULL, "Notes" varchar(250) NOT NULL, "PartType_id" uuid NULL, "org_id" uuid NOT NULL);
--
-- Create model Count_Schedule_History
--
CREATE TABLE "WICS_count_schedule_history" ("ID" uuid NOT NULL PRIMARY KEY, "oldID" integer NOT NULL, "CountDate" date NOT NULL, "Counter" varchar(250) NOT NULL, "Priority" varchar(50) NOT NULL, "ReasonScheduled" varchar(250) NOT NULL, "CMPrintFlag" boolean NOT NULL, "Notes" varchar(250) NOT NULL, "Material_id" uuid NOT NULL, "org_id" uuid NOT NULL);
--
-- Create model ActualCounts
--
CREATE TABLE "WICS_actualcounts" ("ID" uuid NOT NULL PRIMARY KEY, "oldID" integer NOT NULL, "CountDate" date NOT NULL, "CycCtID" varchar(100) NOT NULL, "Counter" varchar(250) NOT NULL, "CTD_QTY_Expr" varchar(500) NOT NULL, "BLDG" varchar(100) NOT NULL, "LOCATION" varchar(250) NOT NULL, "PKGID_Desc" varchar(250) NOT NULL, "TAGQTY" varchar(250) NOT NULL, "FLAG_PossiblyNotRecieved" boolean NOT NULL, "FLAG_MovementDuringCount" boolean NOT NULL, "Notes" varchar(250) NOT NULL, "Material_id" uuid NOT NULL, "org_id" uuid NOT NULL);
ALTER TABLE "WICS_whseparttypes" ADD CONSTRAINT "WICS_whseparttypes_org_id_52165ceb_fk_organizations_ID" FOREIGN KEY ("org_id") REFERENCES "organizations" ("ID");
ALTER TABLE "WICS_org_sapplant" ADD CONSTRAINT "WICS_org_sapplant_org_id_3fa52364_fk_organizations_ID" FOREIGN KEY ("org_id") REFERENCES "organizations" ("ID");
ALTER TABLE "WICS_materiallist" ADD CONSTRAINT "WICS_materiallist_PartType_id_86058a4a_fk_WICS_whseparttypes_ID" FOREIGN KEY ("PartType_id") REFERENCES "WICS_whseparttypes" ("ID");
ALTER TABLE "WICS_materiallist" ADD CONSTRAINT "WICS_materiallist_org_id_6c7bdf21_fk_organizations_ID" FOREIGN KEY ("org_id") REFERENCES "organizations" ("ID");
ALTER TABLE "WICS_count_schedule_history" ADD CONSTRAINT "WICS_count_schedule__Material_id_625a3c03_fk_WICS_mate" FOREIGN KEY ("Material_id") REFERENCES "WICS_materiallist" ("ID");
ALTER TABLE "WICS_count_schedule_history" ADD CONSTRAINT "WICS_count_schedule_history_org_id_259f3b8d_fk_organizations_ID" FOREIGN KEY ("org_id") REFERENCES "organizations" ("ID");
ALTER TABLE "WICS_actualcounts" ADD CONSTRAINT "WICS_actualcounts_Material_id_6f114fcf_fk_WICS_materiallist_ID" FOREIGN KEY ("Material_id") REFERENCES "WICS_materiallist" ("ID");
ALTER TABLE "WICS_actualcounts" ADD CONSTRAINT "WICS_actualcounts_org_id_f7b33a95_fk_organizations_ID" FOREIGN KEY ("org_id") REFERENCES "organizations" ("ID");
