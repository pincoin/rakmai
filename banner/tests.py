from django.apps import apps
from django.test import TestCase

from .apps import BannerConfig


class BannerTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    # apps
    def test_apps(self):
        self.assertEqual(BannerConfig.name, 'banner')
        self.assertEqual(BannerConfig.verbose_name, 'banner')
        self.assertEqual(apps.get_app_config('banner').name, 'banner')

    # models

    # widgets

    # forms

    # viewmixins

    # views
