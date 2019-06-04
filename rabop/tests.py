from django.apps import apps
from django.test import TestCase

from .apps import RabopConfig


class RabopTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    # apps
    def test_apps(self):
        self.assertEqual(RabopConfig.name, 'rabop')
        self.assertEqual(RabopConfig.verbose_name, 'rabop')
        self.assertEqual(apps.get_app_config('rabop').name, 'rabop')

    # models

    # widgets

    # forms

    # viewmixins

    # views
