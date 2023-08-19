FROM python:3.10

WORKDIR /web

COPY looper/app.py .

COPY .env .

RUN pip install python-dotenv

RUN pip install requests

CMD python app.py
