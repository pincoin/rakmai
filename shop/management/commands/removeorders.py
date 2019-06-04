from django.core.management.base import BaseCommand
from django.utils.timezone import timedelta, localtime, make_aware

from shop.models import Order


class Command(BaseCommand):
    help = 'Remove garbage orders'

    def handle(self, *args, **options):
        # orders removed by customers
        Order.objects.filter(is_removed=True).delete()

        # old pending orders
        Order.objects \
            .select_related('user') \
            .filter(is_removed=False,
                    status=Order.STATUS_CHOICES.payment_pending,
                    created__lte=make_aware(localtime().now() - timedelta(hours=1))) \
            .delete()

        self.stdout.write(self.style.SUCCESS('Successfully removed orders'))
