import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from shop.models import Product


class Command(BaseCommand):
    help = 'Update review count'

    def handle(self, *args, **options):
        url = 'https://disqus.com/api/3.0/threads/set.json'
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Origin': 'https://disqus.com',
        }
        params = {
            'api_key': settings.DISQUS_API_KEY,
            'forum': settings.DISQUS_WEBSITE_SHORTNAME,
        }

        # retrieve all products
        products = Product.objects \
            .store('default') \
            .enabled() \
            .available() \
            .select_related('category', 'store')

        for product in products:
            params['thread:link'] = 'https://www.pincoin.co.kr{}'.format(
                reverse('shop:product-detail', args=(product.store.code, product.pk, product.code)))

            try:
                # retrieve review count
                response = requests.get(url, params=params, headers=headers)
                data = response.json()

                # update review count
                if data['response'] and 'posts' in data['response'][0]:
                    product.review_count = data['response'][0]['posts']
                    product.save()
                    self.stdout.write(self.style.SUCCESS(
                        '{} has {} comments'.format(params['thread:link'], data['response'][0]['posts'])))
                else:
                    self.stdout.write(self.style.ERROR(
                        '{} not found'.format(params['thread:link'])))
            except requests.exceptions.RequestException:
                pass

        # retrieve all products (PG)
        products = Product.objects \
            .store('default') \
            .enabled() \
            .available() \
            .select_related('category', 'store') \
            .filter(pg=True)

        for product in products:
            params['thread:link'] = 'https://card.pincoin.co.kr{}'.format(
                reverse('card:product-detail', args=(product.store.code, product.pk, product.code)))

            try:
                # retrieve review count
                response = requests.get(url, params=params, headers=headers)
                data = response.json()

                # update review count
                if data['response'] and 'posts' in data['response'][0]:
                    product.review_count_pg = data['response'][0]['posts']
                    product.save()
                    self.stdout.write(self.style.SUCCESS(
                        '{} has {} comments'.format(params['thread:link'], data['response'][0]['posts'])))
                else:
                    self.stdout.write(self.style.ERROR(
                        '{} not found'.format(params['thread:link'])))
            except requests.exceptions.RequestException:
                pass

        self.stdout.write(self.style.SUCCESS('Successfully updated product review count'))
