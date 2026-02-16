from tests.functional.settings import settings

from pydantic import BaseModel

from typing import Any, Awaitable, Callable


import pytest


class GenreResponse(BaseModel):
    id: str
    name: str
    description: str | None


genre_id = "b780d672-d3cc-4b6c-8439-bcf6333d4223"


@pytest.mark.parametrize(
    "route_parameter, expected_response",
    [
        (
            genre_id,
            {
                "status": 200,
                "body": {
                    "id": genre_id,
                    "name": "Drama",
                    "description": "test description",
                },
            },
        ),
        (
            "01c37dd9-3dfb-4948-875a-39de291f85f1",
            {
                "status": 404,
            },
        ),
        (
            "1",
            {
                "status": 422,
            },
        ),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_single_and_redis(
    es_clear_index: Callable[[str], Awaitable[None]],
    make_get_request: Callable[[dict[str, str], str], Awaitable[tuple[int, Any]]],
    es_write_data: Callable[[list[dict], str, dict], Awaitable[None]],
    route_parameter: str,
    expected_response: dict[str, Any],
):

    # 1. Генерируем данные для ES

    elastic_data = {
        "id": genre_id,
        "name": "Drama",
        "description": "test description",
    }

    bulk_query: list[dict] = []

    data = {"_index": settings.elastic_genres_index, "_id": elastic_data["id"]}
    data.update({"_source": elastic_data})
    bulk_query.append(data)

    # 2. Загружаем данные в ES

    await es_write_data(
        bulk_query,
        settings.elastic_genres_index,
        settings.elastic_genres_index_mapping,
    )

    # 3. Запрашиваем данные по API и заполняем Redis

    await make_get_request(None, "/api/v1/genres/" + route_parameter)

    # 4. Очищаем elastic

    await es_clear_index(settings.elastic_genres_index)

    status, body = await make_get_request(None, "/api/v1/genres/" + route_parameter)

    # 5. Проверяем, что данные закешировались в Redis

    assert status == expected_response["status"]

    if status == 200:
        pydentified_expected_response = GenreResponse(**expected_response["body"])
        pydentified_response = GenreResponse(**body)

        assert pydentified_response == pydentified_expected_response
