import os
import time

from elasticsearch import Elasticsearch

ELASTIC_HOST = os.getenv("ELASTIC_HOST")
ELASTIC_PORT = os.getenv("ELASTIC_PORT")


if __name__ == "__main__":
    es_client = Elasticsearch(
        hosts=f"http://{ELASTIC_HOST}:{ELASTIC_PORT}",
    )
    while True:
        if es_client.ping():
            break
        time.sleep(1)
