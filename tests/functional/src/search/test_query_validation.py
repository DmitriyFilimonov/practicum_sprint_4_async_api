import pytest


@pytest.mark.parametrize(
    "query_params, expected_status",
    [
        ({"page_number": 1, "page_size": 10}, 200),
        ({"page_number": 0, "page_size": 10}, 200),
        ({"page_number": -1, "page_size": 10}, 422),
        ({"page_number": 1, "page_size": 0}, 422),
        ({"page_number": 1, "page_size": -5}, 422),
        ({"page_number": "not a number", "page_size": 10}, 422),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_search_validation(
    make_get_request, query_params, expected_status
):
    status, _ = await make_get_request(query_params, "/api/v1/films/search")
    assert status == expected_status
