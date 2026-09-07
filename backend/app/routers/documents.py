"""Document upload and management router."""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.services.document_service import get_document_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload")
async def upload_document(
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document with OCR processing."""
    service = get_document_service(db)
    doc = await service.upload_document(user.id, file, doc_type)

    return {
        "id": str(doc.id),
        "doc_type": doc.doc_type,
        "verification_status": doc.verification_status,
        "ocr_preview": doc.ocr_extracted_text[:200] + "..." if doc.ocr_extracted_text and len(doc.ocr_extracted_text) > 200 else doc.ocr_extracted_text,
        "message": "Document uploaded successfully. OCR processing complete."
    }


@router.get("")
@router.get("/my-documents")
def list_documents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all user documents."""
    service = get_document_service(db)
    docs = service.list_user_documents(user.id)

    return [
        {
            "id": str(d.id),
            "doc_type": d.doc_type,
            "verification_status": d.verification_status,
            "file_format": d.file_format,
            "uploaded_at": d.created_at.isoformat() if d.created_at else None,
            "ocr_preview": d.ocr_extracted_text[:100] + "..." if d.ocr_extracted_text and len(d.ocr_extracted_text) > 100 else d.ocr_extracted_text
        }
        for d in docs
    ]


@router.post("/{doc_id}/verify")
def verify_document(
    doc_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify a document."""
    service = get_document_service(db)
    doc = service.verify_document(doc_id)
    return {
        "id": str(doc.id),
        "verification_status": doc.verification_status,
        "verified_at": doc.verified_at.isoformat() if doc.verified_at else None
    }
