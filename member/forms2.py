import json
import urllib

from allauth.account.forms import (
    LoginForm, ResetPasswordForm, ResetPasswordKeyForm, AddEmailForm, ChangePasswordForm, SetPasswordForm
)
from crispy_forms.bootstrap import PrependedText
from crispy_forms.helper import (
    FormHelper, Layout
)
from crispy_forms.layout import (
    Fieldset, ButtonHolder, Submit, HTML, Field
)
from django import forms
from django.conf import settings
from django.urls import reverse
from django.utils.timezone import (
    now, timedelta
)
from django.utils.translation import ugettext_lazy as _

from . import settings as member_settings
from .models import Profile
from .widgets import DocumentClearableFileInput

"""
NOTE: These form classes in `forms2.py` must be separately due to circular imports
"""


class MemberLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        self.recaptcha = kwargs.pop('recaptcha', None)

        super(MemberLoginForm, self).__init__(*args, **kwargs)

        del self.fields['login'].widget.attrs['autofocus']

    def clean(self):
        cleaned_data = super(MemberLoginForm, self).clean()

        if self.recaptcha:
            captcha_response = self.data.get('g-recaptcha-response')
            url = 'https://www.google.com/recaptcha/api/siteverify'
            values = {
                'secret': settings.GOOGLE_RECAPTCHA['secret_key'],
                'response': captcha_response
            }
            data = urllib.parse.urlencode(values).encode()
            req = urllib.request.Request(url, data=data)
            captcha_response = urllib.request.urlopen(req)
            result = json.loads(captcha_response.read().decode())

            if not result['success']:
                raise forms.ValidationError(_('Invalid reCAPTCHA. Please try again.'))

        if not self.recaptcha \
                and self.user and self.user.last_login \
                and now() - self.user.last_login > timedelta(days=member_settings.DAYS_LOGIN_RECPATCHA):
            raise forms.ValidationError(_("You haven't logged for a while."
                                          .format(member_settings.DAYS_LOGIN_RECPATCHA)))

        return cleaned_data

    class Media:
        js = ('https://www.google.com/recaptcha/api.js',)


class MemberResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(MemberResetPasswordForm, self).__init__(*args, **kwargs)

        self.fields['email'].label = False

        self.helper = FormHelper()
        self.helper.include_media = False
        self.helper.form_show_errors = False

        self.helper.form_class = 'form'

        self.helper.layout = Layout(
            Fieldset(
                '',  # Hide the legend of fieldset (HTML tag)
                Field(PrependedText('email', '<i class="fas fa-envelope"></i>',
                                    placeholder=self.fields['email'].widget.attrs['placeholder'])),
                HTML('<div class="g-recaptcha" data-sitekey="{}"></div>'.format(settings.GOOGLE_RECAPTCHA['site_key'])),
            ),
            HTML('<hr>'),
            ButtonHolder(
                Submit('submit', _('Reset My Password'), css_class='btn btn-block btn-lg btn-primary')
            ),
        )

    def clean(self):
        cleaned_data = super(MemberResetPasswordForm, self).clean()

        captcha_response = self.data.get('g-recaptcha-response')
        url = 'https://www.google.com/recaptcha/api/siteverify'
        values = {
            'secret': settings.GOOGLE_RECAPTCHA['secret_key'],
            'response': captcha_response
        }
        data = urllib.parse.urlencode(values).encode()
        req = urllib.request.Request(url, data=data)
        captcha_response = urllib.request.urlopen(req)
        result = json.loads(captcha_response.read().decode())

        if not result['success']:
            raise forms.ValidationError(_('Invalid reCAPTCHA. Please try again.'))

        return cleaned_data

    class Media:
        js = ('https://www.google.com/recaptcha/api.js',)


class MemberResetPasswordKeyForm(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super(MemberResetPasswordKeyForm, self).__init__(*args, **kwargs)

        self.fields['password1'].label = False
        self.fields['password2'].label = False

        self.helper = FormHelper()
        self.helper.include_media = False

        self.helper.form_class = 'form'

        self.helper.layout = Layout(
            Fieldset(
                '',  # Hide the legend of fieldset (HTML tag)
                Field(PrependedText('password1', '<i class="fas fa-key"></i>',
                                    placeholder=self.fields['password1'].widget.attrs['placeholder'])),
                Field(PrependedText('password2', '<i class="fas fa-key"></i>',
                                    placeholder=self.fields['password2'].widget.attrs['placeholder'])),
                HTML('<hr>'),
            ),
            ButtonHolder(
                Submit('submit', _('Change Password'), css_class='btn btn-block btn-lg btn-primary')
            ),
        )


class MemberAddEmailForm(AddEmailForm):
    def __init__(self, *args, **kwargs):
        super(MemberAddEmailForm, self).__init__(*args, **kwargs)

        self.fields['email'].label = False

        self.helper = FormHelper()
        self.helper.include_media = False

        self.helper.form_action = reverse('account_email')
        self.helper.form_class = 'form'

        self.helper.layout = Layout(
            Fieldset(
                '',  # Hide the legend of fieldset (HTML tag)
                Field(PrependedText('email', '<i class="fas fa-envelope"></i>',
                                    placeholder=self.fields['email'].widget.attrs['placeholder'])),
            ),
            ButtonHolder(
                # NOTE: Button name must be `action_add`. Otherwise, it does not work.
                Submit('action_add', _('Add E-mail'), css_class='btn btn-block btn-lg btn-primary')
            ),
        )


class MemberChangePasswordForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super(MemberChangePasswordForm, self).__init__(*args, **kwargs)

        self.fields['oldpassword'].label = False
        self.fields['password1'].label = False
        self.fields['password2'].label = False

        self.helper = FormHelper()
        self.helper.include_media = False

        self.helper.form_class = 'form'

        self.helper.layout = Layout(
            Fieldset(
                '',  # Hide the legend of fieldset (HTML tag)
                Field(PrependedText('oldpassword', '<i class="fas fa-key"></i>',
                                    placeholder=self.fields['oldpassword'].widget.attrs['placeholder'])),
                Field(PrependedText('password1', '<i class="fas fa-key"></i>',
                                    placeholder=self.fields['password1'].widget.attrs['placeholder'])),
                Field(PrependedText('password2', '<i class="fas fa-key"></i>',
                                    placeholder=self.fields['password2'].widget.attrs['placeholder'])),
                HTML('<hr>'),
            ),
            ButtonHolder(
                Submit('submit', _('Change Password'), css_class='btn btn-block btn-lg btn-primary')
            ),
        )


class MemberSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(MemberSetPasswordForm, self).__init__(*args, **kwargs)

        self.fields['password1'].label = False
        self.fields['password2'].label = False

        self.helper = FormHelper()
        self.helper.include_media = False

        self.helper.form_class = 'form'

        self.helper.layout = Layout(
            Fieldset(
                '',  # Hide the legend of fieldset (HTML tag)
                Field(PrependedText('password1', '<i class="fas fa-key"></i>',
                                    placeholder=self.fields['password1'].widget.attrs['placeholder'])),
                Field(PrependedText('password2', '<i class="fas fa-key"></i>',
                                    placeholder=self.fields['password2'].widget.attrs['placeholder'])),
                HTML('<hr>'),
            ),
            ButtonHolder(
                Submit('submit', _('Set Password'), css_class='btn btn-block btn-lg btn-primary')
            ),
        )


class MemberDocumentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(MemberDocumentForm, self).__init__(*args, **kwargs)

        self.fields['photo_id'].label = '(1) {}'.format(_('photo ID'))
        self.fields['photo_id'].help_text = _('Max: 4MB')
        self.fields['photo_id'].error_messages['contradiction'] = _(
            'Please either submit a Photo ID or check the clear checkbox, not both.')

        self.fields['card'].label = '(2) {}'.format(_('bank account or debit/credit card'))
        self.fields['card'].help_text = _('Max: 4MB')
        self.fields['card'].error_messages['contradiction'] = _(
            'Please either submit a Card image or check the clear checkbox, not both.')

        self.helper = FormHelper()
        self.helper.include_media = False

        self.helper.form_class = 'form'
        self.helper.label_class = 'col-form-label font-weight-bold pb-0'

        self.helper.layout = Layout(
            Fieldset(
                '',  # Hide the legend of fieldset (HTML tag)
                Field('photo_id', css_class='form-control-file mt-1', wrapper_class='mb-3'),
                Field('card', css_class='form-control-file mt-1', wrapper_class='mb-3'),
                HTML('<hr my-1 my-md-3>'),
            ),
            ButtonHolder(
                Submit('submit', _('Document Submit'), css_class='btn btn-block btn-lg btn-primary')
            ),
        )

    class Meta:
        model = Profile
        fields = [
            'photo_id', 'card',
        ]
        widgets = {
            'photo_id': DocumentClearableFileInput,
            'card': DocumentClearableFileInput,
        }


class MemberUnregisterForm(forms.Form):
    agree = forms.BooleanField(
        label=_('I really would like to unregister.'),
    )


class MemberChangeNameForm(forms.ModelForm):
    first_name = forms.CharField(
        label=_('first name'),
        max_length=30,
        widget=forms.TextInput(),
        help_text=_('First name'),
    )

    last_name = forms.CharField(
        label=_('last name'),
        max_length=30,
        widget=forms.TextInput(),
        help_text=_('Last name'),
    )

    def __init__(self, *args, **kwargs):
        super(MemberChangeNameForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                '',  # Hide the legend of fieldset (HTML tag)
                'last_name',
                'first_name',
            ),
            HTML('<hr>'),
            ButtonHolder(
                Submit('submit', _('Change Your Name'), css_class='btn btn-lg btn-block btn-primary')
            ),
        )
        self.helper.form_method = 'POST'

    class Meta:
        model = Profile
        fields = [
        ]
