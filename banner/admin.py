from django.contrib import admin

from .models import (
    Banner, BannerItem
)


class BannerItemInline(admin.StackedInline):
    model = BannerItem
    ordering = ['position', ]
    extra = 1


class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'start', 'end')
    fields = ('title', 'status', 'start', 'end')
    inlines = [BannerItemInline]


class BannerItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'banner', 'url', 'target', 'position')
    ordering = ['banner', 'position']


admin.site.register(Banner, BannerAdmin)
admin.site.register(BannerItem, BannerItemAdmin)
