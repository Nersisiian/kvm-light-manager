from pydantic_settings import BaseSettings


class AgentSettings(BaseSettings):
    ZMQ_BIND_ADDR: str = "tcp://0.0.0.0:5555"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    LOG_LEVEL: str = "INFO"
    SIM_ERROR_RATE: float = 0.05

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = AgentSettings()