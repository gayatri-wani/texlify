import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS
)


def hash_password(password: str) -> str:
    # bcrypt hard limit is 72 bytes — truncate safely
    truncated = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.hash(truncated)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        truncated = plain.encode("utf-8")[:72].decode("utf-8", errors="ignore")
        return pwd_context.verify(truncated, hashed)
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload.update({
        "exp":  datetime.utcnow() + timedelta(
                    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
        "iat":  datetime.utcnow(),
    })
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    payload.update({
        "exp":  datetime.utcnow() + timedelta(
                    days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh",
        "iat":  datetime.utcnow(),
    })
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


def generate_random_token(length: int = 64) -> str:
    return secrets.token_urlsafe(length)


def hash_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()