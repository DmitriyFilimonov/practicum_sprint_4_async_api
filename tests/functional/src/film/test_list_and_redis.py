import uuid
from typing import Any, Awaitable, Callable

import pytest

from tests.functional.settings import settings


@pytest.mark.parametrize(
    "query_data, expected_response",
    [
        (
            {"genres": ["7e717ef7-1d80-4a80-a6ef-502be18aaa87"]},
            {"status": 200, "length": 10},
        ),
        (
            {"genres": ["56396d84-6f96-488c-a2c3-22c8484cf813"]},
            {"status": 200, "length": 10},
        ),
        (
            {"genres": ["d72c15a9-39e3-4dce-91cc-603c7a8eda3d"]},
            {"status": 200, "length": 20},
        ),
        (
            {"genres": ["11b5e108-3a62-431b-a0aa-7eefe6912838"]},
            {"status": 200, "length": 0},
        ),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_list_and_redis(
    es_clear_index: Callable[[str], Awaitable[None]],
    make_get_request: Callable[[dict[str, str], str], Awaitable[tuple[int, Any]]],
    es_write_data: Callable[[list[dict], str, dict], Awaitable[None]],
    query_data: dict[str, str],
    expected_response: dict[str, int],
):

    # 1. Генерируем данные для ES
    elastic_data_1 = [
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
        for _ in range(10)
    ]

    # Создаем ещё десять фильмов, но меняем один из жанров
    elastic_data_2 = [
        {
            "id": str(uuid.uuid4()),
            "imdb_rating": 8.5,
            "genres": [
                {"id": "56396d84-6f96-488c-a2c3-22c8484cf813", "name": "Drama"},
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
        for _ in range(10)
    ]

    elastic_data = elastic_data_1 + elastic_data_2

    bulk_query: list[dict] = []
    for row in elastic_data:
        data = {"_index": settings.elastic_films_index, "_id": row["id"]}
        data.update({"_source": row})
        bulk_query.append(data)

    # 2. Загружаем данные в ES

    await es_write_data(
        bulk_query, settings.elastic_films_index, settings.elastic_films_index_mapping
    )

    # 3. Запрашиваем данные по API и заполняем Redis

    await make_get_request(query_data, "/api/v1/films")

    # 4. Очищаем elastic

    await es_clear_index(settings.elastic_films_index)

    status, body = await make_get_request(query_data, "/api/v1/films")

    # 5. Ппроверяем, что данные закешировались в Redis

    assert status == expected_response["status"]
    assert len(body) == expected_response["length"]
