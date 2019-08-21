from django.conf import settings

DAYS_DATE_JOINED = getattr(settings, 'DAYS_DATE_JOINED', 7)

DAYS_LOGIN_RECPATCHA = getattr(settings, 'DAYS_LOGIN_RECPATCHA', 21)

# File will be uploaded to MEDIA_ROOT/member/<today>/<uuid>.<ext> by default.
# For further security it must be changed and secret.
DOCUMENT_VAULT = getattr(settings, 'DOCUMENT_VAULT', 'member/{}/{}.{}')

GOOGLE_RECAPTCHA_SESSION_KEY = getattr(settings, 'GOOGLE_RECAPTCHA_SESSION_KEY', 'GOOGLE_RECAPTCHA')

DISALLOWED_EMAIL_DOMAIN = getattr(settings, 'DISALLOWED_EMAIL_DOMAIN', (
    'qq.com', '163.com', '126.com', '188.com', 'yeah.net', 'sina.com', 'hotmail.com', 'live.com'
))
