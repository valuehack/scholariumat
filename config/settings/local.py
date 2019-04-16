from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool('DJANGO_DEBUG', True)
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env('DJANGO_SECRET_KEY', default='fZHvlsQIedWTplwARXrwH0TI4MZXNFpSE7wl8X1a1g4TK4ckuopNSGyQEDmj8B8L')
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    "*",
]

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': ''
    }
}

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG  # noqa F405

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = env('SENDGRID_API_KEY', default='')
SENDGRID_SANDBOX_MODE_IN_DEBUG = env.bool('SENDGRID_SANDBOX_MODE_IN_DEBUG', default=True)

# https://docs.djangoproject.com/en/dev/ref/settings/#email-host
EMAIL_HOST = 'localhost'
# https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = 1025

# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ['debug_toolbar']  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': [
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ],
    'SHOW_TEMPLATE_CONTEXT': True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ['127.0.0.1', '10.0.2.2']


# API keys
# Zotero
ZOTERO_USER_ID = env('ZOTERO_USER_ID', default='')
ZOTERO_API_KEY = env('ZOTERO_API_KEY', default='')
ZOTERO_LIBRARY_TYPE = 'user'

# Buffer
BUFFER_ACCESS_TOKEN = env('BUFFER_ACCESS_TOKEN', default='')
BUFFER_SITE_IDS = env.list('BUFFER_SITE_IDS', default=[])

# Paypal
PAYPAL_SETTINGS = {
    'mode': 'sandbox',
    'client_id': env('PAYPAL_CLIENT_ID', default=''),
    'client_secret': env('PAYPAL_CLIENT_SECRET', default='')}

# Globee
GLOBEE_API_KEY = env('GLOBEE_API_KEY', default='')