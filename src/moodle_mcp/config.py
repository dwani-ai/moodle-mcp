from functools import lru_cache

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_secret_key: SecretStr = Field(default=SecretStr("dev-secret-change-me"))
    app_allowed_origins: str = "http://localhost,http://app.localhost"

    moodle_base_url: AnyHttpUrl = Field(default="http://localhost")
    moodle_token: SecretStr | None = None
    moodle_rest_format: str = "json"

    llm_base_url: AnyHttpUrl = Field(default="https://api.openai.com/v1")
    llm_api_key: SecretStr | None = None
    llm_model: str = "gpt-4o-mini"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.app_allowed_origins.split(",") if origin.strip()]

    @property
    def moodle_token_value(self) -> str:
        if not self.moodle_token or not self.moodle_token.get_secret_value():
            raise ValueError("MOODLE_TOKEN is required for Moodle Web Services calls.")
        return self.moodle_token.get_secret_value()

    @property
    def llm_api_key_value(self) -> str:
        if not self.llm_api_key or not self.llm_api_key.get_secret_value():
            raise ValueError("LLM_API_KEY is required for agent responses.")
        return self.llm_api_key.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()
