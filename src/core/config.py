import os

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseEnvSettings(BaseSettings):
    """Базовый класс настроек переменных окружения."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class EnvSettings(BaseEnvSettings):
    """Настройки из переменных окружения."""

    PROJECT_NAME: str

    HOST: str
    PORT: int

    SWAGGER_URL: str = "/swagger/"


class OpenAISettings(BaseEnvSettings):
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str


class ParserSettings(BaseEnvSettings):
    HEADERS: dict[str, str] = {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }


class Settings(
    EnvSettings,
    OpenAISettings,
    ParserSettings
):

    @property
    def openapi_url(self) -> str:
        return self.SWAGGER_URL + "openapi.json"


settings = Settings()