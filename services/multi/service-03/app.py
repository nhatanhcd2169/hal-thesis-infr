import sys
import time
import requests
import dotenv
import os
from flask import Flask, request
from py_zipkin.zipkin import zipkin_span, create_http_headers_for_new_span, ZipkinAttrs, Kind, zipkin_client_span
from py_zipkin.request_helpers import create_http_headers
from py_zipkin.encoding import Encoding

dotenv.load_dotenv()

address = os.environ.get('ADDRESS', 'empty')

if address == 'empty':
    raise Exception('EMPTY ADDRESS')

ZIPKIN_URL = f'http://{address}:9411'

app = Flask(__name__)

def default_handler(encoded_span):
    body = encoded_span

    app.logger.debug("body %s", body)

    return requests.post(
        f"{ZIPKIN_URL}/api/v2/spans",
        data=body,
        headers={'Content-Type': 'application/json'},
    )


@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())

@zipkin_client_span(service_name='service_03', span_name='service_03_zzzzzz')
def zzzzzz():
    time.sleep(2)


@app.route('/')
def index():
    with zipkin_span(
        service_name='service_03',
        span_name='index_service_03',
        transport_handler=default_handler,
        port=5000,
        sample_rate=100,
        encoding=Encoding.V2_JSON
    ):
        zzzzzz()
    return 'OK', 200


app.run(debug=True, host='0.0.0.0', threaded=True)