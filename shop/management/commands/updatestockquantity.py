from django.core.management.base import BaseCommand
from django.db.models import (
    Count, Case, When
)

from shop import models


class Command(BaseCommand):
    help = 'Update stock quantity'

    def handle(self, *args, **options):
        queryset = models.Product.objects \
            .filter(status=models.Product.STATUS_CHOICES.enabled) \
            .select_related('category') \
            .prefetch_related('vouchers') \
            .annotate(stock_count=Count(Case(When(vouchers__status=models.Voucher.STATUS_CHOICES.purchased,
                                                  vouchers__is_removed=False,
                                                  then=1))))

        for item in queryset:
            models.Product.objects.filter(code=item.code).update(stock_quantity=item.stock_count)

        self.stdout.write(self.style.SUCCESS('Successfully made purchase order'))
