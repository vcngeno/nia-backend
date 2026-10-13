from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CHILD_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Anthropic API
    ANTHROPIC_API_KEY: str
    
    # Server
    PORT: int = 8000
    ENVIRONMENT: str = "production"
    
    # CORS - Updated for Railway frontend
    CORS_ORIGINS: str = "https://nia-frontend-production.up.railway.app,http://localhost:5173"
    
    @property
    def cors_origins_list(self):
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    def validate_runtime_security(self):
        """Reject unsafe settings when starting the production service."""
        if self.ENVIRONMENT.lower() != "production":
            return

        if len(self.SECRET_KEY) < 32:
            raise RuntimeError(
                "SECRET_KEY must be at least 32 characters in production"
            )

        if self.DEBUG:
            raise RuntimeError("DEBUG must be disabled in production")

        if self.CORS_ORIGINS.strip() == "*":
            raise RuntimeError("Wildcard CORS is not allowed in production")
    
    # Debug mode
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

# Initialize settings
db_url = os.getenv("DATABASE_URL", "")

# Railway fix: Convert postgresql:// to postgresql+asyncpg://
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

settings = Settings(
    DATABASE_URL=db_url,
    SECRET_KEY=os.getenv("SECRET_KEY", ""),
    ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY", ""),
    ALGORITHM=os.getenv("ALGORITHM", "HS256"),
    ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    CHILD_TOKEN_EXPIRE_MINUTES=int(os.getenv("CHILD_TOKEN_EXPIRE_MINUTES", "60")),
    PORT=int(os.getenv("PORT", "8000")),
    ENVIRONMENT=os.getenv("ENVIRONMENT", "production"),
    CORS_ORIGINS=os.getenv("CORS_ORIGINS", "https://nia-frontend-production.up.railway.app,http://localhost:5173"),
    DEBUG=os.getenv("DEBUG", "False").lower() == "true"
)
