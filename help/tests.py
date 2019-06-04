from django.apps import apps
from django.test import TestCase

from .apps import HelpConfig


class HelpTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    # apps
    def test_apps(self):
        self.assertEqual(HelpConfig.name, 'help')
        self.assertEqual(HelpConfig.verbose_name, 'help')
        self.assertEqual(apps.get_app_config('help').name, 'help')

    # models

    # widgets

    # forms

    # viewmixins

    # views
