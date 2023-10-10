from celery import Celery

app = Celery("timeseries-prediction")
app.config_from_object("celeryconfig")