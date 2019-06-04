from django import template

from shop.models import (
    LegacyOrderProduct
)

register = template.Library()


@register.simple_tag
def get_legacy_order_products(email):
    return LegacyOrderProduct.objects \
        .select_related('customer_id') \
        .filter(customer_id__email=email)
