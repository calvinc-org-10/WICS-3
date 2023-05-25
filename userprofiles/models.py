from django.contrib.auth.models import User
from django.db import models
import WICS.models as WICSmodels
from cMenu.models import menuGroups


class WICSuser(models.Model):
    user = models.OneToOneField(User,on_delete = models.CASCADE, related_name='WICSuser')
    menuGroup = models.ForeignKey(menuGroups,on_delete=models.RESTRICT,null=True)

    def save(self, *args, **kwargs):
        # the User instance MUST exist first!
        if self.user is None:
            return

        super().save(*args, **kwargs)

    # def delete(self, *args, **kwargs):

    def __str__(self):
        return "<WICS User> " + self.user.get_username()
