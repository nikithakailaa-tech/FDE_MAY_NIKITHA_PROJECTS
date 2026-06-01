from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.attachment import Attachment
from app.models.complaint import Complaint
from app.schemas.attachment import AttachmentResponse
from app.utils.dependencies import get_current_user
from typing import List
import os, uuid

router = APIRouter(prefix="/complaints", tags=["Attachments"])

UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "uploads"
)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx", ".txt", ".xlsx", ".csv"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/{complaint_id}/attachments", response_model=AttachmentResponse)
async def upload_attachment(
    complaint_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Use: PDF, PNG, JPG, DOC, DOCX, TXT, XLSX, CSV")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as f:
        f.write(content)

    attachment = Attachment(
        complaint_id=complaint_id,
        file_name=file.filename,
        file_path=f"/uploads/{unique_name}"
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment

@router.get("/{complaint_id}/attachments", response_model=List[AttachmentResponse])
def get_attachments(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return db.query(Attachment).filter(Attachment.complaint_id == complaint_id).all()

@router.delete("/{complaint_id}/attachments/{attachment_id}")
def delete_attachment(
    complaint_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    attachment = db.query(Attachment).filter(
        Attachment.id == attachment_id,
        Attachment.complaint_id == complaint_id
    ).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    full_path = os.path.join(UPLOAD_DIR, os.path.basename(attachment.file_path))
    if os.path.exists(full_path):
        os.remove(full_path)
    db.delete(attachment)
    db.commit()
    return {"message": "Attachment deleted"}
