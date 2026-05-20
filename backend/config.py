import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    classification_model: str = "mistralai/mistral-7b-instruct"
    draft_model: str = "anthropic/claude-haiku-4-5"
    confidence_threshold: float = 0.70
    max_retries: int = 2
    chroma_path: str = "./chroma_db"
    sqlite_path: str = "./tickets.db"
    site_url: str = "https://ticket-triage.railway.app"

    class Config:
        env_file = ".env"

settings = Settings()
