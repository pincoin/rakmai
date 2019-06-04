import logging
import re
from decimal import Decimal

from django.conf import settings
from django.db.models import (
    Sum, Min, Max
)
from django.utils.timezone import (
    now, timedelta, localtime, make_aware
)
from django.utils.translation import gettext_lazy as _
from rest_framework import (
    status, views
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from member.models import Profile
from shop import settings as shop_settings
from shop.models import (
    Order, OrderPayment, MileageLog
)
from shop.models import (
    Product, Voucher, NaverOrder, NaverOrderProduct, NaverOrderProductVoucher
)
from shop.tasks import (
    send_notification_line, send_sms
)
from shop.utils import send_vouchers
from .permissions import WhiteListPermission
from .serializers import (
    OrderPaymentSerializer, NaverOrderPaymentSerializer
)


class OrderPaymentListView(views.APIView):
    logger = logging.getLogger(__name__)

    permission_classes = (IsAuthenticated,) if not settings.DEBUG else ()

    def get(self, request, format=None):
        payments = [p.pk for p in OrderPayment.objects.all()[:10]] if settings.DEBUG else None
        return Response(payments)

    def post(self, request, format=None):
        serializer = OrderPaymentSerializer(data=request.data)

        notify = True

        if serializer.is_valid():
            # KB 에스크로 입금처리 안함, KB 리브머니 입금처리 함
            if not (int(request.data['account']) == OrderPayment.ACCOUNT_CHOICES.kb
                    and "전자결제입금" in request.data['method']) \
                    and ((int(request.data['account']) == OrderPayment.ACCOUNT_CHOICES.kb
                          and request.data['method'] in ['리브머니', '제휴CD이체'])
                         or "입금" in request.data['method']):
                self.logger.debug('{} {} {} {} {} {}'.format(request.data['account'],
                                                             request.data['received'],
                                                             request.data['name'],
                                                             request.data['method'],
                                                             request.data['amount'],
                                                             request.data['balance']))

                op = OrderPayment()

                amount = Decimal(request.data['amount'].replace(",", ""))

                fullname = request.data['name'].strip()

                if int(request.data['account']) == OrderPayment.ACCOUNT_CHOICES.nh \
                        and re.match('\d{3}-[가-힣]*', fullname):
                    fullname = fullname[4:]

                orders = Order.objects \
                    .select_related('user') \
                    .prefetch_related('products') \
                    .filter(is_removed=False,
                            visible=Order.VISIBLE_CHOICES.visible,
                            status=Order.STATUS_CHOICES.payment_pending,
                            total_selling_price__lte=amount,
                            fullname=fullname,
                            ).order_by('-created')

                # Check duplicate user name
                users = set()

                for o in orders:
                    users.add(o.user.pk)

                found = False

                if len(orders) and len(users) > 1:
                    duplicates = 0
                    for order in orders:
                        if order.total_selling_price == amount:
                            found = True
                            op.order = order
                            duplicates += 1
                    if duplicates > 0:
                        found = False
                elif len(orders) and len(users) == 1:
                    found = True
                    op.order = orders[0]  # Pick the latest order

                if found:
                    op.account = request.data['account']
                    op.amount = amount
                    op.received = make_aware(localtime().now())
                    op.save()

                    # Change order status
                    result = op.order.payments.all().aggregate(total=Sum('amount'))
                    total = result['total'] if result['total'] else Decimal('0.00')

                    if total >= op.order.total_selling_price:
                        if op.order.user.profile.phone_verified_status \
                                == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified \
                                and op.order.user.profile.document_verified:
                            op.order.status = Order.STATUS_CHOICES.payment_verified
                        elif op.order.user.profile.phone_verified_status \
                                != Profile.PHONE_VERIFIED_STATUS_CHOICES.verified \
                                and not op.order.user.profile.document_verified:
                            op.order.status = Order.STATUS_CHOICES.under_review
                            if op.order.user.profile.total_order_count == 0:
                                notify = False
                        else:
                            op.order.status = Order.STATUS_CHOICES.payment_completed
                        op.order.save()

                        # mileage if overpaid
                        if total > op.order.total_selling_price:
                            mileage_log = MileageLog()
                            mileage_log.user = op.order.user
                            mileage_log.order = op.order
                            mileage_log.mileage = total - op.order.total_selling_price
                            mileage_log.memo = _('Overpaid')
                            mileage_log.save()

                    send = False
                    has_safe_vouchers = False

                    for order_product in op.order.products.all():
                        if order_product.name not in [
                            '문화상품권',
                            '해피머니',
                            '도서문화상품권',
                        ]:
                            has_safe_vouchers = True

                    if total >= op.order.total_selling_price:
                        if op.order.user.profile.total_order_count == 0 \
                                and op.order.user.profile.phone_verified_status \
                                == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified:
                            if op.order.total_list_price < Decimal(shop_settings.SUSPICIOUS_AMOUNT20):
                                # 주문 0회, 20만원 미만, 휴대폰인증 완료
                                send = True
                            elif op.order.total_list_price < Decimal(shop_settings.SUSPICIOUS_AMOUNT30) \
                                    and has_safe_vouchers:
                                # 주문 0회, 30만원 미만, 휴대폰인증 완료, 카드상품권 포함
                                send = True
                        elif op.order.user.profile.total_order_count > 0:
                            order_history = Order.objects.filter(
                                user=op.order.user,
                                is_removed=False,
                                status=Order.STATUS_CHOICES.shipped) \
                                .aggregate(Min('created'), Max('created'))

                            if op.order.user.profile.total_order_count > 5 \
                                    and op.order.user.profile.phone_verified_status \
                                    == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified \
                                    and op.order.user.profile.document_verified \
                                    and op.order.total_selling_price <= op.order.user.profile.max_price \
                                    and order_history['created__min'] \
                                    and now() - order_history['created__min'] > timedelta(days=14) \
                                    and order_history['created__max'] \
                                    and now() - order_history['created__max'] < timedelta(days=30):
                                # 주문 5회 초과, 휴대폰인증 and 서류본인인증 완료, 최고 구매액 이하
                                # 첫 구매 14일 경과, 마지막 구매 30일 이내
                                send = True

                            elif op.order.user.profile.total_order_count > 5 \
                                    and (op.order.user.profile.phone_verified_status
                                         == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified
                                         or op.order.user.profile.document_verified) \
                                    and has_safe_vouchers \
                                    and op.order.total_selling_price <= op.order.user.profile.max_price \
                                    and order_history['created__min'] \
                                    and now() - order_history['created__min'] > timedelta(days=14) \
                                    and order_history['created__max'] \
                                    and now() - order_history['created__max'] < timedelta(days=30):
                                # 주문 5회 초과, 휴대폰인증 or 서류본인인증, 최고 구매액 이하, 카드상품권 포함
                                # 첫 구매 14일 경과, 마지막 구매 30일 이내
                                send = True

                            if op.order.total_list_price <= Decimal(shop_settings.SUSPICIOUS_AMOUNT10) \
                                    and op.order.user.profile.document_verified:
                                # 10만원 이하 서류본인인증 완료
                                send = True
                            elif op.order.total_list_price < Decimal(shop_settings.SUSPICIOUS_AMOUNT20) \
                                    and op.order.user.profile.phone_verified_status \
                                    == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified:
                                # 20만원 미만, 휴대폰인증 완료
                                send = True
                            elif op.order.total_list_price <= Decimal(shop_settings.SUSPICIOUS_AMOUNT20) \
                                    and op.order.user.profile.phone_verified_status \
                                    == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified \
                                    and op.order.user.profile.document_verified:
                                # 20만원 이하, 휴대폰인증 and 서류본인인증 완료
                                send = True
                            elif op.order.total_list_price < Decimal(shop_settings.SUSPICIOUS_AMOUNT30) \
                                    and op.order.user.profile.phone_verified_status \
                                    == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified \
                                    and has_safe_vouchers:
                                # 30만원 미만, 휴대폰인증 완료, 카드상품권 포함
                                send = True
                            elif op.order.total_list_price <= Decimal(shop_settings.SUSPICIOUS_AMOUNT50) \
                                    and op.order.user.profile.phone_verified_status \
                                    == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified \
                                    and op.order.user.profile.document_verified \
                                    and has_safe_vouchers:
                                # 50만원 이하, 휴대폰인증 and 서류본인인증 완료, 카드상품권 포함
                                send = True

                    if send and send_vouchers(op.order):
                        return Response(serializer.data, status=status.HTTP_201_CREATED)

        if notify:
            message = '[{}]\n일시: {}\n이름: {}\n입출: {}\n금액: {}\n잔액: {}'.format(
                OrderPayment.ACCOUNT_CHOICES[int(request.data['account'])],
                request.data['received'],
                request.data['name'],
                request.data['method'],
                request.data['amount'],
                request.data['balance'],
            )
            send_notification_line.delay(message)

        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NaverOrderPaymentListView(views.APIView):
    logger = logging.getLogger(__name__)

    permission_classes = (WhiteListPermission, IsAuthenticated,) if not settings.DEBUG else ()

    def get(self, request):
        payments = []
        return Response(payments)

    def post(self, request):
        serializer = NaverOrderPaymentSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            product = Product.objects.get(pk=request.data['product'])

            order = NaverOrder()

            order.fullname = request.data['customer']
            order.phone = str(request.data['phone']).replace('-', '')
            order.total_list_price = product.list_price * request.data['quantity']
            order.total_selling_price = product.selling_price * request.data['quantity']
            order.payment_method = NaverOrder.PAYMENT_METHOD_CHOICES.bank_transfer
            order.transaction_id = request.data['order']
            order.status = NaverOrder.STATUS_CHOICES.payment_verified
            order.save()

            order_product = NaverOrderProduct()

            order_product.order = order
            order_product.name = product.name
            order_product.subtitle = product.subtitle
            order_product.code = product.code
            order_product.list_price = product.list_price
            order_product.selling_price = product.selling_price
            order_product.quantity = request.data['quantity']
            order_product.save()

            order_products = NaverOrderProduct.objects.filter(order=order) \
                .select_related('order') \
                .prefetch_related('codes')

            # 1. Check stock accountability
            out_of_stock = {}

            for order_product in order_products:
                num_vouchers = Voucher.objects \
                    .select_related('product') \
                    .filter(product__code=order_product.code, status=Voucher.STATUS_CHOICES.purchased) \
                    .count()

                if order_product.quantity > num_vouchers:
                    out_of_stock[order_product.code] = order_product.quantity - num_vouchers

            if out_of_stock:
                out_of_stock_item = []

                for key, value in out_of_stock.items():
                    out_of_stock_item.append(_(' {}: {} ea').format(key, value))

                out_of_stock_message = ''.join(out_of_stock_item)

                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

            # 2. Check duplicate sent
            duplicates = {}

            for order_product in order_products:
                num_vouchers = order_product.codes.filter(revoked=False).count()

                if num_vouchers:
                    duplicates[order_product.code] = num_vouchers

            if duplicates:
                duplicates_item = []

                for key, value in duplicates.items():
                    duplicates_item.append(_(' {}: {} ea').format(key, value))

                duplicates_message = ''.join(duplicates_item)

                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

            for order_product in order_products:
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

            # 3. Change order status
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

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NaverChatBot(views.APIView):
    logger = logging.getLogger(__name__)

    def get(self, request, format=None):
        return Response([])

    def post(self, request, format=None):
        event = request.data['event'] if 'event' in request.data else None
        user = request.data['user'] if 'user' in request.data else None
        text_content = request.data['textContent'] if 'textContent' in request.data else None

        response = {
            'event': 'send',
            'textContent': {
                'text': ''
            }
        }

        if event == 'send':
            if text_content:
                # response['textContent']['text'] = 'echo: {}'.format(text_content['text'])
                pass
            else:
                return Response(None, status=status.HTTP_200_OK)
        elif event == 'open':
            response['textContent']['text'] \
                = ("네이버 스마트스토어(smartstore.naver.com/pincoin) 주문은 "
                   "고객님의 결제 후 5~10분 후 SMS로 자동발송됩니다.\n\n"
                   "핀코인 홈페이지 대표몰, 카드몰 주문은 고객님의 결제 후 1분 이내에 발권되며 "
                   "홈페이지 '주문/발송' 페이지에서 확인합니다.\n\n"
                   "핀코인 대표몰(www.pincoin.co.kr)은 계좌이체/페이팔로 상품권 구매할 수 있습니다.\n\n"
                   "핀코인 카드몰(card.pincoin.co.kr)은 신용카드로 상품권 구매할 수 있습니다.\n\n"
                   "답변 가능시간은 오전9시부터 익일 새벽1시까지입니다. 무엇을 도와드릴까요?"
                   )

        return Response(response, status=status.HTTP_200_OK)
