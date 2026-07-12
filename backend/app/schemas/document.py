from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentResponse(BaseModel):
    id: int
    title: str
    original_filename: str
    file_size: int
    page_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommandRequest(BaseModel):
    command: str


class CommandResponse(BaseModel):
    message: str
    actions_performed: list
    status: str