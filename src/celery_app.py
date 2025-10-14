from celery import Celery

from config import get_settings

settings = get_settings()

celery_app = Celery(
    "cinema_app",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,
)


# periodic task template


# @celery_app.task
# def test_task():
#     print("Test task!")
#
#
# celery_app.conf.beat_schedule = {
#     "test-task-every-10-seconds": {
#         "task": "celery_app.test_task",
#         "schedule": 10.0,
#     },
# }
