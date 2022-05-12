import os

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        # create session to s3
        session = boto3.session.Session()
        s3_client = session.client(
            service_name='s3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        media_root = getattr(settings, 'MEDIA_ROOT', None)
        media_root_parent = os.path.join(os.path.dirname(os.path.dirname(media_root)), '', '')

        for root, dirs, files in os.walk(media_root):
            for file in files:
                full_path = os.path.join(root, file)
                upload_path = full_path.split(media_root_parent)[-1]
                try:
                    s3_client.upload_file(full_path, settings.AWS_STORAGE_BUCKET_NAME, upload_path)
                    self.stdout.write(self.style.SUCCESS(upload_path))
                except ClientError as e:
                    self.stdout.write(self.style.ERROR(upload_path))
