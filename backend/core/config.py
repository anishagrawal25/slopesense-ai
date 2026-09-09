"""
Application Configuration and Settings.
Supports PostgreSQL (with SQLite fallback for local development), JWT Auth, Twilio, and GEE credentials.
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Settings(BaseSettings):
    PROJECT_NAME: str = "SlopeSense AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database (PostgreSQL default, with automatic fallback for dev/demo)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'slopesense.db')}"
    )
    
    # Security / JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "slopesense-super-secret-key-sih-2026-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Twilio SMS / Voice Configuration
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID", None)
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN", None)
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER", None)
    TWILIO_MOCK_MODE: bool = os.getenv("TWILIO_MOCK_MODE", "true").lower() in ("true", "1", "t")
    
    # Google Earth Engine
    GEE_PROJECT: Optional[str] = os.getenv("GEE_PROJECT", "slopesense-ner-landslide")
    
    # File upload directory
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
