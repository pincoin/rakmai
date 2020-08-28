import json
import logging
import re
import uuid
from datetime import datetime

import requests
from allauth.account.models import EmailAddress
from allauth.account.views import (
    LoginView, LogoutView, SignupView,
    PasswordChangeView, PasswordSetView,
    PasswordResetView, PasswordResetDoneView, PasswordResetFromKeyView, PasswordResetFromKeyDoneView,
    EmailVerificationSentView, ConfirmEmailView, EmailView, AccountInactiveView
)
from allauth.socialaccount import views as socialaccount_views
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.contrib.auth.mixins import (
    AccessMixin, LoginRequiredMixin
)
from django.contrib.gis.geoip2 import GeoIP2
from django.shortcuts import (
    get_object_or_404
)
from django.urls import reverse
from django.utils.timezone import (
    timedelta, localtime, make_aware, now
)
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    TemplateView, UpdateView, DetailView, FormView
)
from geoip2.errors import AddressNotFoundError
from ipware.ip import get_ip
from rest_framework import (
    status, views
)
from rest_framework.response import Response

from rakmai.viewmixins import HostContextMixin
from shop.models import Order
from shop.tasks import (
    send_notification_line
)
from shop.viewmixins import StoreContextMixin
from . import settings as member_settings
from .forms2 import (
    MemberLoginForm, MemberResetPasswordForm, MemberResetPasswordKeyForm, MemberAddEmailForm,
    MemberChangePasswordForm, MemberSetPasswordForm,
    MemberDocumentForm, MemberUnregisterForm, MemberChangeNameForm,
)
from .models import (
    Profile, PhoneVerificationLog, PhoneBanned
)
from .serializers import IamportSmsCallbackSerializer


class MemberLoginView(HostContextMixin, StoreContextMixin, LoginView):
    template_name = 'member/account/login.html'
    form_class = MemberLoginForm

    def get_form_kwargs(self):
        # Pass 'self.request' object to PostForm instance
        kwargs = super(MemberLoginView, self).get_form_kwargs()

        kwargs['recaptcha'] = False

        if member_settings.GOOGLE_RECAPTCHA_SESSION_KEY in self.request.session:
            kwargs['recaptcha'] = True

        try:
            ip_address = get_ip(self.request)
            if ip_address not in ['127.0.0.1']:
                country = GeoIP2().country(ip_address)
                if country['country_code'] and country['country_code'].upper() not in settings.WHITE_COUNTRY_CODES:
                    kwargs['recaptcha'] = True
        except AddressNotFoundError:
            pass

        return kwargs

    def form_valid(self, form):
        if member_settings.GOOGLE_RECAPTCHA_SESSION_KEY in self.request.session:
            del self.request.session[member_settings.GOOGLE_RECAPTCHA_SESSION_KEY]
        return super(MemberLoginView, self).form_valid(form)

    def form_invalid(self, form):
        self.request.session[member_settings.GOOGLE_RECAPTCHA_SESSION_KEY] = True
        self.request.session.modified = True
        return super(MemberLoginView, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(MemberLoginView, self).get_context_data(**kwargs)
        context['page_title'] = _('Login')
        context['google_recaptcha_site_key'] = settings.GOOGLE_RECAPTCHA['site_key']
        return context


class MemberLogoutView(HostContextMixin, StoreContextMixin, LogoutView):
    template_name = 'member/account/logout.html'

    def get_context_data(self, **kwargs):
        context = super(MemberLogoutView, self).get_context_data(**kwargs)
        context['page_title'] = _('Logout')
        return context


class MemberSignupView(HostContextMixin, StoreContextMixin, SignupView):
    template_name = 'member/account/signup.html'

    def get_context_data(self, **kwargs):
        context = super(MemberSignupView, self).get_context_data(**kwargs)
        context['page_title'] = _('Sign up')
        return context


class MemberPasswordReset(HostContextMixin, StoreContextMixin, PasswordResetView):
    template_name = 'member/account/password_reset.html'
    form_class = MemberResetPasswordForm

    def get_context_data(self, **kwargs):
        context = super(MemberPasswordReset, self).get_context_data(**kwargs)
        context['page_title'] = _('Password Reset')
        return context


class MemberPasswordResetDoneView(HostContextMixin, StoreContextMixin, PasswordResetDoneView):
    template_name = 'member/account/password_reset_done.html'

    def get_context_data(self, **kwargs):
        context = super(MemberPasswordResetDoneView, self).get_context_data(**kwargs)
        context['page_title'] = _('Password Reset Done')
        return context


class MemberPasswordResetFromKeyView(HostContextMixin, StoreContextMixin, PasswordResetFromKeyView):
    template_name = 'member/account/password_reset_from_key.html'
    form_class = MemberResetPasswordKeyForm

    def get_context_data(self, **kwargs):
        context = super(MemberPasswordResetFromKeyView, self).get_context_data(**kwargs)
        context['page_title'] = _('Password Reset')
        return context


class MemberPasswordResetFromKeyDoneView(HostContextMixin, StoreContextMixin, PasswordResetFromKeyDoneView):
    template_name = 'member/account/password_reset_from_key_done.html'

    def get_context_data(self, **kwargs):
        context = super(MemberPasswordResetFromKeyDoneView, self).get_context_data(**kwargs)
        context['page_title'] = _('Password Reset Done')
        return context


class MemberEmailVerificationSentView(HostContextMixin, StoreContextMixin, EmailVerificationSentView):
    template_name = 'member/account/verification_sent.html'

    def get_context_data(self, **kwargs):
        context = super(MemberEmailVerificationSentView, self).get_context_data(**kwargs)
        context['page_title'] = _('Email Verification Sent')
        return context


class MemberConfirmEmailView(HostContextMixin, StoreContextMixin, ConfirmEmailView):
    template_name = 'member/account/email_confirm.html'

    def get_context_data(self, **kwargs):
        context = super(MemberConfirmEmailView, self).get_context_data(**kwargs)
        context['page_title'] = _('Confirm Email Request')
        return context


class MemberEmailView(HostContextMixin, StoreContextMixin, LoginRequiredMixin, EmailView):
    template_name = 'member/account/email.html'
    form_class = MemberAddEmailForm

    def get_context_data(self, **kwargs):
        context = super(MemberEmailView, self).get_context_data(**kwargs)
        context['page_title'] = _('Email Management')
        return context


class MemberAccountInactiveView(HostContextMixin, StoreContextMixin, AccountInactiveView):
    template_name = 'member/account/account_inactive.html'

    def get_context_data(self, **kwargs):
        context = super(MemberAccountInactiveView, self).get_context_data(**kwargs)
        context['page_title'] = _('Account Inactive')
        return context


class MemberPasswordChangeView(HostContextMixin, StoreContextMixin, LoginRequiredMixin, PasswordChangeView):
    template_name = 'member/account/password_change.html'
    form_class = MemberChangePasswordForm

    def get_context_data(self, **kwargs):
        context = super(MemberPasswordChangeView, self).get_context_data(**kwargs)
        context['page_title'] = _('Password Change')
        return context


class MemberPasswordSetView(HostContextMixin, StoreContextMixin, LoginRequiredMixin, PasswordSetView):
    template_name = 'member/account/password_set.html'
    form_class = MemberSetPasswordForm

    def get_context_data(self, **kwargs):
        context = super(MemberPasswordSetView, self).get_context_data(**kwargs)
        context['page_title'] = _('Password Set')
        return context


class MemberSocialLoginCancelledView(HostContextMixin, StoreContextMixin, socialaccount_views.LoginCancelledView):
    template_name = 'member/socialaccount/login_cancelled.html'

    def get_context_data(self, **kwargs):
        context = super(MemberSocialLoginCancelledView, self).get_context_data(**kwargs)
        context['page_title'] = _('Login Cancelled')
        return context


class MemberSocialLoginErrorView(HostContextMixin, StoreContextMixin, socialaccount_views.LoginErrorView):
    template_name = 'member/socialaccount/authentication_error.html'

    def get_context_data(self, **kwargs):
        context = super(MemberSocialLoginErrorView, self).get_context_data(**kwargs)
        context['page_title'] = _('Social Network Login Failure')
        return context


class MemberSocialSignupView(HostContextMixin, StoreContextMixin, socialaccount_views.SignupView):
    template_name = 'member/socialaccount/signup.html'

    def get_context_data(self, **kwargs):
        context = super(MemberSocialSignupView, self).get_context_data(**kwargs)
        context['page_title'] = _('Sign up')
        return context


class MemberSocialConnectionsView(HostContextMixin, StoreContextMixin, LoginRequiredMixin,
                                  socialaccount_views.ConnectionsView):
    template_name = 'member/socialaccount/connections.html'

    def get_context_data(self, **kwargs):
        context = super(MemberSocialConnectionsView, self).get_context_data(**kwargs)
        context['page_title'] = _('Connect with SNS accounts')
        return context


class TermsView(HostContextMixin, StoreContextMixin, TemplateView):
    template_name = 'member/account/terms.html'

    def get_context_data(self, **kwargs):
        context = super(TermsView, self).get_context_data(**kwargs)
        context['page_title'] = _('Terms and Conditions')
        return context


class PrivacyView(HostContextMixin, StoreContextMixin, TemplateView):
    template_name = 'member/account/privacy.html'

    def get_context_data(self, **kwargs):
        context = super(PrivacyView, self).get_context_data(**kwargs)
        context['page_title'] = _('Privacy Policy')
        return context


class MemberProfileView(LoginRequiredMixin, HostContextMixin, StoreContextMixin, DetailView):
    template_name = 'member/account/profile.html'
    context_object_name = 'member'

    def get_object(self, queryset=None):
        # NOTE: This method is overridden because DetailView must be called with either an object pk or a slug.
        queryset = Profile.objects \
            .select_related('user')
        return get_object_or_404(queryset, user__pk=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super(MemberProfileView, self).get_context_data(**kwargs)
        context['page_title'] = _('Profile')

        pattern = re.compile(r'^[가-힣]+$')  # Only Hangul

        context['hangul_name'] = True \
            if pattern.match(self.request.user.last_name) and pattern.match(self.request.user.first_name) else False

        context['iamport_user_code'] = settings.IAMPORT['user_code']
        context['iamport_sms_callback_url'] = self.request.build_absolute_uri(
            reverse(settings.IAMPORT['sms_callback_url']))

        return context


class MemberConfirmDocumentView(LoginRequiredMixin, HostContextMixin, StoreContextMixin, UpdateView):
    template_name = 'member/account/document_confirm.html'
    model = Profile
    form_class = MemberDocumentForm

    def get_object(self, queryset=None):
        # NOTE: This method is overridden because DetailView must be called with either an object pk or a slug.
        queryset = Profile.objects \
            .select_related('user')
        return get_object_or_404(queryset, user__pk=self.request.user.id)

    def form_valid(self, form):
        response = super(MemberConfirmDocumentView, self).form_valid(form)

        '''
        orders = Order.objects.valid(self.request.user).filter(status__in=[
            Order.STATUS_CHOICES.payment_completed,
            Order.STATUS_CHOICES.under_review,
            Order.STATUS_CHOICES.payment_verified
        ])

        if orders:
            html_message = render_to_string('member/account/email/document_verified.html',
                                            {'profile': self.object, 'orders': orders})
            send_notification_email.delay(
                _('[site] Customer Document Verification'),
                'dummy',
                settings.EMAIL_NO_REPLY,
                [settings.EMAIL_CUSTOMER_SERVICE],
                html_message,
            )
        '''

        message = _('Document Verification {} {} {}') \
            .format(self.object.full_name,
                    self.object.email,
                    self.request.build_absolute_uri(reverse('rabop:customer-detail', args=('default', self.object.id))))
        send_notification_line.delay(message)

        return response

    def get_context_data(self, **kwargs):
        context = super(MemberConfirmDocumentView, self).get_context_data(**kwargs)
        context['page_title'] = _('Document Verification')
        return context

    def get_success_url(self):
        return reverse('account_profile')


class MemberUnregisterView(AccessMixin, HostContextMixin, StoreContextMixin, FormView):
    template_name = 'member/account/unregister.html'
    form_class = MemberUnregisterForm

    def dispatch(self, request, *args, **kwargs):
        # LoginRequiredMixin is not used because of inheritance order
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        self.member = get_user_model().objects.get(pk=self.request.user.id)

        return super(MemberUnregisterView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MemberUnregisterView, self).get_context_data(**kwargs)
        context['page_title'] = _('Unregister')
        context['member'] = self.member
        return context

    def form_valid(self, form):
        response = super(MemberUnregisterView, self).form_valid(form)

        self.member.email = self.member.email + '_' + str(uuid.uuid4())
        self.member.username = self.member.username + '_' + str(uuid.uuid4())
        self.member.password = ''
        self.member.is_active = False
        self.member.is_staff = False
        self.member.is_superuser = False
        self.member.save()

        EmailAddress.objects.filter(user__id=self.member.id).delete()
        SocialAccount.objects.filter(user__id=self.member.id).delete()

        logout(self.request)

        return response

    def get_success_url(self):
        return reverse('shop:home', args=(self.store.code,))


class MemberNameUpdateView(LoginRequiredMixin, HostContextMixin, StoreContextMixin, UpdateView):
    template_name = 'member/account/name_change.html'
    model = Profile
    form_class = MemberChangeNameForm

    def get_object(self, queryset=None):
        # NOTE: This method is overridden because DetailView must be called with either an object pk or a slug.
        queryset = Profile.objects \
            .select_related('user')
        return get_object_or_404(queryset, user__pk=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super(MemberNameUpdateView, self).get_context_data(**kwargs)
        context['page_title'] = _('Change Your Name')
        return context

    def form_valid(self, form):
        form.instance.user.first_name = form.cleaned_data['first_name'].strip()
        form.instance.user.last_name = form.cleaned_data['last_name'].strip()
        form.instance.user.save()

        form.instance.phone_verified_status = Profile.PHONE_VERIFIED_STATUS_CHOICES.unverified
        form.instance.document_verified = False

        return super(MemberNameUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('account_profile')


class IamportSmsCallbackView(StoreContextMixin, HostContextMixin, views.APIView):
    logger = logging.getLogger(__name__)
    sub_domain = 'card'

    def get_access_token(self):
        response = requests.post(
            '{}/users/getToken'.format(settings.IAMPORT['api_url']),
            data=json.dumps({
                'imp_key': settings.IAMPORT['api_key'],
                'imp_secret': settings.IAMPORT['secret'],
            }),
            headers={
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache',
            })

        if response.status_code == requests.codes.ok:
            result = response.json()
            if result['code'] == 0:
                return result['response']['access_token']

        return None

    def find(self, imp_uid, token=None):
        if not token:
            token = self.get_access_token()

        response = requests.get(
            '{}certifications/{}'.format(settings.IAMPORT['api_url'], imp_uid),
            headers={
                "Authorization": token
            })

        if response.status_code == requests.codes.ok:
            result = response.json()
            if result['code'] == 0:
                return result['response']

        return None

    def get(self, request, format=None):
        return Response(None)

    def post(self, request, format=None):
        serializer = IamportSmsCallbackSerializer(data=request.data)

        if serializer.is_valid():
            response = self.find(request.data['imp_uid'])

            if response and response['certified']:
                print(request.data)
                print(response)

                try:
                    profile = Profile.objects.select_related('user').get(user__pk=int(request.data['merchant_uid']))

                    log = PhoneVerificationLog()
                    log.owner = profile.user
                    log.transaction_id = response['pg_tid']
                    log.di = response['unique_in_site']
                    log.ci = response['unique_key']
                    log.fullname = response['name']
                    log.date_of_birth = datetime.fromtimestamp(int(response['birth'])).strftime('%Y%m%d')
                    log.gender = 1 if response['gender'] == 'male' else 0
                    log.domestic = 1 if not response['foreigner'] else 0
                    log.telecom = response['carrier']
                    log.cellphone = response['phone']
                    log.save()

                    # check duplicate user verifications
                    logs = PhoneVerificationLog.objects \
                        .filter(ci=log.ci,
                                owner__isnull=False,
                                created__gte=make_aware(localtime().now() - timedelta(hours=48))) \
                        .exclude(owner=log.owner)

                    banned = PhoneBanned.objects.filter(phone=log.cellphone).exists()

                    if not logs:
                        # MVNO + 40 years old + joined within 24 hours
                        if 'MVNO' in log.telecom \
                                and now().date() - datetime.strptime(log.date_of_birth, '%Y%m%d').date() \
                                > timedelta(days=365 * 40) \
                                and now() - profile.user.date_joined < timedelta(hours=24):
                            return Response(data=json.dumps({
                                'code': 400,
                                'message': str(_('MVNO user can verify your account during 24 hours after joined.'))
                            }),
                                status=status.HTTP_400_BAD_REQUEST)

                        # 50 years old + joined within 6 hours
                        if now().date() - datetime.strptime(log.date_of_birth, '%Y%m%d').date() \
                                > timedelta(days=365 * 50) \
                                and now() - profile.user.date_joined < timedelta(hours=6):
                            return Response(data=json.dumps({
                                'code': 400,
                                'message': str(
                                    _('Person aged over 50 can verify your account during 6 hours after joined.'))
                            }),
                                status=status.HTTP_400_BAD_REQUEST)

                        # < 23 years old + women + joined within 90 minutes
                        if now().date() - datetime.strptime(log.date_of_birth, '%Y%m%d').date() \
                                < timedelta(days=365 * 23) \
                                and log.gender == 0 \
                                and now() - profile.user.date_joined < timedelta(minutes=90):
                            return Response(data=json.dumps({
                                'code': 400,
                                'message': str(
                                    _('Person aged under 25 can verify your account during 90 minutes after joined.'))
                            }),
                                status=status.HTTP_400_BAD_REQUEST)

                        # > 45 years old + women + joined within 90 minutes
                        if now().date() - datetime.strptime(log.date_of_birth, '%Y%m%d').date() \
                                > timedelta(days=365 * 45) \
                                and log.gender == 0 \
                                and now() - profile.user.date_joined < timedelta(minutes=90):
                            return Response(data=json.dumps({
                                'code': 400,
                                'message': str(
                                    _('Person aged over 45 can verify your account during 90 minutes after joined.'))
                            }),
                                status=status.HTTP_400_BAD_REQUEST)

                        if not banned:
                            profile.phone = log.cellphone

                            if log.fullname == profile.full_name:
                                profile.phone_verified_status = Profile.PHONE_VERIFIED_STATUS_CHOICES.verified
                                profile.date_of_birth = datetime.strptime(log.date_of_birth, '%Y%m%d').date()
                                profile.gender = log.gender
                                profile.domestic = log.domestic
                                profile.telecom = log.telecom
                                profile.save()

                                orders = Order.objects.valid(profile.user).filter(status__in=[
                                    Order.STATUS_CHOICES.under_review,
                                ])

                                if orders:
                                    message = _('Phone Verification {}').format(profile.full_name)
                                    send_notification_line.delay(message)

                                return Response(serializer.data, status=status.HTTP_200_OK)
                            else:
                                return Response(data=json.dumps({
                                    'code': 400,
                                    'message': str(_('Your name does not match the phone owner.'))
                                }),
                                    status=status.HTTP_400_BAD_REQUEST)
                        else:
                            return Response(data=json.dumps({
                                'code': 400,
                                'message': str(_('Your phone number is banned.'))
                            }),
                                status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response(data=json.dumps({
                            'code': 400,
                            'message': str(_('You have verified within 48 hours.'))
                        }),
                            status=status.HTTP_400_BAD_REQUEST)

                except (Profile.DoesNotExist, PhoneVerificationLog.DoesNotExist):
                    return Response(data=json.dumps({
                        'code': 400,
                        'message': str(_('Illegal access: no record'))
                    }),
                        status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
