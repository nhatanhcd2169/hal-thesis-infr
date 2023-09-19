import os
from celery.schedules import crontab

REDIS_URL = os.environ.get("REDIS_URL", None)

broker_url = REDIS_URL
result_backend = REDIS_URL

beat_schedule = {
    "regression-analysis": {
        "task": "tasks.regression_analyze",
        "schedule": crontab(minute="*/1"),
    },
}

imports = ["tasks"]