FROM python:3.10

COPY . /web

WORKDIR /web

RUN pip install -r requirements.txt

CMD flask --app app run --host=0.0.0.0 --port=5000