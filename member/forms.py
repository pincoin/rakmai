from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Profile


class MemberSignupForm(forms.Form):
    first_name = forms.CharField(
        label=_('first name'),
        max_length=30,
        widget=forms.TextInput(),
    )

    last_name = forms.CharField(
        label=_('last name'),
        max_length=30,
        widget=forms.TextInput(),
    )

    '''
    phone = forms.RegexField(
        label=_('phone number'),
        widget=forms.TextInput(),
        regex=r'^\+?1?\d{9,15}$',
        error_messages={
            'invalid': _('Invalid phone number format'),
        }
    )
    '''

    terms = forms.BooleanField(
        label=_('I agree to Terms and Conditions.'),
    )

    privacy = forms.BooleanField(
        label=_('I agree to Privacy Policy.'),
    )

    valid_name = forms.BooleanField(
        label=_('This is my name.')
    )

    def __init__(self, *args, **kwargs):
        super(MemberSignupForm, self).__init__(*args, **kwargs)

        del self.fields['email'].widget.attrs['placeholder']
        del self.fields['username'].widget.attrs['placeholder']
        del self.fields['username'].widget.attrs['autofocus']

        self.fields['email'].help_text = _('You will sign in using this email.')
        self.fields['username'].help_text = _('Screen username')
        self.fields['last_name'].help_text = _('Last name')
        self.fields['first_name'].help_text = _('First name')

        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['last_name'].widget.attrs['class'] = 'form-control'
        self.fields['first_name'].widget.attrs['class'] = 'form-control'

    def signup(self, request, user):
        # Required fields for Django default model
        user.first_name = self.cleaned_data['first_name'].strip()
        user.last_name = self.cleaned_data['last_name'].strip()

        # Required fields for profile model
        profile = Profile()
        profile.user = user

        '''
        try:
            customer = LegacyCustomer.objects \
                .prefetch_related('order', 'products') \
                .get(email=self.cleaned_data['email'],
                     last_name=self.cleaned_data['last_name'],
                     first_name=self.cleaned_data['first_name'])

            user.date_joined = customer.date_joined

            profile.phone = customer.phone

            if hasattr(customer, 'order'):
                profile.last_purchased = customer.order.last_purchased
                profile.total_order_count = customer.order.total_order_count
                profile.max_price = customer.order.max_price
                profile.average_price = customer.order.average_price

        except LegacyCustomer.DoesNotExist:
            pass
        '''

        user.save()
        profile.save()
