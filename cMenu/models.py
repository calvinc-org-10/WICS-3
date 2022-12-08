from django.db import models
from sqlalchemy import UniqueConstraint


class menuCommands(models.Model):
    Command = models.IntegerField(primary_key=True)
    CommandText = models.CharField(max_length=250)

    class Meta:
        ordering = ['Command']

    def __str__(self) -> str:
        return str(self.Command) + ' - ' + self.CommandText
        # return super().__str__()


class menuGroups(models.Model):
    GroupName = models.CharField(max_length=100,null=False, unique=True)
    GroupInfo = models.CharField(max_length=250, blank=True)
    def __str__(self) -> str:
        return 'menuGroup ' + self.GroupName


class menuItems(models.Model):
    # MenuID, OptionNumber is key, but django doesn't do multi-column keys.  django will create an primary key, but the UniqueConstraint below will give Uniqueness
    MenuGroup = models.ForeignKey(menuGroups,on_delete=models.RESTRICT,null=True)
    MenuID = models.SmallIntegerField()
    OptionNumber = models.SmallIntegerField()
    OptionText = models.CharField(max_length=250)
    Command = models.ForeignKey(menuCommands,on_delete=models.RESTRICT,null=True)
    Argument = models.CharField(max_length=250, blank=True)
    PWord = models.CharField(max_length=250, blank=True)
    TopLine = models.BooleanField(null=True)
    BottomLine = models.BooleanField(null=True)
    UniqueConstraint('MenuGroup','MenuID','OptionNumber')

    class Meta:
        ordering = ['MenuGroup','MenuID', 'OptionNumber']

    def __str__(self) -> str:
        return self.MenuGroup + ', ' + self.MenuID + '/' + self.OptionNumber + ', ' + self.OptionText

