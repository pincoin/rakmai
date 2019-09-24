from django import template

from shop.models import (
    LegacyOrderProduct, OrderPayment
)

register = template.Library()


@register.simple_tag
def get_legacy_order_products(email):
    return LegacyOrderProduct.objects \
        .select_related('customer_id') \
        .filter(customer_id__email=email)


@register.simple_tag
def get_bank_account_balance(account):
    try:
        return OrderPayment.objects.filter(account=account).order_by('-created')[0]
    except IndexError:
        return None
