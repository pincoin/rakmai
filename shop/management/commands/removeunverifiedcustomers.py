from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.timezone import (
    timedelta, localtime, make_aware
)

from member.models import Profile


class Command(BaseCommand):
    help = 'Remove unverified customers'

    def handle(self, *args, **options):
        customers = get_user_model().objects.prefetch_related('profile') \
            .filter(profile__phone_verified_status=Profile.PHONE_VERIFIED_STATUS_CHOICES.unverified,
                    date_joined__lte=make_aware(localtime().now() - timedelta(days=365 * 2)),
                    profile__last_purchased=None,
                    is_staff=False,
                    is_superuser=False)

        for customer in customers:
            if not customer.shop_order_owned.filter(is_removed=False):
                print(customer.email, customer)
                customer.delete()

        self.stdout.write(self.style.SUCCESS('Successfully unverified customers'))
