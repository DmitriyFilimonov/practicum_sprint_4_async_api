from pydantic_settings import BaseSettings

from tests.functional.es_mappings import (
    ELASTIC_FILMS_INDEX_MAPPING,
    ELASTIC_PERSONS_INDEX_MAPPING,
    ELASTIC_GENRES_INDEX_MAPPING,
)


class Settings(BaseSettings):
    service_url: str = "http://fastapi:8000"

    project_name: str
    api_port: str

    redis_host: str
    redis_port: str

    elastic_host: str
    elastic_port: str

    elastic_films_index: str = "movies"
    elastic_films_index_mapping: dict = ELASTIC_FILMS_INDEX_MAPPING

    elastic_persons_index: str = "persons"
    elastic_persons_index_mapping: dict = ELASTIC_PERSONS_INDEX_MAPPING

    elastic_genres_index: str = "genres"
    elastic_genres_index_mapping: dict = ELASTIC_GENRES_INDEX_MAPPING


settings = Settings()
