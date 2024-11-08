from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MYSQL_DB_USERNAME: str
    MYSQL_DB_PASSWORD: str
    MYSQL_DB_HOST: str
    MYSQL_DB_PORT: int
    MYSQL_DB_NAME: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_BUCKET_NAME: str
    model_config = SettingsConfigDict(env_file="core/.env")


@lru_cache
def get_settings():
    return Settings()