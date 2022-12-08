from django.contrib import admin

# Register your models here.

from .models import Organizations, WhsePartTypes
admin.site.register(Organizations)
admin.site.register(WhsePartTypes)
