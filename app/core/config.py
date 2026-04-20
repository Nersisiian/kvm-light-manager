from typing import Optional, Literal
from pydantic import Field, field_validator, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = Field(default=False)

    API_HOST: str = "0.0.0.0"
    API_PORT: int = Field(8000, ge=1024, le=65535)
    API_WORKERS: int = Field(4, ge=1, le=8)

    API_KEY_ENABLED: bool = False
    API_KEY_HEADER: str = "X-API-Key"
    API_KEYS: list[str] = Field(default_factory=list)

    POSTGRES_HOST: str
    POSTGRES_PORT: int = Field(5432, ge=1, le=65535)
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_POOL_SIZE: int = Field(10, ge=1, le=50)
    POSTGRES_MAX_OVERFLOW: int = Field(20, ge=0)

    @property
    def DATABASE_URL(self) -> str:
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        ))

    REDIS_HOST: str
    REDIS_PORT: int = Field(6379, ge=1, le=65535)
    REDIS_DB: int = Field(0, ge=0, le=15)
    REDIS_PASSWORD: Optional[str] = None

    @property
    def REDIS_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    AGENT_ZMQ_ENDPOINT: str = "tcp://agent:5555"
    AGENT_REQUEST_TIMEOUT: int = Field(30, ge=1)
    AGENT_RETRY_ATTEMPTS: int = Field(3, ge=1)
    AGENT_HEARTBEAT_INTERVAL: int = Field(10, ge=1)

    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = Field(5, ge=1)
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = Field(60, ge=10)

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_JSON: bool = True
    LOG_INCLUDE_HEADERS: bool = False

    METRICS_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_prefix="KVM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("API_KEYS", mode="before")
    def parse_api_keys(cls, v):
        if isinstance(v, str):
            return [key.strip() for key in v.split(",") if key.strip()]
        return v


settings = Settings()