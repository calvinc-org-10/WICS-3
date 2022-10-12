NOTE - This is an outline of what to do, not the actual SQL!!

CREATE SCHEMA menusys;
CREATE TABLE menuCommands;
ALTER TABLE menuCommands SET SCHEMA menusys;
CREATE TABLE menuItems;
    MenuID                          Double, 8
    OptionNumber                    Double, 8
    OptionText                      Text, 255
    Command                         Double, 8
    Argument                        Text, 255
    Password                        Text, 255
    Picture                         Text, 255
    TopLine                         Boolean, 2
    BottomLine                      Boolean, 2
ALTER TABLE menuItems SET SCHEMA menusys;
