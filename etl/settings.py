from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    postgres_user: str
    postgres_password: str
    # DB name
    postgres_db: str

    sql_port: str
    # DB service name
    sql_host: str
    # default DB scheme
    sql_options: str
    search_path: str

    # elastic search service name
    es_host: str
    es_port: str

    def get_dsl(self):
        return {
            "dbname": self.postgres_db,
            "user": self.postgres_user,
            "password": self.postgres_password,
            "host": self.sql_host,
            "port": self.sql_port,
        }


settings = Settings()
