from typing import Any, Awaitable, Callable
import pytest


#  Название теста должно начинаться со слова `test_`
#  Любой тест с асинхронными вызовами нужно оборачивать декоратором `pytest.mark.asyncio`, который следит за запуском и работой цикла событий.


@pytest.mark.parametrize(
    "query_data, expected_response",
    [
        ({"query": "The Star"}, {"status": 200, "length": 60}),
        ({"query": "Mashed potato"}, {"status": 200, "length": 0}),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_es_search(
    generate_test_films,
    make_get_request: Callable[[dict[str, str], str], Awaitable[tuple[int, Any]]],
    es_write_data: Callable[[list[dict]], Awaitable[None]],
    query_data: dict[str, str],
    expected_response: dict[str, int],
):

    # 1. Генерируем данные для ES
    elastic_data = generate_test_films(60)

    bulk_query: list[dict] = []
    for row in elastic_data:
        data = {"_index": "movies", "_id": row["id"]}
        data.update({"_source": row})
        bulk_query.append(data)

    # 2. Загружаем данные в ES

    await es_write_data(bulk_query)

    # 3. Запрашиваем данные из ES по API

    status, body = await make_get_request(query_data, "/api/v1/films/search")

    # 4. Проверяем ответ

    assert status == expected_response["status"]
    assert len(body) == expected_response["length"]
