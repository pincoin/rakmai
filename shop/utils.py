from django.conf import settings
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from member.models import Profile
from .models import (
    OrderProduct, OrderProductVoucher, Voucher, Product
)
from .tasks import (
    send_notification_line, send_notification_email, send_sms
)


def send_vouchers(order):
    order_products = OrderProduct.objects \
        .filter(order=order) \
        .select_related('order') \
        .prefetch_related('codes')

    # 1. Check stock accountability
    out_of_stock = {}

    for order_product in order_products:
        num_vouchers = Voucher.objects \
            .select_related('product') \
            .filter(product__code=order_product.code,
                    status=Voucher.STATUS_CHOICES.purchased) \
            .count()

        if order_product.quantity > num_vouchers:
            out_of_stock[order_product.code] = order_product.quantity - num_vouchers

    if out_of_stock:
        out_of_stock_item = []

        for key, value in out_of_stock.items():
            out_of_stock_item.append(_(' {}: {} ea').format(key, value))

        out_of_stock_message = ''.join(out_of_stock_item)

        send_notification_line.delay(_('Out of stock! {}').format(out_of_stock_message))
        return False

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

        send_notification_line.delay(_('Already sent! {}').format(duplicates_message))
        return False

    # 3. Mark vouchers as sold and Associate vouchers with order products
    # TODO: Orphans(marked as sold, but not copied)?
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
            order_product_voucher_list.append(OrderProductVoucher(
                order_product=order_product,
                voucher=voucher,
                code=voucher.code,
                remarks=voucher.remarks,
                revoked=False,
            ))

        OrderProductVoucher.objects.bulk_create(order_product_voucher_list)

    # 4. Update transaction verification data
    order.user.profile.last_purchased = now()

    if not order.user.profile.first_purchased:
        order.user.profile.first_purchased = order.user.profile.last_purchased

    if order.user.profile.not_purchased_months and not order.user.profile.repurchased:
        order.user.profile.repurchased = order.user.profile.last_purchased

    if order.total_selling_price > order.user.profile.max_price:
        order.user.profile.max_price = order.total_selling_price

    order.user.profile.average_price = (order.user.profile.average_price
                                        * order.user.profile.total_order_count
                                        + order.total_selling_price) / \
                                       (order.user.profile.total_order_count + 1)
    order.user.profile.total_order_count += 1

    order.user.profile.save()

    # 5. Change order status
    order.status = order.STATUS_CHOICES.shipped
    order.save()

    # 6. Send email
    html_message = render_to_string('shop/{}/email/order_sent.html'.format('default'),
                                    {'order': order, 'store_code': 'www'})
    send_notification_email.delay(
        _('[site] Order shipped: {}').format(order.order_no),
        'dummy',
        settings.EMAIL_NO_REPLY,
        [order.user.email],
        html_message,
    )

    # 7. Send SMS
    if order.user.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.verified \
            or order.user.profile.phone_verified_status == Profile.PHONE_VERIFIED_STATUS_CHOICES.revoked:
        send_sms.delay(
            order.user.profile.phone,
            _("You've got your vouchers.")
        )

    return True
