import math

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import (
    Count, Case, When
)
from django.template.defaultfilters import date as _date
from django.template.defaultfilters import linebreaks as _linebreaks
from django.utils import timezone

from shop import models
from shop.tasks import send_notification_email


class Command(BaseCommand):
    help = 'Purchase order'

    def handle(self, *args, **options):
        queryset = models.Product.objects \
            .filter(status=models.Product.STATUS_CHOICES.enabled) \
            .select_related('category') \
            .prefetch_related('vouchers') \
            .annotate(stock_count=Count(Case(When(vouchers__status=models.Voucher.STATUS_CHOICES.purchased,
                                                  vouchers__is_removed=False,
                                                  then=1)))) \
            .exclude(maximum_stock_level=0) \
            .order_by('category', 'position')

        email_string = []

        item_name = ''

        count = 0

        for item in queryset:
            if item_name != item.name:
                email_string.append('----\n')
                item_name = item.name

            if item.stock_count < 0.7 * item.minimum_stock_level + 0.3 * item.maximum_stock_level:
                count += 1
                email_string.append('{} {} {}\n'
                                    .format(item.name, item.subtitle,
                                            int(math.ceil((item.maximum_stock_level - item.stock_count) / 10.0) * 10)))

        if count:
            send_notification_email.delay(
                '[핀코인] {} 주문'.format(_date(timezone.make_aware(timezone.localtime().now()), 'Y-m-d H:i')),
                'dummy',
                settings.EMAIL_JONGHWA,
                [settings.EMAIL_HAN, ],
                _linebreaks(''.join(email_string)),
            )

        self.stdout.write(self.style.SUCCESS('Successfully made purchase order'))
