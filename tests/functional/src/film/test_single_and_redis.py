from typing import Any, Awaitable, Callable

import pytest
from pydantic import BaseModel

from tests.functional.settings import settings


class FilmDetailResponsePerson(BaseModel):
    id: str
    name: str


class FilmDetailsResponse(BaseModel):
    id: str
    title: str
    description: str | None
    directors_names: list[str]
    actors_names: list[str]
    writers_names: list[str]
    directors: list[FilmDetailResponsePerson]
    actors: list[FilmDetailResponsePerson]
    writers: list[FilmDetailResponsePerson]


uuid = "b45bd7bc-2e16-46d5-b125-983d356768c6"


@pytest.mark.parametrize(
    "query_data, expected_response",
    [
        (
            {},
            {
                "status": 200,
                "body": {
                    "id": uuid,
                    "imdb_rating": 8.5,
                    "genres": [
                        {
                            "id": "7e717ef7-1d80-4a80-a6ef-502be18aaa87",
                            "name": "Action",
                        },
                        {
                            "id": "d72c15a9-39e3-4dce-91cc-603c7a8eda3d",
                            "name": "Sci-Fi",
                        },
                    ],
                    "title": "Bim bam boom",
                    "description": "New World",
                    "directors_names": ["Stan"],
                    "actors_names": ["Ann", "Bob"],
                    "writers_names": ["Ben"],
                    "directors": [],
                    "actors": [
                        {"id": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95", "name": "Ann"},
                        {"id": "fb111f22-121e-44a7-b78f-b19191810fbf", "name": "Bob"},
                    ],
                    "writers": [
                        {"id": "caf76c67-c0fe-477e-8766-3ab3ff2574b5", "name": "Ben"},
                    ],
                },
            },
        ),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_single_and_redis(
    es_clear_index: Callable[[str], Awaitable[None]],
    make_get_request: Callable[[dict[str, str], str], Awaitable[tuple[int, Any]]],
    es_write_data: Callable[[list[dict], str, dict], Awaitable[None]],
    query_data: dict[str, str],
    expected_response: dict[str, int],
):

    # 1. Генерируем данные для ES

    elastic_data = {
        "id": uuid,
        "imdb_rating": 8.5,
        "genres": [
            {"id": "7e717ef7-1d80-4a80-a6ef-502be18aaa87", "name": "Action"},
            {"id": "d72c15a9-39e3-4dce-91cc-603c7a8eda3d", "name": "Sci-Fi"},
        ],
        "title": "Bim bam boom",
        "description": "New World",
        "directors_names": ["Stan"],
        "actors_names": ["Ann", "Bob"],
        "writers_names": ["Ben"],
        "directors": [],
        "actors": [
            {"id": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95", "name": "Ann"},
            {"id": "fb111f22-121e-44a7-b78f-b19191810fbf", "name": "Bob"},
        ],
        "writers": [
            {"id": "caf76c67-c0fe-477e-8766-3ab3ff2574b5", "name": "Ben"},
        ],
    }

    bulk_query: list[dict] = []

    data = {"_index": settings.elastic_films_index, "_id": elastic_data["id"]}
    data.update({"_source": elastic_data})
    bulk_query.append(data)

    # 2. Загружаем данные в ES

    await es_write_data(
        bulk_query, settings.elastic_films_index, settings.elastic_films_index_mapping
    )

    # 3. Запрашиваем данные по API и заполняем Redis

    await make_get_request(query_data, "/api/v1/films/" + uuid)

    # 4. Очищаем elastic

    await es_clear_index(settings.elastic_films_index)

    status, body = await make_get_request(query_data, "/api/v1/films/" + uuid)

    # 5. Ппроверяем, что данные закешировались в Redis

    pydentified_expected_response = FilmDetailsResponse(**expected_response["body"])
    pydentified_response = FilmDetailsResponse(**body)

    assert pydentified_response == pydentified_expected_response

    assert status == expected_response["status"]
