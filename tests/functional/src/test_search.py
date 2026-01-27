import datetime
import uuid

import aiohttp
import pytest
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from tests.functional.settings import settings

#  Название теста должно начинаться со слова `test_`
#  Любой тест с асинхронными вызовами нужно оборачивать декоратором `pytest.mark.asyncio`, который следит за запуском и работой цикла событий.


@pytest.mark.asyncio
async def test_search():

    # 1. Генерируем данные для ES
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
        for _ in range(60)
    ]

    bulk_query: list[dict] = []
    for row in elastic_data:
        data = {"_index": "movies", "_id": row["id"]}
        data.update({"_source": row})
        bulk_query.append(data)

    # 2. Загружаем данные в ES
    elastic_client = AsyncElasticsearch(
        hosts=f"http://{settings.elastic_host}:{settings.elastic_port}",
        verify_certs=False,
    )
    if await elastic_client.indices.exists(index=settings.elastic_index):
        await elastic_client.indices.delete(index=settings.elastic_index)
    await elastic_client.indices.create(
        index=settings.elastic_index, **settings.elastic_index_mapping
    )

    updated, errors = await async_bulk(
        client=elastic_client, actions=bulk_query, refresh="wait_for"
    )

    await elastic_client.close()

    if errors:
        for error in errors:
            print(error)

        raise Exception("Ошибка записи данных в Elasticsearch")

    # 3. Запрашиваем данные из ES по API

    session = aiohttp.ClientSession()
    url = "http://fastapi:8000" + "/api/v1/films/search/"
    query_data = {"query": "The Star"}
    async with session.get(url, params=query_data) as response:
        text = await response.text()
        print(text)
        body = await response.json()
        headers = response.headers
        status = response.status
    await session.close()

    # 4. Проверяем ответ

    assert status == 200
    assert len(body) == 60
