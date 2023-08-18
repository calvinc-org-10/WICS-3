from django.contrib import admin

# Register your models here.

from .models import Organizations, WhsePartTypes, WorksheetZones, Location_WorksheetZone, WICSPermissions, async_comm
admin.site.register(Organizations)
admin.site.register(WhsePartTypes)
admin.site.register(WorksheetZones)
admin.site.register(Location_WorksheetZone)
admin.site.register(WICSPermissions)
admin.site.register(async_comm)
