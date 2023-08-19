FROM python:3.10

WORKDIR /web

RUN pip install python-dotenv

RUN pip install requests

COPY looper/app.py .

COPY .env .

CMD python app.py
