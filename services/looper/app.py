import requests
import time
import json
import dotenv
import os

dotenv.load_dotenv()

address = os.environ.get('ADDRESS', 'empty')

if address == 'empty':
    raise Exception('EMPTY ADDRESS')

URL = address

if 'http' not in URL:
    URL = 'http://' + URL

URL += ':8000/service-'

tails = ['01', '02', '03', 'single']

itr = 0

while True:
    itr += 1
    for tail in tails:
        for _ in range(20):
            requests.get(URL + tail)
    requests.post(URL + tails[-1], {
        'itr': itr,
        'test': True
    })
    time.sleep(6)
    
