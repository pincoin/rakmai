from allauth.account.adapter import DefaultAccountAdapter
from django import forms
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from rakmai.helpers import get_sub_domain
from shop.tasks import send_notification_email
from .models import EmailBanned
from . import settings as member_settings


class MyAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        subject = render_to_string('member/{0}_subject.txt'.format(template_prefix), context)
        # remove superfluous line breaks
        subject = " ".join(subject.splitlines()).strip()
        subject = self.format_email_subject(subject)

        from_email = self.get_from_email()

        bodies = {}
        template_name = 'member/{0}_message.{1}'.format(template_prefix, 'html')
        # bodies['txt'] = render_to_string(template_name, context).strip()
        bodies['html'] = render_to_string(template_name, context).strip()

        send_notification_email.delay(subject, 'dummy', from_email, email, html_message=bodies['html'])

    def clean_email(self, email):
        if email.lower().split('@')[1] not in member_settings.ALLOWED_EMAIL_DOMAIN:
            raise forms.ValidationError(_('Your email domain is not allowed.'))

        if EmailBanned.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('Your email is banned.'))

        return email

    def get_login_redirect_url(self, request):
        sub_domain = get_sub_domain(self.request)

        if sub_domain == 'card':
            return reverse('card:home', args=('default',))
        else:
            return reverse('shop:home', args=('default',))
