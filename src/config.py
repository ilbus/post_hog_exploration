from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PostHog Exploration Pipeline"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    ASYNC_DATABASE_URL: str
    REDIS_URL: str
    QUEUE_NAME: str
    DLQ_NAME: str
    API_SECRET_KEY: str

    # worker settings
    BATCH_SIZE: int = 100
    FLUSH_INTERVAL: float = 2.0  # seconds

    # db pool settings
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
