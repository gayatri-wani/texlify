from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger
from sqlalchemy.sql import func
from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    id                = Column(Integer, primary_key=True, index=True)
    user_id           = Column(Integer, index=True, nullable=False)
    title             = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    stored_filename   = Column(String(500), nullable=False)
    file_path         = Column(String(1000), nullable=False)
    file_size         = Column(BigInteger, default=0)
    page_count        = Column(Integer, default=1)
    is_active         = Column(Boolean, default=True)
    created_at        = Column(DateTime, server_default=func.now())
    updated_at        = Column(DateTime, server_default=func.now(),
                               onupdate=func.now())