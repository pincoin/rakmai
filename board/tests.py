from django.apps import apps
from django.test import TestCase

from .apps import BoardConfig

class BoardTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    # apps
    def test_apps(self):
        self.assertEqual(BoardConfig.name, 'board')
        self.assertEqual(BoardConfig.verbose_name, 'board')
        self.assertEqual(apps.get_app_config('board').name, 'board')

    # models

    # widgets

    # forms

    # viewmixins

    # views
