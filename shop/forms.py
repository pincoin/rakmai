from django import forms
from django.utils.translation import gettext_lazy as _

from . import models


class ProductAdminForm(forms.ModelForm):
    discount_rate = forms.FloatField(
        label=_('discount rate'),
    )

    def __init__(self, *args, **kwargs):
        super(ProductAdminForm, self).__init__(*args, **kwargs)

        self.fields['discount_rate'].initial = 0

        if self.instance.list_price and self.instance.selling_price:
            self.fields['discount_rate'].initial = (self.instance.list_price - self.instance.selling_price) \
                                                   * 100 / self.instance.list_price

    class Meta:
        model = models.Product
        fields = [
            'name', 'subtitle', 'code', 'list_price', 'selling_price', 'discount_rate',
            'description', 'category', 'store', 'status',
            'stock', 'minimum_stock_level', 'maximum_stock_level', 'position',
            'pg', 'pg_selling_price',
            'naver_partner', 'naver_partner_title', 'naver_partner_title_pg', 'naver_attribute',
        ]


class ProductSearchForm(forms.Form):
    q = forms.CharField(
        label=_('search word'),
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': _('search word'),
                'required': 'True',
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        q = kwargs.pop('q', '')

        super(ProductSearchForm, self).__init__(*args, **kwargs)

        self.fields['q'].initial = q


class ProductAddCartForm(forms.Form):
    product_pk = forms.IntegerField()
    quantity = forms.IntegerField()


class ProductDeleteCartForm(forms.Form):
    product_pk = forms.IntegerField()


class CurrencyForm(forms.Form):
    currency_code = forms.CharField()


class PaypalCallbackForm(forms.Form):
    custom = forms.UUIDField()  # order_no


class DummyForm(forms.Form):
    pass


class OrderChangeForm(forms.ModelForm):
    class Meta:
        model = models.Order
        fields = []
