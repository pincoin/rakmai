import os

from . import BASE_DIR

try:
    from .secret import Secret
except ImportError:
    raise ImportError(
        'Failed to import Secret values.'
    )

# SECURITY WARNING: Keep them secret!
SECRET_KEY = Secret.SECRET_KEY
ALLOWED_HOSTS = Secret.ALLOWED_HOSTS
DATABASES = Secret.DATABASES

LINE_NOTIFY_ACCESS_TOKEN = Secret.LINE_NOTIFY_ACCESS_TOKEN

ALIGO_API_KEY = Secret.ALIGO_API_KEY
ALIGO_USER_ID = Secret.ALIGO_USER_ID
ALIGO_SENDER = Secret.ALIGO_SENDER

EMAIL_HOST = Secret.EMAIL_HOST
EMAIL_HOST_USER = Secret.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = Secret.EMAIL_HOST_PASSWORD
EMAIL_PORT = Secret.EMAIL_PORT
EMAIL_USE_TLS = Secret.EMAIL_USE_TLS
EMAIL_NO_REPLY = Secret.EMAIL_NO_REPLY
EMAIL_JONGHWA = Secret.EMAIL_JONGHWA
EMAIL_HAN = Secret.EMAIL_HAN
EMAIL_CUSTOMER_SERVICE = Secret.EMAIL_CUSTOMER_SERVICE

GOOGLE_RECAPTCHA = Secret.GOOGLE_RECAPTCHA

PAYPAL = Secret.PAYPAL
IAMPORT = Secret.IAMPORT
BOOTPAY = Secret.BOOTPAY

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
    'django.contrib.sitemaps',
]

INSTALLED_APPS += [
    'mptt',
    'taggit',
    'rest_framework',
    'rest_framework.authtoken',
    'rakmai',
    'import_export',
    'easy_thumbnails',
    'crispy_forms',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.kakao',
    'allauth.socialaccount.providers.naver',
    'member',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'debug_toolbar',
    'disqus',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # i18n
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'rakmai.middleware.UserRestrict',
    'rakmai.middleware.GeoIPRestrict',
    'shop.middleware.AdvertisementLogMiddleware',
]

ROOT_URLCONF = 'sandbox.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]

WSGI_APPLICATION = 'sandbox.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # Django default
    'allauth.account.auth_backends.AuthenticationBackend',  # Allauth
)

# django.contrib.sites settings for allauth
SITE_ID = 1

# django.contrib.auth settings for allauth
PASSWORD_RESET_TIMEOUT_DAYS = 1  # default=3
LOGIN_URL = '/accounts/login/'  # default=/accounts/login/
LOGOUT_URL = '/accounts/logout/'  # default=/accounts/logout/
LOGIN_REDIRECT_URL = '/shop/default'  # default=/accounts/profile/
# LOGOUT_REDIRECT_URL = '/'

# django-allauth
DEFAULT_FROM_EMAIL = Secret.EMAIL_NO_REPLY
ACCOUNT_ADAPTER = 'member.adapters.MyAccountAdapter'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300
ACCOUNT_SIGNUP_FORM_CLASS = 'member.forms.MemberSignupForm'
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True  # default=False
SOCIALACCOUNT_AUTO_SIGNUP = False

# Social providers for django-allauth
# Each key has an empty dictionary value that will eventually contain provider specific configuration options by admin
SOCIALACCOUNT_PROVIDERS = {
    'facebook': {},
    'google': {},
    'kakao': {},
    'naver': {},
}

# Member

# Blog

# Board

# Forum

# Bleach sanitizing text fragments
BLEACH_ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'ol', 'ul', 'li', 'div', 'p', 'code', 'blockquote', 'pre', 'span', 'table', 'thead',
    'tbody', 'tr', 'th', 'td', 'a', 'em', 'strong', 'hr', 'img', 'b', 'span', 'br'
]

BLEACH_ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id'],
    'a': ['href', 'rel'],
    'img': ['alt', 'src', 'title'],
    'span': ['style', ],
    'td': ['colspan', ],
    'tr': ['rowspan', ],
}

# crispy-form template
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# easy-thumbnail
THUMBNAIL_ALIASES = {
    'shop': {
        'product': {'size': (156, 100), 'crop': 'smart', 'quality': 100},
    },
    'member': {
        'photo': {'size': (35, 20), 'crop': 'smart'},
    },
}

# GeoIP2
GEOIP_PATH = os.path.join(BASE_DIR, 'GeoLite2-Country.mmdb')

OTP_TOTP_ISSUER = 'PINCOIN'

INTERNAL_IPS = Secret.DEBUG_TOOLBAR_INTERNAL_IPS

# Celery
CELERY_BROKER_URL = Secret.CELERY_BROKER_URL

# Disqus
DISQUS_API_KEY = Secret.DISQUS_API_KEY
DISQUS_API_SECRET = Secret.DISQUS_API_SECRET
DISQUS_WEBSITE_SHORTNAME = Secret.DISQUS_WEBSITE_SHORTNAME

# REST API Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

REST_FRAMEWORK_TOKEN = Secret.REST_FRAMEWORK_TOKEN
REST_FRAMEWORK_WHITELIST = Secret.REST_FRAMEWORK_WHITELIST
