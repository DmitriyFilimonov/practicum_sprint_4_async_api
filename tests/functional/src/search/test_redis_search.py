from typing import Any, Awaitable, Callable
import uuid

import pytest


#  Название теста должно начинаться со слова `test_`
#  Любой тест с асинхронными вызовами нужно оборачивать декоратором `pytest.mark.asyncio`, который следит за запуском и работой цикла событий.


@pytest.mark.parametrize(
    "query_data, expected_response",
    [
        ({"query": "Bim bam boom"}, {"status": 200, "length": 100}),
        ({"query": "qwerty12345"}, {"status": 200, "length": 0}),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_redis_search(
    es_clear_index: Callable[[None], Awaitable[None]],
    make_get_request: Callable[[dict[str, str], str], Awaitable[tuple[int, Any]]],
    es_write_data: Callable[[list[dict]], Awaitable[None]],
    query_data: dict[str, str],
    expected_response: dict[str, int],
):

    # 1. Генерируем данные для ES
    elastic_data = [
        {
            "id": str(uuid.uuid4()),
            "imdb_rating": 8.5,
            "genres": [
                {"id": "7e717ef7-1d80-4a80-a6ef-502be18aaa87", "name": "Action"},
                {"id": "d72c15a9-39e3-4dce-91cc-603c7a8eda3d", "name": "Sci-Fi"},
            ],
            "title": "Bim bam boom",
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
        for _ in range(160)
    ]

    bulk_query: list[dict] = []
    for row in elastic_data:
        data = {"_index": "movies", "_id": row["id"]}
        data.update({"_source": row})
        bulk_query.append(data)

    # 2. Загружаем данные в ES

    await es_write_data(bulk_query)

    # 3. Запрашиваем данные по API и заполняем Redis

    await make_get_request(query_data, "/api/v1/films/search")

    # 4. Очищаем elastic

    await es_clear_index()

    status, body = await make_get_request(query_data, "/api/v1/films/search")

    # 5. Ппроверяем, что данные закешировались в Redis

    assert status == expected_response["status"]
    assert len(body) == expected_response["length"]
