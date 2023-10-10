import os
import json
from celery.schedules import crontab

REDIS_URL = os.environ.get("REDIS_URL", None)
assert REDIS_URL

broker_url = REDIS_URL
result_backend = REDIS_URL

beat_schedule = {
    "run-predict-pipeline": {
        "task": "tasks.run_pipeline",
        "schedule": crontab(minute="*/1"),
    },
}

imports = ["tasks"]
