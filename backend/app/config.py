import json
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./hr_sentinel.db"
    DB_ECHO: bool = False

    # JWT
    JWT_SECRET_KEY: str = "hr-sentinel-change-this-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI / OpenRouter
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENAI_MODEL: str = "openrouter/free"

    # ChromaDB (Phase 3)
    CHROMA_URL: str = "http://localhost:8000"

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10

    # CORS
    CORS_ORIGINS: str = '["http://localhost:5173", "http://localhost:3000"]'

    # Rate Limiting
    RATE_LIMIT_DEFAULT: int = 100

    # App
    APP_NAME: str = "HR Sentinel AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return '["http://localhost:5173"]'
            try:
                json.loads(v)
                return v
            except json.JSONDecodeError:
                return json.dumps([v])
        if isinstance(v, list):
            return json.dumps(v)
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        try:
            return json.loads(self.CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:5173"]


settings = Settings()
