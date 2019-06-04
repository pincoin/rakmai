from django.apps import apps
from django.test import TestCase

from .apps import ShopConfig


class ShopTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    # apps
    def test_apps(self):
        self.assertEqual(ShopConfig.name, 'shop')
        self.assertEqual(ShopConfig.verbose_name, 'shop')
        self.assertEqual(apps.get_app_config('shop').name, 'shop')

    # models

    # widgets

    # forms

    # viewmixins

    # views
