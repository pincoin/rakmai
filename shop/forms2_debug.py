from django import forms
from django.utils.timezone import (
    localtime
)
from django.utils.translation import gettext_lazy as _
from model_utils import Choices

from . import models
from . import settings as shop_settings


class OrderForm(forms.ModelForm):
    agreement = forms.BooleanField(
        label=_('I agree to Commercial Law.'),
        help_text=_('Do you agree to buy items in your cart?')
    )

    agreement1 = forms.BooleanField(
        label=_('I purchase by myself on my own purpose.'),
        help_text=_('It is 100 percent fraud if you are asked to buy the codes.')
    )

    payment_method = forms.ChoiceField(
        required=True,
        choices=Choices(
            (0, 'bank_transfer', _('Bank Transfer')),
            (1, 'escrow', _('Escrow (KB)')),
            (2, 'paypal', _('PayPal')),
        ),
        widget=forms.RadioSelect(),
    )

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop('cart', None)
        self.request = kwargs.pop('request', None)
        self.store = kwargs.pop('store', None)

        super(OrderForm, self).__init__(*args, **kwargs)

        self.fields['payment_method'].label = False
        self.fields['payment_method'].initial = models.Order.PAYMENT_METHOD_CHOICES.bank_transfer

    class Meta:
        model = models.Order
        fields = [
            'payment_method'
        ]

    def clean(self):
        if self.cart.is_empty:
            raise forms.ValidationError(_('Empty cart! Please, put items in your cart.'))

        if self.request.user.profile.allow_order:
            return


class RefundForm(forms.ModelForm):
    vouchers = forms.CharField()

    message = forms.CharField(
        label=_('order message'),
        help_text=_('Your bank account and your full name'),
        widget=forms.TextInput(),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.voucher_required = kwargs.pop('voucher_required', True)
        self.message_required = kwargs.pop('message_required', True)

        super(RefundForm, self).__init__(*args, **kwargs)

        self.fields['vouchers'].required = self.voucher_required
        self.fields['message'].required = self.message_required

    class Meta:
        model = models.Order
        fields = [
        ]

    def clean_vouchers(self):
        voucher_dict = {}

        for i in self.data.getlist('vouchers'):
            k, v = map(int, i.split('_'))

            if k in voucher_dict:
                voucher_dict[k].append(v)
            else:
                voucher_dict[k] = [v]

        order_product_queryset = models.OrderProduct.objects \
            .select_related('order') \
            .prefetch_related('codes', 'codes__voucher') \
            .filter(pk__in=voucher_dict.keys(),
                    order__user=self.request.user)

        self.cleaned_data['order_product_queryset'] = order_product_queryset
        self.cleaned_data['voucher_dict'] = voucher_dict

    def clean(self):
        if shop_settings.OPENING_TIME > localtime().now().hour >= shop_settings.CLOSING_TIME:
            raise forms.ValidationError(_('You cannot refund at night.'))
