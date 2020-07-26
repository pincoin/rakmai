from django.core.management.base import BaseCommand

from shop import models


class Command(BaseCommand):
    help = 'Update stock quantity'

    def handle(self, *args, **options):
        products = models.Product.objects.filter(status=models.Product.STATUS_CHOICES.enabled)

        for product in products:
            quantity = models.Voucher.objects \
                .filter(status=models.Voucher.STATUS_CHOICES.purchased, is_removed=False,product=product) \
                .count()

            product.stock_quantity = quantity
            product.save()

        self.stdout.write(self.style.SUCCESS('Successfully updated stock quantity'))
