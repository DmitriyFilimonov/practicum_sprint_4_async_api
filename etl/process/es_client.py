import json
from dataclasses import asdict
from typing import Any

import requests
from process.es_scheme import genres_scheme, movies_schema, persons_scheme
from settings import settings
from utils import backoff

ES_URL = f"http://{settings.es_host}:{settings.es_port}"


@backoff(border_sleep_time=60, factor=1.5, start_sleep_time=10)
def create_movies_scheme():
    headers = {"Content-Type": "application/json"}
    requests.put(f"{ES_URL}/movies", json=movies_schema, headers=headers)


@backoff(border_sleep_time=60, factor=1.5, start_sleep_time=10)
def create_genres_scheme():
    headers = {"Content-Type": "application/json"}
    requests.put(f"{ES_URL}/genres", json=genres_scheme, headers=headers)


@backoff(border_sleep_time=60, factor=1.5, start_sleep_time=10)
def create_persons_scheme():
    headers = {"Content-Type": "application/json"}
    requests.put(f"{ES_URL}/persons", json=persons_scheme, headers=headers)


@backoff(border_sleep_time=60, factor=1.5, start_sleep_time=10)
def send_bulk(index: str, bulk: list[Any]):

    bulk_req_body = ""
    for item in bulk:
        action = {"index": {"_index": index, "_id": item.id}}
        bulk_req_body += json.dumps(action) + "\n"
        bulk_req_body += json.dumps(asdict(item)) + "\n"

    headers = {"Content-Type": "application/json"}

    requests.post(f"{ES_URL}/_bulk", data=bulk_req_body, headers=headers)
