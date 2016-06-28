"""A standard implementation of celeryconfig.

See:
http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#entries
http://celery.readthedocs.org/en/latest/configuration.html#example-configuration-file
"""

from datetime import timedelta
import os
import sys

from service_layer.parsers import parser_passthrough


DESTINATION_PREFIX = 'data/'
REDIS_SERVER = 'redis.local'

BROKER_URL = 'redis://{hostname}:6379/0'.format(hostname=REDIS_SERVER)
BROKER_TRANSPORT_OPTIONS = {
    'fanout_prefix': True, 'fanout_patterns': True, 'visibility_timeout': 480
}

CELERY_RESULT_BACKEND = BROKER_URL
CELERY_TIMEZONE = 'UTC'
CELERYBEAT_SCHEDULE = {
    'update_all-on-interval': {
        'task': 'service_layer.tasks.update_all',  # complete name is needed
        'schedule': timedelta(seconds=10),
        'args': (),
    },
}

FEEDS = [
    """{
        'destination': 'file://example/index.html',
        'parser': parser_example,
        'url': 'http://example.com',
    }"""
]


def configure(overrides):
    """
    Applies custom configuration to global settings. Overrides can either be
    a python import path string like 'foo.bar.baz' or a filesystem path like
    'foo/bar/baz.py'
    :param overrides: an importable python path string like 'foo.bar' or a
                      filesystem path to a python file like 'foo/bar.py'
    """
    this = sys.modules[__name__]

    # Filesystem path to settings file
    if os.path.isfile(overrides):
        if sys.version_info >= (3, 0):
            with open(overrides) as f:
                code = compile(f.read(), overrides, 'exec')
                exec(code, this.__dict__)
        else:
            execfile(overrides, this.__dict__)
        return

    # Module import path settings file
    fromlist = [overrides.split('.')[-1]]
    overrides = __import__(overrides, this.__dict__, {}, fromlist)

    for attr in filter(lambda x: not x.startswith('_'), dir(overrides)):
        setattr(this, attr, getattr(overrides, attr))


# Append custom settings if exists
settings_file = os.environ.get('MSL_SETTINGS', '')
if settings_file:
    configure(settings_file)
