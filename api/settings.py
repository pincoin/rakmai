from django.conf import settings

REST_FRAMEWORK_WHITELIST = getattr(settings, 'REST_FRAMEWORK_WHITELIST', ['127.0.0.1', ])
