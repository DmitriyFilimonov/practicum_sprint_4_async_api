from enum import Enum

from src.models.film import FilmSortableFields


def map_sorting(sort: FilmSortableFields | None, sortable_fields: Enum):
    if not sort:
        return None

    field = sort

    if sort.startswith("-"):
        field = sortable_fields[sort[1:]]

        return field, "desc"

    return sortable_fields[field], "asc"
