import pytest


@pytest.mark.parametrize(
    "query_params, expected_status",
    [
        ({"query": 2}, 200),
        ({"page_number": 1, "page_size": 10}, 200),
        ({"page_number": 0, "page_size": 10}, 200),
        ({"page_number": -1, "page_size": 10}, 422),
        ({"page_number": 1, "page_size": 0}, 422),
        ({"page_number": 1, "page_size": -5}, 422),
        ({"page_number": 1, "page_size": 5000}, 422),
        ({"page_number": "not a number", "page_size": 10}, 422),
        (
            {
                "not_existed_parameter": "any value",
                "another_not_existed_parameter": 100500,
            },
            200,
        ),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_search_query_validation(make_get_request, query_params, expected_status):
    status, _ = await make_get_request(query_params, "/api/v1/persons/search")
    assert status == expected_status
