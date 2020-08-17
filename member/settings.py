from django.conf import settings

DAYS_DATE_JOINED = getattr(settings, 'DAYS_DATE_JOINED', 7)

DAYS_LOGIN_RECPATCHA = getattr(settings, 'DAYS_LOGIN_RECPATCHA', 21)

# File will be uploaded to MEDIA_ROOT/member/<today>/<uuid>.<ext> by default.
# For further security it must be changed and secret.
DOCUMENT_VAULT = getattr(settings, 'DOCUMENT_VAULT', 'member/{}/{}.{}')

GOOGLE_RECAPTCHA_SESSION_KEY = getattr(settings, 'GOOGLE_RECAPTCHA_SESSION_KEY', 'GOOGLE_RECAPTCHA')

DISALLOWED_EMAIL_DOMAIN = getattr(settings, 'DISALLOWED_EMAIL_DOMAIN', (
    'qq.com', '163.com', '126.com', '188.com', 'yeah.net', 'sina.com', 'hotmail.com', 'live.com',
    'rael.cc','grr.la', 'guerrillamail.com', 'ruu.kr', 'arasj.net',
    'moakt.cc', 'disbox.net', 'tmpmail.org', 'tmpmail.net'
))

ALLOWED_EMAIL_DOMAIN = getattr(settings, 'ALLOWED_EMAIL_DOMAIN', (
    'gmail.com', 'naver.com', 'hanmail.net', 'nate.com', 'daum.net', 'jr.naver.com',
    'hanmir.com', 'dreamwiz.com', 'paran.com', 'kakao.com', 'lycos.co.kr', 'sayclub.com', 'empal.com',
    'icloud.com', 'korea.com', 'nexon.com', 'freechal.com', 'netian.com', 'cyworld.com', 'nexonclub.com', 'hanafos.com',
    'empas.com', 'chol.com',

    # yahoo.co.kr yahoo.com hotmail.com live.com msn.com outlook.com me.com
))
