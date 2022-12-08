from django.contrib import admin

# Register your models here.
from .models import menuItems, menuGroups
admin.site.register(menuItems)
admin.site.register(menuGroups)
