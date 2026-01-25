import os
from logging import config as logging_config

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.logger import LOGGING


class Settings(BaseSettings):
    project_name: str

    api_port: str

    redis_host: str
    redis_port: str

    elastic_host: str
    elastic_port: str


settings = Settings()

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Название проекта. Используется в Swagger-документации
PROJECT_NAME = settings.project_name

API_PORT = settings.api_port

# Настройки Redis
REDIS_HOST = settings.redis_host
REDIS_PORT = int(settings.redis_port)

# Настройки Elasticsearch
ELASTIC_HOST = settings.elastic_host
ELASTIC_PORT = int(settings.elastic_port)

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ELASTIC_SCHEMA = "http://"
