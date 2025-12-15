from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PostHog Exploration Pipeline"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    REDIS_URL: str
    QUEUE_NAME: str
    API_SECRET_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()