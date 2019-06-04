from django import forms
from django.utils.translation import gettext_lazy as _

from shop import models


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


class DummyForm(forms.Form):
    pass


class OrderChangeForm(forms.ModelForm):
    class Meta:
        model = models.Order
        fields = []


class CurrencyForm(forms.Form):
    currency_code = forms.CharField()
