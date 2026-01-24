from contextlib import asynccontextmanager
import logging

from src.api.v1 import films, genres, persons

from src.core.logger import LOGGING
from fastapi import APIRouter, FastAPI
from fastapi.responses import ORJSONResponse


from src.core import config
from src.db import elastic
from src.db import cache
from elasticsearch import AsyncElasticsearch


import uvicorn

router = APIRouter()


@asynccontextmanager
async def lifespan(_: FastAPI):
    cache.cache = cache.Cache(cache_db=cache.RedisCahce())

    await cache.cache.init()

    elastic.elastic_wrapper = elastic.ElasticWrapper(
        elastic=AsyncElasticsearch(
            hosts=[
                f"{config.ELASTIC_SCHEMA}{config.settings.elastic_host}:{config.settings.elastic_port}"
            ]
        )
    )

    yield

    await cache.cache.close()
    await elastic.elastic_wrapper.close()


app = FastAPI(
    # Конфигурируем название проекта. Оно будет отображаться в документации
    title=config.settings.project_name,
    # Адрес документации в красивом интерфейсе
    docs_url="/api/openapi",
    # Адрес документации в формате OpenAPI
    openapi_url="/api/openapi.json",
    # Можно сразу сделать небольшую оптимизацию сервиса
    # и заменить стандартный JSON-сериализатор на более шуструю версию, написанную на Rust
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


# Подключаем роутер к серверу, указав префикс /v1/films
# Теги указываем для удобства навигации по документации
app.include_router(films.router, prefix="/api/v1/films", tags=["films"])
app.include_router(genres.router, prefix="/api/v1/genres", tags=["genres"])
app.include_router(persons.router, prefix="/api/v1/persons", tags=["persons"])


if __name__ == "__main__":
    # Приложение может запускаться командой
    # `uvicorn main:app --host 0.0.0.0 --port 8000`
    # но чтобы не терять возможность использовать дебагер,
    # запустим uvicorn-сервер через python
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_config=LOGGING,
        log_level=logging.DEBUG,
    )
