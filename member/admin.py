from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import (
    Profile, LoginLog, PhoneVerificationLog, Mms, MmsData
)


class MmsDataInline(admin.TabularInline):
    model = MmsData
    extra = 0


class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'email', 'full_name', 'phone',
        'phone_verified_status', 'document_verified',
    )
    list_filter = ('phone_verified_status', 'document_verified', 'not_purchased_months', 'allow_order')
    search_fields = ('user__email', 'phone')
    readonly_fields = ('user', 'full_name', 'email', 'date_joined', 'document_verified', 'not_purchased_months',
                       'photo_id_preview', 'card_preview', 'mileage')
    ordering = ['-created']

    fieldsets = (
        (_('Account'), {
            'fields': ('user', 'full_name', 'email', 'date_joined',
                       'phone_verified_status', 'document_verified', 'not_purchased_months', 'allow_order')
        }),
        (_('Profile'), {
            'fields': ('phone', 'address', 'photo_id_preview', 'card_preview', 'mileage', 'memo',
                       'first_purchased', 'last_purchased')
        }),
    )

    def get_queryset(self, request):
        return super(ProfileAdmin, self).get_queryset(request) \
            .select_related('user')

    def phone_verified_status(self, instance):
        if instance.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified:
            return mark_safe('<img src="/assets/admin/img/icon-yes.svg" alt="verified">')
        elif instance.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.unverified:
            return mark_safe('<img src="/assets/admin/img/icon-no.svg" alt="unverified">')
        elif instance.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.revoked:
            return mark_safe('<img src="/assets/admin/img/icon-unknown.svg" alt="revoked">')

    phone_verified_status.short_description = _('phone verified')


class LoginLogAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'user', 'ip_address', 'created'
    )
    list_select_related = ('user', 'user__profile')
    search_fields = ('user__email', 'ip_address')
    ordering = ['-created']

    def get_queryset(self, request):
        return super(LoginLogAdmin, self).get_queryset(request) \
            .select_related('user', 'user__profile') \
            .filter(user__profile__isnull=False)

    def full_name(self, instance):
        return '{} / {} / {}'.format(instance.user.profile.full_name, instance.user.email, instance.user.profile.phone)

    full_name.short_description = _('Full name')


class PhoneVerificationLogAdmin(admin.ModelAdmin):
    list_display = (
        'fullname', 'cellphone', 'telecom', 'gender', 'date_of_birth', 'created'
    )
    fields = (
        'owner', 'fullname', 'cellphone', 'telecom', 'date_of_birth', 'gender', 'domestic', 'token',
    )
    search_fields = ('fullname', 'cellphone')
    readonly_fields = (
        'owner', 'fullname', 'date_of_birth', 'gender', 'domestic', 'telecom', 'cellphone',
        'token', 'code', 'reason', 'result_code', 'message', 'transaction_id', 'di', 'ci', 'return_message',
    )
    ordering = ['-created']


class MmsAdmin(admin.ModelAdmin):
    list_display = (
        'cellphone', 'sent',
    )
    search_fields = ('cellphone',)
    inlines = [MmsDataInline]
    ordering = ['-sent']


class MmsDataAdmin(admin.ModelAdmin):
    pass


admin.site.register(Profile, ProfileAdmin)
admin.site.register(LoginLog, LoginLogAdmin)
admin.site.register(PhoneVerificationLog, PhoneVerificationLogAdmin)
admin.site.register(Mms, MmsAdmin)
admin.site.register(MmsData, MmsDataAdmin)
