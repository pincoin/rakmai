import json
import logging
import re
from decimal import Decimal

import requests
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Q
from django.http import (
    Http404, JsonResponse, HttpResponseRedirect, HttpResponse
)
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import (
    now, timedelta, localtime, make_aware
)
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from ipware import get_client_ip
from rest_framework import (
    status, views
)
from rest_framework.response import Response
from weasyprint import HTML

from member.models import Profile
from rakmai.viewmixins import HostRestrict
from rakmai.viewmixins import PageableMixin
from shop import models
from shop import settings as shop_settings
from shop.helpers import Cart
from shop.tasks import (
    send_notification_email, send_notification_line
)
from shop.utils import send_vouchers
from shop.viewmixins import StoreContextMixin
from . import forms
from .serializers import (
    IamportCallbackSerializer, BootpayCallbackSerializer
)

if settings.DEBUG:
    from .forms2_debug import (
        OrderForm, RefundForm
    )
else:
    from .forms2 import (
        OrderForm, RefundForm
    )


class HomeView(StoreContextMixin, HostRestrict, generic.TemplateView):
    logger = logging.getLogger(__name__)
    sub_domain = 'card'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['page_title'] = _('1st online shop')
        return context

    def get_template_names(self):
        return 'card/{}/home.html'.format(self.store.theme)


class ProductCategoryView(StoreContextMixin, HostRestrict, generic.ListView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    context_object_name = 'products'

    def dispatch(self, *args, **kwargs):
        cache_key = 'card.views.ProductCategoryView.dispatch({})'.format(self.kwargs['slug'])
        cache_time = settings.CACHES['default']['TIMEOUT']

        self.category = cache.get(cache_key)

        if not self.category:
            try:
                self.category = models.Category.objects.get(slug=self.kwargs['slug'], pg=True)
                cache.set(cache_key, self.category, cache_time)
            except models.Category.DoesNotExist:
                raise Http404('No category matches the given query.')

        return super(ProductCategoryView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        queryset = models.Product.objects \
            .store(self.kwargs['store']) \
            .enabled() \
            .select_related('category', 'store') \
            .filter(pg=True, category__in=models.Category.objects
                    .filter(slug=self.kwargs['slug'], pg=True)
                    .get_descendants(include_self=True))

        queryset = queryset.order_by('position')

        if not (shop_settings.OPENING_TIME <= localtime().now().hour < shop_settings.CLOSING_TIME) \
                and self.category.title in shop_settings.UNAVAILABLE_NIGHT_PRODUCTS:
            for p in queryset:
                p.stock = models.Product.STOCK_CHOICES.sold_out

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProductCategoryView, self).get_context_data(**kwargs)
        context['page_title'] = _('Products By Categories {}').format(self.kwargs['slug'])
        context['category'] = self.category
        context['og_image'] = self.category.thumbnail.url if self.category.thumbnail else None
        context['night_order'] = True \
            if not (shop_settings.OPENING_TIME <= localtime().now().hour < shop_settings.CLOSING_TIME) \
               and self.category.title in shop_settings.UNAVAILABLE_NIGHT_PRODUCTS \
            else False
        return context

    def get_template_names(self):
        return 'card/{}/product_list.html'.format(self.store.theme)


class ProductListView(PageableMixin, StoreContextMixin, HostRestrict, generic.ListView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    context_object_name = 'products'
    product_search_form_class = forms.ProductSearchForm

    def get_queryset(self):
        queryset = models.Product.objects \
            .store(self.kwargs['store']) \
            .enabled() \
            .filter(pg=True) \
            .select_related('category', 'store')

        form = self.product_search_form_class(self.request.GET)
        if form.is_valid() and form.cleaned_data['q']:
            q = form.cleaned_data['q']
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q) |
                Q(category__description__icontains=q) |
                Q(category__description1__icontains=q)
            )

        queryset = queryset.order_by('position')

        if not (shop_settings.OPENING_TIME <= localtime().now().hour < shop_settings.CLOSING_TIME):
            for p in queryset:
                if p.name in shop_settings.UNAVAILABLE_NIGHT_PRODUCTS:
                    p.stock = models.Product.STOCK_CHOICES.sold_out

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProductListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Products')
        return context

    def get_template_names(self):
        return 'card/{}/product_list.html'.format(self.store.theme)


class ProductDetailView(StoreContextMixin, HostRestrict, generic.DetailView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    context_object_name = 'product'

    def get_object(self, queryset=None):
        cache_key = 'card.viewmixins.StoreContextMixin.get_object({})'.format(self.kwargs['pk'])
        cache_time = settings.CACHES['default']['TIMEOUT']

        o = cache.get(cache_key)

        if not o:
            o = super(ProductDetailView, self).get_object(queryset)
            cache.set(cache_key, o, cache_time)

        return o

    def get_queryset(self):
        queryset = models.Product.objects \
            .enabled() \
            .available() \
            .filter(pg=True) \
            .select_related('category', 'store') \
            .store(self.kwargs['store'])

        if not (shop_settings.OPENING_TIME <= localtime().now().hour < shop_settings.CLOSING_TIME):
            queryset = queryset.exclude(name__in=shop_settings.UNAVAILABLE_NIGHT_PRODUCTS)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        context['page_title'] = '{} {}'.format(self.object.name, self.object.subtitle)
        context['og_image'] = self.object.category.thumbnail.url if self.object.category.thumbnail else None
        context['product_absolute_url'] = self.request.build_absolute_uri(
            reverse('card:product-detail', args=(self.object.store.code, self.object.pk, self.object.code)))
        return context

    def get_template_names(self):
        return 'card/{}/product_detail.html'.format(self.store.theme)


class CartView(LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.CreateView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    form_class = OrderForm

    def get_context_data(self, **kwargs):
        context = super(CartView, self).get_context_data(**kwargs)
        context['page_title'] = _('Cart')

        try:
            member = Profile.objects.select_related('user').get(user__pk=self.request.user.id)
            context['member'] = member
        except Profile.DoesNotExist:
            raise Http404('Your profile does not exist.')

        return context

    def get_form_kwargs(self):
        kwargs = super(CartView, self).get_form_kwargs()
        self.cart = Cart(self.request.session, shop_settings.CARD_CART_SESSION_KEY)
        kwargs['cart'] = self.cart
        kwargs['request'] = self.request
        return kwargs

    def get_template_names(self):
        return 'card/{}/cart.html'.format(self.store.theme)

    def form_valid(self, form):
        order_product_list = []

        total_list_price = 0
        total_selling_price = 0

        # 1. Construct order products
        for item in self.cart.items:
            order_product_list.append(models.OrderProduct(
                order=None,
                name=item.product.name,
                subtitle=item.product.subtitle,
                code=item.product.code,
                list_price=item.product.list_price,
                selling_price=item.product.pg_selling_price,
                quantity=item.quantity,
            ))

            total_list_price += item.product.list_price * item.quantity
            total_selling_price += item.product.pg_selling_price * item.quantity

        # 2. Setup order meta information
        form.instance.ip_address = get_client_ip(self.request)[0]
        form.instance.user = self.request.user

        pattern = re.compile(r'^[가-힣]+$')  # Only Hangul

        if pattern.match(self.request.user.last_name) and pattern.match(self.request.user.first_name):
            form.instance.fullname = '{}{}'.format(self.request.user.last_name, self.request.user.first_name)
        else:
            form.instance.fullname = '{} {}'.format(self.request.user.first_name, self.request.user.last_name)

        form.instance.accept_language = self.request.META['HTTP_ACCEPT_LANGUAGE'] \
            if 'HTTP_ACCEPT_LANGUAGE' in self.request.META.keys() else _('No language set')
        form.instance.user_agent = self.request.META['HTTP_USER_AGENT']
        form.instance.total_list_price = total_list_price

        if form.instance.payment_method == models.Order.PAYMENT_METHOD_CHOICES.phone_bill:
            form.instance.total_selling_price = total_selling_price * Decimal(1.09)
        else:
            form.instance.total_selling_price = total_selling_price

        # Restrict currency according to payment method
        form.instance.currency = 'KRW'

        response = super(CartView, self).form_valid(form)

        # 3. Associate order
        for product in order_product_list:
            product.order = self.object

        models.OrderProduct.objects.bulk_create(order_product_list)

        # 4. Destroy cart session
        self.cart.clear()

        # 5. Send notification email
        html_message = render_to_string('card/{}/email/order_complete.html'.format(self.store.theme),
                                        {'order': self.object, 'store_code': self.store.code})

        send_notification_email.delay(
            _('[site] Order complete: {}').format(self.object.order_no),
            'dummy',
            settings.EMAIL_NO_REPLY,
            [self.request.user.email],
            html_message,
        )

        return response

    def get_success_url(self):
        return reverse('card:order-detail', args=(self.store.code, self.object.order_no))


class CartAddView(HostRestrict, generic.FormView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    form_class = forms.ProductAddCartForm

    def form_valid(self, form):
        data = {}

        product = models.Product.objects \
            .enabled() \
            .available() \
            .get(pk=form.cleaned_data['product_pk'])

        if product:
            cart = Cart(self.request.session, shop_settings.CARD_CART_SESSION_KEY)
            cart.add(product=product, price=product.pg_selling_price, quantity=form.cleaned_data['quantity'])
            data = cart.items_json

        return JsonResponse(data)

    def form_invalid(self, form):
        return JsonResponse({
            'status': 'false',
            'message': 'Bad Request'
        }, status=400)


class CartRemoveView(HostRestrict, generic.FormView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    form_class = forms.ProductDeleteCartForm

    def form_valid(self, form):
        cart = Cart(self.request.session, shop_settings.CARD_CART_SESSION_KEY)
        cart.remove(form.cleaned_data['product_pk'])
        data = cart.items_json

        return JsonResponse(data)

    def form_invalid(self, form):
        print(form.errors)
        return JsonResponse({
            'status': 'false',
            'message': 'Bad Request'
        }, status=400)


class CartDeleteView(HostRestrict, generic.FormView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    form_class = forms.ProductDeleteCartForm

    def form_valid(self, form):
        cart = Cart(self.request.session, shop_settings.CARD_CART_SESSION_KEY)
        cart.delete(form.cleaned_data['product_pk'])
        data = cart.items_json

        return JsonResponse(data)

    def form_invalid(self, form):
        print(form.errors)
        return JsonResponse({
            'status': 'false',
            'message': 'Bad Request'
        }, status=400)


class CartClearView(HostRestrict, generic.View):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'

    def post(self, request, store):
        if request.is_ajax():
            cart = Cart(request.session, shop_settings.CARD_CART_SESSION_KEY)
            cart.clear()
            return JsonResponse({})


class CartSetQuantityView(HostRestrict, generic.FormView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    form_class = forms.ProductAddCartForm

    def form_valid(self, form):
        data = {}

        product = models.Product.objects \
            .enabled() \
            .available() \
            .get(pk=form.cleaned_data['product_pk'])

        if product:
            cart = Cart(self.request.session, shop_settings.CARD_CART_SESSION_KEY)
            cart.set_quantity(product=product, quantity=form.cleaned_data['quantity'])
            data = cart.items_json

        return JsonResponse(data)

    def form_invalid(self, form):
        return JsonResponse({
            'status': 'false',
            'message': 'Bad Request'
        }, status=400)


class CartItemsView(HostRestrict, generic.FormView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    form_class = forms.DummyForm

    def form_valid(self, form):
        cart = Cart(self.request.session, shop_settings.CARD_CART_SESSION_KEY)
        data = cart.items_json

        return JsonResponse(data)

    def form_invalid(self, form):
        return JsonResponse({
            'status': 'false',
            'message': 'Bad Request'
        }, status=400)


class OrderListView(PageableMixin, LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.ListView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    context_object_name = 'orders'

    def get_queryset(self):
        return models.Order.objects \
            .valid(self.request.user) \
            .filter(payment_method__in=[models.Order.PAYMENT_METHOD_CHOICES.credit_card,
                                        models.Order.PAYMENT_METHOD_CHOICES.bank_transfer_pg,
                                        models.Order.PAYMENT_METHOD_CHOICES.virtual_account,
                                        models.Order.PAYMENT_METHOD_CHOICES.phone_bill]) \
            .order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(OrderListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Order History')
        context['under_review'] = models.Order.objects \
            .valid(self.request.user) \
            .filter(status=models.Order.STATUS_CHOICES.under_review,
                    payment_method__in=[models.Order.PAYMENT_METHOD_CHOICES.bank_transfer,
                                        models.Order.PAYMENT_METHOD_CHOICES.escrow]) \
            .exists()
        return context

    def get_template_names(self):
        return 'card/{}/order_list.html'.format(self.store.theme)


class OrderDetailView(LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.DetailView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    context_object_name = 'order'

    def get_object(self, queryset=None):
        # NOTE: This method is overridden because DetailView must be called with either an object pk or a slug.
        queryset = models.Order.objects \
            .valid(self.request.user) \
            .select_related('parent') \
            .prefetch_related('products', 'products__codes')
        return get_object_or_404(queryset, order_no=self.kwargs['uuid'])

    def get_context_data(self, **kwargs):
        context = super(OrderDetailView, self).get_context_data(**kwargs)
        context['page_title'] = _('Order Details - {}').format(self.object.order_no)

        context['store'] = self.store

        delta = now() - self.object.created

        no_refund_product = False

        for product in self.object.products.all():
            if product.name in ['구글기프트카드', ]:
                no_refund_product = True
                break

        context['show_confirm_order_button'] = self.object.status in [
            models.Order.STATUS_CHOICES.payment_pending,
            models.Order.STATUS_CHOICES.payment_completed,
            models.Order.STATUS_CHOICES.under_review,
        ]

        context['show_refund_order_button'] = (self.object.status in [
            models.Order.STATUS_CHOICES.payment_completed,
            models.Order.STATUS_CHOICES.under_review,
            models.Order.STATUS_CHOICES.payment_verified,
        ] and delta < timedelta(days=shop_settings.REFUNDABLE_DAYS)) \
                                              or (self.object.status in [
            models.Order.STATUS_CHOICES.shipped,
        ] and timedelta(hours=2) < delta < timedelta(days=shop_settings.REFUNDABLE_DAYS))

        if self.object.status in [
            models.Order.STATUS_CHOICES.payment_completed,
            models.Order.STATUS_CHOICES.under_review,
            models.Order.STATUS_CHOICES.payment_verified,
        ] and delta < timedelta(days=shop_settings.REFUNDABLE_DAYS):
            context['show_refund_order_button'] = True
        elif self.object.status in [models.Order.STATUS_CHOICES.shipped, ]:
            if not no_refund_product:
                if self.object.user.profile.total_order_count > 1:
                    context['show_refund_order_button'] = True
                elif timedelta(hours=2) < delta < timedelta(days=shop_settings.REFUNDABLE_DAYS):
                    context['show_refund_order_button'] = True
            else:
                context['show_refund_order_button'] = False

        context['show_delete_order_button'] = self.object.status in [
            models.Order.STATUS_CHOICES.payment_pending,
        ]

        context['show_hide_order_button'] = self.object.status in [
            models.Order.STATUS_CHOICES.shipped,
        ]

        context['show_voucher_list'] = self.object.status in [
            models.Order.STATUS_CHOICES.shipped,
            models.Order.STATUS_CHOICES.refund_requested,
            models.Order.STATUS_CHOICES.refunded1,  # original
        ]

        context['show_related_order'] = self.object.status in [
            models.Order.STATUS_CHOICES.refund_pending,
            models.Order.STATUS_CHOICES.refund_requested,
            models.Order.STATUS_CHOICES.refunded1,
            models.Order.STATUS_CHOICES.refunded2,
        ]

        context['iamport_user_code'] = settings.IAMPORT['user_code']
        context['iamport_callback_url'] = self.request.build_absolute_uri(
            reverse(settings.IAMPORT['callback_url'], args=(self.store.code,)))

        context['bootpay_user_code'] = settings.BOOTPAY['user_code']

        context['billgate_service_id'] = settings.BILLGATE['service_id']
        context['billgate_callback_url'] = self.request.build_absolute_uri(
            reverse(settings.BILLGATE['callback_url'], args=(self.store.code,)))

        context['total_amount'] = self.object.total_selling_price / Decimal(1.09) \
            if self.object.payment_method == models.Order.PAYMENT_METHOD_CHOICES.phone_bill \
            else self.object.total_selling_price
        context['service_charge'] = context['total_amount'] * Decimal(0.09) \
            if self.object.payment_method == models.Order.PAYMENT_METHOD_CHOICES.phone_bill \
            else 0

        return context

    def get_template_names(self):
        return 'card/{}/order_detail.html'.format(self.store.theme)


class OrderReceiptView(LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.DetailView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    context_object_name = 'order'

    def get_object(self, queryset=None):
        # NOTE: This method is overridden because DetailView must be called with either an object pk or a slug.
        queryset = models.Order.objects \
            .valid(self.request.user) \
            .shipped() \
            .select_related('parent') \
            .prefetch_related('products', 'products__codes')
        return get_object_or_404(queryset, order_no=self.kwargs['uuid'])

    def render_to_response(self, context, **response_kwargs):
        order = self.get_object()

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="{}.pdf"'.format(order.order_no)
        response['Content-Transfer-Encoding'] = 'binary'

        html_string = render_to_string('card/{}/order_receipt.html'.format(self.store.theme),
                                       {'order': order})

        html = HTML(string=html_string, base_url=self.request.build_absolute_uri())
        html.write_pdf(target=response)

        return response


class OrderAgainView(LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.FormView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    form_class = forms.DummyForm

    def form_valid(self, form):
        queryset = models.Order.objects \
            .valid(self.request.user) \
            .select_related('parent') \
            .prefetch_related('products', 'products__codes')

        order = get_object_or_404(queryset, order_no=self.kwargs['uuid'])

        self.cart = Cart(self.request.session, shop_settings.CART_SESSION_KEY)
        self.cart.clear()

        order_product_dict = {op.code: op.quantity for op in order.products.all()}

        products = models.Product.objects \
            .enabled() \
            .available() \
            .filter(code__in=order_product_dict.keys())

        for product in products:
            self.cart.add(product=product, price=product.pg_selling_price, quantity=order_product_dict[product.code])

        return super(OrderAgainView, self).form_valid(form)

    def form_invalid(self, form):
        return JsonResponse({
            'status': 'false',
            'message': 'Bad Request'
        }, status=400)

    def get_success_url(self):
        return reverse('card:cart', args=(self.store.code,))

    def get_template_names(self):
        return 'card/{}/error.html'.format(self.store.theme)


class OrderDeleteView(LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.DeleteView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    context_object_name = 'order'

    def get_object(self, queryset=None):
        # NOTE: This method is overridden because DetailView must be called with either an object pk or a slug.
        queryset = models.Order.objects.valid(self.request.user).pending().prefetch_related('products')
        return get_object_or_404(queryset, order_no=self.kwargs['uuid'])

    def get_success_url(self):
        return reverse('card:order-list', args=(self.store.code,))

    def get_template_names(self):
        return 'card/{}/order_confirm_delete.html'.format(self.store.code)


class OrderHideView(LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.UpdateView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    context_object_name = 'order'
    model = models.Order
    form_class = forms.OrderChangeForm

    def get_object(self, queryset=None):
        # NOTE: This method is overridden because DetailView must be called with either an object pk or a slug.
        queryset = models.Order.objects \
            .valid(self.request.user) \
            .shipped() \
            .select_related('parent') \
            .prefetch_related('products', 'products__codes')
        return get_object_or_404(queryset, order_no=self.kwargs['uuid'])

    def form_valid(self, form):
        form.instance.visible = models.Order.VISIBLE_CHOICES.hidden
        return super(OrderHideView, self).form_valid(form)

    def get_success_url(self):
        return reverse('card:order-list', args=(self.store.code,))

    def get_template_names(self):
        return 'card/{}/order_confirm_hide.html'.format(self.store.code)


class OrderRefundCreateView(LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.CreateView):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    form_class = RefundForm

    def dispatch(self, request, *args, **kwargs):
        queryset = models.Order.objects \
            .select_related('user__profile') \
            .prefetch_related('products', 'products__codes') \
            .filter(status__in=[models.Order.STATUS_CHOICES.payment_completed,
                                models.Order.STATUS_CHOICES.under_review,
                                models.Order.STATUS_CHOICES.payment_verified,
                                models.Order.STATUS_CHOICES.shipped],
                    created__gte=make_aware(localtime().today() - timedelta(days=shop_settings.REFUNDABLE_DAYS))) \
            .valid(self.request.user)

        self.order = get_object_or_404(queryset, order_no=self.kwargs['uuid'])

        return super(OrderRefundCreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(OrderRefundCreateView, self).get_context_data(**kwargs)
        context['page_title'] = _('Refund Payment - {}').format(self.order.order_no)
        context['order'] = self.order
        context['voucher_required'] = self.order.status in [models.Order.STATUS_CHOICES.shipped]
        context['message_required'] = self.order.payment_method in [
            models.Order.PAYMENT_METHOD_CHOICES.bank_transfer_pg,
            models.Order.PAYMENT_METHOD_CHOICES.virtual_account,
        ]

        return context

    def get_form_kwargs(self):
        kwargs = super(OrderRefundCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['voucher_required'] = self.order.status in [models.Order.STATUS_CHOICES.shipped]
        kwargs['message_required'] = self.order.payment_method in [
            models.Order.PAYMENT_METHOD_CHOICES.bank_transfer_pg,
            models.Order.PAYMENT_METHOD_CHOICES.virtual_account,
        ]

        return kwargs

    def form_valid(self, form):
        order_product_list = []
        total_revoke_selling_price = 0

        shipped = self.order.status == models.Order.STATUS_CHOICES.shipped

        # 1. Revoke vouchers when already shipped
        if shipped:
            product_order_voucher_pk = []
            voucher_pk = []

            for product in form.cleaned_data['order_product_queryset']:
                quantity = 0
                for code in product.codes.all():
                    if product.id in form.cleaned_data['voucher_dict'] \
                            and code.id in form.cleaned_data['voucher_dict'][product.id]:
                        total_revoke_selling_price += product.selling_price
                        product_order_voucher_pk.append(code.id)
                        voucher_pk.append(code.voucher.id)
                        quantity += 1
                if quantity > 0:
                    product.quantity = quantity
                    order_product_list.append(product)

            models.OrderProductVoucher.objects.filter(pk__in=product_order_voucher_pk).update(revoked=True)
            models.Voucher.objects.filter(pk__in=voucher_pk).update(status=models.Voucher.STATUS_CHOICES.purchased)

        # 2. Update old order
        self.order.status = models.Order.STATUS_CHOICES.refund_requested
        self.order.save()

        # 3. Create new refund order (refund amount)
        form.instance.total_selling_price = total_revoke_selling_price if shipped else self.order.total_selling_price
        form.instance.message = form.cleaned_data['message']

        form.instance.ip_address = get_client_ip(self.request)[0]
        form.instance.user = self.request.user

        pattern = re.compile(r'^[가-힣]+$')  # Only Hangul

        if pattern.match(self.request.user.last_name) and pattern.match(self.request.user.first_name):
            form.instance.fullname = '{}{}'.format(self.request.user.last_name, self.request.user.first_name)
        else:
            form.instance.fullname = '{} {}'.format(self.request.user.first_name, self.request.user.last_name)

        form.instance.accept_language = self.request.META['HTTP_ACCEPT_LANGUAGE'] \
            if 'HTTP_ACCEPT_LANGUAGE' in self.request.META.keys() else _('No language set')
        form.instance.user_agent = self.request.META['HTTP_USER_AGENT']
        form.instance.status = models.Order.STATUS_CHOICES.refund_pending
        form.instance.payment_method = self.order.payment_method
        form.instance.parent = self.order

        # 4. Update transaction verification data
        if shipped:
            self.order.user.profile.total_order_count -= 1
            self.order.user.profile.save()

        response = super(OrderRefundCreateView, self).form_valid(form)

        # 5. Refund Order Products for display
        if shipped:
            for order_product in order_product_list:
                order_product.pk = None
                order_product.order = self.object
        else:
            for order_product in self.order.products.all():
                order_product.pk = None
                order_product.order = self.object

                order_product_list.append(order_product)

        models.OrderProduct.objects.bulk_create(order_product_list)

        return response

    def get_template_names(self):
        return 'card/{}/refund_create.html'.format(self.store.theme)

    def get_success_url(self):
        return reverse('card:order-detail', args=(self.store.code, self.object.order_no))


class CurrencyUpdateView(HostRestrict, generic.edit.FormMixin, generic.View):
    logger = logging.getLogger(__name__)

    sub_domain = 'card'
    form_class = forms.CurrencyForm

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        redirect_to = self.request.META.get('HTTP_REFERER')
        self.request.session['currency_code'] = form.cleaned_data['currency_code']
        return HttpResponseRedirect(redirect_to)

    def form_invalid(self, form):
        return HttpResponseRedirect('/')


class IamportCallbackView(StoreContextMixin, HostRestrict, views.APIView):
    logger = logging.getLogger(__name__)
    sub_domain = 'card'

    def get_access_token(self):
        response = requests.post(
            '{}/users/getToken'.format(settings.IAMPORT['api_url']),
            data=json.dumps({
                'imp_key': settings.IAMPORT['api_key'],
                'imp_secret': settings.IAMPORT['secret'],
            }),
            headers={
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache',
            })

        if response.status_code == requests.codes.ok:
            result = response.json()
            if result['code'] == 0:
                return result['response']['access_token']

        return None

    def find(self, imp_uid, token=None):
        if not token:
            token = self.get_access_token()

        response = requests.get(
            '{}payments/{}'.format(settings.IAMPORT['api_url'], imp_uid),
            headers={
                "Authorization": token
            })

        if response.status_code == requests.codes.ok:
            result = response.json()
            if result['code'] == 0:
                return result['response']

        return None

    def get(self, request, store, format=None):
        return Response(None)

    def post(self, request, store, format=None):
        serializer = IamportCallbackSerializer(data=request.data)

        if serializer.is_valid():
            response = self.find(request.data['imp_uid'])

            if response \
                    and response['merchant_uid'] == request.data['merchant_uid'] \
                    and response['apply_num'] == request.data['apply_num'] \
                    and response['amount'] == int(request.data['paid_amount']):

                order = models.Order.objects \
                    .select_related('user', 'user__profile') \
                    .get(order_no=response['merchant_uid'])

                if order.user.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified \
                        and order.user.profile.full_name == order.fullname:
                    if order.total_selling_price == Decimal(response['amount']):
                        if send_vouchers(order):
                            return Response(serializer.data, status=status.HTTP_200_OK)
                        else:
                            # failure
                            order.status = models.Order.STATUS_CHOICES.payment_completed
                            order.save()
                            send_notification_line.delay(_('Failure: credit card 1'))
                            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
                    else:
                        # invalid paid amount
                        order.status = models.Order.STATUS_CHOICES.voided
                        order.save()
                        send_notification_line.delay(_('Failure: credit card 2'))
                else:
                    # invalid user
                    order.status = models.Order.STATUS_CHOICES.voided
                    order.save()
                    send_notification_line.delay(_('Failure: credit card 3'))

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BootpayCallbackView(StoreContextMixin, HostRestrict, views.APIView):
    logger = logging.getLogger(__name__)
    sub_domain = 'card'

    def get_access_token(self):
        response = requests.post(
            '{}/request/token'.format(settings.BOOTPAY['api_url']),
            data=json.dumps({
                'application_id': settings.BOOTPAY['api_key'],
                'private_key': settings.BOOTPAY['secret'],
            }),
            headers={
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache',
            })

        if response.status_code == requests.codes.ok:
            result = response.json()
            if result['code'] == 0:
                return result['data']['token']

        return None

    def find(self, receipt_id, token=None):
        if not token:
            token = self.get_access_token()

        response = requests.get(
            '{}/receipt/{}'.format(settings.BOOTPAY['api_url'], receipt_id),
            headers={
                "Authorization": token
            })

        if response.status_code == requests.codes.ok:
            result = response.json()
            if result['code'] == 0:
                return result['data']

        return None

    def get(self, request, store, format=None):
        return Response(None)

    def post(self, request, store, format=None):
        serializer = BootpayCallbackSerializer(data=request.data)

        if serializer.is_valid():
            response = self.find(request.data['receipt_id'])

            if response and response['status'] == 1 \
                    and response['order_id'] == request.data['order_id'] \
                    and response['price'] == int(request.data['price']):

                order = models.Order.objects \
                    .select_related('user', 'user__profile') \
                    .get(order_no=response['order_id'])

                if order.user.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified \
                        and order.user.profile.full_name == order.fullname:
                    if order.total_selling_price == Decimal(response['price']):
                        if send_vouchers(order):
                            pass
                        else:
                            # failure
                            order.status = models.Order.STATUS_CHOICES.payment_completed
                            order.save()
                            send_notification_line.delay(_('Failure: credit card 1'))
                    else:
                        # invalid paid amount
                        order.status = models.Order.STATUS_CHOICES.voided
                        order.save()
                        send_notification_line.delay(_('Failure: credit card 2'))
                else:
                    # invalid user
                    order.status = models.Order.STATUS_CHOICES.voided
                    order.save()
                    send_notification_line.delay(_('Failure: credit card 3'))

        return HttpResponse('OK')


@method_decorator(csrf_exempt, name='dispatch')
class BillgateCallbackView(StoreContextMixin, HostRestrict, generic.FormView):
    logger = logging.getLogger(__name__)
    sub_domain = 'card'
    form_class = forms.BillgateForm

    def form_valid(self, form):
        form_data = json.dumps({
            'SERVICE_CODE': form.cleaned_data['SERVICE_CODE'],
            'SERVICE_ID': form.cleaned_data['SERVICE_ID'],
            'ORDER_ID': form.cleaned_data['ORDER_ID'],
            'ORDER_DATE': form.cleaned_data['ORDER_DATE'],
            'PAY_MESSAGE': form.cleaned_data['PAY_MESSAGE'],
        })

        response = requests.post(
            # TODO: 상용 주소 변경 https://webapi.billgate.net:8443/webapi/approve.jsp
            'https://twebapi.billgate.net:10443/webapi/approve.jsp',
            data=form_data,
            headers={
                'Accept': 'application/x-www-form-urlencoded xml',
                'Content-Type': 'application/json; charset=EUC-KR',
                'Accept-language': 'gx',
                'Cache-Control': 'no-cache',
            })

        if response.status_code == requests.codes.ok:
            result = response.json()

            if result['RESPONSE_CODE'] == '0000':
                order = models.Order.objects \
                    .select_related('user', 'user__profile') \
                    .get(order_no=result['ORDER_ID'])

                if order.user.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified \
                        and order.user.profile.full_name == order.fullname:
                    if order.total_selling_price == Decimal(result['AUTH_AMOUNT']):
                        # TODO: dev@pincoin.co.kr 체크 삭제 시작
                        if order.user.email == 'dev@pincoin.co.kr':
                            order.status = order.STATUS_CHOICES.shipped
                            order.save()
                        else:
                            # TODO: 삭제 끝
                            if send_vouchers(order):
                                pass
                            else:
                                # failure
                                order.status = models.Order.STATUS_CHOICES.payment_completed
                                order.save()
                                send_notification_line.delay(_('Failure: credit card 1'))
                    else:
                        # invalid paid amount
                        order.status = models.Order.STATUS_CHOICES.voided
                        order.save()
                        send_notification_line.delay(_('Failure: credit card 2'))
                else:
                    # invalid user
                    order.status = models.Order.STATUS_CHOICES.voided
                    order.save()
                    send_notification_line.delay(_('Failure: credit card 3'))

        return HttpResponse('<script>opener.location.reload(); self.close();</script>')

    def form_invalid(self, form):
        self.logger.error(form.errors)
        return JsonResponse({
            'status': 'false',
            'message': 'Bad Request'
        }, status=400)
