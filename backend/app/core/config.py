import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "ZeroGate ZTNA Simulator API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    
    # Database: SQLite default for zero-config local development, PostgreSQL compatible
    DATABASE_URL: str = "sqlite:///./zerogate.db"
    
    # Security Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "super_secret_key_change_in_production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days for demo purposes
    
    # Demo credentials
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "Admin@123")
    DEMO_USER_PASSWORD: str = os.getenv("DEMO_USER_PASSWORD", "User@123")

    # CORS Origins
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
