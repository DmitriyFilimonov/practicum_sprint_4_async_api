import aiohttp
from elasticsearch.helpers import async_bulk

from elasticsearch import AsyncElasticsearch
import pytest
import pytest_asyncio

from tests.functional.settings import settings
import uuid


@pytest_asyncio.fixture(name="generate_test_films")
def generate_test_films():
    def inner(count: int):
        elastic_data = [
            {
                "id": str(uuid.uuid4()),
                "imdb_rating": 8.5,
                "genres": [
                    {"id": "7e717ef7-1d80-4a80-a6ef-502be18aaa87", "name": "Action"},
                    {"id": "d72c15a9-39e3-4dce-91cc-603c7a8eda3d", "name": "Sci-Fi"},
                ],
                "title": "The Star",
                "description": "New World",
                "directors_names": ["Stan"],
                "actors_names": ["Ann", "Bob"],
                "writers_names": ["Ben", "Howard"],
                "directors": [],
                "actors": [
                    {"id": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95", "name": "Ann"},
                    {"id": "fb111f22-121e-44a7-b78f-b19191810fbf", "name": "Bob"},
                ],
                "writers": [
                    {"id": "caf76c67-c0fe-477e-8766-3ab3ff2574b5", "name": "Ben"},
                    {"id": "b45bd7bc-2e16-46d5-b125-983d356768c6", "name": "Howard"},
                ],
            }
            for _ in range(count)
        ]

        return elastic_data

    return inner


@pytest_asyncio.fixture(name="http_client", scope="session")
async def http_client():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest_asyncio.fixture(name="make_get_request")
def make_get_request(http_client: aiohttp.ClientSession):
    async def inner(query_data: dict[str, str], api_route: str):
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


@pytest_asyncio.fixture(name="es_clear_index")
def es_clear_index(es_client: AsyncElasticsearch):
    async def inner():
        await es_client.delete_by_query(
            index=settings.elastic_index,
            body={"query": {"match_all": {}}},
            refresh=True,
        )

    return inner
