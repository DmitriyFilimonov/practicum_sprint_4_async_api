from typing import Optional


def map_sorting(sort: Optional[str]):
    if not sort:
        return None

    field = sort

    if sort.startswith("-"):
        field = sort[1:]

        return field, "desc"

    return field, "asc"
