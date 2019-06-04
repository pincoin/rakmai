from decimal import Decimal

from django.conf import settings

SUSPICIOUS_AMOUNT10 = getattr(settings, 'SUSPICIOUS_AMOUNT10', Decimal(100000))

SUSPICIOUS_AMOUNT15 = getattr(settings, 'SUSPICIOUS_AMOUNT15', Decimal(150000))

SUSPICIOUS_AMOUNT20 = getattr(settings, 'SUSPICIOUS_AMOUNT20', Decimal(200000))

SUSPICIOUS_AMOUNT30 = getattr(settings, 'SUSPICIOUS_AMOUNT30', Decimal(300000))

SUSPICIOUS_AMOUNT50 = getattr(settings, 'SUSPICIOUS_AMOUNT50', Decimal(500000))
