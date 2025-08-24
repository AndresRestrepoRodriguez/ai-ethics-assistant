from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class VectorDBConfig(BaseSettings):
    host: str = "localhost"
    port: int = 6333
    collection_name: str = "ai_ethics_docs"


class LLMConfig(BaseSettings):
    model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"
    api_key: SecretStr | None = None
    max_tokens: int = 1000
    temperature: float = 0.7


class S3Config(BaseSettings):
    bucket_name: str = ""
    region: str = "us-east-1"
    access_key_id: SecretStr | None = None
    secret_access_key: SecretStr | None = None


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    dev_mode: bool = False
    log_level: str = "INFO"

    root_path: str = ""
    cors_origins: Optional[str] = None

    # Vector database configuration
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)

    # LLM configuration
    llm: LLMConfig = Field(default_factory=LLMConfig)

    # S3 configuration
    s3: S3Config = Field(default_factory=S3Config)

    # Document processing settings
    chunk_size: int = 1000
    chunk_overlap: int = 200


def get_config() -> Config:
    return Config()
