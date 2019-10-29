"""A script to trigger Django unit tests.

This is based on the conceit of defining a fake site project. This site is
not packaged with the application.

"""

import sys

import django
from django.conf import settings
from django.core.management import call_command


def _run():
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'test-only',
            }
        },
        INSTALLED_APPS=['vedm'],
    )

    django.setup()

    return call_command('test', 'vedm')


if __name__ == '__main__':
    sys.exit(bool(_run()))
