import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    GENERATION_MODE: str = "quality"  # fast or quality
    DEMO_OFFLINE_MODE: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
