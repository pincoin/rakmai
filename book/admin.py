from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from ipware.ip import get_ip
from mptt.admin import (
    DraggableMPTTAdmin, MPTTModelAdmin
)

from .forms import BookAdminForm
from .models import (
    Book, Attachment, Category, Page
)


class PageNullFilterSpec(SimpleListFilter):
    title = _('page')
    parameter_name = 'page'

    def lookups(self, request, model_admin):
        return (
            ('1', _('Has page'),),
            ('0', _('No page'),),
        )

    def queryset(self, request, queryset):
        kwargs = {
            '{}'.format(self.parameter_name): None,
        }
        if self.value() == '0':
            return queryset.filter(**kwargs)
        if self.value() == '1':
            return queryset.exclude(**kwargs)
        return queryset


class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'owner', 'status', 'view_count')
    ordering = ['-created']
    raw_id_fields = ('owner',)
    readonly_fields = ('view_count', 'updated')
    form = BookAdminForm

    def save_model(self, request, obj, form, change):
        obj.updated = now()
        super(BookAdmin, self).save_model(request, obj, form, change)


class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'page', 'file', 'created')
    list_filter = (PageNullFilterSpec,)
    ordering = ['-created', ]


class CategoryAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    mptt_level_indent = 20
    ordering = ['tree_id', 'lft']


class PageAdmin(MPTTModelAdmin):
    list_display = ('title',)
    list_filter = ('status', 'book')
    mptt_level_indent = 20
    readonly_fields = ('ip_address', 'view_count')
    ordering = ['tree_id', 'lft']

    def save_model(self, request, obj, form, change):
        obj.updated = now()

        if obj.id is None:
            obj.ip_address = get_ip(request)

        super(PageAdmin, self).save_model(request, obj, form, change)


admin.site.register(Book, BookAdmin)
admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Page, PageAdmin)
