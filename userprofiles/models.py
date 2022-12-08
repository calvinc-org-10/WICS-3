from django.contrib.auth.models import User
from django.db import models
from WICS.models import Organizations
from cMenu.models import menuGroups


class WICSuser(models.Model):
    user = models.OneToOneField(User,on_delete = models.CASCADE, related_name='WICSuser')
    org = models.ForeignKey(Organizations, on_delete=models.CASCADE)
    menuGroup = models.ForeignKey(menuGroups,on_delete=models.RESTRICT,null=True)

    def save(self, *args, **kwargs):
        # the User instance MUST exist first!
        if self.user is None:
            return
        if self.org is None:
            return

        super().save(*args, **kwargs)

    # def delete(self, *args, **kwargs):

    def __str__(self):
        return "<WICS User> " + self.user.get_username()
