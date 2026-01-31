from elasticsearch.helpers import async_bulk

from elasticsearch import AsyncElasticsearch
import pytest_asyncio

from tests.functional.settings import settings


@pytest_asyncio.fixture(name="es_write_data")
def es_write_data():
    async def inner(data: list[dict]):
        es_client = AsyncElasticsearch(
            hosts=f"http://{settings.elastic_host}:{settings.elastic_port}",
            verify_certs=False,
        )
        if await es_client.indices.exists(index=settings.elastic_index):
            await es_client.indices.delete(index=settings.elastic_index)
        await es_client.indices.create(
            index=settings.elastic_index, **settings.elastic_index_mapping
        )

        updated, errors = await async_bulk(client=es_client, actions=data, refresh=True)

        await es_client.close()

        if errors:
            raise Exception("Ошибка записи данных в Elasticsearch")

    return inner
