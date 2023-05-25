--
-- Create model menuCommands
--
CREATE TABLE `cMenu_menucommands` (`Command` integer NOT NULL PRIMARY KEY, `CommandText` varchar(250) NOT NULL);
--
-- Create model menuItems
--
CREATE TABLE `cMenu_menuitems` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `MenuID` smallint NOT NULL, `OptionNumber` smallint NOT NULL, `OptionText` varchar(250) NOT NULL, `Argument` varchar(250) NOT NULL, `PWord` varchar(250) NOT NULL, `TopLine` bool NOT NULL, `BottomLine` bool NOT NULL, `Command_id` integer NOT NULL);
ALTER TABLE `cMenu_menuitems` ADD CONSTRAINT `cMenu_menuitems_Command_id_e5304cf4_fk_cMenu_men` FOREIGN KEY (`Command_id`) REFERENCES `cMenu_menucommands` (`Command`);
