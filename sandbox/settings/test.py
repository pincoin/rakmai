SECRET_KEY = 'rakmai_fake_key'

DEBUG = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

INSTALLED_APPS += [
    'mptt',
    'taggit',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # 'allauth.socialaccount.providers.facebook',
    # 'allauth.socialaccount.providers.google',
    # 'allauth.socialaccount.providers.kakao',
    # 'allauth.socialaccount.providers.line',
    'import_export',
    'easy_thumbnails',
    'crispy_forms',
    'rakmai',
    'member',
    'blog',
    'board',
    'book',
    'shop',
    'help',
    'rabop',
    'banner',
]

ROOT_URLCONF = 'sandbox.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db_test.sqlite3',
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ADMIN_URL = 'secret-admin/'

RABOP_URL = 'rabop/'

API_URL = 'api/'

# Allauth

# Member

# Blog

# Board

# Forum

# Bleach sanitizing text fragments
BLEACH_ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'ol', 'ul', 'li', 'div', 'p', 'code', 'blockquote', 'pre', 'span', 'table', 'thead',
    'tbody', 'tr', 'th', 'td', 'a', 'em', 'strong', 'hr', 'img'
]

BLEACH_ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id'],
    'a': ['href', 'rel'],
    'img': ['alt', 'src'],
}

# crispy-form
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Dummy cache for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'TIMEOUT': 300,
    }
}

GOOGLE_OTP_ENABLED = False
