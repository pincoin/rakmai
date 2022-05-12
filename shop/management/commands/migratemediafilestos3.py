import mimetypes
import os

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        session = boto3.session.Session()
        s3_client = session.client(
            service_name='s3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        media_root_parent = os.path.join(os.path.dirname(os.path.dirname(settings.MEDIA_ROOT)), '', '')

        content_types = mimetypes.types_map
        content_types.update(
            {
                '.tgz': 'application/x-tar-gz',
            }
        )

        for root, dirs, files in os.walk(settings.MEDIA_ROOT):
            for file in files:
                full_path = os.path.join(root, file)
                upload_path = full_path.split(media_root_parent)[-1]
                try:
                    s3_client.upload_file(full_path,
                                          settings.AWS_STORAGE_BUCKET_NAME,
                                          upload_path,
                                          ExtraArgs={'Metadata': {
                                              'ContentType': mimetypes.types_map[
                                                  str(os.path.splitext(upload_path)[1]).lower()
                                              ],
                                          }})
                    self.stdout.write(self.style.SUCCESS(upload_path))
                except ClientError as e:
                    self.stdout.write(self.style.ERROR(upload_path))
