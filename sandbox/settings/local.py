from django.utils.translation import ugettext_lazy as _

from .base import *

DEBUG = True

INSTALLED_APPS += [
    'shop',
    'help',
    'rabop',
    'book',
    'blog',
    'bookkeeping',
    'card',
    'api',
]

# Internationalization
LANGUAGE_CODE = 'ko-kr'
LANGUAGES = [
    ('ko', _('Korean')),
    ('en', _('English')),
]
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_L10N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/assets/'
STATIC_ROOT = os.path.join(BASE_DIR, 'assets/')
STATICFILES_DIRS = [
]

# Media files (Uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# Secure Admin URL in production
ADMIN_URL = 'secret-admin/'

RABOP_URL = 'rabop/'

API_URL = 'api/'

# django-hosts
ROOT_HOSTCONF = 'sandbox.hosts'
DEFAULT_HOST = 'www'
PARENT_HOST = 'pincoin.local'
HOST_PORT = '8000'

# djagno-allauth social
SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile', ],  # 'user_friends' are not requested
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},  # If commented out, doesn't ask password.
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
            'verified',
            'locale',
            'timezone',
            'link',
            'gender',
            'updated_time',
        ],
        'EXCHANGE_TOKEN': True,
        'LOCALE_FUNC': lambda request: 'kr_KR',
        'VERIFIED_EMAIL': False,
        'VERSION': 'v2.5',
    },
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'rakmai': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'blog': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'bookkeeping': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'book': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'shop': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'member': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'help': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'api': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': 300,
    }
}

GAMEMECA_RSS_DIR = '/Users/mairoo/rss'

SESSION_COOKIE_DOMAIN = '.pincoin.local'

"""
SESSION_COOKIE_SECURE = True
CSRF_USE_SESSIONS=False
CSRF_COOKIE_HTTPONLY=False
CSRF_COOKIE_SECURE = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_AGE = 15 * 60

FILE_UPLOAD_PERMISSIONS = 0o644
UPLOAD_FILE_MAX_SIZE = 8388608

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = True
X_FRAME_OPTIONS = 'DENY'
"""

GOOGLE_OTP_ENABLED = False

# CN(China), RU(Russian Federation), UA(Ukraine)
BLOCK_COUNTRY_CODES = ['CN', ]

# KR(Korea, Republic of)
WHITE_COUNTRY_CODES = ['KR', ]

if DEBUG:
    TEMPLATES[0]['APP_DIRS'] = True
    TEMPLATES[0]['OPTIONS'].pop('loaders', None)

# Disable DRF admin interface
if not DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = ('rest_framework.renderers.JSONRenderer',)
