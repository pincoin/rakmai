from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import (
    Category, Product, NoticeMessage, Testimonials
)


class StaticSitemap(Sitemap):
    priority = 0.7
    changefreq = 'daily'

    def items(self):
        return [
            ('shop:home', {'store': 'default'}),
            ('help:faq-list', {'store': 'default'}),
            ('help:guide', {'store': 'default'}),
            ('shop:gamemeca-ranking', {'store': 'default'}),
            ('shop:gamemeca-news', {'store': 'default', 'slug': 'latest'}),
            ('shop:gamemeca-news', {'store': 'default', 'slug': 'top'}),
            ('shop:gamemeca-news', {'store': 'default', 'slug': 'review'}),
            ('shop:gamemeca-news', {'store': 'default', 'slug': 'preview'}),
            ('shop:gamemeca-news', {'store': 'default', 'slug': 'feature'}),
            ('site_terms', {}),
            ('site_privacy', {}),
        ]

    def location(self, item):
        (name, kwargs) = item
        return reverse(name, kwargs=kwargs)


class ProductCategorySitemap(Sitemap):
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        """
        Retrieve leaf nodes
        Category.objects.filter(children__isnull=True)
        Category.objects.filter(lft=F('rght') - 1)
        """
        categories = []

        for category in Category.objects.filter(level__gt=0):
            categories.append(('shop:product-category', {'store': 'default', 'slug': category.slug}))

        return categories

    def location(self, item):
        (name, kwargs) = item
        return reverse(name, kwargs=kwargs)


class ProductSitemap(Sitemap):
    priority = 0.9
    changefreq = 'daily'

    def items(self):
        products = []

        for product in Product.objects.store('default').enabled().available():
            products.append(('shop:product-detail', {'store': 'default', 'pk': product.pk, 'code': product.code}))

        return products

    def location(self, item):
        (name, kwargs) = item
        return reverse(name, kwargs=kwargs)


class NoticeMessageSitemap(Sitemap):
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        messages = []

        for message in NoticeMessage.objects.filter(store__code='default', is_removed=False).order_by('-created'):
            messages.append(('help:notice-detail', {'store': 'default', 'pk': message.pk}))

        return messages

    def location(self, item):
        (name, kwargs) = item
        return reverse(name, kwargs=kwargs)


class TestimonialsSitemap(Sitemap):
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        messages = []

        for message in Testimonials.objects.filter(store__code='default', is_removed=False).order_by('-created'):
            messages.append(('help:testimonials-detail', {'store': 'default', 'pk': message.pk}))

        return messages

    def location(self, item):
        (name, kwargs) = item
        return reverse(name, kwargs=kwargs)
