from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./clm_database.db"
    
    # JWT
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Gemini AI
    gemini_api_key: str = ""
    # Any model id from the Gemini API; the alias tracks the current Flash release
    gemini_model: str = "gemini-flash-latest"
    
    # File Upload
    upload_dir: str = "./uploads"
    max_file_size: int = 10485760  # 10MB
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
