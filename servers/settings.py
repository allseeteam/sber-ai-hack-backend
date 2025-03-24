from typing import Optional, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict 
# Read more about pydantic_settings here: https://docs.pydantic.dev/latest/concepts/pydantic_settings/.


class LLMSettings(BaseSettings):
    """
    Class for storing LLM settings for OpenAI-compatible API

    Attributes:
        BASE_API (str): The base API URL for the LLM. Default is None (OpenAI).
        API_KEY (str): The API key for the LLM.
        MODEL (str): The model name for the LLM.
    """
    model_config = SettingsConfigDict(env_prefix="LLM_", env_file=".env", extra='ignore')

    BASE_API: Optional[str] = None
    API_KEY: str
    MODEL: str = "gpt-4o-2024-08-06"
    PROXY_URL: Optional[str] = None


class CheckpointerSettings(BaseSettings):
    """
    Class for storing LangGraph checkpointer settings with PostgreSQL configuration

    Attributes:
        POSTGRES_HOST (str): PostgreSQL host. Default is "localhost".
        POSTGRES_PORT (int): PostgreSQL port. Default is 5432.
        POSTGRES_DB (str): PostgreSQL database name. Default is "graph_memory".
        POSTGRES_USER (str): PostgreSQL user.
        POSTGRES_PASSWORD (str): PostgreSQL password.
        DB_URI (property): Constructed PostgreSQL connection string.
    """
    model_config = SettingsConfigDict(env_prefix="CHECKPOINTER_", env_file=".env", extra='ignore')

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "checkpointer"
    POSTGRES_USER: str = "checkpointer"
    POSTGRES_PASSWORD: str

    @property
    def POSGRES_CONNECTION_STRING(self) -> str:
        """Construct PostgreSQL connection string from settings"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


class Settings(BaseSettings):
    llm: LLMSettings = LLMSettings()
    checkpointer: CheckpointerSettings = CheckpointerSettings()


settings = Settings()