from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.command_history import CommandHistory, CommandStatus
from app.services.document_service import DocumentService
from app.schemas.document import DocumentResponse, CommandRequest, CommandResponse
from app.agent.parser import parse_command
from app.agent.executor import DocumentExecutor, backup_document
import os
import json
import time

router = APIRouter(prefix="/documents", tags=["Documents"])


# ─── Pydantic schema for selection commands ───────────────────────────────────

class SelectionCommandRequest(BaseModel):
    command_type: str
    selected_texts: List[str]
    font_name: Optional[str]       = None
    font_size: Optional[int]       = None
    color: Optional[str]           = None
    highlight_color: Optional[str] = None
    alignment: Optional[str]       = None
    make_heading: Optional[int]    = None


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=DocumentResponse,
             status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return DocumentService.upload(db, current_user, file)


@router.get("", response_model=List[DocumentResponse])
def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return DocumentService.get_all(db, current_user)


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    try:
        html = DocumentService.convert_to_html(document.file_path)
        return HTMLResponse(content=html)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview failed: {str(e)}"
        )


@router.post("/{document_id}/command", response_model=CommandResponse)
def execute_command(
    document_id: int,
    request: CommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = DocumentService.get_by_id(db, document_id, current_user)
    history  = CommandHistory(
        user_id=current_user.id,
        document_id=document_id,
        command_text=request.command,
        status=CommandStatus.processing
    )
    db.add(history)
    db.commit()
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
    """Execute a command directly on selected paragraphs — bypasses AI parser"""
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
    db.add(history)
    db.commit()
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