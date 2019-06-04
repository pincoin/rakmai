import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


def runtests():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'sandbox.settings.test'
    django.setup()

    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    failures = test_runner.run_tests([
        'rakmai',
        'member',
        'blog',
        'board',
        'book',
        'shop',
        'help',
        'rabop',
        'banner'
    ])
    sys.exit(bool(failures))


if __name__ == "__main__":
    runtests()
