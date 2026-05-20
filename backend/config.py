from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    openrouter_api_key: str  # no default — fails fast if not set
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    classification_model: str = "mistralai/mistral-7b-instruct"
    draft_model: str = "anthropic/claude-3-haiku-20240307"
    confidence_threshold: float = 0.70
    max_retries: int = 2
    chroma_path: str = "./chroma_db"
    sqlite_path: str = "./tickets.db"
    site_url: str = "https://ticket-triage.railway.app"

settings = Settings()
