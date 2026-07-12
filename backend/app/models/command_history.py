from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.database import Base


class CommandStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    success = "success"
    failed = "failed"


class CommandHistory(Base):
    __tablename__ = "command_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    command_text = Column(Text, nullable=False)
    parsed_actions = Column(Text, nullable=True)
    status = Column(Enum(CommandStatus), default=CommandStatus.pending)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    backup_filename = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="command_history")
    document = relationship("Document", back_populates="command_history")