from typing import Optional
from pydantic import BaseModel

from typing import Any, Awaitable, Callable


import pytest


class FilmDetailResponsePerson(BaseModel):
    id: str
    name: str


class FilmDetailsResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    directors_names: list[str]
    actors_names: list[str]
    writers_names: list[str]
    directors: list[FilmDetailResponsePerson]
    actors: list[FilmDetailResponsePerson]
    writers: list[FilmDetailResponsePerson]


@pytest.mark.parametrize(
    "query_data, expected_response",
    [
        (
            {},
            {"status": 200},
        ),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_list_and_redis(
    es_clear_index: Callable[[None], Awaitable[None]],
    make_get_request: Callable[[dict[str, str], str], Awaitable[tuple[int, Any]]],
    es_write_data: Callable[[list[dict]], Awaitable[None]],
    query_data: dict[str, str],
    expected_response: dict[str, int],
):

    # 1. Генерируем данные для ES

    uuid = "b45bd7bc-2e16-46d5-b125-983d356768c6"

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

    data = {"_index": "movies", "_id": elastic_data["id"]}
    data.update({"_source": elastic_data})
    bulk_query.append(data)

    # 2. Загружаем данные в ES

    await es_write_data(bulk_query)

    # 3. Запрашиваем данные по API и заполняем Redis

    await make_get_request(query_data, "/api/v1/films/" + uuid)

    # 4. Очищаем elastic

    await es_clear_index()

    status, body = await make_get_request(query_data, "/api/v1/films/" + uuid)

    # 5. Ппроверяем, что данные закешировались в Redis

    expected_film = FilmDetailsResponse(**elastic_data)
    pydentified_response = FilmDetailsResponse(**body)

    assert pydentified_response == expected_film

    assert status == expected_response["status"]
