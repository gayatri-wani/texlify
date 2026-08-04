from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME:                    str  = "Texlify"
    APP_VERSION:                 str  = "1.0.0"
    DEBUG:                       bool = True
    ENVIRONMENT:                 str  = "development"
    DATABASE_URL:                str
    SECRET_KEY:                  str
    ALGORITHM:                   str  = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int  = 30
    REFRESH_TOKEN_EXPIRE_DAYS:   int  = 7
    ALLOWED_ORIGINS:             str  = "http://localhost:5173"
    GROQ_API_KEY:                str
    GROQ_TIMEOUT_SECONDS:        int  = 15
    MAX_FILE_SIZE_MB:            int  = 50
    UPLOAD_DIR:                  str  = "uploads"
    MAX_BACKUPS_PER_DOCUMENT:    int  = 5
    SMTP_EMAIL:                  str  = ""
    SMTP_PASSWORD:               str  = ""
    FRONTEND_URL:                str  = "http://localhost:5173"
    RATE_LIMIT_COMMANDS:         int  = 30
    RATE_LIMIT_UPLOADS:          int  = 10
    RATE_LIMIT_WINDOW_SEC:       int  = 60
    RATE_LIMIT_LOGIN_ATTEMPTS:   int  = 5
    RATE_LIMIT_LOGIN_WINDOW_SEC: int  = 300
    MAX_REQUEST_SIZE_MB:         int  = 100
    BCRYPT_ROUNDS:               int  = 12
    SENTRY_DSN:                  str  = ""
    LOG_FORMAT:                  str  = "json"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()