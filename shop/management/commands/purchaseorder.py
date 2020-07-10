import math
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
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
            .exclude(maximum_stock_level=0) \
            .order_by('category', 'position')

        email_string = []

        item_name = ''

        count = 0

        d = dict()

        for item in queryset:
            if item_name in d and d[item_name] and item_name != item.name:
                email_string.append('----\n\n')

            if item_name != item.name:
                item_name = item.name

            if item.stock_quantity < 0.7 * item.minimum_stock_level + 0.3 * item.maximum_stock_level:
                count += 1

                if item.name in d:
                    d[item.name] += 1
                else:
                    d[item.name] = 1

                if item.name == '넥슨카드' and item.list_price < Decimal('30000'):
                    email_string.append('{} {} {}매\n'
                                        .format(item.name, item.subtitle,
                                                int(math.ceil(
                                                    (item.maximum_stock_level - item.stock_quantity) / 100.0) * 100)))
                else:
                    email_string.append('{} {} {}매\n'
                                        .format(item.name, item.subtitle,
                                                int(math.ceil(
                                                    (item.maximum_stock_level - item.stock_quantity) / 10.0) * 10)))

        if count:
            title = '[핀코인] {} 주문'.format(_date(timezone.make_aware(timezone.localtime().now()), 'Y-m-d H:i'))
            content = ''.join(email_string)

            self.stdout.write(content)

            po = models.PurchaseOrder()
            po.title = title
            po.content = content
            po.save()

            send_notification_email.delay(
                title,
                content,
                settings.EMAIL_JONGHWA,
                [settings.EMAIL_HAN, ],
                _linebreaks(content),
            )

        self.stdout.write(self.style.SUCCESS('Successfully made purchase order'))
