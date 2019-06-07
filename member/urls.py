from importlib import import_module

from allauth.socialaccount import providers
from django.urls import (
    path, re_path
)

from member.views import (
    MemberLoginView, MemberLogoutView, MemberSignupView, MemberAccountInactiveView, MemberUnregisterView,
    MemberPasswordChangeView, MemberPasswordSetView,
    MemberPasswordReset, MemberPasswordResetDoneView, MemberPasswordResetFromKeyView,
    MemberPasswordResetFromKeyDoneView,
    MemberSocialLoginCancelledView, MemberSocialLoginErrorView, MemberSocialSignupView, MemberSocialConnectionsView,
    MemberEmailVerificationSentView, MemberConfirmEmailView, MemberEmailView,
    TermsView, PrivacyView,
    MemberProfileView, MemberConfirmDocumentView, MemberNameUpdateView, IamportSmsCallbackView,
)

urlpatterns = [
    # Account
    path('login/',
         MemberLoginView.as_view(), name="account_login"),
    path('logout/',
         MemberLogoutView.as_view(), name="account_logout"),
    path('signup/',
         MemberSignupView.as_view(), name="account_signup"),
    path('inactive/',
         MemberAccountInactiveView.as_view(), name="account_inactive"),
    path('unregister/',
         MemberUnregisterView.as_view(), name="account_unregister"),

    # Password Change
    path('password/change/',
         MemberPasswordChangeView.as_view(), name="account_change_password"),
    path('password/set/',
         MemberPasswordSetView.as_view(), name="account_set_password"),

    # Password Reset
    path('password/reset/',
         MemberPasswordReset.as_view(), name="account_reset_password"),
    path('password/reset/done/',
         MemberPasswordResetDoneView.as_view(), name="account_reset_password_done"),
    re_path(r'^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$',
            MemberPasswordResetFromKeyView.as_view(), name="account_reset_password_from_key"),
    path('password/reset/key/done/',
         MemberPasswordResetFromKeyDoneView.as_view(), name="account_reset_password_from_key_done"),

    # Email Confirmation
    path('confirm-email/',
         MemberEmailVerificationSentView.as_view(), name="account_email_verification_sent"),
    re_path(r'^confirm-email/(?P<key>[-:\w]+)/$',
            MemberConfirmEmailView.as_view(), name="account_confirm_email"),
    path('email/',
         MemberEmailView.as_view(), name="account_email"),

    # Site Terms and Conditions / Privacy Policy
    path('terms/',
         TermsView.as_view(), name="site_terms"),
    path('privacy/',
         PrivacyView.as_view(), name="site_privacy"),

    # Profile
    path('profile/',
         MemberProfileView.as_view(), name="account_profile"),

    path('change-name/',
         MemberNameUpdateView.as_view(), name="account_change_name"),

    # Verification
    path('confirm-document/',
         MemberConfirmDocumentView.as_view(), name="account_confirm_document"),
    path('confirm-phone/',
         IamportSmsCallbackView.as_view(), name='iamport-sms-callback'),

    # Social Providers
    path('social/login/cancelled/',
         MemberSocialLoginCancelledView.as_view(), name='socialaccount_login_cancelled'),
    path('social/login/error/',
         MemberSocialLoginErrorView.as_view(), name='socialaccount_login_error'),
    path('social/signup/',
         MemberSocialSignupView.as_view(), name='socialaccount_signup'),
    path('social/connections/',
         MemberSocialConnectionsView.as_view(), name='socialaccount_connections'),
]

# URL patterns for social providers
for provider in providers.registry.get_list():
    try:
        prov_mod = import_module(provider.get_package() + '.urls')
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, 'urlpatterns', None)
    if prov_urlpatterns:
        urlpatterns += prov_urlpatterns
