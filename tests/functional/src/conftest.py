from elasticsearch.helpers import async_bulk

from elasticsearch import AsyncElasticsearch
import pytest_asyncio

from tests.functional.settings import settings


@pytest_asyncio.fixture(name="es_client")
async def es_client():
    es_client = AsyncElasticsearch(
        hosts=f"http://{settings.elastic_host}:{settings.elastic_port}",
        verify_certs=False,
    )
    yield es_client
    await es_client.close()


@pytest_asyncio.fixture(name="es_write_data")
def es_write_data(es_client: AsyncElasticsearch):
    async def inner(data: list[dict]):
        if await es_client.indices.exists(index=settings.elastic_index):
            await es_client.indices.delete(index=settings.elastic_index)
        await es_client.indices.create(
            index=settings.elastic_index, **settings.elastic_index_mapping
        )

        updated, errors = await async_bulk(client=es_client, actions=data, refresh=True)

        if errors:
            raise Exception("Ошибка записи данных в Elasticsearch")

    return inner
