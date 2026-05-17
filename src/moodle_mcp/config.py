from functools import lru_cache

from pydantic import AliasChoices, AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_secret_key: SecretStr = Field(default=SecretStr("dev-secret-change-me"))
    app_allowed_origins: str = "http://localhost,http://app.localhost"
    agent_runtime: str = "legacy"
    allow_user_id_override: bool = False

    moodle_base_url: AnyHttpUrl = Field(default="http://localhost")
    moodle_token: SecretStr | None = None
    moodle_rest_format: str = "json"
    moodle_creator_user_ids: str = ""
    mcp_server_url: AnyHttpUrl | None = None
    mcp_client_transport: str = "streamable-http"

    llm_base_url: AnyHttpUrl = Field(
        default="https://api.openai.com/v1",
        validation_alias=AliasChoices("LITELLM_BASE_URL", "LLM_BASE_URL"),
    )
    llm_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("LITELLM_API_KEY", "LLM_API_KEY"),
    )
    llm_provider: str = Field(
        default="openai",
        validation_alias=AliasChoices("LITELLM_PROVIDER", "LLM_PROVIDER"),
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("LITELLM_MODEL", "LLM_MODEL"),
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.app_allowed_origins.split(",") if origin.strip()]

    @property
    def creator_user_ids(self) -> set[int]:
        ids: set[int] = set()
        for raw_id in self.moodle_creator_user_ids.split(","):
            raw_id = raw_id.strip()
            if raw_id:
                ids.add(int(raw_id))
        return ids

    @property
    def moodle_token_value(self) -> str:
        if not self.moodle_token or not self.moodle_token.get_secret_value():
            raise ValueError("MOODLE_TOKEN is required for Moodle Web Services calls.")
        return self.moodle_token.get_secret_value()

    @property
    def llm_api_key_value(self) -> str:
        if not self.llm_api_key or not self.llm_api_key.get_secret_value():
            raise ValueError("LITELLM_API_KEY or LLM_API_KEY is required for agent responses.")
        return self.llm_api_key.get_secret_value()

    @property
    def litellm_model(self) -> str:
        if "/" in self.llm_model:
            return self.llm_model
        return f"{self.llm_provider}/{self.llm_model}"

    def validate_runtime(self) -> None:
        if self.agent_runtime == "adk" and not self.mcp_server_url:
            raise ValueError("MCP_SERVER_URL is required when AGENT_RUNTIME=adk.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
