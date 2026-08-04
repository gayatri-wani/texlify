from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, Index
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class CommandStatus(str, enum.Enum):
    processing = "processing"
    success    = "success"
    failed     = "failed"


class CommandHistory(Base):
    __tablename__ = "command_history"

    id                = Column(Integer, primary_key=True, index=True)
    user_id           = Column(Integer, nullable=False)
    document_id       = Column(Integer, nullable=False)
    command_text      = Column(Text, nullable=False)
    parsed_actions    = Column(Text, nullable=True)
    status            = Column(Enum(CommandStatus),
                               default=CommandStatus.processing)
    error_message     = Column(Text, nullable=True)
    backup_filename   = Column(String(500), nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    created_at        = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_cmd_doc_created", "document_id", "created_at"),
        Index("ix_cmd_user_created", "user_id", "created_at"),
    )