from django.core.management.base import BaseCommand

from member.models import Profile


class Command(BaseCommand):
    help = 'Revoke customer allow order'

    def handle(self, *args, **options):
        Profile.objects \
            .select_related('user') \
            .filter(allow_order=True, user__is_active=True) \
            .update(allow_order=False)

        self.stdout.write(self.style.SUCCESS('Successfully revoked profiles'))
