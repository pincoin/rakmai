from django.apps import apps
from django.test import TestCase

from .apps import MemberConfig


class BlogTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    # apps
    def test_apps(self):
        self.assertEqual(MemberConfig.name, 'member')
        self.assertEqual(MemberConfig.verbose_name, 'member')
        self.assertEqual(apps.get_app_config('member').name, 'member')

    # models

    # widgets

    # forms

    # viewmixins

    # views
