SECRET_KEY = 'test-only-not-a-secret'
DEBUG = False
ALLOWED_HOSTS = ['testserver']
SECURE_SSL_REDIRECT = True
USE_TZ = True
ROOT_URLCONF = 'tests.urls'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'ct_django_health',
]
MIDDLEWARE = [
    'ct_django_health.middleware.HealthMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]
CT_HEALTH_CHECKS = [
    'ct_django_health.checks.database',
    'ct_django_health.checks.migrations',
]
