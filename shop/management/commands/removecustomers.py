import uuid

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.timezone import (
    timedelta, localtime, make_aware
)


class Command(BaseCommand):
    help = 'Remove unregistered customers'

    def handle(self, *args, **options):
        customers = get_user_model().objects \
            .filter(last_login__lte=make_aware(localtime().now() - timedelta(days=365)),
                    is_staff=False,
                    is_superuser=False)

        for customer in customers:
            if customer.shop_order_owned.filter(is_removed=False):
                customer.email = customer.email + '_' + str(uuid.uuid4())
                customer.username = customer.username + '_' + str(uuid.uuid4())
                customer.password = ''
                customer.is_active = False
                customer.is_staff = False
                customer.is_superuser = False
                customer.save()
            else:
                customer.delete()

        self.stdout.write(self.style.SUCCESS('Successfully removed customers'))
