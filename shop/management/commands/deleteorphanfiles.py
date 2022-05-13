from datetime import datetime, timedelta

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q

from member.models import Profile


class Command(BaseCommand):
    help = 'Delete s3 orphan files'

    def handle(self, *args, **options):
        yesterday = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')

        session = boto3.session.Session()
        s3_client = session.client(
            service_name='s3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=f'media/member/{yesterday}')

        orphans = []
        for page in pages:
            for content in page['Contents']:
                path = content['Key'].split('media/')[1]
                if not Profile.objects.filter(Q(photo_id__contains=path) | Q(card__contains=path)).exists():
                    orphans.append(path)
                    s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=content['Key'])

        print(orphans)
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {len(orphans)} orphan files'))

        #
        # media_root = getattr(settings, 'MEDIA_ROOT', None)

        # for root, dirs, files in os.walk(os.path.join(media_root, 'member')):
        #   for file in files:
        #     if '35x20_q85_crop-smart' in file:
        #       self.stdout.write(self.style.SUCCESS(os.path.join(root, file)))
        #       os.unlink(os.path.join(root, file))
        #     else:
        #       if not Profile.objects.filter(Q(photo_id__contains=file) | Q(card__contains=file)).exists():
        #       # self.stdout.write(self.style.SUCCESS(os.path.join(root, file)))
        #       os.unlink(os.path.join(root, file))

        # subdirectory: blog, book, shop
