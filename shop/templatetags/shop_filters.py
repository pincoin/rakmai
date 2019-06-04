import locale

from django import template

from .. import settings as shop_settings

register = template.Library()


@register.filter()
def currency(value, code):
    if code in shop_settings.CURRENCY_RATE:
        locale.setlocale(locale.LC_ALL, shop_settings.CURRENCY_RATE[code]['locale'])
        value = value * shop_settings.CURRENCY_RATE[code]['rate']

    return locale.currency(value, grouping=True)
