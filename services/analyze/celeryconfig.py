import os
import json
from celery.schedules import crontab

REDIS_URL = os.environ.get("REDIS_URL", None)
assert REDIS_URL

PREDICT_RANGE = os.environ.get("PREDICT_RANGE", "{}")
PREDICT_RANGE = json.loads(PREDICT_RANGE)

broker_url = REDIS_URL
result_backend = REDIS_URL

args = (PREDICT_RANGE, )

beat_schedule = {
    "regression-analysis": {
        "task": "tasks.regression_analyze",
        "schedule": crontab(minute="*/1"),
        "args": args
    },
}

imports = ["tasks"]