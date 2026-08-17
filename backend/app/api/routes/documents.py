from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.command_history import CommandHistory, CommandStatus
from app.services.document_service import (
    DocumentService, _safe_path, _cleanup_old_backups,
    get_image_storage_key
)
from app.schemas.document import DocumentResponse, CommandRequest, CommandResponse
from app.agent.parser import parse_command
from app.agent.executor import DocumentExecutor, backup_document
from app.core.config import settings
from app.core.cache import cache_get, cache_set, cache_delete_pattern
from app.core.storage import upload_file, download_file, get_temp_copy, cleanup_temp_copy
import os, json, time, uuid, shutil, logging, tempfile
from collections import defaultdict
import threading

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger("texlify.documents")

_rate_store = defaultdict(list)
_rate_lock  = threading.Lock()
RATE_LIMIT_COMMANDS   = 30
RATE_LIMIT_WINDOW_SEC = 60
RATE_LIMIT_UPLOADS    = 10


def _check_rate_limit(user_id: int, action: str = "command") -> bool:
    key   = f"{user_id}:{action}"
    now   = time.time()
    limit = RATE_LIMIT_COMMANDS if action == "command" else RATE_LIMIT_UPLOADS
    with _rate_lock:
        timestamps = [t for t in _rate_store[key] if now - t < RATE_LIMIT_WINDOW_SEC]
        if len(timestamps) >= limit:
            _rate_store[key] = timestamps
            return False
        timestamps.append(now)
        _rate_store[key] = timestamps
        return True


def _invalidate_preview_cache(document_id: int):
    cache_delete_pattern(f"preview:{document_id}:*")


def _backup_document(local_path: str) -> str:
    """Create a backup of the local file. Returns backup path."""
    from datetime import datetime
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{local_path}.backup_{timestamp}"
    shutil.copy2(local_path, backup_path)
    return backup_path


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


@router.post("/upload", response_model=DocumentResponse,
             status_code=status.HTTP_201_CREATED)
def upload_document(
    file:         UploadFile = File(...),
    db:           Session    = Depends(get_db),
    current_user: User       = Depends(get_current_user)
):
    if not _check_rate_limit(current_user.id, "upload"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Upload limit reached. Max {RATE_LIMIT_UPLOADS} per minute."
        )
    return DocumentService.upload(db, current_user, file)


@router.post("/upload-image")
def upload_image(
    file:         UploadFile = File(...),
    db:           Session    = Depends(get_db),
    current_user: User       = Depends(get_current_user)
):
    allowed = ["image/jpeg","image/png","image/gif","image/webp","image/bmp"]
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only image files allowed")
    contents  = file.file.read()
    file_size = len(contents)
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size exceeds 10MB")

    ext             = os.path.splitext(file.filename)[1].lower()
    stored_filename = f"img_{uuid.uuid4().hex}{ext}"
    storage_key     = get_image_storage_key(current_user.id, stored_filename)

    # Write to temp file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(contents)
    tmp.close()

    try:
        if settings.use_cloudinary:
            upload_file(tmp.name, storage_key)
            server_path = tmp.name  # temp path for executor to use immediately
        else:
            img_dir = os.path.join("uploads", str(current_user.id), "images")
            os.makedirs(img_dir, exist_ok=True)
            server_path = os.path.join(img_dir, stored_filename)
            _safe_path(server_path, img_dir)
            shutil.copy2(tmp.name, server_path)
    finally:
        if settings.use_cloudinary:
            pass  # keep tmp alive for executor
        else:
            os.remove(tmp.name)

    return {
        "filename":    stored_filename,
        "server_path": server_path,
        "storage_key": storage_key,
        "url":         f"/api/v1/documents/images/{current_user.id}/{stored_filename}",
        "size":        file_size,
        "content_type": file.content_type
    }


@router.get("/images/{user_id}/{filename}")
def serve_image(
    user_id:      int,
    filename:     str,
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if settings.use_cloudinary:
        import cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
        )
        storage_key = get_image_storage_key(user_id, filename)
        url = cloudinary.CloudinaryImage(storage_key).build_url(
            resource_type="raw", secure=True
        )
        import requests as req
        r = req.get(url, timeout=15)
        return StreamingResponse(
            iter([r.content]),
            media_type=r.headers.get("content-type", "image/jpeg")
        )
    else:
        img_dir   = os.path.join("uploads", str(user_id), "images")
        file_path = os.path.join(img_dir, filename)
        _safe_path(file_path, img_dir)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image not found")
        return FileResponse(file_path)


@router.get("", response_model=List[DocumentResponse])
def get_documents(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    return DocumentService.get_all(db, current_user)


@router.patch("/{document_id}/rename")
def rename_document(
    document_id:  int,
    request:      RenameRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    document = DocumentService.get_by_id(db, document_id, current_user)
    if not request.title or not request.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    document.title = request.title.strip()
    db.commit(); db.refresh(document)
    return {"message": "Document renamed", "title": document.title}


@router.delete("/{document_id}")
def delete_document(
    document_id:  int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    _invalidate_preview_cache(document_id)
    DocumentService.delete(db, document_id, current_user)
    return {"message": "Document deleted successfully"}


@router.get("/{document_id}/download")
def download_document(
    document_id:  int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    document   = DocumentService.get_by_id(db, document_id, current_user)
    local_path = DocumentService.get_local_path(document)
    try:
        return FileResponse(
            path=local_path,
            filename=document.original_filename,
            media_type=(
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            )
        )
    finally:
        if settings.use_cloudinary:
            # Clean up after response is sent
            pass  # FastAPI handles this


@router.get("/{document_id}/preview")
def preview_document(
    document_id:  int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    document = DocumentService.get_by_id(db, document_id, current_user)

    # Try cache first
    cache_key = f"preview:{document_id}:v1"
    cached    = cache_get(cache_key)
    if cached:
        logger.info("Preview cache HIT: doc=%s", document_id)
        return HTMLResponse(content=cached)

    local_path = DocumentService.get_local_path(document)
    try:
        html = DocumentService.convert_to_html(local_path)
        cache_set(cache_key, html, ttl_seconds=settings.PREVIEW_CACHE_TTL)
        return HTMLResponse(content=html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")
    finally:
        DocumentService.release_local_path(document, local_path, modified=False)


@router.get("/{document_id}/backups")
def get_backups(
    document_id:  int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    # In Cloudinary mode, backups are stored as Cloudinary resources
    # For simplicity we track them in the command history instead
    document = DocumentService.get_by_id(db, document_id, current_user)
    if settings.use_cloudinary:
        # Return backups from command history
        from app.models.command_history import CommandHistory, CommandStatus
        history = (
            db.query(CommandHistory)
            .filter(
                CommandHistory.document_id == document_id,
                CommandHistory.status      == CommandStatus.success,
                CommandHistory.backup_filename != None
            )
            .order_by(CommandHistory.created_at.desc())
            .limit(10)
            .all()
        )
        backups = []
        for h in history:
            if h.backup_filename:
                backups.append({
                    "filename":  h.backup_filename,
                    "timestamp": h.created_at.strftime("%Y%m%d_%H%M%S"),
                    "display":   h.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "command":   h.command_text[:50]
                })
        return {"backups": backups}
    else:
        backup_dir = os.path.dirname(document.file_path)
        base_name  = os.path.basename(document.file_path)
        backups    = []
        try:
            for f in os.listdir(backup_dir):
                if f.startswith(base_name + ".backup_"):
                    backup_time = f.split(".backup_")[1]
                    backups.append({
                        "filename":  f,
                        "timestamp": backup_time,
                        "display": (
                            f"{backup_time[:4]}-{backup_time[4:6]}-"
                            f"{backup_time[6:8]} "
                            f"{backup_time[9:11]}:{backup_time[11:13]}:"
                            f"{backup_time[13:15]}"
                        )
                    })
        except Exception:
            pass
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        return {"backups": backups[:10]}


@router.post("/{document_id}/undo")
def undo_command(
    document_id:  int,
    request:      UndoRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    document = DocumentService.get_by_id(db, document_id, current_user)

    if settings.use_cloudinary:
        # Restore from Cloudinary backup key
        backup_key = request.backup_filename
        local_path = DocumentService.get_local_path(document)
        try:
            download_file(backup_key, local_path)
            upload_file(local_path, document.file_path)
            _invalidate_preview_cache(document_id)
            return {"message": "Document restored successfully"}
        finally:
            cleanup_temp_copy(local_path, document.file_path)
    else:
        backup_dir  = os.path.dirname(document.file_path)
        backup_path = os.path.join(backup_dir, request.backup_filename)
        _safe_path(backup_path, backup_dir)
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="Backup not found")
        if not request.backup_filename.startswith(
                os.path.basename(document.file_path)):
            raise HTTPException(status_code=403, detail="Access denied")
        shutil.copy2(backup_path, document.file_path)
        _invalidate_preview_cache(document_id)
        return {"message": "Document restored successfully"}


@router.post("/{document_id}/command", response_model=CommandResponse)
def execute_command(
    document_id:  int,
    request:      CommandRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
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
    start_time  = time.time()
    local_path  = None

    try:
        # Get local working copy
        local_path = DocumentService.get_local_path(document)

        # Create backup
        if settings.use_cloudinary:
            backup_key = f"{document.file_path}.backup_{int(time.time())}"
            upload_file(local_path, backup_key)
            history.backup_filename = backup_key
        else:
            backup_path             = _backup_document(local_path)
            history.backup_filename = os.path.basename(backup_path)
            _cleanup_old_backups(local_path,
                                 keep=settings.MAX_BACKUPS_PER_DOCUMENT)

        # Parse command
        parsed = parse_command(request.command)
        if parsed.get("error"):
            history.status        = CommandStatus.failed
            history.error_message = parsed.get("summary")
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=parsed.get("summary", "Could not understand command")
            )

        # Execute
        executor = DocumentExecutor(local_path)
        results  = executor.execute_actions(parsed.get("actions", []))
        elapsed  = int((time.time() - start_time) * 1000)

        if elapsed > 5000:
            logger.warning("Slow command: user=%s doc=%s elapsed=%dms",
                           current_user.id, document_id, elapsed)

        # Push changes back to Cloudinary
        DocumentService.release_local_path(document, local_path, modified=True)
        local_path = None  # mark as released

        history.parsed_actions    = json.dumps(parsed.get("actions", []))
        history.status            = CommandStatus.success
        history.execution_time_ms = elapsed
        db.commit()

        _invalidate_preview_cache(document_id)

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
        logger.error("Command failed: user=%s doc=%s err=%s",
                     current_user.id, document_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )
    finally:
        if local_path and settings.use_cloudinary:
            cleanup_temp_copy(local_path, document.file_path)


@router.post("/{document_id}/selection-command",
             response_model=CommandResponse)
def execute_selection_command(
    document_id:  int,
    request:      SelectionCommandRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    if not _check_rate_limit(current_user.id, "command"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many commands. Max {RATE_LIMIT_COMMANDS} per minute."
        )
    document   = DocumentService.get_by_id(db, document_id, current_user)
    history    = CommandHistory(
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
    local_path = None

    try:
        local_path = DocumentService.get_local_path(document)

        if settings.use_cloudinary:
            backup_key = f"{document.file_path}.backup_{int(time.time())}"
            upload_file(local_path, backup_key)
            history.backup_filename = backup_key
        else:
            backup_path             = _backup_document(local_path)
            history.backup_filename = os.path.basename(backup_path)
            _cleanup_old_backups(local_path,
                                 keep=settings.MAX_BACKUPS_PER_DOCUMENT)

        executor = DocumentExecutor(local_path)
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

        DocumentService.release_local_path(document, local_path, modified=True)
        local_path = None

        history.status            = CommandStatus.success
        history.execution_time_ms = int((time.time() - start_time) * 1000)
        db.commit()
        _invalidate_preview_cache(document_id)

        return CommandResponse(
            message=(
                f"Applied '{request.command_type}' to "
                f"{len(request.selected_texts)} paragraph(s)"
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
    finally:
        if local_path and settings.use_cloudinary:
            cleanup_temp_copy(local_path, document.file_path)