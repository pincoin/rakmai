from crispy_forms.helper import (
    FormHelper
)
from crispy_forms.layout import (
    Submit
)
from django import forms
from django.forms.widgets import DateTimeInput
from django.urls import reverse
from django.utils.timezone import datetime
from django.utils.translation import ugettext_lazy as _

from member.models import Profile
from shop.models import (
    Order, OrderPayment, OrderProduct, Voucher, QuestionAnswer, ShortMessageService,
    NaverOrder, NaverOrderProduct
)


class OrderPaymentAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.store_code = kwargs.pop('store_code', None)
        self.order_id = kwargs.pop('order_id', None)
        self.amount = kwargs.pop('amount', 0)

        super(OrderPaymentAddForm, self).__init__(*args, **kwargs)

        self.fields['amount'].initial = self.amount
        self.fields['received'].initial = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.helper = FormHelper()
        self.helper.form_action = reverse('rabop:payment-add', args=(self.store_code, self.order_id))
        self.helper.add_input(Submit('submit', _('Add Payment'), css_class='btn btn-lg btn-block btn-primary'))
        self.helper.form_method = 'POST'

    class Meta:
        model = OrderPayment
        fields = ['account', 'amount', 'received']
        widgets = {
            'received': DateTimeInput(),
        }


class OrderPaymentDeleteForm(forms.ModelForm):
    class Meta:
        model = OrderPayment
        fields = []


class OrderChangeForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = []


class OrderSendForm(OrderChangeForm):
    def __init__(self, *args, **kwargs):
        self.order_id = kwargs.pop('order_id', None)

        super(OrderSendForm, self).__init__(*args, **kwargs)

    def clean(self):
        order = Order.objects.get(pk=self.order_id)

        order_products = OrderProduct.objects.filter(order=order) \
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

            raise forms.ValidationError(_('Out of stock! {}').format(out_of_stock_message))

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

            raise forms.ValidationError(_('Already sent! {}').format(duplicates_message))

        self.cleaned_data['order'] = order
        self.cleaned_data['order_products'] = order_products


class QuestionSearchForm(forms.Form):
    category = forms.ChoiceField(
        choices=(
            ('1', _('fullname'),),
            ('2', _('phone number'),),
            ('3', _('Email'),),
            ('4', _('user id'),),
        ),
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'required': 'True',
            }
        )
    )

    keyword = forms.CharField(
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
        category = kwargs.pop('category', '1')
        keyword = kwargs.pop('keyword', '')

        super(QuestionSearchForm, self).__init__(*args, **kwargs)

        self.fields['category'].initial = category
        self.fields['keyword'].initial = keyword


class QuestionAnswerForm(forms.ModelForm):
    answer = forms.ChoiceField(
        label=_('Template answer'),
        choices=(
            ('0', _('-----'),),
            ('1', _('01. 발송지연'),),
            ('2', _('02. 처리완료'),),
            ('3', _('03. 주문자 입금자 이름 불일치'),),
            ('4', _('04. 교환/환불 안내'),),
            ('5', _('05. 환불완료'),),
            ('6', _('06. 페이팔 무효 안내'),),
            ('7', _('07. 카드 실패 안내'),),
            ('8', _('08. 초과입금'),),
            ('9', _('09. 처리해드렸습니다.'),),
            ('10', _('10. 처리됩니다.'),),
            ('11', _('11. 감사합니다.'),),
        ),
        widget=forms.Select(
            attrs={
                'class': 'form-control',
            }
        ),
        required=False,
    )

    gift = forms.BooleanField(
        label=_('Send a giftcard.'),
        required=False,
    )

    sms = forms.BooleanField(
        label=_('No SMS'),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(QuestionAnswerForm, self).__init__(*args, **kwargs)

        self.fields['gift'].initial = False

        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _('Post Answer'), css_class='btn btn-lg btn-block btn-primary'))
        self.helper.form_method = 'POST'

    class Meta:
        model = QuestionAnswer
        fields = ['content']

        widgets = {
            'content': forms.Textarea(
                attrs={
                    'rows': 5
                }
            ),
        }


class ProfileChangeForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = []


class OrderSearchForm(forms.Form):
    category = forms.ChoiceField(
        choices=(
            ('1', _('fullname'),),
            ('2', _('order no'),),
            ('3', _('phone number'),),
            ('4', _('Email'),),
            ('5', _('user id'),),
        ),
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'required': 'True',
            }
        )
    )

    keyword = forms.CharField(
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
        category = kwargs.pop('category', '1')
        keyword = kwargs.pop('keyword', '')

        super(OrderSearchForm, self).__init__(*args, **kwargs)

        self.fields['category'].initial = category
        self.fields['keyword'].initial = keyword


class OrderStatusSearchForm(forms.Form):
    status = forms.ChoiceField(
        choices=Order.STATUS_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'required': 'True',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        status = kwargs.pop('status', '0')

        super(OrderStatusSearchForm, self).__init__(*args, **kwargs)

        self.fields['status'].initial = status


class NaverOrderSearchForm(forms.Form):
    category = forms.ChoiceField(
        choices=(
            ('1', _('fullname'),),
            ('2', _('order no'),),
            ('3', _('phone number'),),
        ),
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'required': 'True',
            }
        )
    )

    keyword = forms.CharField(
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
        category = kwargs.pop('category', '1')
        keyword = kwargs.pop('keyword', '')

        super(NaverOrderSearchForm, self).__init__(*args, **kwargs)

        self.fields['category'].initial = category
        self.fields['keyword'].initial = keyword


class NaverOrderStatusSearchForm(forms.Form):
    status = forms.ChoiceField(
        choices=NaverOrder.STATUS_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'required': 'True',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        status = kwargs.pop('status', '0')

        super(NaverOrderStatusSearchForm, self).__init__(*args, **kwargs)

        self.fields['status'].initial = status


class NaverOrderForm(forms.ModelForm):
    phone = forms.RegexField(
        label=_('to phone number'),
        help_text='010-1234-5678',
        regex=r'^01([0|1|6|7|8|9]?)-?([0-9]{3,4})-?([0-9]{4})$',
        error_messages={'invalid': _('Not a valid phone number')}
    )

    product = forms.IntegerField(
        label=_('voucher amount'),
        widget=forms.HiddenInput()
    )

    quantity = forms.ChoiceField(
        choices=(
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6'),
            ('7', '7'),
            ('8', '8'),
            ('9', '9'),
            ('10', '10'),

        ),
        label=_('Quantity'),
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'required': 'True',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(NaverOrderForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _('Naver Order Create'), css_class='btn btn-lg btn-block btn-primary'))
        self.helper.form_method = 'POST'

    class Meta:
        model = NaverOrder
        fields = (
            'fullname', 'phone', 'transaction_id', 'quantity',
            'message'
        )
        widgets = {
            'message': forms.Textarea(
                attrs={
                    'rows': 2
                }
            ),
        }


class NaverOrderSendForm(OrderChangeForm):
    def __init__(self, *args, **kwargs):
        self.order_id = kwargs.pop('order_id', None)

        super(NaverOrderSendForm, self).__init__(*args, **kwargs)

    def clean(self):
        order = NaverOrder.objects.get(pk=self.order_id)

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

            raise forms.ValidationError(_('Out of stock! {}').format(out_of_stock_message))

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

            raise forms.ValidationError(_('Already sent! {}').format(duplicates_message))

        self.cleaned_data['order'] = order
        self.cleaned_data['order_products'] = order_products


class VoucherFilterForm(forms.Form):
    voucher = forms.ChoiceField(
        choices=(
            ('2', _('Google Card'),),
            ('3', _('Nexon Card'),),
            ('8', _('Munhwa Card'),),
            ('7', _('Book and Life'),),
            ('11', _('Happy Money'),),
            ('10', _('Egg Money'),),
            ('22', _('Afreeca TV'),),
            ('13', _('Oncash'),),
            ('6', _('Smart Munhwa'),),
            ('4', _('Funny Card'),),
            ('14', _('Teencash'),),
            ('16', _('N Coin'),),
            ('17', _('WoW Cash'),),
            ('18', _('Itemmania'),),
            ('19', _('itemBay'),),
        ),
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'required': 'True',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        voucher = kwargs.pop('voucher', '1')

        super(VoucherFilterForm, self).__init__(*args, **kwargs)

        self.fields['voucher'].initial = voucher


class VoucherSearchForm(forms.Form):
    category = forms.ChoiceField(
        choices=(
            ('1', _('voucher code'),),
            ('2', _('id'),),
        ),
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'required': 'True',
            }
        )
    )

    keyword = forms.CharField(
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
        category = kwargs.pop('category', '1')
        keyword = kwargs.pop('keyword', '')

        super(VoucherSearchForm, self).__init__(*args, **kwargs)

        self.fields['category'].initial = category
        self.fields['keyword'].initial = keyword


class CustomerSearchForm(forms.Form):
    category = forms.ChoiceField(
        choices=(
            ('1', _('fullname'),),
            ('2', _('phone number'),),
            ('3', _('Email'),),
        ),
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'required': 'True',
            }
        )
    )

    keyword = forms.CharField(
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
        category = kwargs.pop('category', '1')
        keyword = kwargs.pop('keyword', '')

        super(CustomerSearchForm, self).__init__(*args, **kwargs)

        self.fields['category'].initial = category
        self.fields['keyword'].initial = keyword


class OrderByFilterForm(forms.Form):
    order_by = forms.ChoiceField(
        choices=(
            ('order_total', _('Order Total'),),
            ('order_count', _('Order Count'),),
        ),
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'required': 'True',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        order_by = kwargs.pop('order_by', 'order_total')

        super(OrderByFilterForm, self).__init__(*args, **kwargs)

        self.fields['order_by'].initial = order_by


class SmsSendForm(forms.ModelForm):
    phone_to = forms.RegexField(
        label=_('to phone number'),
        help_text='01012345678',
        regex=r'^\d{10,11}$',
        error_messages={'invalid': _('Not a valid phone number')}
    )

    sms_answer = forms.ChoiceField(
        label=_('Template answer'),
        choices=(
            ('0', _('-----'),),
            ('1', _('01. [핀코인]'),),
            ('2', _('02. 신분증 사진 요청')),
            ('3', _('03. 통장/카드사진 요청')),
            ('4', _('04. 입금액 부족')),
            ('5', _('05. 인증명의 불일치')),
            ('6', _('06. 환불안내')),
            ('7', _('07. 재주문 요청')),
        ),
        widget=forms.Select(
            attrs={
                'class': 'form-control',
            }
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.phone_to_initial = kwargs.pop('phone_to', None)

        super(SmsSendForm, self).__init__(*args, **kwargs)

        self.fields['phone_to'].initial = self.phone_to_initial

        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _('Send short message'), css_class='btn btn-lg btn-block btn-primary'))
        self.helper.form_method = 'POST'

    class Meta:
        model = ShortMessageService
        fields = ('phone_to', 'content')


class VoucherBulkUploadForm(forms.Form):
    product = forms.IntegerField(widget=forms.HiddenInput())

    json_content = forms.CharField(widget=forms.Textarea(
        attrs={
            'rows': 10,
            'readonly': True,
            'class': 'form-control',
            'placeholder': 'no data',
        }
    ))
