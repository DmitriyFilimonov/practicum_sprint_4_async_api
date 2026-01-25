import time

from elasticsearch import Elasticsearch
from tests.functional import settings


if __name__ == "__main__":
    es_client = Elasticsearch(
        hosts=f"{settings.settings.elastic_host}:{settings.settings.elastic_port}",
        validate_cert=False,
        use_ssl=False,
    )
    while True:
        if es_client.ping():
            break
        time.sleep(1)
