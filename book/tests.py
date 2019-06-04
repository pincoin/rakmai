from django.apps import apps
from django.test import TestCase

from .apps import BookConfig


class BookTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    # apps
    def test_apps(self):
        self.assertEqual(BookConfig.name, 'book')
        self.assertEqual(BookConfig.verbose_name, 'book')
        self.assertEqual(apps.get_app_config('book').name, 'book')

    # models

    # widgets

    # forms

    # viewmixins

    # views
