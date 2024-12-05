from celery import Celery

from config import Config


def make_celery(app=None):
    celery = Celery(
        app.import_name,
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND
    )
    celery.conf.update(app.config)

    # Celery worker configurations to manage task visibility, retries, memory leaks, and shutdown behavior
    celery.conf.update(
        broker_transport_options = {
            'visibility_timeout': 3600,  # 1 hour
            'max_retries': 3,
        },
        worker_max_tasks_per_child = 50,  # Restart worker after 50 tasks to prevent memory leaks
        worker_shutdown_timeout = 60,  # Wait up to 60 seconds for tasks to complete on shutdown
    )
    celery.autodiscover_tasks()

    return celery
