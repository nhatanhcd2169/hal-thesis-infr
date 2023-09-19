from celery import Celery

app = Celery("linear-prediction")
app.config_from_object("celeryconfig")