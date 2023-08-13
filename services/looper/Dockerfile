FROM python:3.10

WORKDIR /app

COPY app.py .

COPY .env .

RUN pip install requests

RUN pip install python-dotenv

CMD python app.py
