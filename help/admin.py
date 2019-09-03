from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from member.models import Profile
from shop import models
from . import forms


class NoAnswerFilterSpec(SimpleListFilter):
    title = _('No Answer')
    parameter_name = 'no_answer'

    def lookups(self, request, model_admin):
        return (
            ('1', _('No Answer'),),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.annotate(answers_count=Count('answers')).filter(answers_count=0)


class QuestionAnswerInline(admin.StackedInline):
    model = models.QuestionAnswer
    extra = 0
    fields = ('content', 'created')
    readonly_fields = ('created',)
    ordering = ['-created']


class TestimonialsAnswerInline(admin.StackedInline):
    model = models.TestimonialsAnswer
    extra = 0
    fields = ('content', 'created')
    readonly_fields = ('created',)
    ordering = ['-created']


class NoticeMessageAdmin(admin.ModelAdmin):
    list_display = ('category', 'title', 'store', 'created', 'owner')
    list_select_related = ('owner',)
    list_display_links = ('category', 'title')
    list_filter = ('category', 'store')
    raw_id_fields = ('owner',)
    form = forms.NoticeMessageAdminForm
    ordering = ['-created']

    def save_model(self, request, obj, form, change):
        if obj.owner is None:
            obj.owner = request.user

        super(NoticeMessageAdmin, self).save_model(request, obj, form, change)


class FaqMessageAdmin(admin.ModelAdmin):
    list_display = ('position', 'category', 'title', 'store', 'created')
    list_select_related = ('owner',)
    list_display_links = ('category', 'title')
    list_filter = ('category', 'store')
    form = forms.FaqMessageAdminForm
    ordering = ['position', '-created']

    def save_model(self, request, obj, form, change):
        if obj.owner is None:
            obj.owner = request.user

        super(FaqMessageAdmin, self).save_model(request, obj, form, change)


class CustomerQuestionAdmin(admin.ModelAdmin):
    list_display = ('category', 'title', 'order_no', 'created')
    list_display_links = ('category', 'title')
    search_fields = ['owner__email', ]
    list_filter = ('category', 'store', NoAnswerFilterSpec)
    inlines = [QuestionAnswerInline]
    fieldsets = (
        (_('Profile'), {
            'fields': (
                'full_name', 'phone', 'phone_verified_status', 'document_verified',
            )
        }),
        (_('customer question'), {
            'fields': (
                'order_no', 'category', 'content', 'created', 'store',
            )
        }),
    )
    readonly_fields = (
        'full_name', 'phone', 'phone_verified_status', 'document_verified',
        'order_no', 'category', 'created', 'content', 'store',
    )
    ordering = ['-created']

    def get_queryset(self, request):
        return super(CustomerQuestionAdmin, self).get_queryset(request) \
            .select_related('store', 'owner', 'owner__profile', 'order') \
            .prefetch_related('answers')

    def save_model(self, request, obj, form, change):
        if obj.owner is None:
            obj.owner = request.user

        super(CustomerQuestionAdmin, self).save_model(request, obj, form, change)

    def order_no(self, instance):
        if instance.order:
            return mark_safe('<a href="{}">{}</a>'.format(
                reverse('admin:shop_order_change', args=(instance.order.id,)),
                instance.order.order_no,
            )
            )
        else:
            return '-'

    order_no.short_description = _('order no')

    def full_name(self, instance):
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse('admin:member_profile_change', args=(instance.owner.profile.id,)),
            instance.owner.profile.full_name,
        )
        )

    full_name.short_description = _('Full name')

    def phone(self, instance):
        return instance.owner.profile.phone

    phone.short_description = _('phone number')

    def phone_verified_status(self, instance):
        if instance.owner.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified:
            return mark_safe('<img src="/assets/admin/img/icon-yes.svg" alt="verified">')
        elif instance.owner.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.unverified:
            return mark_safe('<img src="/assets/admin/img/icon-no.svg" alt="unverified">')
        elif instance.owner.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.revoked:
            return mark_safe('<img src="/assets/admin/img/icon-unknown.svg" alt="revoked">')

    phone_verified_status.short_description = _('phone verified')

    def document_verified(self, instance):
        if instance.owner.profile.document_verified:
            return mark_safe('<img src="/assets/admin/img/icon-yes.svg" alt="True">')
        else:
            return mark_safe('<img src="/assets/admin/img/icon-no.svg" alt="False">')

    document_verified.short_description = _('document verified')


class TestimonialsAdmin(admin.ModelAdmin):
    list_display = ('title', 'created')
    search_fields = ['owner__email', ]
    raw_id_fields = ('owner',)
    inlines = [TestimonialsAnswerInline]
    ordering = ['-created']

    def get_queryset(self, request):
        return super(TestimonialsAdmin, self).get_queryset(request) \
            .select_related('store', 'owner', 'owner__profile') \
            .prefetch_related('answers')


admin.site.register(models.NoticeMessage, NoticeMessageAdmin)
admin.site.register(models.FaqMessage, FaqMessageAdmin)
admin.site.register(models.CustomerQuestion, CustomerQuestionAdmin)
admin.site.register(models.Testimonials, TestimonialsAdmin)
