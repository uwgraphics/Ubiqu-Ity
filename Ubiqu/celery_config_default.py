# coding=utf-8

# List of modules to import when Celery starts.
CELERY_IMPORTS = ("tasks",)

BROKER_URL = 'amqp://'
CELERY_RESULT_BACKEND = 'amqp://'
# SENTRY_DSN = None
OUTPUT_ROOT = "../temp"