from django.core.management.base import BaseCommand
from django.utils.timezone import (
    timedelta, localtime, make_aware
)

from member.models import Profile


class Command(BaseCommand):
    help = 'Limit customers who stopped buying.'

    def handle(self, *args, **options):
        results = Profile.objects \
            .filter(not_purchased_months=False,
                    last_purchased__lt=make_aware(localtime().now() - timedelta(hours=1440))) \
            .exclude(last_purchased__isnull=True) \
            .update(not_purchased_months=True)

        self.stdout.write(self.style.SUCCESS('limited: {}'.format(results)))

        results = Profile.objects \
            .filter(not_purchased_months=True,
                    repurchased__gt=make_aware(localtime().now() - timedelta(hours=1440)),
                    repurchased__lt=make_aware(localtime().now() - timedelta(hours=48))) \
            .exclude(last_purchased__isnull=True, repurchased__isnull=True) \
            .update(not_purchased_months=False, repurchased=None)

        self.stdout.write(self.style.SUCCESS('unlimited: {}'.format(results)))

        self.stdout.write(self.style.SUCCESS('Successfully limited customers who stopped buying.'))
