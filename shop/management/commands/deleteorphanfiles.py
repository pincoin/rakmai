import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q

from member.models import Profile


class Command(BaseCommand):
    help = 'Delete orphan files'

    def handle(self, *args, **options):
        media_root = getattr(settings, 'MEDIA_ROOT', None)

        # subdirectory: member
        for root, dirs, files in os.walk(os.path.join(media_root, 'member')):
            for file in files:
                if '35x20_q85_crop-smart' in file:
                    self.stdout.write(self.style.SUCCESS(os.path.join(root, file)))
                    os.unlink(os.path.join(root, file))
                else:
                    if not Profile.objects.filter(Q(photo_id__contains=file) | Q(card__contains=file)).exists():
                        self.stdout.write(self.style.SUCCESS(os.path.join(root, file)))
                        os.unlink(os.path.join(root, file))

        # subdirectory: blog

        # subdirectory: book

        # subdirectory: shop

        self.stdout.write(self.style.SUCCESS('Successfully deleted orphan files'))
