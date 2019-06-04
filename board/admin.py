from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from django.utils.translation import gettext_lazy as _
from mptt.admin import DraggableMPTTAdmin

from . import settings as board_settings
from .forms import MessageAdminForm
from .models import (
    Board, Message, Category, Attachment
)


class BoardAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'allow_comments', 'chunk_size', 'block_size')
    ordering = ['-created']


class CategoryAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'slug', 'board')
    list_filter = ('board__title', 'created')
    prepopulated_fields = {'slug': ('title',)}
    mptt_level_indent = 20
    ordering = ['tree_id', 'lft']


class MessageAdmin(admin.ModelAdmin):
    list_display = ('board', 'title', 'owner', 'created', 'status', 'is_removed', 'secret', 'ip_address')
    list_display_links = ('title',)
    list_filter = ('board__title', 'status')
    search_fields = ('title', 'content')
    ordering = ['-created']

    raw_id_fields = ('owner',)
    readonly_fields = ('ip_address', 'view_count')
    form = MessageAdminForm


class MessageNullFilterSpec(SimpleListFilter):
    title = _('message')
    parameter_name = 'message'

    def lookups(self, request, model_admin):
        return (
            ('1', _('Has message'),),
            ('0', _('No message'),),
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


class AttachmentInline(admin.StackedInline):
    model = Attachment
    extra = 2
    max_num = board_settings.MESSAGE_MAX_FILE_COUNT


class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'message', 'file', 'created')
    list_filter = (MessageNullFilterSpec,)
    ordering = ['-created', ]


admin.site.register(Board, BoardAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Attachment, AttachmentAdmin)
