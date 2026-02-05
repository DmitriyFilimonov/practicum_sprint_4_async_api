import uuid

from tests.functional.settings import settings

from pydantic import BaseModel

from typing import Any, Awaitable, Callable


import pytest


class PersonDetailsResponseFilm(BaseModel):
    uuid: str
    roles: list[str]


class PersonDetailsResponseItem(BaseModel):
    uuid: str
    full_name: str
    films: list[PersonDetailsResponseFilm]


person_uuid = "f1b1cce3-2fe9-4966-aee6-7a94dcc360f4"
film_uuid = "8427dc8c-a85f-4aef-822b-f2d83db1e820"


@pytest.mark.parametrize(
    "query_data, expected_response",
    [
        (
            {},
            {
                "status": 200,
                "body": {
                    "uuid": person_uuid,
                    "full_name": "Ridley Scott",
                    "films": [
                        {"uuid": film_uuid, "roles": ["Director", "Screenwriter"]}
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
    expected_response: dict[str, Any],
):

    # 1. Генерируем данные для ES

    elastic_data = {
        "id": person_uuid,
        "name": "Ridley Scott",
        "films": [{"id": film_uuid, "roles": ["Director", "Screenwriter"]}],
    }

    bulk_query: list[dict] = []

    data = {"_index": settings.elastic_persons_index, "_id": elastic_data["id"]}
    data.update({"_source": elastic_data})
    bulk_query.append(data)

    # 2. Загружаем данные в ES

    await es_write_data(
        bulk_query,
        settings.elastic_persons_index,
        settings.elastic_persons_index_mapping,
    )

    # 3. Запрашиваем данные по API и заполняем Redis

    await make_get_request(query_data, "/api/v1/persons/" + person_uuid)

    # 4. Очищаем elastic

    await es_clear_index(settings.elastic_persons_index)

    status, body = await make_get_request(query_data, "/api/v1/persons/" + person_uuid)

    # 5. Ппроверяем, что данные закешировались в Redis

    pydentified_expected_response = PersonDetailsResponseItem(
        **expected_response["body"]
    )
    pydentified_response = PersonDetailsResponseItem(**body)

    assert pydentified_response == pydentified_expected_response

    assert status == expected_response["status"]
