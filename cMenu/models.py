from django.db import models


class menuCommands(models.Model):
    Command = models.IntegerField(primary_key=True)
    CommandText = models.CharField(max_length=250)

    class Meta:
        ordering = ['Command']

    def __str__(self) -> str:
        return f'{self.Command} - {self.CommandText}'
        # return super().__str__()


class menuGroups(models.Model):
    GroupName = models.CharField(max_length=100,null=False, unique=True)
    GroupInfo = models.CharField(max_length=250, blank=True)
    def __str__(self) -> str:
        return f'menuGroup {self.GroupName}'


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

    class Meta:
        ordering = ['MenuGroup','MenuID', 'OptionNumber']
        constraints = [
                models.UniqueConstraint(fields=['MenuGroup','MenuID','OptionNumber'], name='mnuItUNQ_mGrp_mID_OptNum')
            ]

    def __str__(self) -> str:
        return f'{self.MenuGroup}, {self.MenuID}/{self.OptionNumber}, {self.OptionText}'


class cParameters(models.Model):
    ParmName = models.CharField(primary_key=True, max_length=100)
    ParmValue = models.CharField(max_length=512, blank=True, null=False, default='')
    UserModifiable = models.BooleanField(blank=True, null=False, default=True)
    Comments = models.CharField(max_length=512, blank=True, null=False, default='')

    class Meta:
        ordering = ['ParmName']

    def __str__(self) -> str:
        S = ''
        if self.ParmName: 
            S += self.ParmName
        else:
            S += '----'
        S += ' ('
        if self.ParmValue: S += self.ParmValue
        S += ')'
        return S

def getcParm(parmname):
    if cParameters.objects.filter(ParmName=parmname).exists():
        return cParameters.objects.get(ParmName=parmname).ParmValue
    else:
        return ''

def setcParm(parmname, parmvalue):
    P = cParameters.objects.get_or_create(ParmName=parmname)
    P.ParmValue = parmvalue
    P.save()


class cGreetings(models.Model):
    id = models.AutoField(primary_key=True)
    Greeting = models.CharField(max_length=2000)

    def __str__(self):
        return f'{self.Greeting}'
    
