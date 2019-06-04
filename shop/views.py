import csv
import logging
import os
import re
import urllib
from decimal import Decimal
from xml.etree.ElementTree import parse

from django.conf import settings
from django.contrib.auth.mixins import (
    AccessMixin, LoginRequiredMixin
)
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.cache import cache
from django.db.models import (
    Q, Min
)
from django.http import (
    Http404, JsonResponse, HttpResponseRedirect, QueryDict, HttpResponse
)
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import (
    localtime, now, timedelta, make_aware, datetime
)
from django.utils.translation import ugettext_lazy as _
from django.views import (
    generic, View
)
from django.views.decorators.csrf import csrf_exempt
from ipware.ip import get_ip
from weasyprint import HTML

from member.models import Profile
from rakmai.viewmixins import (
    PageableMixin, HostRestrict
)
from . import forms
from . import models
from . import settings as shop_settings
from .forms2 import (
    OrderForm, RefundForm
)
from .helpers import Cart
from .tasks import (
    send_notification_email, send_notification_line, send_paypal_refund
)
from .utils import send_vouchers
from .viewmixins import StoreContextMixin


class HomeView(StoreContextMixin, HostRestrict, generic.TemplateView):
    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['page_title'] = _('1st online shop')
        return context

    def get_template_names(self):
        return 'shop/{}/home.html'.format(self.store.theme)


class ProductListView(PageableMixin, StoreContextMixin, HostRestrict, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'products'
    product_search_form_class = forms.ProductSearchForm

    def get_queryset(self):
        queryset = models.Product.objects \
            .store(self.kwargs['store']) \
            .enabled() \
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

        if shop_settings.OPENING_TIME > localtime().now().hour >= shop_settings.CLOSING_TIME:
            for p in queryset:
                if p.name in shop_settings.UNAVAILABLE_NIGHT_PRODUCTS:
                    p.stock = models.Product.STOCK_CHOICES.sold_out

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProductListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Products')
        return context

    def get_template_names(self):
        return 'shop/{}/product_list.html'.format(self.store.theme)


class ProductDetailView(StoreContextMixin, HostRestrict, generic.DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'product'

    def get_object(self, queryset=None):
        cache_key = 'shop.viewmixins.StoreContextMixin.get_object({})'.format(self.kwargs['pk'])
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
            .select_related('category', 'store') \
            .store(self.kwargs['store'])

        if shop_settings.OPENING_TIME > localtime().now().hour >= shop_settings.CLOSING_TIME:
            queryset = queryset.exclude(name__in=shop_settings.UNAVAILABLE_NIGHT_PRODUCTS)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        context['page_title'] = '{} {}'.format(self.object.name, self.object.subtitle)
        context['og_image'] = self.object.category.thumbnail.url if self.object.category.thumbnail else None
        context['product_absolute_url'] = self.request.build_absolute_uri(
            reverse('shop:product-detail', args=(self.object.store.code, self.object.pk, self.object.code)))
        return context

    def get_template_names(self):
        return 'shop/{}/product_detail.html'.format(self.store.theme)


class ProductDetailRedirectView(generic.RedirectView):
    permanent = False
    query_string = True
    pattern_name = 'card:product-detail'

    def get_redirect_url(self, *args, **kwargs):
        return 'https://card.pincoin.co.kr{}' \
            .format(super(ProductDetailRedirectView, self).get_redirect_url(*args, **kwargs))


class ProductCategoryView(StoreContextMixin, HostRestrict, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'products'

    def dispatch(self, *args, **kwargs):
        cache_key = 'shop.views.ProductCategoryView.dispatch({})'.format(self.kwargs['slug'])
        cache_time = settings.CACHES['default']['TIMEOUT']

        self.category = cache.get(cache_key)

        if not self.category:
            try:
                self.category = models.Category.objects.get(slug=self.kwargs['slug'])
                cache.set(cache_key, self.category, cache_time)
            except models.Category.DoesNotExist:
                raise Http404('No category matches the given query.')

        return super(ProductCategoryView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        queryset = models.Product.objects \
            .store(self.kwargs['store']) \
            .enabled() \
            .select_related('category', 'store') \
            .filter(category__in=models.Category.objects
                    .filter(slug=self.kwargs['slug'])
                    .get_descendants(include_self=True))

        queryset = queryset.order_by('position')

        if shop_settings.OPENING_TIME > localtime().now().hour >= shop_settings.CLOSING_TIME \
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
            if shop_settings.OPENING_TIME > localtime().now().hour >= shop_settings.CLOSING_TIME \
               and self.category.title in shop_settings.UNAVAILABLE_NIGHT_PRODUCTS \
            else False
        return context

    def get_template_names(self):
        return 'shop/{}/product_list.html'.format(self.store.theme)


class CartView(LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.CreateView):
    logger = logging.getLogger(__name__)
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
        self.cart = Cart(self.request.session, shop_settings.CART_SESSION_KEY)
        kwargs['cart'] = self.cart
        kwargs['request'] = self.request
        return kwargs

    def get_template_names(self):
        return 'shop/{}/cart.html'.format(self.store.theme)

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
                selling_price=item.product.selling_price,
                quantity=item.quantity,
            ))

            total_list_price += item.product.list_price * item.quantity
            total_selling_price += item.product.selling_price * item.quantity

        # 2. Setup order meta information
        form.instance.ip_address = get_ip(self.request)
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
        form.instance.total_selling_price = total_selling_price

        # Restrict currency according to payment method
        if int(form.cleaned_data['payment_method']) in [models.Order.PAYMENT_METHOD_CHOICES.bank_transfer,
                                                        models.Order.PAYMENT_METHOD_CHOICES.escrow]:
            form.instance.currency = 'KRW'
        elif int(form.cleaned_data['payment_method']) in [models.Order.PAYMENT_METHOD_CHOICES.paypal]:
            form.instance.currency = 'USD'

        # form.instance.suspicious = form.cleaned_data['suspicious']

        response = super(CartView, self).form_valid(form)

        # 3. Associate order
        for product in order_product_list:
            product.order = self.object

        models.OrderProduct.objects.bulk_create(order_product_list)

        # 4. Destroy cart session
        self.cart.clear()

        # 5. Send notification email
        html_message = render_to_string('shop/{}/email/order_complete.html'.format(self.store.theme),
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
        return reverse('shop:order-detail', args=(self.store.code, self.object.order_no))


class CartAddView(HostRestrict, generic.FormView):
    form_class = forms.ProductAddCartForm

    def form_valid(self, form):
        data = {}

        product = models.Product.objects \
            .enabled() \
            .available() \
            .get(pk=form.cleaned_data['product_pk'])

        if product:
            cart = Cart(self.request.session, shop_settings.CART_SESSION_KEY)
            cart.add(product=product, price=product.selling_price, quantity=form.cleaned_data['quantity'])
            data = cart.items_json

        return JsonResponse(data)

    def form_invalid(self, form):
        return JsonResponse({
            'status': 'false',
            'message': 'Bad Request'
        }, status=400)


class CartRemoveView(HostRestrict, generic.FormView):
    form_class = forms.ProductDeleteCartForm

    def form_valid(self, form):
        cart = Cart(self.request.session, shop_settings.CART_SESSION_KEY)
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
    form_class = forms.ProductDeleteCartForm

    def form_valid(self, form):
        cart = Cart(self.request.session, shop_settings.CART_SESSION_KEY)
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
    def post(self, request, store):
        if request.is_ajax():
            cart = Cart(request.session, shop_settings.CART_SESSION_KEY)
            cart.clear()
            return JsonResponse({})


class CartSetQuantityView(HostRestrict, generic.FormView):
    form_class = forms.ProductAddCartForm

    def form_valid(self, form):
        data = {}

        product = models.Product.objects \
            .enabled() \
            .available() \
            .get(pk=form.cleaned_data['product_pk'])

        if product:
            cart = Cart(self.request.session, shop_settings.CART_SESSION_KEY)
            cart.set_quantity(product=product, quantity=form.cleaned_data['quantity'])
            data = cart.items_json

        return JsonResponse(data)

    def form_invalid(self, form):
        return JsonResponse({
            'status': 'false',
            'message': 'Bad Request'
        }, status=400)


class OrderListView(PageableMixin, LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'orders'

    def get_queryset(self):
        return models.Order.objects \
            .valid(self.request.user) \
            .filter(payment_method__in=[models.Order.PAYMENT_METHOD_CHOICES.bank_transfer,
                                        models.Order.PAYMENT_METHOD_CHOICES.escrow,
                                        models.Order.PAYMENT_METHOD_CHOICES.paypal]) \
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
        return 'shop/{}/order_list.html'.format(self.store.theme)


class OrderDetailView(LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'order'

    def get_object(self, queryset=None):
        # NOTE: This method is overridden because DetailView must be called with either an object pk or a slug.
        queryset = models.Order.objects \
            .valid(self.request.user) \
            .select_related('parent', 'user__profile') \
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
            if self.object.user.profile.total_order_count > 1:
                context['show_refund_order_button'] = True
            elif timedelta(hours=2) < delta < timedelta(days=shop_settings.REFUNDABLE_DAYS):
                context['show_refund_order_button'] = True
            elif no_refund_product:
                context['show_refund_order_button'] = True

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

        context['paypal'] = settings.PAYPAL
        context['paypal_return'] = self.request.build_absolute_uri(
            reverse(settings.PAYPAL['return'], args=(self.store.code,)))
        context['paypal_notify_url'] = self.request.build_absolute_uri(
            reverse(settings.PAYPAL['notify_url'], args=(self.store.code,)))
        context['paypal_cancel_return'] = self.request.build_absolute_uri(
            reverse(settings.PAYPAL['cancel_return'], args=(self.store.code, self.object.order_no)))

        return context

    def get_template_names(self):
        return 'shop/{}/order_detail.html'.format(self.store.theme)


class OrderReceiptView(LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.DetailView):
    logger = logging.getLogger(__name__)
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

        html_string = render_to_string('shop/{}/order_receipt.html'.format(self.store.theme),
                                       {'order': order,
                                        'corp': True if order.created > make_aware(datetime(2019, 4, 25)) else False})

        html = HTML(string=html_string, base_url=self.request.build_absolute_uri())
        html.write_pdf(target=response)

        return response


class OrderAgainView(LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.FormView):
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
            self.cart.add(product=product, price=product.selling_price, quantity=order_product_dict[product.code])

        return super(OrderAgainView, self).form_valid(form)

    def form_invalid(self, form):
        return JsonResponse({
            'status': 'false',
            'message': 'Bad Request'
        }, status=400)

    def get_success_url(self):
        return reverse('shop:cart', args=(self.store.code,))

    def get_template_names(self):
        return 'shop/{}/error.html'.format(self.store.theme)


class OrderDeleteView(LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.DeleteView):
    logger = logging.getLogger(__name__)
    context_object_name = 'order'

    def get_object(self, queryset=None):
        # NOTE: This method is overridden because DetailView must be called with either an object pk or a slug.
        queryset = models.Order.objects.valid(self.request.user).pending().prefetch_related('products')
        return get_object_or_404(queryset, order_no=self.kwargs['uuid'])

    def get_success_url(self):
        return reverse('shop:order-list', args=(self.store.code,))

    def get_template_names(self):
        return 'shop/{}/order_confirm_delete.html'.format(self.store.code)


class OrderHideView(LoginRequiredMixin, StoreContextMixin, HostRestrict, generic.UpdateView):
    logger = logging.getLogger(__name__)
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
        return reverse('shop:order-list', args=(self.store.code,))

    def get_template_names(self):
        return 'shop/{}/order_confirm_hide.html'.format(self.store.code)


class OrderRefundCreateView(AccessMixin, StoreContextMixin, HostRestrict, generic.CreateView):
    logger = logging.getLogger(__name__)
    form_class = RefundForm

    def dispatch(self, request, *args, **kwargs):
        # LoginRequiredMixin is not used because of inheritance order
        if not request.user.is_authenticated:
            return self.handle_no_permission()

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
        context['message_required'] = self.order.payment_method not in [models.Order.PAYMENT_METHOD_CHOICES.paypal]

        return context

    def get_form_kwargs(self):
        kwargs = super(OrderRefundCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['voucher_required'] = self.order.status in [models.Order.STATUS_CHOICES.shipped]
        kwargs['message_required'] = self.order.payment_method not in [models.Order.PAYMENT_METHOD_CHOICES.paypal]

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

        form.instance.ip_address = get_ip(self.request)
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
        return 'shop/{}/refund_create.html'.format(self.store.theme)

    def get_success_url(self):
        return reverse('shop:order-detail', args=(self.store.code, self.object.order_no))


class CurrencyUpdateView(HostRestrict, generic.edit.FormMixin, generic.View):
    logger = logging.getLogger(__name__)
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


class PaypalSuccessView(StoreContextMixin, HostRestrict, generic.TemplateView):
    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = super(PaypalSuccessView, self).get_context_data(**kwargs)
        return context

    def get_template_names(self):
        return 'shop/{}/paypal_success.html'.format(self.store.theme)


@method_decorator(csrf_exempt, name='dispatch')
class PaypalCallbackView(HostRestrict, generic.FormView):
    logger = logging.getLogger(__name__)
    http_method_names = ['post']
    form_class = forms.PaypalCallbackForm

    def form_valid(self, form):
        # self.logger.error('1', form)
        if not self.request.META \
                .get('CONTENT_TYPE', '') \
                .startswith('application/x-www-form-urlencoded'):
            self.logger.error('3', 'type error')
            raise AssertionError(_('Invalid Content-Type'))

        encoding = self.request.POST.get('charset', 'windows-1252')

        try:
            dict = QueryDict(self.request.body, encoding=encoding).copy()
            dict['cmd'] = '_notify-validate'
        except LookupError:
            self.logger.error('4', 'lookup error')
            dict = None

        if dict:
            url = settings.PAYPAL['form_action']
            req = urllib.request.Request(url, data=dict.urlencode().encode())
            req.add_header('Content-type', 'application/x-www-form-urlencoded')
            response = urllib.request.urlopen(req).read().decode('utf-8')

            order = models.Order.objects.select_related('user', 'user__profile').get(order_no=dict['custom'])

            # IPN simulator: https://developer.paypal.com/developer/ipnSimulator/

            if response == 'VERIFIED' and dict['business'] == settings.PAYPAL['business']:
                if dict['payment_status'] == 'Completed' \
                        and dict['payment_type'] == 'instant' \
                        and dict['payer_status'] == 'verified' \
                        and dict['payer_email'] == order.user.email:
                    if order.user.profile.document_verified:  # order.user.profile.phone_verified
                        self.logger.error('5', 'document verified)')
                        order.status = models.Order.STATUS_CHOICES.payment_verified
                        order.transaction_id = dict['txn_id']
                        order.save()
                    else:
                        self.logger.error('6', 'document unverified)')
                        order.status = models.Order.STATUS_CHOICES.under_review
                        order.transaction_id = dict['txn_id']
                        order.save()

                    notify = True

                    order_history = order.user.shop_order_owned \
                        .filter(is_removed=False,
                                status__in=[models.Order.STATUS_CHOICES.payment_completed,
                                            models.Order.STATUS_CHOICES.under_review,
                                            models.Order.STATUS_CHOICES.payment_verified,
                                            models.Order.STATUS_CHOICES.shipped]) \
                        .aggregate(Min('created'))

                    if order.user.profile.total_order_count >= 3 \
                            and order_history['created__min'] \
                            and now() - order_history['created__min'] > timedelta(days=60) \
                            and order.total_list_price <= Decimal(shop_settings.SUSPICIOUS_AMOUNT15) \
                            and send_vouchers(order):
                        # 구매 3회 이상, 최초 결제일 60일 경과, 15만원 한도 자동 발송
                        notify = False

                    if notify:
                        send_notification_line.delay(_('PayPal Completed'))

                    result = {'status': 'complete'}
                    return JsonResponse(result)

                elif dict['payment_status'] == 'Refunded':
                    self.logger.error('7', 'refunded)')
                    order.status = models.Order.STATUS_CHOICES.refunded1
                    order.transaction_id = dict['txn_id']
                    order.save()

                    result = {'status': 'refunded'}
                    return JsonResponse(result)

            # Canceled_Reversal, Reversed, Voided, Denied, Expired, Failed, Pending, Processed,
            self.logger.error('8', 'voided)')
            order.status = models.Order.STATUS_CHOICES.voided
            order.transaction_id = dict['txn_id']
            order.save()

            html_message = render_to_string('shop/{}/email/order_paypal_voided.html'.format('default'),
                                            {'order': order, 'store_code': 'default'})

            send_notification_email.delay(
                _('[site] Order voided: {}').format(order.order_no),
                'dummy',
                settings.EMAIL_NO_REPLY,
                [order.user.email],
                html_message,
            )

            # message = _('PayPal Voided')
            # send_notification_line.delay(message)

            send_paypal_refund.delay(dict['txn_id'])

            result = {'status': 'voided'}
            return JsonResponse(result)

    def form_invalid(self, form):
        self.logger.error(form.errors)
        return JsonResponse({
            'status': 'false',
            'message': 'Bad Request'
        }, status=400)


class GamemecaRankingView(StoreContextMixin, HostRestrict, generic.TemplateView):
    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = super(GamemecaRankingView, self).get_context_data(**kwargs)
        context['page_title'] = _('Game ranking')

        cache_key = 'shop.viewmixins.GamemecaRankingView.get_context_data()'
        cache_time = settings.CACHES['default']['TIMEOUT']

        tree = cache.get(cache_key)

        if not tree:
            tree = parse(os.path.join(settings.GAMEMECA_RSS_DIR, 'gamemeca-chart.xml'))
            cache.set(cache_key, tree, cache_time)

        root = tree.getroot()

        context['lastupdt'] = root.find('lastupdt').text
        context['mecaurl50'] = root.find('mecaurl50').text
        context['games'] = []

        for data in root.findall('data'):
            for field in data.getchildren():
                game = {
                    'order': field.find('order').text,
                    'gm_id': field.find('gm_id').text,
                    'link': field.find('item').find('link').text,
                    'content': field.find('item').find('content').text,
                    'rank': field.find('item').find('rank').text,
                }
                context['games'].append(game)

        return context

    def get_template_names(self):
        return 'shop/{}/gamemeca_ranking.html'.format(self.store.theme)


class GamemecaNewsView(StoreContextMixin, HostRestrict, generic.TemplateView):
    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = super(GamemecaNewsView, self).get_context_data(**kwargs)

        if self.kwargs['slug'] in ['latest', 'headline', 'top', 'review', 'preview', 'feature']:
            if self.kwargs['slug'] == 'latest':
                context['page_title'] = _('Game Latest News')
            elif self.kwargs['slug'] == 'headline':
                context['page_title'] = _('Game Headline News')
            elif self.kwargs['slug'] == 'top':
                context['page_title'] = _('Game Top News')
            elif self.kwargs['slug'] == 'feature':
                context['page_title'] = _('Game Featured News')
            elif self.kwargs['slug'] == 'review':
                context['page_title'] = _('Game Review')
            elif self.kwargs['slug'] == 'preview':
                context['page_title'] = _('Game Preview')

            cache_time = settings.CACHES['default']['TIMEOUT']

            cache_key = 'shop.viewmixins.GamemecaNewsView.get_context_data({})'.format(self.kwargs['slug'])
            tree = cache.get(cache_key)

            if not tree:
                tree = parse(os.path.join(settings.GAMEMECA_RSS_DIR, 'gamemeca-{}.xml'.format(self.kwargs['slug'])))
                cache.set(cache_key, tree, cache_time)

            root = tree.getroot().find('channel')

            context['news'] = []

            for item in root.findall('item'):
                article = {
                    'title': item.find('title').text,
                    'link': item.find('link').text,
                    'image_url': item.find('image').find('url').text.replace('http:', ''),
                    'description': item.find('description').text,
                    'author': item.find('author').text,
                    'category': item.find('category').text,
                    'source': item.find('source').text,
                    # 'pubDate': datetime.strptime(item.find('pubDate').text, '%a, %d %b %Y %H:%M:%S %z'),
                }

                context['news'].append(article)

        return context

    def get_template_names(self):
        return 'shop/{}/gamemeca_news.html'.format(self.store.theme)


class NaverAdcenterView(HostRestrict, View):
    csv_filename = 'naver-adcenter.txt'

    def get_csv_filename(self):
        return self.csv_filename

    def render_to_csv(self, data):
        response = HttpResponse(content_type='text/plain')
        # response['Content-Disposition'] = 'attachment; filename="{0}"'.format(self.get_csv_filename())

        writer = csv.writer(response, delimiter='\t')
        for row in data:
            writer.writerow(row)

        return response

    def get(self, request, *args, **kwargs):
        pg = True if request.GET.get('pg') else False

        products = models.Product.objects \
            .store('default') \
            .enabled() \
            .select_related('category', 'store') \
            .filter(naver_partner=True)

        data = (
            ('id', 'title',
             'price_pc', 'price_mobile', 'normal_price',
             'link', 'mobile_link', 'image_link',
             'category_name1', 'category_name2', 'naver_category', 'review_count', 'shipping',
             'origin', 'search_tag', 'brand', 'maker', 'attribute'),
        )

        params = QueryDict('utm_source=naver&utm_medium=partner&utm_campaign=sale')

        for product in products:
            base_url = reverse('shop:product-detail', args=('default', product.pk, product.code))

            data = data \
                   + (('PINCOIN-{}-{}'.format(product.category.pk, product.pk),
                       product.naver_partner_title,
                       int(product.selling_price), int(product.selling_price), int(product.list_price),
                       self.request.build_absolute_uri('?'.join([base_url, params.urlencode()])),
                       self.request.build_absolute_uri('?'.join([base_url, params.urlencode()])),
                       'http://{}{}'.format(
                           self.request.get_host(),
                           static('images/shop/naver/code/www-{}-{}.jpg'.format(product.category.pk, product.pk))),
                       product.category.parent, product.category, '50001745', product.review_count, '0',
                       '대한민국',
                       product.category.naver_search_tag,
                       product.category.naver_brand_name,
                       product.category.naver_maker_name,
                       product.naver_attribute),)

        products = models.Product.objects \
            .store('default') \
            .enabled() \
            .select_related('category', 'store') \
            .filter(naver_partner=True, pg=True)

        for product in products:
            base_url = reverse('shop:product-detail', args=('default', product.pk, product.code)) + 'card/'

            data = data \
                   + (('PINCOIN-CARD-{}-{}'.format(product.category.pk, product.pk),
                       product.naver_partner_title_pg,
                       int(product.pg_selling_price), int(product.pg_selling_price), int(product.list_price),
                       self.request.build_absolute_uri('?'.join([base_url, params.urlencode()])),
                       self.request.build_absolute_uri('?'.join([base_url, params.urlencode()])),
                       'http://{}{}'.format(
                           self.request.get_host(),
                           static('images/shop/naver/code/card-{}-{}.jpg'.format(product.category.pk, product.pk))),
                       product.category.parent, product.category, '50001745', product.review_count_pg, '0',
                       '대한민국',
                       product.category.naver_search_tag,
                       product.category.naver_brand_name,
                       product.category.naver_maker_name,
                       product.naver_attribute),)

        return self.render_to_csv(data)


class ProductJSONView(StoreContextMixin, generic.TemplateView):
    def render_to_response(self, context, **response_kwargs):
        data = {'context': []}

        cache_key_category = 'shop.views.ProductJSONView.render_to_response(categories)'
        cache_key_product = 'shop.views.ProductJSONView.render_to_response(products)'

        cache_time = settings.CACHES['default']['TIMEOUT']

        categories = cache.get(cache_key_category)

        if not categories:
            categories = models.Category.objects \
                .filter(store__code='default', level__gt=0) \
                .order_by('title')

            cache.set(cache_key_category, categories, cache_time)

        products = cache.get(cache_key_product)

        if not products:
            products = models.Product.objects \
                .store('default') \
                .enabled() \
                .select_related('category', 'store') \
                .order_by('category_id', '-list_price')

            cache.set(cache_key_product, products, cache_time)

        for category in categories:
            p_list = []

            for p in [product for product in products if product.category.pk == category.pk]:
                p_list.append({
                    'title': p.subtitle,
                    'pk': p.pk,
                })

            c = {
                'title': category.title,
                'id': category.pk,
                'amount': p_list,
            }

            data['context'].append(c)

        return JsonResponse(
            data,
            json_dumps_params={'ensure_ascii': False},
            **response_kwargs
        )
