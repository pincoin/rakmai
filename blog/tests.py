from django.apps import apps
from django.test import TestCase

from .apps import BlogConfig


class BlogTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    # apps
    def test_apps(self):
        self.assertEqual(BlogConfig.name, 'blog')
        self.assertEqual(BlogConfig.verbose_name, 'blog')
        self.assertEqual(apps.get_app_config('blog').name, 'blog')

    # models

    # widgets

    # forms

    # viewmixins

    # views
