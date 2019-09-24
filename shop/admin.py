import logging
from decimal import Decimal
from urllib.parse import quote as urlquote

from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.filters import SimpleListFilter
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.gis.geoip2 import GeoIP2
from django.db.models import (
    Sum, Count
)
from django.forms.models import BaseInlineFormSet
from django.http import HttpResponseRedirect
from django.template.defaultfilters import date as _date
from django.template.defaultfilters import linebreaks as _linebreaks
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime, now, timedelta, make_aware
from django.utils.translation import gettext_lazy as _
from geoip2.errors import AddressNotFoundError
from import_export import resources
from import_export.admin import ImportMixin
from import_export.formats import base_formats
from ipware.ip import get_ip
from mptt.admin import DraggableMPTTAdmin

from member import settings as member_settings
from member.models import LoginLog
from member.models import Profile
from shop.models import Category
from shop.tasks import send_notification_email
from . import forms
from . import models
from . import settings as shop_settings
from .helpers import currency_filter


# Filter Spec

class RemovedOrderFilterSpec(SimpleListFilter):
    title = _('Removed Order')
    parameter_name = 'is_removed'

    def lookups(self, request, model_admin):
        return (
            ('1', _('Removed Order'),),
        )

    def queryset(self, request, queryset):
        kwargs = {
            '{}'.format(self.parameter_name): True,
        }
        if self.value() == '1':
            return queryset.filter(**kwargs)
        return queryset


class ProductCategoryFilterSpec(SimpleListFilter):
    title = _('category')
    parameter_name = 'category'

    def __init__(self, *args, **kwargs):
        self.categories = Category.objects \
            .filter(store__code='default', level__gt=0) \
            .order_by('tree_id', 'lft')
        super(ProductCategoryFilterSpec, self).__init__(*args, **kwargs)

    def lookups(self, request, model_admin):
        categories = ()

        for category in self.categories:
            categories += ((str(category.id), category.title),)

        return categories

    def queryset(self, request, queryset):
        kwargs = {
            '{}'.format(self.parameter_name): self.value(),
        }
        if self.value() in list(map(lambda x: str(x.id), self.categories)):
            return queryset.filter(**kwargs)
        return queryset


class VoucherProductCategoryFilterSpec(ProductCategoryFilterSpec):
    parameter_name = 'product__category'


class VoucherListPriceFilterSpec(SimpleListFilter):
    title = _('list price')
    parameter_name = 'product__subtitle'

    def __init__(self, *args, **kwargs):
        super(VoucherListPriceFilterSpec, self).__init__(*args, **kwargs)

    def lookups(self, request, model_admin):
        return (
            ('50만원', '50만원'),
            ('30만원', '30만원'),
            ('20만원', '20만원'),
            ('15만원', '15만원'),
            ('10만원', '10만원'),
            ('5만원', '5만원'),
            ('4만9천9백원', '4만9천9백원'),
            ('3만5천원', '3만5천원'),
            ('3만원', '3만원'),
            ('2만9천7백원', '2만9천7백원'),
            ('2만원', '2만원'),
            ('1만9천9백원', '1만9천9백원'),
            ('1만9천8백원', '1만9천8백원'),
            ('1만5천원', '1만5천원'),
            ('1만원', '1만원'),
            ('9천9백원', '9천9백원'),
            ('5천원', '5천원'),
            ('4천9백원', '4천9백원'),
            ('3천원', '3천원'),
            ('1천원', '1천원'),
            ('90일 정액권', '90일 정액권'),
            ('30일 정액권', '30일 정액권'),
        )

    def queryset(self, request, queryset):
        kwargs = {
            '{}'.format(self.parameter_name): self.value(),
        }
        if self.value():
            return queryset.filter(**kwargs)
        return queryset


# Formset and Inlines

class OrderPaymentInlineFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(OrderPaymentInlineFormset, self).__init__(*args, **kwargs)
        self.queryset = models.OrderPayment.objects \
            .select_related('order') \
            .filter(order=self.instance)

        self.initial = []

        for i in range(self.initial_form_count()):
            self.initial.append({})

        self.initial.append({'amount': self.instance.total_selling_price})


class OrderProductInlineFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(OrderProductInlineFormset, self).__init__(*args, **kwargs)
        self.queryset = models.OrderProduct.objects \
            .select_related('order') \
            .filter(order=self.instance)


class PurchaseOrderPaymentInlineFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(PurchaseOrderPaymentInlineFormset, self).__init__(*args, **kwargs)
        self.queryset = models.PurchaseOrderPayment.objects \
            .select_related('order') \
            .filter(order=self.instance)

        total = 0
        for p in self.queryset:
            total += p.amount

        self.initial = []

        for i in range(self.initial_form_count()):
            self.initial.append({})

        self.initial.append({'amount': self.instance.amount - total})


class OrderPaymentInline(admin.StackedInline):
    model = models.OrderPayment
    extra = 1
    formset = OrderPaymentInlineFormset
    fields = ('account', 'amount', 'received')
    ordering = ['-created']


class ProductInline(admin.TabularInline):
    model = models.ProductList.products.through
    extra = 1


class OrderProductVoucherInline(admin.TabularInline):
    model = models.OrderProductVoucher
    extra = 0
    fields = ('revoked', 'get_edit_link', 'code', 'remarks', 'order_no', 'created')
    readonly_fields = ('get_edit_link', 'code', 'remarks', 'order_no', 'created')
    can_delete = False
    ordering = ['-created']

    def get_edit_link(self, obj=None):
        if obj.pk:  # if object has already been saved and has a primary key, show link to it
            # url = reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=(obj.pk,))
            return mark_safe('<a href="{url}">{text}</a>'.format(
                url=reverse('admin:shop_voucher_change', args=(obj.voucher.pk,)),
                text='{} {}'.format(obj.order_product.name, obj.order_product.subtitle),
            ))
        return _("(save and continue editing to create a link)")

    get_edit_link.short_description = _('voucher')

    def order_no(self, obj=None):
        return mark_safe('<a href="{url}">{text}</a>'.format(
            url=reverse('rabop:order-detail', args=('default', obj.order_product.order.pk)),
            text='{}'.format(obj.order_product.order.order_no),
        ))

    order_no.short_description = _('order no')


class NaverOrderProductVoucherInline(admin.TabularInline):
    model = models.NaverOrderProductVoucher
    extra = 0
    fields = ('revoked', 'get_edit_link', 'code', 'remarks', 'order_no', 'created')
    readonly_fields = ('get_edit_link', 'code', 'remarks', 'order_no', 'created')
    can_delete = False

    def get_edit_link(self, obj=None):
        if obj.pk:  # if object has already been saved and has a primary key, show link to it
            # url = reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=(obj.pk,))
            return mark_safe('<a href="{url}">{text}</a>'.format(
                url=reverse('admin:shop_voucher_change', args=(obj.voucher.pk,)),
                text='{} {}'.format(obj.order_product.name, obj.order_product.subtitle),
            ))
        return _("(save and continue editing to create a link)")

    get_edit_link.short_description = _('voucher')

    def order_no(self, obj=None):
        return mark_safe('<a href="{url}">{text}</a>'.format(
            url=reverse('rabop:naver-order-detail', args=('default', obj.order_product.order.pk)),
            text='{}'.format(obj.order_product.order.order_no),
        ))

    order_no.short_description = _('order no')


class OrderProductInline(admin.TabularInline):
    model = models.OrderProduct
    fields = ('get_edit_link', 'selling_price')
    readonly_fields = ('get_edit_link', 'selling_price')
    formset = OrderProductInlineFormset
    can_delete = False
    extra = 0

    def get_edit_link(self, obj=None):
        if obj.pk:  # if object has already been saved and has a primary key, show link to it
            # url = reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=(obj.pk,))
            return mark_safe('<a href="{url}">{text}</a>'.format(
                url=reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=(obj.pk,)),
                text='{} {} x {}'.format(obj.name, obj.subtitle, obj.quantity),
            ))
        return _("(save and continue editing to create a link)")

    get_edit_link.short_description = _('product name')


class PurchaseOrderPaymentInline(admin.StackedInline):
    model = models.PurchaseOrderPayment
    extra = 1
    formset = PurchaseOrderPaymentInlineFormset
    fields = ('account', 'amount')
    ordering = ['-created']


# Import Resources

class VoucherResource(resources.ModelResource):
    class Meta:
        model = models.Voucher
        #  product, code, remarks
        exclude = ('created', 'modified', 'is_removed', 'status')


# Model Admins

class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'theme', 'chunk_size', 'block_size')
    ordering = ['-created']


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'subtitle', 'code',
        'selling_price_with_rate', 'stock', 'minimum_stock_level', 'maximum_stock_level', 'status', 'position',
        'pg', 'pg_selling_price_with_rate',
        'naver_partner', 'naver_partner_title'
    )
    list_display_links = ('name', 'subtitle')
    list_filter = ('store__name', ProductCategoryFilterSpec, 'status', 'stock', 'naver_partner', 'pg')
    readonly_fields = ('selling_price_with_rate', 'pg_selling_price_with_rate')
    ordering = ['category__title', 'position']
    form = forms.ProductAdminForm
    inlines = [ProductInline]

    class Media:
        js = ('admin/js/jquery.init.js', 'js/admin/shop/product.js',)

    def selling_price_with_rate(self, instance):
        return '{} ({}%)'.format(instance.selling_price, round(instance.discount_rate, 2))

    selling_price_with_rate.short_description = _('selling price')

    def pg_selling_price_with_rate(self, instance):
        return '{} ({}%)'.format(instance.pg_selling_price, round(instance.pg_discount_rate, 2))

    pg_selling_price_with_rate.short_description = _('Payment Gateway selling price')


class ProductListAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'store')
    inlines = [ProductInline]
    exclude = ('products',)


class CategoryAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'slug', 'discount_rate', 'pg', 'pg_discount_rate', 'store')
    list_filter = ('store__name', 'created')
    prepopulated_fields = {'slug': ('title',)}
    mptt_level_indent = 20
    ordering = ['tree_id', 'lft']


class OrderAdmin(admin.ModelAdmin):
    logger = logging.getLogger(__name__)
    # change_form_template = "admin/shop/order_change_form.html"

    list_display = (
        'order_no', 'fullname',
        'total_amount', 'payment_method',
        'status', 'created', 'is_removed')
    list_filter = ('payment_method', 'status', RemovedOrderFilterSpec,)
    date_hierarchy = 'created'
    search_fields = ('user__email',)
    fieldsets = (
        (_('Order Info'), {
            'fields': (
                'order_no', 'fullname', 'phone',
                'total_amount', 'payment_method', 'status', 'created', 'visible'
            )
        }),
        (_('Transaction Verification'), {
            'fields': (
                'suspicious',
                'phone_verified_status', 'document_verified',
                'date_joined', 'last_login_count', 'last_purchased', 'last_total',
                'max_price', 'average_price', 'total_order_count',
                'country', 'accept_language', 'user_agent', 'message'
            )
        }),
    )
    readonly_fields = (
        'order_no', 'fullname', 'phone',
        'total_amount', 'total_list_price', 'payment_method', 'currency', 'created',
        'phone_verified_status', 'document_verified',
        'date_joined', 'last_login_count', 'last_purchased', 'last_total',
        'max_price', 'average_price', 'total_order_count',
        'country', 'accept_language', 'user_agent', 'message'
    )
    inlines = [OrderProductInline, OrderPaymentInline]
    ordering = ['-created', ]

    class Media:
        js = ('js/admin/shop/order.js',)
        css = {
            'all': ('css/admin/shop/order.css',)
        }

    def get_queryset(self, request):
        return super(OrderAdmin, self).get_queryset(request) \
            .select_related('user', 'user__profile', 'parent')

    def save_model(self, request, obj, form, change):
        if not obj.id:
            obj.ip_address = get_ip(request)

        if not obj.user:
            obj.user = request.user

        if not obj.accept_language:
            obj.accept_language = request.META['HTTP_ACCEPT_LANGUAGE'] \
                if 'HTTP_ACCEPT_LANGUAGE' in request.META.keys() else _('No language set')

        if not obj.user_agent:
            obj.user_agent = request.META['HTTP_USER_AGENT']

        super(OrderAdmin, self).save_model(request, obj, form, change)

    """
    def response_change(self, request, obj):
        opts = self.model._meta
        preserved_filters = self.get_preserved_filters(request)

        msg_dict = {
            'name': opts.verbose_name,
            'obj': format_html('<a href="{}">{}</a>', urlquote(request.path), obj),
        }

        if '_verify' in request.POST:
            if obj.status in [models.Order.STATUS_CHOICES.payment_completed, models.Order.STATUS_CHOICES.under_review]:
                obj.status = obj.STATUS_CHOICES.payment_verified
                obj.save()

            msg = format_html(
                _('Payment was verified successfully. You may edit it again below.'),
                **msg_dict
            )
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = request.path
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)

        elif '_unverify' in request.POST:
            if obj.status in [models.Order.STATUS_CHOICES.payment_verified]:
                obj.status = obj.STATUS_CHOICES.under_review
                obj.save()

            msg = format_html(
                _('Payment was unverified successfully. You may edit it again below.'),
                **msg_dict
            )
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = request.path
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)

        elif '_send-codes' in request.POST:
            order_products = models.OrderProduct.objects.filter(order=obj) \
                .select_related('order') \
                .prefetch_related('codes')

            # 1. Check stock accountability
            out_of_stock = {}

            for order_product in order_products:
                num_vouchers = models.Voucher.objects \
                    .select_related('product') \
                    .filter(product__code=order_product.code, status=models.Voucher.STATUS_CHOICES.purchased) \
                    .count()

                if order_product.quantity > num_vouchers:
                    out_of_stock[order_product.name] = order_product.quantity - num_vouchers

            if out_of_stock:
                out_of_stock_item = []

                for key, value in out_of_stock.items():
                    out_of_stock_item.append(_(' {}: {} ea').format(key, value))

                out_of_stock_message = ''.join(out_of_stock_item)

                msg = format_html(
                    _('Out of stock! {}').format(out_of_stock_message),
                    **msg_dict
                )
                self.message_user(request, msg, messages.ERROR)
                redirect_url = request.path
                redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts},
                                                     redirect_url)
                return HttpResponseRedirect(redirect_url)

            # 2. Check duplicate sent
            duplicates = {}

            for order_product in order_products:
                num_vouchers = order_product.codes.filter(revoked=False).count()

                if num_vouchers:
                    duplicates[order_product.name] = num_vouchers

            if duplicates:
                duplicates_item = []

                for key, value in duplicates.items():
                    duplicates_item.append(_(' {}: {} ea').format(key, value))

                duplicates_message = ''.join(duplicates_item)

                msg = format_html(
                    _('Already sent! {}').format(duplicates_message),
                    **msg_dict
                )
                self.message_user(request, msg, messages.ERROR)
                redirect_url = request.path
                redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts},
                                                     redirect_url)
                return HttpResponseRedirect(redirect_url)

            # 3. Mark vouchers as sold and Associate vouchers with order products
            # TODO: Orphans(marked as sold, but not copied)?
            for order_product in order_products:
                vouchers = models.Voucher.objects \
                               .select_related('product') \
                               .filter(product__code=order_product.code,
                                       status=models.Voucher.STATUS_CHOICES.purchased)[:order_product.quantity]

                # Mark as sold
                # NOTE: Cannot update a query once a slice has been taken.
                voucher_pk = list(map(lambda x: x.id, vouchers))

                models.Voucher.objects.filter(pk__in=voucher_pk).update(status=models.Voucher.STATUS_CHOICES.sold)

                # Associate them (Copy vouchers)
                order_product_voucher_list = []

                for voucher in vouchers:
                    order_product_voucher_list.append(models.OrderProductVoucher(
                        order_product=order_product,
                        voucher=voucher,
                        code=voucher.code,
                        remarks=voucher.remarks,
                        revoked=False,
                    ))

                models.OrderProductVoucher.objects.bulk_create(order_product_voucher_list)

            # 4. Update transaction verification data
            obj.user.profile.last_purchased = now()
            if obj.total_selling_price > obj.user.profile.max_price:
                obj.user.profile.max_price = obj.total_selling_price

            obj.user.profile.average_price = (obj.user.profile.average_price * obj.user.profile.total_order_count
                                              + obj.total_selling_price) / (obj.user.profile.total_order_count + 1)
            obj.user.profile.total_order_count += 1

            obj.user.profile.save()

            # 5. Change order status
            obj.status = obj.STATUS_CHOICES.shipped
            obj.save()

            msg = format_html(
                _('The voucher codes were sent successfully. You may edit it again below.'),
                **msg_dict
            )
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = request.path
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)

        elif '_send-refund' in request.POST:
            if obj.status in [models.Order.STATUS_CHOICES.refund_pending]:
                obj.status = obj.STATUS_CHOICES.refunded2
                obj.parent.status = obj.STATUS_CHOICES.refunded1
                obj.parent.save()
                obj.save()

            msg = format_html(
                _('Payment was refunded successfully. You may edit it again below.'),
                **msg_dict
            )
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = request.path
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)

        else:
            return super(OrderAdmin, self).response_change(request, obj)
    """

    def phone(self, instance):
        return instance.user.profile.phone

    phone.short_description = _('phone number')

    def date_joined(self, instance):
        delta = now() - instance.user.date_joined
        if delta < timedelta(days=member_settings.DAYS_DATE_JOINED):
            return mark_safe('{} <strong style="color:red;">{}  days</strong>'
                             .format(instance.user.date_joined, delta.days))
        else:
            return instance.user.date_joined

    date_joined.short_description = _('date joined')

    def phone_verified_status(self, instance):
        if instance.user.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified:
            return mark_safe('<img src="/assets/admin/img/icon-yes.svg" alt="verified">')
        elif instance.user.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.unverified:
            return mark_safe('<img src="/assets/admin/img/icon-no.svg" alt="unverified">')
        elif instance.user.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.revoked:
            return mark_safe('<img src="/assets/admin/img/icon-unknown.svg" alt="revoked">')

    phone_verified_status.short_description = _('phone verified')

    def document_verified(self, instance):
        if instance.user.profile.document_verified:
            return mark_safe('<img src="/assets/admin/img/icon-yes.svg" alt="True">')
        else:
            return mark_safe('<img src="/assets/admin/img/icon-no.svg" alt="False">')

    document_verified.short_description = _('document verified')

    def total_order_count(self, instance):
        return instance.user.profile.total_order_count

    total_order_count.short_description = _('total order count')

    def last_purchased(self, instance):
        return instance.user.profile.last_purchased

    last_purchased.short_description = _('last purchased date')

    def max_price(self, instance):
        return currency_filter(instance.user.profile.max_price, instance.currency)

    max_price.short_description = _('max price')

    def average_price(self, instance):
        return currency_filter(instance.user.profile.average_price, instance.currency)

    average_price.short_description = _('average price')

    def last_total(self, instance):
        result = models.Order.objects \
            .filter(user__pk=instance.user.pk,
                    is_removed=False,
                    modified__gte=make_aware(
                        localtime().today() - timedelta(days=shop_settings.RECENT_ACCUMULATIVE_DAYS))
                    ) \
            .exclude(status=0) \
            .aggregate(last_total=Sum('total_list_price'))
        total = result['last_total'] if result['last_total'] else Decimal('0.00')

        if total + instance.total_list_price > shop_settings.RECENT_ACCUMULATIVE_TOTAL:
            return mark_safe('<strong style="color:red;">{}</strong>'.format(currency_filter(total, instance.currency)))
        else:
            return total

    last_total.short_description = _('last total')

    def last_login_count(self, instance):
        result = LoginLog.objects \
            .select_related('user') \
            .filter(ip_address=instance.ip_address,
                    created__gte=make_aware(localtime().today() - timedelta(days=shop_settings.RECENT_LOGIN_IP_DAYS))) \
            .exclude(user__id=instance.user.pk) \
            .annotate(Count('user_id', distinct=True))

        if result:
            return mark_safe('''
            <strong style="color:red;">
                <a href="{}?q={}">{}</a>
            </strong>
            '''.format(reverse('admin:member_loginlog_changelist'), instance.ip_address, result[0].user_id__count))
        else:
            return '0'

    last_login_count.short_description = _('last login count')

    def total_amount(self, instance):
        return currency_filter(instance.total_selling_price, instance.currency)

    total_amount.short_description = _('total price')

    def country(self, instance):
        # https://dev.maxmind.com/geoip/geoip2/geolite2/
        # http://www.famfamfam.com/lab/icons/flags/

        if instance.ip_address not in ['127.0.0.1']:
            try:
                country = GeoIP2().country(instance.ip_address)
                return mark_safe('<img src="/assets/images/shop/flag/{}.png" alt="{}">'
                                 .format(country['country_code'].lower(), country['country_name']))
            except AddressNotFoundError:
                return instance.ip_address

        return 'localhost'

    country.short_description = _('country')


class VoucherAdmin(ImportMixin, admin.ModelAdmin):
    resource_class = VoucherResource
    formats = (base_formats.CSV,)

    list_display = ('status', 'product_name_subtitle', 'code_truncated', 'remarks', 'created', 'modified')
    list_select_related = ('product',)
    list_display_links = ('product_name_subtitle', 'code_truncated',)
    list_filter = ('status', VoucherProductCategoryFilterSpec, VoucherListPriceFilterSpec)
    search_fields = ('code',)
    date_hierarchy = 'created'
    fields = ('product_name_subtitle', 'product', 'code', 'remarks', 'status', 'created')
    readonly_fields = ('product_name_subtitle', 'is_removed', 'created')
    inlines = [OrderProductVoucherInline, NaverOrderProductVoucherInline]

    change_list_template = 'admin/import_export/voucher_change_list_import.html'

    actions = ['make_purchased', 'make_sold', 'make_revoked']

    order = ['-created']

    def code_truncated(self, instance):
        return truncatechars(instance.code, 8)

    code_truncated.short_description = _('code')

    def make_purchased(self, request, queryset):
        rows_updated = queryset.update(status=models.Voucher.STATUS_CHOICES.purchased)

        if rows_updated == 1:
            message_bit = _('1 voucher was')
        else:
            message_bit = _('{} vouchers were').format(rows_updated)
        self.message_user(request, _('{} successfully marked as purchased.').format(message_bit))

    make_purchased.short_description = _('Mark selected vouchers as purchased')

    def make_sold(self, request, queryset):
        rows_updated = queryset.update(status=models.Voucher.STATUS_CHOICES.sold)

        if rows_updated == 1:
            message_bit = _('1 voucher was')
        else:
            message_bit = _('{} vouchers were').format(rows_updated)
        self.message_user(request, _('{} successfully marked as sold.').format(message_bit))

    make_sold.short_description = _('Mark selected vouchers as sold')

    def make_revoked(self, request, queryset):
        rows_updated = queryset.update(status=models.Voucher.STATUS_CHOICES.revoked)

        if rows_updated == 1:
            message_bit = _('1 voucher was')
        else:
            message_bit = _('{} vouchers were').format(rows_updated)
        self.message_user(request, _('{} successfully marked as revoked.').format(message_bit))

    make_revoked.short_description = _('Mark selected vouchers as revoked')

    def product_name_subtitle(self, obj):
        return '{} {}'.format(obj.product.name, obj.product.subtitle)

    product_name_subtitle.short_description = _('product name')


class OrderProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'subtitle', 'selling_price', 'quantity', 'subtotal', 'order_no', 'created')
    list_display_links = ('name', 'subtitle')
    list_select_related = ('order', 'order__user')
    search_fields = ('order__order_no',)
    date_hierarchy = 'created'
    fields = ('order_no', 'name', 'code', 'list_price', 'selling_price', 'quantity')
    readonly_fields = ('order', 'order_no', 'name', 'code', 'list_price', 'selling_price', 'quantity')
    inlines = [OrderProductVoucherInline]
    order = ['-created']

    def get_queryset(self, request):
        return super(OrderProductAdmin, self).get_queryset(request) \
            .select_related('order', 'order__user')

    def order_no(self, obj):
        return obj.order.order_no

    order_no.short_description = _('order no')


class OrderProductVoucherAdmin(admin.ModelAdmin):
    list_display = ('revoked', 'product_name_subtitle', 'code', 'remarks', 'order_no', 'created')
    list_display_links = ('product_name_subtitle', 'code',)
    list_select_related = ('order_product', 'order_product__order')
    search_fields = ('order_product__order__order_no', 'code')
    list_filter = ('revoked',)
    fields = ('order_no', 'product_name_subtitle', 'code_truncated', 'remarks', 'created')
    readonly_fields = ('order_no', 'product_name_subtitle', 'code_truncated', 'remarks', 'created',)
    order = ['-created']

    def order_no(self, obj):
        return obj.order_product.order.order_no

    order_no.short_description = _('order no')

    def product_name_subtitle(self, obj):
        return '{} {}'.format(obj.order_product.name, obj.order_product.subtitle)

    product_name_subtitle.short_description = _('product name')

    def code_truncated(self, instance):
        return truncatechars(instance.code, 8)

    code_truncated.short_description = _('code')


class NaverOrderAdmin(admin.ModelAdmin):
    logger = logging.getLogger(__name__)
    # change_form_template = "admin/shop/order_change_form.html"

    list_display = (
        'order_no', 'fullname',
        'total_amount', 'payment_method',
        'status', 'created', 'is_removed')
    list_filter = ('payment_method', 'status', RemovedOrderFilterSpec,)
    date_hierarchy = 'created'
    search_fields = ('fullname',)
    fields = (
        'order_no', 'fullname', 'phone',
        'total_list_price', 'total_selling_price', 'payment_method', 'status', 'message'
    )
    readonly_fields = (
        'order_no', 'fullname', 'phone',
        'total_list_price', 'total_selling_price', 'payment_method',  # 'status'
    )

    # inlines = [OrderProductInline, OrderPaymentInline]
    ordering = ['-created', ]

    def total_amount(self, instance):
        return currency_filter(instance.total_selling_price, "KRW")

    total_amount.short_description = _('total price')


class NaverOrderProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'subtitle', 'selling_price', 'quantity', 'subtotal', 'order_no', 'created')
    list_display_links = ('name', 'subtitle')
    list_select_related = ('order',)
    search_fields = ('order__order_no',)
    date_hierarchy = 'created'
    fields = ('order_no', 'name', 'code', 'list_price', 'selling_price', 'quantity')
    readonly_fields = ('order', 'order_no', 'name', 'code', 'list_price', 'selling_price', 'quantity')
    inlines = [NaverOrderProductVoucherInline]
    order = ['-created']

    def get_queryset(self, request):
        return super(NaverOrderProductAdmin, self).get_queryset(request) \
            .select_related('order')

    def order_no(self, obj):
        return obj.order.order_no

    order_no.short_description = _('order no')


class NaverOrderProductVoucherAdmin(admin.ModelAdmin):
    list_display = ('revoked', 'product_name_subtitle', 'code', 'remarks', 'order_no', 'created')
    list_display_links = ('product_name_subtitle', 'code',)
    list_select_related = ('order_product', 'order_product__order')
    search_fields = ('order_product__order__order_no', 'code')
    list_filter = ('revoked',)
    fields = ('order_no', 'product_name_subtitle', 'code_truncated', 'remarks', 'created')
    readonly_fields = ('order_no', 'product_name_subtitle', 'code_truncated', 'remarks', 'created',)
    order = ['-created']

    def order_no(self, obj):
        return obj.order_product.order.order_no

    order_no.short_description = _('order no')

    def product_name_subtitle(self, obj):
        return '{} {}'.format(obj.order_product.name, obj.order_product.subtitle)

    product_name_subtitle.short_description = _('product name')

    def code_truncated(self, instance):
        return truncatechars(instance.code, 8)

    code_truncated.short_description = _('code')


class LegacyOrderAdmin(admin.ModelAdmin):
    pass


class LegacyOrderProductAdmin(admin.ModelAdmin):
    pass


class LegacyCustomerAdmin(admin.ModelAdmin):
    pass


class NaverAdvertisementLogAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'rank', 'campaign_type', 'media', 'query',
                    'ip_address', 'country', 'ip_address_count', 'created')
    search_fields = ('keyword', 'ip_address')
    readonly_fields = ('keyword', 'rank', 'campaign_type', 'media', 'query',
                       'ip_address', 'ad_group', 'ad', 'keyword_id', 'user_agent')
    list_filter = ('campaign_type', 'media')
    date_hierarchy = 'created'

    ordering = ['-created']

    def changelist_view(self, request, extra_context=None):
        response = super(NaverAdvertisementLogAdmin, self).changelist_view(request, extra_context)
        try:
            # Final queryset to be rendered on the page after pagination.
            _cl = response.context_data['cl']

            qs = _cl.result_list._clone()

            # Mysql 5.5 does not support subquery with LIMIT
            # Fetch all the IP addresses on that page
            ips = list(set([obj.ip_address for obj in qs]))
            result_qs = models.NaverAdvertisementLog.objects \
                .values('ip_address') \
                .filter(ip_address__in=ips) \
                .annotate(ip_address_count=Count('ip_address'))

            result = {_r['ip_address']: _r['ip_address_count'] for _r in result_qs}

            setattr(self, '_ip_addr_count', result)
        except:
            pass
        return response

    def country(self, instance):
        # https://dev.maxmind.com/geoip/geoip2/geolite2/
        # http://www.famfamfam.com/lab/icons/flags/

        if instance.ip_address not in ['127.0.0.1']:
            try:
                country = GeoIP2().country(instance.ip_address)
                return mark_safe('<img src="/assets/images/shop/flag/{}.png" alt="{}">'
                                 .format(country['country_code'].lower(), country['country_name']))
            except AddressNotFoundError:
                return instance.ip_address

        return 'localhost'

    country.short_description = _('country')

    def ip_address_count(self, instance):
        return self._ip_addr_count.get(instance.ip_address)

    ip_address_count.short_description = _('IP Address Count')


class MileageLogAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'mileage', 'created', 'order')
    list_select_related = ('user', 'user__profile', 'order')
    search_fields = ('user__email',)
    readonly_fields = ('is_removed', 'created')
    date_hierarchy = 'created'
    ordering = ['-created']

    raw_id_fields = ('user', 'order')

    def full_name(self, instance):
        return '{} / {} / {}'.format(instance.user.profile.full_name, instance.user.email, instance.user.profile.phone)

    full_name.short_description = _('Full name')


class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('title', 'bank_account', 'amount', 'created')
    search_fields = ('bank_account', 'amount')
    date_hierarchy = 'created'
    ordering = ['-created']

    inlines = [PurchaseOrderPaymentInline, ]

    change_form_template = "admin/shop/purchaseorder_change_form.html"

    def response_change(self, request, obj):
        opts = self.model._meta
        preserved_filters = self.get_preserved_filters(request)

        msg_dict = {
            'name': opts.verbose_name,
            'obj': format_html('<a href="{}">{}</a>', urlquote(request.path), obj),
        }

        if '_send_payment_notification' in request.POST:
            email_string = ['입금액 / 입금일시\n', '----\n']

            for p in obj.payments.all():
                email_string.append('{:,.0f} / {}\n'.format(p.amount, _date(p.created, 'Y-m-d H:i')))

            print(''.join(email_string))

            send_notification_email.delay(
                '[핀코인] 입금완료 {}'.format(obj.bank_account),
                'dummy',
                settings.EMAIL_JONGHWA,
                [settings.EMAIL_HAN, ],
                _linebreaks(''.join(email_string)),
            )

            msg = format_html(
                _('Payment notification email sent'),
                **msg_dict
            )
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = request.path
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)
        else:
            return super(PurchaseOrderAdmin, self).response_change(request, obj)


admin.site.site_header = _('PINCOIN admin')
admin.site.site_title = _('PINCOIN admin')
admin.site.index_title = _('PINCOIN administration')

admin.site.register(models.Store, StoreAdmin)
admin.site.register(models.Product, ProductAdmin)
admin.site.register(models.ProductList, ProductListAdmin)
admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Order, OrderAdmin)
admin.site.register(models.OrderProduct, OrderProductAdmin)
admin.site.register(models.Voucher, VoucherAdmin)
admin.site.register(models.OrderProductVoucher, OrderProductVoucherAdmin)
admin.site.register(models.NaverOrder, NaverOrderAdmin)
admin.site.register(models.NaverOrderProduct, NaverOrderProductAdmin)
admin.site.register(models.NaverOrderProductVoucher, NaverOrderProductVoucherAdmin)
admin.site.register(models.LegacyCustomer, LegacyCustomerAdmin)
admin.site.register(models.LegacyOrder, LegacyOrderAdmin)
admin.site.register(models.LegacyOrderProduct, LegacyOrderProductAdmin)
admin.site.register(models.NaverAdvertisementLog, NaverAdvertisementLogAdmin)
admin.site.register(models.MileageLog, MileageLogAdmin)
admin.site.register(models.PurchaseOrder, PurchaseOrderAdmin)
