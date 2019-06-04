from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin

from .models import (
    MenuItem, Google
)


class MenuItemAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'url', 'match', 'target')
    mptt_level_indent = 20
    ordering = ['tree_id', 'lft']


class GoogleAdmin(admin.ModelAdmin):
    list_display = ('site_id', 'analytics_uid')


admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(Google, GoogleAdmin)
