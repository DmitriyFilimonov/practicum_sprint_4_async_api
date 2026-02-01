import aiohttp
from elasticsearch.helpers import async_bulk

from elasticsearch import AsyncElasticsearch
import pytest_asyncio

from tests.functional.settings import settings


@pytest_asyncio.fixture(name="http_client", scope="session")
async def http_client():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest_asyncio.fixture(name="make_get_request")
def make_get_request(http_client):
    async def inner(query_data: dict[str, str], api_route:str):
        url = settings.service_url + api_route

        async with http_client.get(url, params=query_data) as response:
            body = await response.json()
            headers = response.headers
            status = response.status

        return status, body

    return inner


@pytest_asyncio.fixture(name="es_client", scope="session")
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
