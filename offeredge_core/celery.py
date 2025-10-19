import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'offeredge_core.settings')

app = Celery('offeredge_core')

# Base config
app.conf.broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.conf.result_backend = os.environ.get('CELERY_RESULT_BACKEND', app.conf.broker_url)

# Respect Django settings with CELERY_ namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks.py in installed apps
app.autodiscover_tasks()

# Beat schedule: run auto-finalization periodically
app.conf.beat_schedule = {
    'auto-finalize-deals-every-1-min': {
        'task': 'deals.tasks.auto_finalize_deals_task',
        'schedule': 60.0,  # every 1 minute
    },
}
