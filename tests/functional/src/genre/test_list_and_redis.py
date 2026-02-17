import uuid
from typing import Any, Awaitable, Callable

import pytest

from tests.functional.settings import settings


@pytest.mark.parametrize(
    "query_data, expected_response",
    [
        ({"page_number": 10}, {"status": 200, "length": 0}),
        ({"page_number": 0, "page_size": 50}, {"status": 200, "length": 50}),
        ({"page_size": 50}, {"status": 200, "length": 50}),
        ({"page_number": 3, "page_size": 50}, {"status": 200, "length": 10}),
        ({}, {"status": 200, "length": 100}),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_es_search(
    make_get_request: Callable[[dict[str, str], str], Awaitable[tuple[int, Any]]],
    es_write_data: Callable[[list[dict], str, dict], Awaitable[None]],
    query_data: dict[str, str],
    expected_response: dict[str, int],
):

    # 1. Генерируем данные для ES
    elastic_data = [
        {
            "id": str(uuid.uuid4()),
            "name": "Drama",
            "description": "test description",
        }
        for _ in range(160)
    ]

    bulk_query: list[dict] = []
    for row in elastic_data:
        data = {"_index": settings.elastic_genres_index, "_id": row["id"]}
        data.update({"_source": row})
        bulk_query.append(data)

    # 2. Загружаем данные в ES

    await es_write_data(
        bulk_query, settings.elastic_genres_index, settings.elastic_genres_index_mapping
    )

    # 3. Запрашиваем данные из ES по API

    status, body = await make_get_request(query_data, "/api/v1/genres")

    # 4. Проверяем ответ

    assert status == expected_response["status"]
    assert len(body) == expected_response["length"]
