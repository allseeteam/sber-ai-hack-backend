from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class CodeSearchSettings(BaseSettings):
    """
    Class for storing Code Search API settings

    Attributes:
        QDRANT_URL (str): Qdrant server URL. Default is "http://localhost:6333".
        QDRANT_API_KEY (str): API key for Qdrant server. Optional.
        EMBEDDER_URL (str): Embedder service URL. Default is "http://embedder:8000/v1/embeddings".
        COLLECTION_NAME (str): Name of the Qdrant collection. Default is "code-search".
        REPOS_DIR (str): Directory to store cloned repositories. Default is "./data/semantic_search/repos".
        CONFIG_FILE (str): Path to repositories configuration file. Default is "repos_config.json".
        EMBEDDER_MODEL (str): Model name for embeddings. Default is "Qodo/Qodo-Embed-1-1.5B".
    """
    model_config = SettingsConfigDict(env_prefix="CODE_SEARCH_", env_file=".env", extra='ignore')

    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    EMBEDDER_URL: str = "http://embedder:8000/v1/embeddings"
    COLLECTION_NAME: str = "code-search"
    REPOS_DIR: str = "./data/semantic_search/repos"
    CONFIG_FILE: str = "repos_config.json"
    EMBEDDER_MODEL: str = "Qodo/Qodo-Embed-1-1.5B"


settings = CodeSearchSettings()