from django.contrib import admin

from . import models


class AccountAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'active')
    list_filter = ('type', 'active')
    search_fields = ('title',)


class WithdrawalSlipAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'account', 'amount', 'completed', 'status')
    list_filter = ('type', 'status')
    search_fields = ('title', 'remarks',)
    fields = ('type', 'status', 'account', 'amount', 'completed', 'title', 'remarks')
    date_hierarchy = 'completed'
    ordering = ['-completed', ]


class UnidentifiedDepositSlip(admin.ModelAdmin):
    list_display = ('title', 'type', 'account', 'amount', 'completed', 'status')
    list_filter = ('type', 'status')
    search_fields = ('title', 'remarks',)
    fields = ('type', 'status', 'account', 'amount', 'completed', 'title', 'remarks')
    date_hierarchy = 'completed'

    ordering = ['-completed', ]


admin.site.register(models.Account, AccountAdmin)
admin.site.register(models.WithdrawalSlip, WithdrawalSlipAdmin)
admin.site.register(models.UnidentifiedDepositSlip, UnidentifiedDepositSlip)
