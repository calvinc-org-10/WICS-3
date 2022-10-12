from django.db import models
from sqlalchemy import UniqueConstraint


class menuCommands(models.Model):
    Command = models.IntegerField(primary_key=True, db_column = 'command')
    CommandText = models.CharField(max_length=250, db_column = 'commandtext')

    class Meta:
        # db_tablespace = 'menusys'
        db_table = 'zzutilmenucommands'
        managed = False


class menuItems(models.Model):
    MenuID = models.SmallIntegerField(db_column = 'menuid', primary_key=True)
    # OptionNumber = models.SmallIntegerField(db_column = 'optionnumber', primary_key=True)
    OptionNumber = models.SmallIntegerField(db_column = 'optionnumber')
    OptionText = models.CharField(max_length=250, db_column = 'optiontext')
    Command = models.ForeignKey(menuCommands,on_delete=models.RESTRICT, db_column = 'command')
    Argument = models.CharField(max_length=250, db_column = 'argument')
    PWord = models.CharField(max_length=250, db_column = 'Password')
    TopLine = models.BooleanField(db_column = 'topline')
    BottomLine = models.BooleanField(db_column = 'bottomline')
    UniqueConstraint('MenuID','OptionNumber')

    class Meta:
        # db_tablespace = 'menusys'
        db_table = 'zapplmenuitems'
        managed = False

