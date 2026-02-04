from tests.functional.settings import settings
from typing import Any, Awaitable, Callable
import pytest
import uuid


@pytest.mark.parametrize(
    "query_data, expected_response",
    [
        ({"query": "Ridley Scott"}, {"status": 200, "length": 1}),
        ({"query": "qwerty12345"}, {"status": 200, "length": 0}),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_es_search(
    es_clear_index: Callable[[str], Awaitable[None]],
    make_get_request: Callable[[dict[str, str], str], Awaitable[tuple[int, Any]]],
    es_write_data: Callable[[list[dict], str, dict], Awaitable[None]],
    query_data: dict[str, str],
    expected_response: dict[str, int],
):
    elastic_data = [
        {
            "id": str(uuid.uuid4()),
            "name": "Ridley Scott",
            "films": [{"id": str(uuid.uuid4()), "roles": ["Director", "Screenwriter"]}],
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Charlie Chaplin",
            "films": [
                {
                    "id": str(uuid.uuid4()),
                    "roles": ["Director", "Screenwriter", "Actor"],
                }
            ],
        },
    ]

    bulk_query: list[dict] = []
    for row in elastic_data:
        data = {"_index": "persons", "_id": row["id"]}
        data.update({"_source": row})
        bulk_query.append(data)

    # 2. Загружаем данные в ES

    await es_write_data(
        bulk_query,
        settings.elastic_persons_index,
        settings.elastic_persons_index_mapping,
    )

    # 3. Запрашиваем данные из ES по API

    status, body = await make_get_request(query_data, "/api/v1/persons/search")

    # 4. Очищаем elastic

    await es_clear_index(settings.elastic_persons_index)

    status, body = await make_get_request(query_data, "/api/v1/persons/search")

    # 5. Ппроверяем, что данные закешировались в Redis

    assert status == expected_response["status"]
    assert len(body) == expected_response["length"]
