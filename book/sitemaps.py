from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Page


class PageSitemap(Sitemap):
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        posts = []

        for page in Page.objects.public().order_by('tree_id', 'lft'):
            posts.append(('book:page-detail', {'book': page.book_id, 'pk': page.pk}))

        return posts

    def location(self, item):
        (name, kwargs) = item
        return reverse(name, kwargs=kwargs)
