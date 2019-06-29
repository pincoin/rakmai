import json
import logging
import re
from decimal import Decimal

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib import messages
from django.contrib.gis.geoip2 import GeoIP2
from django.core.cache import cache
from django.db import transaction
from django.db.models import (
    Count, Sum, Case, When, F
)
from django.db.models.fields import DecimalField
from django.db.models.functions import (
    TruncMonth, TruncDay
)
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.timezone import (
    localtime, timedelta, now, make_aware, datetime
)
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from geoip2.errors import AddressNotFoundError

from member.models import (
    MmsData, Profile, LoginLog
)
from rabop.viewmixins import StoreContextMixin
from rakmai.viewmixins import (
    SuperuserRequiredMixin, PageableMixin
)
from shop import settings as shop_settings
from shop.models import (
    Order, OrderPayment, Product, Voucher, OrderProductVoucher, OrderProduct,
    CustomerQuestion, ShortMessageService, LegacyCustomer,
    NaverOrder, NaverOrderProduct, NaverOrderProductVoucher
)
from shop.tasks import (
    send_notification_email, send_sms, send_notification_line
)
from .forms import (
    OrderPaymentAddForm, OrderPaymentDeleteForm, OrderChangeForm, OrderSendForm, OrderSearchForm, OrderStatusSearchForm,
    QuestionSearchForm, QuestionAnswerForm, ProfileChangeForm, CustomerSearchForm, VoucherFilterForm, OrderByFilterForm,
    SmsSendForm, NaverOrderForm, NaverOrderSearchForm, NaverOrderStatusSearchForm, NaverOrderSendForm,
    VoucherBulkUploadForm
)


class HomeView(SuperuserRequiredMixin, StoreContextMixin, generic.TemplateView):
    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['page_title'] = _('rabop')
        return context

    def get_template_names(self):
        return 'rabop/{}/home.html'.format(self.store.theme)


class OrderListView(PageableMixin, SuperuserRequiredMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'orders'

    order_search_form_class = OrderSearchForm
    order_status_search_form_class = OrderStatusSearchForm

    def get_queryset(self):
        queryset = Order.objects \
            .select_related('user', 'user__profile') \
            .filter(is_removed=False)

        if 'status' in self.request.GET and self.request.GET['status']:
            queryset = queryset.filter(status=int(self.request.GET['status'].strip()))

        if 'category' in self.request.GET \
                and 'keyword' in self.request.GET \
                and self.request.GET['keyword']:
            if self.request.GET['category'] == '1':
                fullname = self.request.GET['keyword'].split()
                if len(fullname) == 2:
                    queryset = queryset.filter(
                        user__last_name__contains=fullname[0].strip(),
                        user__first_name__contains=fullname[1].strip(),
                    )
            elif self.request.GET['category'] == '2':
                queryset = queryset.filter(order_no=self.request.GET['keyword'].strip())
            elif self.request.GET['category'] == '3':
                queryset = queryset.filter(user__profile__phone__contains=self.request.GET['keyword'].strip())
            elif self.request.GET['category'] == '4':
                queryset = queryset.filter(user__email__contains=self.request.GET['keyword'].strip())
            elif self.request.GET['category'] == '5':
                queryset = queryset.filter(user__id=self.request.GET['keyword'].strip())

        return queryset.order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(OrderListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Pincoin Customer Orders')

        context['order_search_form'] = self.order_search_form_class(
            category=self.request.GET.get('category') if self.request.GET.get('category') else '1',
            keyword=self.request.GET.get('keyword') if self.request.GET.get('keyword') else '',
        )

        context['order_status_search_form'] = self.order_status_search_form_class(
            status=self.request.GET.get('status') if self.request.GET.get('status') else '',
        )

        return context

    def get_template_names(self):
        return 'rabop/{}/order_list.html'.format(self.store.theme)


class OrderDetailView(SuperuserRequiredMixin, StoreContextMixin, generic.DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'order'
    form_class = OrderPaymentAddForm

    def get_queryset(self):
        return Order.objects \
            .select_related('user', 'user__profile') \
            .prefetch_related('payments')

    def get_context_data(self, **kwargs):
        context = super(OrderDetailView, self).get_context_data(**kwargs)
        context['page_title'] = _('Order Details')

        context['form'] = self.form_class(
            store_code=self.store.code,
            order_id=self.kwargs['pk'],
            amount=self.object.total_selling_price,
        )

        context['country_code'] = None
        context['country_name'] = None

        try:
            country = GeoIP2().country(self.object.ip_address)

            context['country_code'] = country['country_code'].lower()
            context['country_name'] = country['country_name']
        except AddressNotFoundError:
            pass

        login_log_result = LoginLog.objects \
            .select_related('user') \
            .filter(ip_address=self.object.ip_address,
                    created__gte=make_aware(localtime().today() - timedelta(days=shop_settings.RECENT_LOGIN_IP_DAYS))) \
            .exclude(user__id=self.object.user.pk) \
            .annotate(Count('user_id', distinct=True))

        context['last_login_count'] = login_log_result[0].user_id__count if login_log_result else 0

        last_total_result = Order.objects \
            .filter(user__pk=self.object.user.pk,
                    is_removed=False,
                    created__gte=make_aware(
                        localtime().today() - timedelta(days=1)),
                    ) \
            .exclude(status=0) \
            .aggregate(last_total=Sum('total_list_price'))

        context['one_day_total'] = last_total_result['last_total'] \
            if last_total_result['last_total'] else Decimal('0.00')

        if context['one_day_total'] + self.object.total_list_price > shop_settings.ONE_DAY_ACCUMULATIVE_TOTAL:
            context['one_day_total_over'] = True

        last_total_result = Order.objects \
            .filter(user__pk=self.object.user.pk,
                    is_removed=False,
                    created__gte=make_aware(
                        localtime().today() - timedelta(days=shop_settings.RECENT_ACCUMULATIVE_DAYS)),
                    ) \
            .exclude(status=0) \
            .aggregate(last_total=Sum('total_list_price'))

        context['last_total'] = last_total_result['last_total'] if last_total_result['last_total'] else Decimal('0.00')

        if context['last_total'] + self.object.total_list_price > shop_settings.RECENT_ACCUMULATIVE_TOTAL:
            context['last_total_over'] = True

        context['show_verify_payment_button'] = self.object.status in [
            Order.STATUS_CHOICES.payment_completed,
            Order.STATUS_CHOICES.under_review,
        ]

        context['show_unverify_payment_button'] = self.object.status in [
            Order.STATUS_CHOICES.payment_verified,
        ]

        context['show_send_button'] = self.object.status in [
            Order.STATUS_CHOICES.payment_verified,
        ]

        context['show_refund_button'] = self.object.status in [
            Order.STATUS_CHOICES.refund_pending,
        ]

        context['show_voucher_list'] = self.object.status in [
            Order.STATUS_CHOICES.shipped,
            Order.STATUS_CHOICES.refund_requested,
            Order.STATUS_CHOICES.refunded1,  # original
        ]

        context['show_related_order'] = self.object.status in [
            Order.STATUS_CHOICES.refund_pending,
            Order.STATUS_CHOICES.refund_requested,
            Order.STATUS_CHOICES.refunded1,
            Order.STATUS_CHOICES.refunded2,
        ]

        pattern = re.compile(r'^01([0|1|6|7|8|9]?)-?([0-9]{3,4})-?([0-9]{4})$')
        context['phone_number_format'] = True \
            if self.object.user.profile.phone and pattern.match(self.object.user.profile.phone) else False

        context['accounts'] = self.object.user.socialaccount_set.all()

        return context

    def get_template_names(self):
        return 'rabop/{}/order_detail.html'.format(self.store.theme)


class OrderPaymentAddView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    logger = logging.getLogger(__name__)
    form_class = OrderPaymentAddForm

    def get_form_kwargs(self):
        kwargs = super(OrderPaymentAddView, self).get_form_kwargs()
        kwargs['store_code'] = self.store.code
        kwargs['order_id'] = self.kwargs['order']
        return kwargs

    def form_valid(self, form):
        order = Order.objects.get(pk=self.kwargs['order'])
        form.instance.order = order
        form.save()

        result = order.payments.all().aggregate(total=Sum('amount'))
        total = result['total'] if result['total'] else Decimal('0.00')

        if total >= order.total_selling_price:
            if order.user.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified \
                    and order.user.profile.document_verified:
                order.status = Order.STATUS_CHOICES.payment_verified
            else:
                order.status = Order.STATUS_CHOICES.under_review
            order.save()

        return super(OrderPaymentAddView, self).form_valid(form)

    def get_success_url(self):
        return reverse('rabop:order-detail', args=(self.store.code, self.kwargs['order']))


class OrderPaymentDeleteView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    logger = logging.getLogger(__name__)
    form_class = OrderPaymentDeleteForm

    def form_valid(self, form):
        payment = OrderPayment.objects.get(pk=self.kwargs['pk'])
        order = payment.order
        payment.delete()

        result = order.payments.all().aggregate(total=Sum('amount'))
        total = result['total'] if result['total'] else Decimal('0.00')

        if total < order.total_selling_price:
            order.status = Order.STATUS_CHOICES.payment_pending
            order.save()

        return super(OrderPaymentDeleteView, self).form_valid(form)

    def get_success_url(self):
        return reverse('rabop:order-detail', args=(self.store.code, self.kwargs['order']))


class OrderVerifyView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    logger = logging.getLogger(__name__)
    form_class = OrderChangeForm

    def form_valid(self, form):
        order = Order.objects.get(pk=self.kwargs['pk'])

        if order.status in [Order.STATUS_CHOICES.payment_completed, Order.STATUS_CHOICES.under_review]:
            order.status = Order.STATUS_CHOICES.payment_verified
            order.save()
            return super(OrderVerifyView, self).form_valid(form)

    def get_success_url(self):
        return reverse('rabop:order-detail', args=(self.store.code, self.kwargs['pk']))


class OrderUnverifyView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    logger = logging.getLogger(__name__)
    form_class = OrderChangeForm

    def form_valid(self, form):
        order = Order.objects.get(pk=self.kwargs['pk'])

        if order.status in [Order.STATUS_CHOICES.payment_verified]:
            order.status = Order.STATUS_CHOICES.under_review
            order.save()
            return super(OrderUnverifyView, self).form_valid(form)

    def get_success_url(self):
        return reverse('rabop:order-detail', args=(self.store.code, self.kwargs['pk']))


class OrderSendView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    logger = logging.getLogger(__name__)
    form_class = OrderSendForm

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        return super(OrderSendView, self).post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(OrderSendView, self).get_form_kwargs()
        kwargs['order_id'] = self.kwargs['pk']
        return kwargs

    def form_valid(self, form):
        # 1. Mark vouchers as sold and Associate vouchers with order products
        # TODO: Orphans(marked as sold, but not copied)?
        for order_product in form.cleaned_data['order_products']:
            vouchers = Voucher.objects \
                           .select_related('product') \
                           .filter(product__code=order_product.code,
                                   status=Voucher.STATUS_CHOICES.purchased) \
                           .order_by('pk')[:order_product.quantity]

            # Mark as sold
            # NOTE: Cannot update a query once a slice has been taken.
            voucher_pk = list(map(lambda x: x.id, vouchers))

            Voucher.objects.filter(pk__in=voucher_pk).update(status=Voucher.STATUS_CHOICES.sold)

            # Associate them (Copy vouchers)
            order_product_voucher_list = []

            for voucher in vouchers:
                order_product_voucher_list.append(OrderProductVoucher(
                    order_product=order_product,
                    voucher=voucher,
                    code=voucher.code,
                    remarks=voucher.remarks,
                    revoked=False,
                ))

            OrderProductVoucher.objects.bulk_create(order_product_voucher_list)

        # 2. Update transaction verification data
        order = form.cleaned_data['order']

        order.user.profile.last_purchased = now()

        if not order.user.profile.first_purchased:
            order.user.profile.first_purchased = order.user.profile.last_purchased

        if order.user.profile.not_purchased_months and not order.user.profile.repurchased:
            order.user.profile.repurchased = order.user.profile.last_purchased

        if order.total_selling_price > order.user.profile.max_price:
            order.user.profile.max_price = order.total_selling_price

        order.user.profile.average_price = (order.user.profile.average_price * order.user.profile.total_order_count
                                            + order.total_selling_price) / (order.user.profile.total_order_count + 1)
        order.user.profile.total_order_count += 1

        order.user.profile.save()

        # 3. Change order status
        order.status = order.STATUS_CHOICES.shipped
        order.save()

        # 4. Send email
        html_message = render_to_string('shop/{}/email/order_sent.html'.format('default'),
                                        {'order': order, 'store_code': self.store.code})
        send_notification_email.delay(
            _('[site] Order shipped: {}').format(order.order_no),
            'dummy',
            settings.EMAIL_NO_REPLY,
            [order.user.email],
            html_message,
        )

        # 5. Send SMS
        if order.user.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified \
                or order.user.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.revoked:
            send_sms.delay(
                order.user.profile.phone,
                _("You've got your vouchers.")
            )

        return super(OrderSendView, self).form_valid(form)

    def get_success_url(self):
        return reverse('rabop:order-detail', args=(self.store.code, self.kwargs['pk']))

    def get_context_data(self, **kwargs):
        context = super(OrderSendView, self).get_context_data(**kwargs)
        context['page_title'] = _('send error')
        context['order_id'] = self.kwargs['pk']
        return context

    def get_template_names(self):
        return 'rabop/{}/order_send_errors.html'.format(self.store.theme)


class OrderRefundView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    logger = logging.getLogger(__name__)
    form_class = OrderChangeForm

    def form_valid(self, form):
        order = Order.objects.get(pk=self.kwargs['pk'])

        if order.status in [Order.STATUS_CHOICES.refund_pending]:
            order.status = order.STATUS_CHOICES.refunded2
            order.parent.status = order.STATUS_CHOICES.refunded1
            order.parent.save()
            order.save()

        html_message = render_to_string('shop/{}/email/order_refunded.html'.format('default'),
                                        {'order': order, 'store_code': self.store.code})
        send_notification_email.delay(
            _('[site] Order refunded: {}').format(order.order_no),
            'dummy',
            settings.EMAIL_NO_REPLY,
            [order.user.email],
            html_message,
        )

        return super(OrderRefundView, self).form_valid(form)

    def get_success_url(self):
        return reverse('rabop:order-detail', args=(self.store.code, self.kwargs['pk']))


class NaverOrderListView(PageableMixin, SuperuserRequiredMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'orders'

    order_search_form_class = NaverOrderSearchForm
    order_status_search_form_class = NaverOrderStatusSearchForm

    def get_queryset(self):
        queryset = NaverOrder.objects \
            .filter(is_removed=False)

        if 'status' in self.request.GET and self.request.GET['status']:
            queryset = queryset.filter(status=int(self.request.GET['status'].strip()))

        if 'category' in self.request.GET \
                and 'keyword' in self.request.GET \
                and self.request.GET['keyword']:
            if self.request.GET['category'] == '1':
                queryset = queryset.filter(fullname=self.request.GET['keyword'].strip())
            elif self.request.GET['category'] == '2':
                queryset = queryset.filter(order_no=self.request.GET['keyword'].strip())
            elif self.request.GET['category'] == '3':
                queryset = queryset.filter(phone=self.request.GET['keyword'].strip())

        return queryset.order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(NaverOrderListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Naver Customer Orders')

        context['order_search_form'] = self.order_search_form_class(
            category=self.request.GET.get('category') if self.request.GET.get('category') else '1',
            keyword=self.request.GET.get('keyword') if self.request.GET.get('keyword') else '',
        )

        context['order_status_search_form'] = self.order_status_search_form_class(
            status=self.request.GET.get('status') if self.request.GET.get('status') else '',
        )

        return context

    def get_template_names(self):
        return 'rabop/{}/naver_order_list.html'.format(self.store.theme)


class NaverOrderDetailView(SuperuserRequiredMixin, StoreContextMixin, generic.DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'order'
    model = NaverOrder

    def get_context_data(self, **kwargs):
        context = super(NaverOrderDetailView, self).get_context_data(**kwargs)
        context['page_title'] = _('Naver Order Details')
        return context

    def get_template_names(self):
        return 'rabop/{}/naver_order_detail.html'.format(self.store.theme)


class NaverOrderCreateView(SuperuserRequiredMixin, StoreContextMixin, generic.CreateView):
    logger = logging.getLogger(__name__)
    form_class = NaverOrderForm

    def get_template_names(self):
        return 'rabop/{}/naver_order_create.html'.format(self.store.theme)

    def form_valid(self, form):
        product = Product.objects.get(pk=form.cleaned_data['product'])

        form.instance.phone = str(form.cleaned_data['phone']).replace('-', '')

        form.instance.total_list_price = product.list_price * int(form.cleaned_data['quantity'])
        form.instance.total_selling_price = product.selling_price * int(form.cleaned_data['quantity'])

        form.instance.payment_method = NaverOrder.PAYMENT_METHOD_CHOICES.bank_transfer
        form.instance.status = NaverOrder.STATUS_CHOICES.payment_verified

        response = super(NaverOrderCreateView, self).form_valid(form)

        order_product = NaverOrderProduct()
        order_product.order = self.object
        order_product.name = product.name
        order_product.subtitle = product.subtitle
        order_product.code = product.code
        order_product.list_price = product.list_price
        order_product.selling_price = product.selling_price
        order_product.quantity = form.cleaned_data['quantity']
        order_product.save()

        return response

    def form_invalid(self, form):
        print(form.errors)
        return super(NaverOrderCreateView, self).form_invalid(form)

    def get_success_url(self):
        return reverse('rabop:naver-order-detail', args=(self.store.code, self.object.pk))


class NaverOrderSendView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    logger = logging.getLogger(__name__)
    form_class = NaverOrderSendForm

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        return super(NaverOrderSendView, self).post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(NaverOrderSendView, self).get_form_kwargs()
        kwargs['order_id'] = self.kwargs['pk']
        return kwargs

    def form_valid(self, form):
        # 1. Mark vouchers as sold and Associate vouchers with order products
        # TODO: Orphans(marked as sold, but not copied)?
        for order_product in form.cleaned_data['order_products']:
            vouchers = Voucher.objects \
                           .select_related('product') \
                           .filter(product__code=order_product.code,
                                   status=Voucher.STATUS_CHOICES.purchased) \
                           .order_by('pk')[:order_product.quantity]

            # Mark as sold
            # NOTE: Cannot update a query once a slice has been taken.
            voucher_pk = list(map(lambda x: x.id, vouchers))

            Voucher.objects.filter(pk__in=voucher_pk).update(status=Voucher.STATUS_CHOICES.sold)

            # Associate them (Copy vouchers)
            order_product_voucher_list = []

            for voucher in vouchers:
                order_product_voucher_list.append(NaverOrderProductVoucher(
                    order_product=order_product,
                    voucher=voucher,
                    code=voucher.code,
                    remarks=voucher.remarks,
                    revoked=False,
                ))

            NaverOrderProductVoucher.objects.bulk_create(order_product_voucher_list)

        # 2. Change order status
        order = form.cleaned_data['order']
        order.status = order.STATUS_CHOICES.shipped
        order.save()

        # 4. Send SMS
        for product in order.products.all():
            for voucher in product.codes.all():
                if '해피' in product.name:
                    send_sms.delay(order.phone, "[핀코인] [{} {}] {} 발행일자 {}".format(
                        product.name, product.subtitle,
                        voucher.code, voucher.remarks))
                elif '도서' in product.name:
                    send_sms.delay(order.phone, "[핀코인] [{} {}] {} 비밀번호 {}".format(
                        product.name, product.subtitle,
                        voucher.code, voucher.remarks))
                else:
                    send_sms.delay(order.phone, "[핀코인] [{} {}] {}".format(
                        product.name, product.subtitle,
                        voucher.code))

        return super(NaverOrderSendView, self).form_valid(form)

    def get_success_url(self):
        return reverse('rabop:naver-order-detail', args=(self.store.code, self.kwargs['pk']))

    def get_context_data(self, **kwargs):
        context = super(NaverOrderSendView, self).get_context_data(**kwargs)
        context['page_title'] = _('send error')
        context['order_id'] = self.kwargs['pk']
        return context

    def get_template_names(self):
        return 'rabop/{}/order_send_errors.html'.format(self.store.theme)


class NaverOrderRevokeView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    logger = logging.getLogger(__name__)
    form_class = OrderChangeForm

    def dispatch(self, request, *args, **kwargs):
        queryset = NaverOrder.objects \
            .prefetch_related('products', 'products__codes') \
            .filter(status=NaverOrder.STATUS_CHOICES.shipped)

        self.order = get_object_or_404(queryset, pk=self.kwargs['pk'])

        return super(NaverOrderRevokeView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if self.order.status == NaverOrder.STATUS_CHOICES.shipped:
            self.order.status = NaverOrder.STATUS_CHOICES.refund_requested
            self.order.save()

            for product in self.order.products.all():
                product.codes.all().update(revoked=True)

                for code in product.codes.all():
                    code.voucher.status = Voucher.STATUS_CHOICES.purchased
                    code.voucher.save()

        return super(NaverOrderRevokeView, self).form_valid(form)

    def get_success_url(self):
        return reverse('rabop:naver-order-detail', args=(self.store.code, self.kwargs['pk']))


class NaverOrderResendView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    logger = logging.getLogger(__name__)
    form_class = OrderChangeForm

    def dispatch(self, request, *args, **kwargs):
        queryset = NaverOrder.objects \
            .prefetch_related('products', 'products__codes') \
            .filter(status=NaverOrder.STATUS_CHOICES.shipped)

        self.order = get_object_or_404(queryset, pk=self.kwargs['pk'])

        return super(NaverOrderResendView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if self.order.status == NaverOrder.STATUS_CHOICES.shipped:
            for product in self.order.products.all():
                for voucher in product.codes.all():
                    if '해피' in product.name:
                        send_sms.delay(self.order.phone, "[핀코인] [{} {}] {} 발행일자 {}".format(
                            product.name, product.subtitle,
                            voucher.code, voucher.remarks))
                    elif '도서' in product.name:
                        send_sms.delay(self.order.phone, "[핀코인] [{} {}] {} 비밀번호 {}".format(
                            product.name, product.subtitle,
                            voucher.code, voucher.remarks))
                    else:
                        send_sms.delay(self.order.phone, "[핀코인] [{} {}] {}".format(
                            product.name, product.subtitle,
                            voucher.code))

        return super(NaverOrderResendView, self).form_valid(form)

    def get_success_url(self):
        return reverse('rabop:naver-order-detail', args=(self.store.code, self.kwargs['pk']))


class NaverOrderRefundView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    logger = logging.getLogger(__name__)
    form_class = OrderChangeForm

    def dispatch(self, request, *args, **kwargs):
        queryset = NaverOrder.objects.filter(status=NaverOrder.STATUS_CHOICES.refund_requested)

        self.order = get_object_or_404(queryset, pk=self.kwargs['pk'])

        return super(NaverOrderRefundView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if self.order.status == NaverOrder.STATUS_CHOICES.refund_requested:
            self.order.status = NaverOrder.STATUS_CHOICES.refunded
            self.order.save()

        return super(NaverOrderRefundView, self).form_valid(form)

    def get_success_url(self):
        return reverse('rabop:naver-order-detail', args=(self.store.code, self.kwargs['pk']))


class NaverOrderDeleteView(SuperuserRequiredMixin, StoreContextMixin, generic.DeleteView):
    logger = logging.getLogger(__name__)
    context_object_name = 'order'

    def get_object(self, queryset=None):
        # NOTE: This method is overridden because DetailView must be called with either an object pk or a slug.
        queryset = NaverOrder.objects.prefetch_related('products')

        return get_object_or_404(queryset, pk=self.kwargs['pk'])

    def get_success_url(self):
        return reverse('rabop:naver-order-list', args=(self.store.code,))

    def get_template_names(self):
        return 'rabop/{}/naver_order_confirm_delete.html'.format(self.store.code)


class CustomerQuestionListView(PageableMixin, SuperuserRequiredMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'questions'

    question_search_form_class = QuestionSearchForm

    def get_queryset(self):
        queryset = CustomerQuestion.objects \
            .select_related('owner', 'owner__profile') \
            .filter(store__code=self.store.code, is_removed=False) \
            .order_by('-created')

        if 'category' in self.request.GET \
                and 'keyword' in self.request.GET \
                and self.request.GET['keyword']:
            if self.request.GET['category'] == '1':
                fullname = self.request.GET['keyword'].split()
                if len(fullname) == 2:
                    queryset = queryset.filter(
                        owner__last_name__contains=fullname[0].strip(),
                        owner__first_name__contains=fullname[1].strip(),
                    )
            elif self.request.GET['category'] == '2':
                queryset = queryset.filter(owner__profile__phone__contains=self.request.GET['keyword'].strip())
            elif self.request.GET['category'] == '3':
                queryset = queryset.filter(owner__email__contains=self.request.GET['keyword'].strip())
            elif self.request.GET['category'] == '4':
                queryset = queryset.filter(owner__id=self.request.GET['keyword'].strip())

        return queryset.annotate(answers_count=Count('answers')).order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(CustomerQuestionListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Customer Questions')

        context['question_search_form'] = self.question_search_form_class(
            category=self.request.GET.get('category') if self.request.GET.get('category') else '1',
            keyword=self.request.GET.get('keyword') if self.request.GET.get('keyword') else '',
        )

        return context

    def get_template_names(self):
        return 'rabop/{}/question_list.html'.format(self.store.theme)


class CustomerQuestionDetailView(SuperuserRequiredMixin, StoreContextMixin, generic.edit.FormMixin, generic.DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'question'
    form_class = QuestionAnswerForm

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_queryset(self):
        return CustomerQuestion.objects \
            .select_related('order', 'owner', 'owner__profile') \
            .filter(store__code=self.store.code, is_removed=False) \
            .annotate(answers_count=Count('answers')) \
            .order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(CustomerQuestionDetailView, self).get_context_data(**kwargs)
        context['page_title'] = _('Customer Questions')
        return context

    def form_valid(self, form):
        code = '해피1천'

        if form.cleaned_data['gift']:
            count = Voucher.objects \
                .select_related('product') \
                .filter(product__code=code,
                        status=Voucher.STATUS_CHOICES.purchased) \
                .count()

            if count > 0:
                vouchers = Voucher.objects \
                               .select_related('product') \
                               .filter(product__code=code, status=Voucher.STATUS_CHOICES.purchased) \
                               .order_by('pk')[:1]

                # Mark as sold
                # NOTE: Cannot update a query once a slice has been taken.
                voucher_pk = list(map(lambda x: x.id, vouchers))

                Voucher.objects.filter(pk__in=voucher_pk).update(status=Voucher.STATUS_CHOICES.sold)

                form.instance.content = '{}\n\n해피머니 1천원: {}\n발행일자: {}'.format(form.instance.content,
                                                                              vouchers[0].code,
                                                                              vouchers[0].remarks)
            else:
                send_notification_line.delay(_('No giftcard'))

        question = CustomerQuestion.objects.get(pk=self.kwargs['pk'])
        form.instance.question = question
        form.save()

        response = super(CustomerQuestionDetailView, self).form_valid(form)

        html_message = render_to_string('shop/{}/email/question_answer.html'.format('default'),
                                        {'answer': form.instance})
        send_notification_email.delay(
            _('[site] Question Answer'),
            'dummy',
            settings.EMAIL_NO_REPLY,
            [self.object.owner.email],
            html_message,
        )

        if self.object.owner.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified \
                or self.object.owner.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.revoked:
            send_sms.delay(
                self.object.owner.profile.phone,
                _("You've got a question answer.")
            )

        return response

    def get_success_url(self):
        return reverse('rabop:question-detail', args=(self.store.code, self.kwargs['pk']))

    def get_template_names(self):
        return 'rabop/{}/question_detail.html'.format(self.store.theme)


class CustomerListView(PageableMixin, SuperuserRequiredMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'customers'

    customer_search_form_class = CustomerSearchForm

    def get_queryset(self):
        queryset = Profile.objects \
            .select_related('user') \
            .filter(user__is_active=True)

        if 'category' in self.request.GET \
                and 'keyword' in self.request.GET \
                and self.request.GET['keyword']:
            if self.request.GET['category'] == '1':
                fullname = self.request.GET['keyword'].split()
                if len(fullname) == 2:
                    queryset = queryset.filter(
                        user__last_name__contains=fullname[0].strip(),
                        user__first_name__contains=fullname[1].strip(),
                    )
            elif self.request.GET['category'] == '2':
                queryset = queryset.filter(phone__contains=self.request.GET['keyword'].strip())
            elif self.request.GET['category'] == '3':
                queryset = queryset.filter(user__email__contains=self.request.GET['keyword'].strip())

        return queryset.order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(CustomerListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Customers')

        context['customer_search_form'] = self.customer_search_form_class(
            category=self.request.GET.get('category') if self.request.GET.get('category') else '1',
            keyword=self.request.GET.get('keyword') if self.request.GET.get('keyword') else '',
        )

        return context

    def get_template_names(self):
        return 'rabop/{}/customer_list.html'.format(self.store.theme)


class CustomerDetailView(SuperuserRequiredMixin, StoreContextMixin, generic.DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'customer'

    def get_queryset(self):
        queryset = Profile.objects \
            .select_related('user') \
            .filter(user__is_active=True)

        return queryset.order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(CustomerDetailView, self).get_context_data(**kwargs)
        context['page_title'] = _('Customer')

        last_total_result = Order.objects \
            .filter(user__pk=self.object.user.pk,
                    is_removed=False,
                    created__gte=make_aware(
                        localtime().today() - timedelta(days=1)),
                    ) \
            .exclude(status=0) \
            .aggregate(last_total=Sum('total_list_price'))

        context['one_day_total'] = last_total_result['last_total'] \
            if last_total_result['last_total'] else Decimal('0.00')

        last_total_result = Order.objects \
            .filter(user__pk=self.object.user.pk,
                    is_removed=False,
                    created__gte=make_aware(
                        localtime().today() - timedelta(days=shop_settings.RECENT_ACCUMULATIVE_DAYS)
                    )) \
            .exclude(status=0) \
            .aggregate(last_total=Sum('total_list_price'))

        context['last_total'] = last_total_result['last_total'] if last_total_result['last_total'] else Decimal('0.00')
        context['email_verified'] = EmailAddress.objects.filter(user__id=self.object.user.id,
                                                                verified=True,
                                                                primary=True).exists()

        pattern = re.compile(r'^01([0|1|6|7|8|9]?)-?([0-9]{3,4})-?([0-9]{4})$')
        context['phone_number_format'] = True \
            if self.object.user.profile.phone and pattern.match(self.object.user.profile.phone) else False

        context['accounts'] = self.object.user.socialaccount_set.all()

        return context

    def get_template_names(self):
        return 'rabop/{}/customer_detail.html'.format(self.store.theme)


class CustomerDocumentVerifyView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    logger = logging.getLogger(__name__)
    form_class = ProfileChangeForm

    def form_valid(self, form):
        profile = Profile.objects.get(pk=self.kwargs['pk'])
        profile.document_verified = True
        profile.save()
        return super(CustomerDocumentVerifyView, self).form_valid(form)

    def get_success_url(self):
        return reverse('rabop:customer-detail', args=(self.store.code, self.kwargs['pk']))


class CustomerDocumentUnverifyView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    logger = logging.getLogger(__name__)
    form_class = ProfileChangeForm

    def form_valid(self, form):
        profile = Profile.objects.get(pk=self.kwargs['pk'])
        profile.document_verified = False
        profile.save()
        return super(CustomerDocumentUnverifyView, self).form_valid(form)

    def get_success_url(self):
        return reverse('rabop:customer-detail', args=(self.store.code, self.kwargs['pk']))


class CustomerEmailVerifyView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    form_class = ProfileChangeForm

    def form_valid(self, form):
        email = EmailAddress.objects \
            .select_related('user') \
            .prefetch_related('user__profile').get(user__profile__id=self.kwargs['pk'], primary=True)
        email.verified = True
        email.save()
        return super(CustomerEmailVerifyView, self).form_valid(form)

    def get_success_url(self):
        return reverse('rabop:customer-detail', args=(self.store.code, self.kwargs['pk']))


class CustomerEmailUnverifyView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    logger = logging.getLogger(__name__)
    form_class = ProfileChangeForm

    def form_valid(self, form):
        email = EmailAddress.objects \
            .select_related('user') \
            .prefetch_related('user__profile').get(user__profile__id=self.kwargs['pk'], primary=True)
        email.verified = False
        email.save()
        return super(CustomerEmailUnverifyView, self).form_valid(form)

    def get_success_url(self):
        return reverse('rabop:customer-detail', args=(self.store.code, self.kwargs['pk']))


class SmsListView(PageableMixin, SuperuserRequiredMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'messages'

    def get_queryset(self):
        return ShortMessageService.objects.order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(SmsListView, self).get_context_data(**kwargs)
        context['page_title'] = _('SMS Log')
        return context

    def get_template_names(self):
        return 'rabop/{}/sms_list.html'.format(self.store.theme)


class SmsCreateView(SuperuserRequiredMixin, StoreContextMixin, generic.CreateView):
    logger = logging.getLogger(__name__)
    form_class = SmsSendForm

    def get_template_names(self):
        return 'rabop/{}/sms_send.html'.format(self.store.theme)

    def get_form_kwargs(self):
        # Pass 'self.request' object to SmsSendForm instance
        kwargs = super(SmsCreateView, self).get_form_kwargs()
        kwargs['phone_to'] = self.request.GET.get('phone_to') if self.request.GET.get('phone_to') else ''
        return kwargs

    def form_valid(self, form):
        form.instance.phone_from = settings.ALIGO_SENDER
        response = super(SmsCreateView, self).form_valid(form)

        send_sms.delay(form.instance.phone_to, form.instance.content)

        return response

    def get_success_url(self):
        return reverse('rabop:sms-list', args=(self.store.code,))


class StockStatusListView(PageableMixin, SuperuserRequiredMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'vouchers'

    voucher_filter_form_class = VoucherFilterForm

    def get_queryset(self):
        queryset = Product.objects \
            .filter(status=Product.STATUS_CHOICES.enabled) \
            .select_related('category') \
            .prefetch_related('vouchers') \
            .annotate(stock_count=Count(Case(When(vouchers__status=Voucher.STATUS_CHOICES.purchased,
                                                  vouchers__is_removed=False,
                                                  then=1)))) \
            .annotate(stock_level=F('stock_count') - F('minimum_stock_level'))

        if 'voucher' in self.request.GET and self.request.GET['voucher']:
            queryset = queryset.filter(category__id=int(self.request.GET['voucher'].strip()))
        else:
            queryset = queryset.exclude(stock_count=0, minimum_stock_level=0)

        return queryset.order_by('stock_level')

    def get_context_data(self, **kwargs):
        context = super(StockStatusListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Stock Status')

        queryset = Product.objects \
            .filter(status=Product.STATUS_CHOICES.enabled) \
            .select_related('category') \
            .prefetch_related('vouchers')

        if 'voucher' in self.request.GET and self.request.GET['voucher']:
            queryset = queryset.filter(category__id=int(self.request.GET['voucher'].strip()))

        context['total'] = queryset \
            .annotate(stock_count=Count(Case(When(vouchers__status=Voucher.STATUS_CHOICES.purchased, then=1)))) \
            .aggregate(total=Sum(F('selling_price') * F('stock_count'), output_field=DecimalField()))['total']

        context['voucher_filter_form'] = self.voucher_filter_form_class(
            voucher=self.request.GET.get('voucher') if self.request.GET.get('voucher') else '1',
        )
        return context

    def get_template_names(self):
        return 'rabop/{}/stock_status.html'.format(self.store.theme)


class StockBulkUploadView(SuperuserRequiredMixin, StoreContextMixin, generic.FormView):
    logger = logging.getLogger(__name__)
    form_class = VoucherBulkUploadForm

    def get_context_data(self, **kwargs):
        context = super(StockBulkUploadView, self).get_context_data(**kwargs)
        context['page_title'] = _('stock bulk upload')
        return context

    def get_template_names(self):
        return 'rabop/{}/stock_bulk_upload.html'.format(self.store.theme)

    def form_valid(self, form):
        product = Product.objects.get(pk=form.cleaned_data['product'])

        vouchers = json.loads(form.cleaned_data['json_content'])

        duplicate = False

        if Voucher.objects \
                .select_related('product', 'product__category') \
                .filter(code__in=list(map(lambda x: x['code'], vouchers)),
                        product__category__title=product.category.title) \
                .exists():
            duplicate = True
            messages.add_message(self.request, messages.ERROR, _('Duplicated voucher code'))

        if not duplicate:
            voucher_list = []

            for voucher in vouchers:
                voucher_list.append(Voucher(product=product, code=voucher['code'], remarks=voucher['remarks']))

            Voucher.objects.bulk_create(voucher_list)

            messages.add_message(self.request, messages.INFO, _(' {}: {} ea').format(product.code, len(vouchers)))

        return super(StockBulkUploadView, self).form_valid(form)

    def get_success_url(self):
        return reverse('admin:shop_voucher_changelist')


class MonthlySalesReportView(SuperuserRequiredMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'sales'

    def __init__(self):
        self.year = make_aware(datetime.now()).year
        super(MonthlySalesReportView, self).__init__()

    def get_queryset(self):
        cache_key = 'rabop.views.MonthlySalesReportView.get_context_data()'
        cache_time = settings.CACHES['default']['TIMEOUT']

        queryset = cache.get(cache_key)

        if not queryset:
            queryset = Order.objects \
                .filter(status=Order.STATUS_CHOICES.shipped,
                        is_removed=False,
                        created__year__gte=self.year) \
                .annotate(month=TruncMonth('created')) \
                .values('month') \
                .annotate(amount=Sum('total_selling_price')) \
                .values('month', 'amount') \
                .order_by('month')

            cache.set(cache_key, queryset, cache_time)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(MonthlySalesReportView, self).get_context_data(**kwargs)
        context['page_title'] = _('Monthly Sales Report')
        context['year'] = self.year
        return context

    def get_template_names(self):
        return 'rabop/{}/monthly_sales_report.html'.format(self.store.theme)


class DailySalesReportView(SuperuserRequiredMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'sales'

    def get_queryset(self):
        cache_key = 'rabop.views.DailySalesReportView.get_context_data()'
        cache_time = settings.CACHES['default']['TIMEOUT']

        queryset = cache.get(cache_key)

        if not queryset:
            queryset = Order.objects \
                .filter(status=Order.STATUS_CHOICES.shipped,
                        is_removed=False,
                        created__gte=make_aware(localtime().today().replace(hour=0, minute=0, second=0, microsecond=0)
                                                - timedelta(days=50))) \
                .annotate(day=TruncDay('created')) \
                .values('day') \
                .annotate(amount=Sum('total_selling_price'), count=Count('id')) \
                .values('day', 'amount', 'count') \
                .order_by('-day')

            cache.set(cache_key, queryset, cache_time)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(DailySalesReportView, self).get_context_data(**kwargs)
        context['page_title'] = _('Daily Sales Report')
        return context

    def get_template_names(self):
        return 'rabop/{}/daily_sales_report.html'.format(self.store.theme)


class BestCustomersReportView(PageableMixin, SuperuserRequiredMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'customers'

    order_by_filter_form_class = OrderByFilterForm

    def get_queryset(self):
        order_by = self.request.GET['order_by'] if 'order_by' in self.request.GET else 'order_total'

        cache_key = 'rabop.views.BestCustomersReportView.get_context_data({})'.format(order_by)
        cache_time = settings.CACHES['default']['TIMEOUT']

        queryset = cache.get(cache_key)

        if not queryset:
            queryset = Order.objects \
                .select_related('user') \
                .filter(is_removed=False, status=Order.STATUS_CHOICES.shipped, user__is_active=True) \
                .values('user__id') \
                .annotate(order_total=Sum('total_selling_price')) \
                .annotate(order_count=Count('id')) \
                .values('order_total', 'order_count', 'user__last_name', 'user__first_name')

            if order_by == 'order_total':
                queryset = queryset.order_by('-order_total')
            elif order_by == 'order_count':
                queryset = queryset.order_by('-order_count')

            cache.set(cache_key, queryset, cache_time)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(BestCustomersReportView, self).get_context_data(**kwargs)
        context['page_title'] = _('Best Customers Report')

        context['order_by_filter_form'] = self.order_by_filter_form_class(
            order_by=self.request.GET.get('order_by') if 'order_by' in self.request.GET else 'order_total',
        )
        return context

    def get_template_names(self):
        return 'rabop/{}/best_customers_report.html'.format(self.store.theme)


class BestSellersReportView(PageableMixin, SuperuserRequiredMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'products'

    order_by_filter_form_class = OrderByFilterForm

    def get_queryset(self):
        order_by = self.request.GET['order_by'] if 'order_by' in self.request.GET else 'order_total'

        cache_key = 'rabop.views.BestSellersReportView.get_context_data({})'.format(order_by)
        cache_time = settings.CACHES['default']['TIMEOUT']

        queryset = cache.get(cache_key)

        if not queryset:
            queryset = OrderProductVoucher.objects \
                .select_related('order_product', 'voucher', 'order_product__order') \
                .filter(is_removed=False, revoked=False, order_product__order__status=Order.STATUS_CHOICES.shipped) \
                .values('order_product__code') \
                .annotate(order_total=Sum('order_product__selling_price')) \
                .annotate(order_count=Count('order_product__id')) \
                .values('order_product__code', 'order_total', 'order_count')

            if order_by == 'order_total':
                queryset = queryset.order_by('-order_total')
            elif order_by == 'order_count':
                queryset = queryset.order_by('-order_count')

            cache.set(cache_key, queryset, cache_time)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(BestSellersReportView, self).get_context_data(**kwargs)
        context['page_title'] = _('Best Sellers Report')

        context['order_by_filter_form'] = self.order_by_filter_form_class(
            order_by=self.request.GET.get('order_by') if 'order_by' in self.request.GET else 'order_total',
        )
        return context

    def get_template_names(self):
        return 'rabop/{}/best_sellers_report.html'.format(self.store.theme)


class BestSellersByCategoryReportView(SuperuserRequiredMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'products'

    order_by_filter_form_class = OrderByFilterForm

    def __init__(self):
        self.year = make_aware(datetime.now()).year
        self.month = make_aware(datetime.now()).month

        super(BestSellersByCategoryReportView, self).__init__()

    def get_queryset(self):
        order_by = self.request.GET['order_by'] if 'order_by' in self.request.GET else 'order_total'

        cache_key = 'rabop.views.BestSellersByCategoryReportView.get_context_data({})'.format(order_by)
        cache_time = settings.CACHES['default']['TIMEOUT']

        queryset = cache.get(cache_key)

        if not queryset:
            queryset = OrderProduct.objects \
                .select_related('codes', 'voucher', 'order') \
                .filter(is_removed=False,
                        codes__revoked=False,
                        order__status=Order.STATUS_CHOICES.shipped,
                        order__created__month=self.month,
                        order__created__year=self.year) \
                .values('name') \
                .annotate(order_total=Sum('selling_price')) \
                .values('name', 'order_total') \
                .order_by('-order_total')

            cache.set(cache_key, queryset, cache_time)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(BestSellersByCategoryReportView, self).get_context_data(**kwargs)
        context['page_title'] = _('Best Sellers Report')

        context['order_by_filter_form'] = self.order_by_filter_form_class(
            order_by=self.request.GET.get('order_by') if 'order_by' in self.request.GET else 'order_total',
        )

        return context

    def get_template_names(self):
        return 'rabop/{}/best_sellers_by_category_report.html'.format(self.store.theme)


class DailyPaymentReportView(SuperuserRequiredMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'payments'

    def get_queryset(self):
        cache_key = 'rabop.views.DailyPaymentReportView.get_context_data()'
        cache_time = settings.CACHES['default']['TIMEOUT']

        queryset = cache.get(cache_key)

        if not queryset:
            queryset = OrderProduct.objects \
                .select_related('order') \
                .filter(is_removed=False,
                        codes__revoked=False,
                        order__status=Order.STATUS_CHOICES.shipped,
                        created__gte=make_aware(localtime().today().replace(hour=0, minute=0, second=0, microsecond=0))) \
                .values('order__payment_method') \
                .annotate(order_total=Sum('selling_price'), count=Count('order__id', distinct=True)) \
                .values('order__payment_method', 'order_total', 'count') \
                .order_by('-order_total')

            cache.set(cache_key, queryset, cache_time)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(DailyPaymentReportView, self).get_context_data(**kwargs)
        context['page_title'] = _('Daily Payments Report')
        return context

    def get_template_names(self):
        return 'rabop/{}/daily_payments_report.html'.format(self.store.theme)


class LegacyCustomerListView(PageableMixin, SuperuserRequiredMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'customers'
    customer_search_form_class = CustomerSearchForm

    def get_queryset(self):
        queryset = LegacyCustomer.objects.all()

        if 'category' in self.request.GET \
                and 'keyword' in self.request.GET \
                and self.request.GET['keyword']:
            if self.request.GET['category'] == '1':
                fullname = self.request.GET['keyword'].split()
                if len(fullname) == 2:
                    queryset = queryset.filter(
                        last_name__contains=fullname[0].strip(),
                        first_name__contains=fullname[1].strip(),
                    )
            elif self.request.GET['category'] == '2':
                queryset = queryset.filter(phone__contains=self.request.GET['keyword'].strip())
            elif self.request.GET['category'] == '3':
                queryset = queryset.filter(email__contains=self.request.GET['keyword'].strip())

        return queryset.order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super(LegacyCustomerListView, self).get_context_data(**kwargs)
        context['page_title'] = _('legacy customers')

        context['customer_search_form'] = self.customer_search_form_class(
            category=self.request.GET.get('category') if self.request.GET.get('category') else '1',
            keyword=self.request.GET.get('keyword') if self.request.GET.get('keyword') else '',
        )
        return context

    def get_template_names(self):
        return 'rabop/{}/legacy_customer_list.html'.format(self.store.theme)


class LegacyCustomerDetailView(SuperuserRequiredMixin, StoreContextMixin, generic.DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'customer'

    def get_object(self, queryset=None):
        # NOTE: This method is overridden because DetailView must be called with either an object pk or a slug.
        queryset = LegacyCustomer.objects.prefetch_related('order', 'products')
        return get_object_or_404(queryset, customer_id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(LegacyCustomerDetailView, self).get_context_data(**kwargs)
        context['page_title'] = _('legacy customer')
        return context

    def get_template_names(self):
        return 'rabop/{}/legacy_customer_detail.html'.format(self.store.theme)


class LegacyCustomerMmsListView(PageableMixin, SuperuserRequiredMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'messages'
    customer_search_form_class = CustomerSearchForm

    def get_queryset(self):
        queryset = MmsData.objects \
            .select_related('mms') \
            .filter(mms__cellphone=self.kwargs['cellphone']) \
            .all()

        return queryset.order_by('-mms__sent')

    def get_context_data(self, **kwargs):
        context = super(LegacyCustomerMmsListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Customer MMS')

        return context

    def get_template_names(self):
        return 'rabop/{}/legacy_customer_mms_list.html'.format(self.store.theme)
