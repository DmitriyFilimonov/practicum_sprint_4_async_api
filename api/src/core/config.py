from logging import config as logging_config

from pydantic_settings import BaseSettings
from src.core.logger import LOGGING


class Settings(BaseSettings):
    project_name: str

    api_port: str

    redis_host: str
    redis_port: str

    elastic_host: str
    elastic_port: str

    elastic_scheme: str = "http://"


settings = Settings()

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)
