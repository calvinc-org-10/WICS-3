from django.contrib import admin

# Register your models here.

from .models import Organizations, WhsePartTypes, WorksheetZones, Location_WorksheetZone, WICSPermissions
admin.site.register(Organizations)
admin.site.register(WhsePartTypes)
admin.site.register(WorksheetZones)
admin.site.register(Location_WorksheetZone)
admin.site.register(WICSPermissions)

