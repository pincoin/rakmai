from decimal import Decimal

from django.conf import settings

DEFAULT_STORE = getattr(settings, 'DEFAULT_STORE', 'default')

CART_SESSION_KEY = getattr(settings, 'CART_SESSION_KEY', 'CART')

CARD_CART_SESSION_KEY = getattr(settings, 'CARD_CART_SESSION_KEY', 'CARD_CART')

OPENING_TIME = getattr(settings, 'OPENING_TIME', 10)

CLOSING_TIME = getattr(settings, 'CLOSING_TIME', 23)

RECENT_ACCUMULATIVE_DAYS = getattr(settings, 'RECENT_ACCUMULATIVE_DAYS', 30)

ONE_DAY_ACCUMULATIVE_TOTAL = getattr(settings, 'ONE_DAY_ACCUMULATIVE_TOTAL', Decimal(100000))

RECENT_ACCUMULATIVE_TOTAL = getattr(settings, 'RECENT_ACCUMULATIVE_TOTAL', Decimal(300000))

FIRST_ORDER_LIMIT_HOURS = getattr(settings, 'FIRST_ORDER_LIMIT_HOURS', 48)

SUSPICIOUS_AMOUNT10 = getattr(settings, 'SUSPICIOUS_AMOUNT10', Decimal(100000))

SUSPICIOUS_AMOUNT15 = getattr(settings, 'SUSPICIOUS_AMOUNT15', Decimal(150000))

SUSPICIOUS_AMOUNT20 = getattr(settings, 'SUSPICIOUS_AMOUNT20', Decimal(200000))

SUSPICIOUS_AMOUNT30 = getattr(settings, 'SUSPICIOUS_AMOUNT30', Decimal(300000))

SUSPICIOUS_AMOUNT50 = getattr(settings, 'SUSPICIOUS_AMOUNT50', Decimal(500000))

RECENT_LOGIN_IP_DAYS = getattr(settings, 'RECENT_LOGIN_IP_DAYS', 7)

RECENT_LOGIN_IP_HOURS = getattr(settings, 'RECENT_LOGIN_IP_HOURS', 6)

REFUNDABLE_DAYS = getattr(settings, 'REFUNDABLE_DAYS', 3)

PAYPAL_MINIMUM_ORDER_AMOUNT = getattr(settings, 'PAYPAL_MINIMUM_ORDER_AMOUNT', Decimal(9000))

CURRENCY_RATE = getattr(settings, 'CURRENCY_RATE', {
    'KRW': {
        'locale': 'ko_KR.UTF-8',
        'rate': Decimal(1.0),
    },
    'USD': {
        'locale': 'en_US.UTF-8',
        'rate': Decimal(0.00105000),  # 0.00106000
    },
})

UNAVAILABLE_NIGHT_PRODUCTS = getattr(settings, '', ['엔코인',
                                                    '와우캐시',
                                                    '매니아선불쿠폰',
                                                    '아이템베이선불쿠폰'])

NO_REFUND = getattr(settings, 'NO_REFUND', False)
