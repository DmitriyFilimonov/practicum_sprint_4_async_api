from dataclasses import asdict
import requests
import json
from settings import settings
from process.entities.models import FilmWorkESDoc
from utils import backoff

from process.es_scheme import schema

ES_URL = f"http://{settings.es_host}:{settings.es_port}"


@backoff(border_sleep_time=60, factor=1.5, start_sleep_time=10)
def create_scheme():
    headers = {"Content-Type": "application/json"}
    requests.put(f"{ES_URL}/movies", json=schema, headers=headers)


@backoff(border_sleep_time=60, factor=1.5, start_sleep_time=10)
def send_bulk(bulk: list[FilmWorkESDoc]):

    bulk_req_body = ""
    for fw in bulk:
        action = {"index": {"_index": "movies", "_id": fw.id}}
        bulk_req_body += json.dumps(action) + "\n"
        bulk_req_body += json.dumps(asdict(fw)) + "\n"

    headers = {"Content-Type": "application/json"}

    requests.post(f"{ES_URL}/_bulk", data=bulk_req_body, headers=headers)
