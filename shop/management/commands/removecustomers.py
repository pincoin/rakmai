import uuid

import boto3
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.timezone import (
    timedelta, localtime, make_aware
)

from member.models import Profile


class Command(BaseCommand):
    help = 'Remove unregistered customers'

    def handle(self, *args, **options):
        session = boto3.session.Session()
        s3_client = session.client(
            service_name='s3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        customers = get_user_model().objects \
            .filter(last_login__lte=make_aware(localtime().now() - timedelta(days=365)),
                    is_staff=False,
                    is_superuser=False) \
            .select_related('profile')

        result = []

        for customer in customers:
            try:
                if customer.profile:
                    dirty = False
                    if customer.profile.photo_id:
                        s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                                Key='media/' + customer.profile.photo_id.name)
                        customer.profile.photo_id = ''
                        dirty = True
                    if customer.profile.card:
                        s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                                Key='media/' + customer.profile.card.name)
                        customer.profile.card = ''
                        dirty = True

                    if dirty:
                        customer.profile.save()
            except Profile.DoesNotExist:
                pass

            if len(customer.email) < 36:
                if customer.shop_order_owned.filter(is_removed=False):
                    customer.email = (customer.email + '_' + str(uuid.uuid4()))[:149]
                    customer.username = (customer.username + '_' + str(uuid.uuid4()))[:149]
                    customer.password = ''
                    customer.is_active = False
                    customer.is_staff = False
                    customer.is_superuser = False
                    customer.save()
                else:
                    result.append(customer)
                    customer.delete()

        print(result)

        self.stdout.write(self.style.SUCCESS(f'Successfully removed {len(result)} customers'))
