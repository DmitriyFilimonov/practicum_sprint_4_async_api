from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    project_name: str

    api_port: str

    redis_host: str
    redis_port: str

    elastic_host: str
    elastic_port: str

settings = Settings()