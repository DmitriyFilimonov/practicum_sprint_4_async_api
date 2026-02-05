from tests.functional.settings import settings
from typing import Any, Awaitable, Callable
import pytest


#  Название теста должно начинаться со слова `test_`
#  Любой тест с асинхронными вызовами нужно оборачивать декоратором `pytest.mark.asyncio`, который следит за запуском и работой цикла событий.


@pytest.mark.parametrize(
    "query_data, expected_response",
    [
        ({"query": "molestias placeat"}, {"status": 200, "length": 1}),
        ({"query": "dolor"}, {"status": 200, "length": 1}),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_record_by_string(
    generate_test_films,
    make_get_request: Callable[[dict[str, str], str], Awaitable[tuple[int, Any]]],
    es_write_data: Callable[[list[dict], str, dict], Awaitable[None]],
    query_data: dict[str, str],
    expected_response: dict[str, int],
):

    # 1. Генерируем данные для ES
    elastic_data_1 = generate_test_films(
        count=1,
        description="Lorem ipsum dolor sit amet consectetur, adipisicing elit. Maxime porro ipsa quos voluptatum corrupti vero cum in, _ reiciendis repellendus veniam, laudantium voluptatem iste. Adipisci asperiores eius repellendus id.",
    )

    elastic_data_2 = generate_test_films(
        count=1,
        description="Lorem ipsum _ sit amet consectetur, adipisicing elit. Maxime porro ipsa quos voluptatum corrupti vero cum in, molestias placeat reiciendis repellendus veniam, laudantium voluptatem iste. Adipisci asperiores eius repellendus id.",
    )

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

    # 3. Запрашиваем данные из ES по API

    status, body = await make_get_request(query_data, "/api/v1/films/search")

    # 4. Проверяем ответ

    assert status == expected_response["status"]
    assert len(body) == expected_response["length"]
