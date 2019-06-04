import collections
import locale
from decimal import Decimal

from django.utils.translation import gettext_lazy as _

from . import settings as shop_settings
from .models import Product


class CartItem(object):
    def __init__(self, product, quantity, price):
        self.product = product  # Object
        self.quantity = quantity  # Integer
        self.price = price  # Decimal

    def __str__(self):
        return _('CartItem quantity={} price={}').format(self.quantity, self.price)

    def to_dict(self):
        return {
            'quantity': self.quantity,
            'price': str(self.price),  # Decimal is not JSON serializable
            'name': '{} {}'.format(self.product.name, self.product.subtitle)
        }

    @property
    def subtotal(self):
        return self.price * self.quantity


class Cart(object):
    def __init__(self, session, key):
        # Python ordered dictionary type for cart items
        self._items_dict = collections.OrderedDict()

        self.session = session
        self.session_key = key

        if self.session_key in self.session:
            self._items_json = self.session[self.session_key]

            products = Product.objects.enabled().filter(pk__in=self._items_json.keys())

            for product in products:
                item = self._items_json[str(product.pk)]
                self._items_dict[product.pk] = CartItem(product, item['quantity'], Decimal(item['price']))

    @property
    def items(self):
        return self._items_dict.values()

    @property
    def items_json(self):
        # Serializes the dictionary of CartItem objects
        """
        {
            '1': {'quantity': 2, price: '9.99', name: 'product1'},
            '2': {'quantity': 3, price: '29.99', name: 'product2'},
        }
        """
        json = {}

        for product_pk, item in self._items_dict.items():
            # JSON attribute must be a string
            json[str(product_pk)] = item.to_dict()

        return json

    @property
    def count(self):
        return sum([item.quantity for item in self.items])

    @property
    def unique_count(self):
        return len(self._items_dict)

    @property
    def is_empty(self):
        return self.unique_count == 0

    @property
    def total(self):
        return sum([item.subtotal for item in self.items])

    def add(self, product, price=None, quantity=1):
        if quantity < 1:
            raise ValueError('Quantity must be at least 1 when adding to cart')

        if not price:
            raise ValueError('Missing price when adding to cart')

        if product.pk in self._items_dict.keys():
            self._items_dict[product.pk].quantity += quantity
        else:
            self._items_dict[product.pk] = CartItem(product, quantity, price)

        self.session[self.session_key] = self.items_json
        self.session.modified = True

    def remove(self, product_pk):
        if product_pk in self._items_dict.keys():
            if self._items_dict[product_pk].quantity <= 1:
                del self._items_dict[product_pk]
            else:
                self._items_dict[product_pk].quantity -= 1

        self.session[self.session_key] = self.items_json
        self.session.modified = True

    def delete(self, product_pk):
        if product_pk in self._items_dict.keys():
            del self._items_dict[product_pk]

        self.session[self.session_key] = self.items_json
        self.session.modified = True

    def clear(self):
        self._items_dict = {}

        self.session[self.session_key] = self.items_json
        self.session.modified = True

    def set_quantity(self, product, quantity):
        quantity = int(quantity)

        if quantity < 0:
            raise ValueError('Quantity must be positive when updating cart')

        if product.pk in self._items_dict.keys():
            self._items_dict[product.pk].quantity = quantity
            if self._items_dict[product.pk].quantity < 1:
                del self._items_dict[product.pk]

        self.session[self.session_key] = self.items_json
        self.session.modified = True


def currency_filter(value, code):
    if code in shop_settings.CURRENCY_RATE:
        locale.setlocale(locale.LC_ALL, shop_settings.CURRENCY_RATE[code]['locale'])
        value = value * shop_settings.CURRENCY_RATE[code]['rate']

    return locale.currency(value, grouping=True)
