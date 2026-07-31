from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id                   = Column(Integer, primary_key=True, index=True)
    full_name            = Column(String(255), nullable=False)
    email                = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password      = Column(String(255), nullable=False)
    is_active            = Column(Boolean, default=True)
    is_verified          = Column(Boolean, default=True)
    verification_token   = Column(String(255), nullable=True)
    reset_password_token = Column(String(255), nullable=True)
    reset_token_expires  = Column(DateTime, nullable=True)
    created_at           = Column(DateTime, server_default=func.now())
    updated_at           = Column(DateTime, server_default=func.now(),
                                  onupdate=func.now())