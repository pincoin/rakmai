from django.core.management.base import BaseCommand
from django.utils.timezone import timedelta, localtime, make_aware

from member.models import Profile


class Command(BaseCommand):
    help = 'Revoke customer phone verification'

    def handle(self, *args, **options):
        Profile.objects \
            .select_related('user') \
            .filter(phone_verified_status=Profile.PHONE_VERIFIED_STATUS_CHOICES.verified,
                    user__is_active=True,
                    user__last_login__lte=make_aware(localtime().now() - timedelta(days=180))) \
            .update(phone_verified_status=Profile.PHONE_VERIFIED_STATUS_CHOICES.revoked)

        self.stdout.write(self.style.SUCCESS('Successfully revoked profiles'))
