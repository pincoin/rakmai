from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Post


class PostSitemap(Sitemap):
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        posts = []

        for post in Post.objects.published():
            posts.append(('blog:post-detail', {'blog': 'www', 'pk': post.pk, 'slug': post.slug}))

        return posts

    def location(self, item):
        (name, kwargs) = item
        return reverse(name, kwargs=kwargs)
