from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    APP_NAME: str = "Texlify"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:5173"
    OPENAI_API_KEY: str = "dummy"
    GEMINI_API_KEY: str = "dummy"
    GROQ_API_KEY: str
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_file = ".env"


settings = Settings()