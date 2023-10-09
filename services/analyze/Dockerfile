FROM python:3.11

WORKDIR /app

RUN pip install psycopg2==2.9.7
RUN pip install flask==3.0.0
RUN pip install pandas==2.1.0
RUN pip install scikit-learn==1.3.0
RUN pip install celery[redis]
RUN pip install elasticsearch==8.8.0

COPY *.py .
