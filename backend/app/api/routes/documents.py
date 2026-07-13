from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.command_history import CommandHistory, CommandStatus
from app.services.document_service import DocumentService
from app.schemas.document import DocumentResponse, CommandRequest, CommandResponse
from app.agent.parser import parse_command
from app.agent.executor import DocumentExecutor, backup_document
import os
import json
import time

router = APIRouter(prefix="/documents", tags=["Documents"])

# ── Rate limiting (simple in-memory) ─────────────────────────────────────────
from collections import defaultdict
import threading

_rate_store = defaultdict(list)
_rate_lock  = threading.Lock()

RATE_LIMIT_COMMANDS   = 30   # max commands per window
RATE_LIMIT_WINDOW_SEC = 60   # per 60 seconds
RATE_LIMIT_UPLOADS    = 10   # max uploads per window


def _check_rate_limit(user_id: int, action: str = "command") -> bool:
    """Returns True if allowed, False if rate limited."""
    key    = f"{user_id}:{action}"
    now    = time.time()
    limit  = RATE_LIMIT_COMMANDS if action == "command" else RATE_LIMIT_UPLOADS
    with _rate_lock:
        timestamps = [t for t in _rate_store[key] if now - t < RATE_LIMIT_WINDOW_SEC]
        if len(timestamps) >= limit:
            _rate_store[key] = timestamps
            return False
        timestamps.append(now)
        _rate_store[key] = timestamps
        return True


# ── Schemas ───────────────────────────────────────────────────────────────────

class SelectionCommandRequest(BaseModel):
    command_type:    str
    selected_texts:  List[str]
    font_name:       Optional[str] = None
    font_size:       Optional[int] = None
    color:           Optional[str] = None
    highlight_color: Optional[str] = None
    alignment:       Optional[str] = None
    make_heading:    Optional[int] = None


class RenameRequest(BaseModel):
    title: str


class UndoRequest(BaseModel):
    backup_filename: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=DocumentResponse,
             status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not _check_rate_limit(current_user.id, "upload"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Upload limit reached. Max {RATE_LIMIT_UPLOADS} uploads per minute."
        )
    return DocumentService.upload(db, current_user, file)


@router.post("/upload-image")
def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload an image file to the server and return its server path for use in commands."""
    allowed_types = ["image/jpeg", "image/png", "image/gif",
                     "image/webp", "image/bmp", "image/tiff"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed (JPEG, PNG, GIF, WEBP, BMP)"
        )
    contents  = file.file.read()
    file_size = len(contents)
    if file_size > 10 * 1024 * 1024:  # 10MB limit for images
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size exceeds 10MB limit"
        )
    import uuid
    ext             = os.path.splitext(file.filename)[1].lower()
    stored_filename = f"img_{uuid.uuid4().hex}{ext}"
    img_dir         = os.path.join("uploads", str(current_user.id), "images")
    os.makedirs(img_dir, exist_ok=True)
    file_path = os.path.join(img_dir, stored_filename)
    with open(file_path, "wb") as f:
        f.write(contents)
    return {
        "filename":    stored_filename,
        "server_path": file_path,
        "url":         f"/api/v1/documents/images/{current_user.id}/{stored_filename}",
        "size":        file_size,
        "content_type": file.content_type
    }


@router.get("/images/{user_id}/{filename}")
def serve_image(
    user_id: int,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Serve an uploaded image file."""
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    file_path = os.path.join("uploads", str(user_id), "images", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return FileResponse(file_path)


@router.get("", response_model=List[DocumentResponse])
def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return DocumentService.get_all(db, current_user)


@router.patch("/{document_id}/rename")
def rename_document(
    document_id: int,
    request: RenameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rename a document."""
    document = DocumentService.get_by_id(db, document_id, current_user)
    if not request.title or not request.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty"
        )
    document.title = request.title.strip()
    db.commit()
    db.refresh(document)
    return {"message": "Document renamed successfully", "title": document.title}


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    DocumentService.delete(db, document_id, current_user)
    return {"message": "Document deleted successfully"}


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = DocumentService.get_by_id(db, document_id, current_user)
    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    return FileResponse(
        path=document.file_path,
        filename=document.original_filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@router.get("/{document_id}/preview")
def preview_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = DocumentService.get_by_id(db, document_id, current_user)
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    try:
        html = DocumentService.convert_to_html(document.file_path)
        return HTMLResponse(content=html)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview failed: {str(e)}"
        )


@router.get("/{document_id}/backups")
def get_backups(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of available backups for a document."""
    document = DocumentService.get_by_id(db, document_id, current_user)
    backup_dir  = os.path.dirname(document.file_path)
    base_name   = os.path.basename(document.file_path)
    backups = []
    try:
        for f in os.listdir(backup_dir):
            if f.startswith(base_name + ".backup_"):
                backup_time = f.split(".backup_")[1]
                backups.append({
                    "filename": f,
                    "timestamp": backup_time,
                    "display":  f"{backup_time[:4]}-{backup_time[4:6]}-{backup_time[6:8]} "
                                f"{backup_time[9:11]}:{backup_time[11:13]}:{backup_time[13:15]}"
                })
    except Exception:
        pass
    backups.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"backups": backups[:10]}  # return latest 10


@router.post("/{document_id}/undo")
def undo_command(
    document_id: int,
    request: UndoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restore document from a backup file."""
    document = DocumentService.get_by_id(db, document_id, current_user)
    backup_dir  = os.path.dirname(document.file_path)
    backup_path = os.path.join(backup_dir, request.backup_filename)
    if not os.path.exists(backup_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup not found: {request.backup_filename}"
        )
    # Security: ensure backup belongs to this user's document
    if not request.backup_filename.startswith(os.path.basename(document.file_path)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this backup"
        )
    import shutil
    shutil.copy2(backup_path, document.file_path)
    return {"message": "Document restored successfully", "backup": request.backup_filename}


@router.post("/{document_id}/command", response_model=CommandResponse)
def execute_command(
    document_id: int,
    request: CommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Rate limiting
    if not _check_rate_limit(current_user.id, "command"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many commands. Max {RATE_LIMIT_COMMANDS} per minute."
        )

    document = DocumentService.get_by_id(db, document_id, current_user)
    history  = CommandHistory(
        user_id=current_user.id,
        document_id=document_id,
        command_text=request.command,
        status=CommandStatus.processing
    )
    db.add(history); db.commit()
    start_time = time.time()
    try:
        backup_path             = backup_document(document.file_path)
        history.backup_filename = os.path.basename(backup_path)
        parsed = parse_command(request.command)
        if parsed.get("error"):
            history.status        = CommandStatus.failed
            history.error_message = parsed.get("summary")
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=parsed.get("summary", "Could not understand command")
            )
        executor = DocumentExecutor(document.file_path)
        results  = executor.execute_actions(parsed.get("actions", []))
        history.parsed_actions    = json.dumps(parsed.get("actions", []))
        history.status            = CommandStatus.success
        history.execution_time_ms = int((time.time() - start_time) * 1000)
        db.commit()
        return CommandResponse(
            message=parsed.get("summary", "Command executed successfully"),
            actions_performed=results,
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        history.status        = CommandStatus.failed
        history.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )


@router.post("/{document_id}/selection-command", response_model=CommandResponse)
def execute_selection_command(
    document_id: int,
    request: SelectionCommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute a command directly on selected paragraphs — bypasses AI parser."""
    if not _check_rate_limit(current_user.id, "command"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many commands. Max {RATE_LIMIT_COMMANDS} per minute."
        )

    document = DocumentService.get_by_id(db, document_id, current_user)
    history  = CommandHistory(
        user_id=current_user.id,
        document_id=document_id,
        command_text=(
            f"[Selection] {request.command_type}: "
            f"{', '.join(request.selected_texts[:2])}"
        ),
        status=CommandStatus.processing
    )
    db.add(history); db.commit()
    start_time = time.time()
    try:
        backup_path             = backup_document(document.file_path)
        history.backup_filename = os.path.basename(backup_path)
        executor = DocumentExecutor(document.file_path)
        results  = executor.execute_actions([{
            "type": "apply_to_selection",
            "params": {
                "selected_texts":  request.selected_texts,
                "command_type":    request.command_type,
                "font_name":       request.font_name,
                "font_size":       request.font_size,
                "color":           request.color,
                "highlight_color": request.highlight_color,
                "alignment":       request.alignment,
                "make_heading":    request.make_heading,
            }
        }])
        history.status            = CommandStatus.success
        history.execution_time_ms = int((time.time() - start_time) * 1000)
        db.commit()
        return CommandResponse(
            message=(
                f"Applied '{request.command_type}' to "
                f"{len(request.selected_texts)} selected paragraph(s)"
            ),
            actions_performed=results,
            status="success"
        )
    except Exception as e:
        history.status        = CommandStatus.failed
        history.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Selection command failed: {str(e)}"
        )