import requests
import time
import json
import dotenv
import os
import base64
import logging

logger = logging.getLogger("looper")

dotenv.load_dotenv()

INTERVAL = int(os.environ.get('INTERVAL', '6'))
address = os.environ.get('ADDRESS', 'empty')
if address == 'empty':
    raise Exception('EMPTY ADDRESS')

URL = address

if 'http' not in URL:
    URL = 'http://' + URL

URL += ':8000/service-'

tails = ['01', '02', '03', 'single']

itr = 0


headers = [
    {'Authorization': f'Basic %s' % base64.b64encode(b"dummy:dummy").decode()},
    {'Authorization': f'Basic %s' % base64.b64encode(b"dummier:dummier").decode()},
]

while True:
    itr += 1
    for tail in tails:
        for _ in range(20):
            requests.get(URL + tail, headers=headers[0])
            logging.info(f"Called [GET] {URL + tail}")
            requests.post(
                URL + tails[-1], 
                json={
                    'itr': itr,
                    'test': True
                },
                headers=headers[0]
            )
            logging.info(f"Called [POST] {URL + tails[-1]}")

    for _ in range(4):
        requests.get(URL + tail)
        logging.info(f"Called [GET] {URL + tail}")
        requests.post(
            URL + tails[-1], 
            json={
                'itr': itr,
                'test': True
            },
            headers=headers[1]
        )
        logging.info(f"Called [POST] {URL + tails[-1]}")

    time.sleep(INTERVAL)
    
