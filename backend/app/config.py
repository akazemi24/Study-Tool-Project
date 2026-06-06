from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Study Tool API"
    anthropic_api_key: str = ""
    database_url: str = ""
    openai_api_key: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    # token expires after 7 days
    # user needs to log in again
    jwt_expire_minutes: int = 60 * 24 * 7
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()