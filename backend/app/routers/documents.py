"""Document upload, OCR, verification, auto-fill, and readiness router."""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.rate_limit import RateLimiter
from app.models import User
from app.schemas import (
    DocumentUploadResponse, 
    DocumentReadinessResponse, 
    AutoFillProfileResponse
)
from app.services.document_service import get_document_service

router = APIRouter(prefix="/documents", tags=["Documents"])
upload_limiter = RateLimiter(requests=20, window_seconds=60, key_prefix="rl_doc_upload")


@router.post("/upload", response_model=DocumentUploadResponse, dependencies=[Depends(upload_limiter)])
async def upload_document(
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document with OCR extraction, structured field parsing, and duplicate check."""
    service = get_document_service(db)
    doc = await service.upload_document(user.id, file, doc_type)

    meta = doc.meta_info or {}
    extracted = meta.get("extracted_fields")
    dup_warning = meta.get("duplicate_warning")

    return {
        "id": doc.id,
        "doc_type": doc.doc_type,
        "verification_status": doc.verification_status,
        "verification_tier": meta.get("verification_tier", "Internal Heuristic OCR (Not Official Govt API)"),
        "ocr_preview": doc.ocr_extracted_text[:200] + "..." if doc.ocr_extracted_text and len(doc.ocr_extracted_text) > 200 else doc.ocr_extracted_text,
        "extracted_fields": extracted,
        "duplicate_warning": dup_warning,
        "message": "Document uploaded and parsed successfully. Sensitive numbers masked safely."
    }


@router.get("/readiness", response_model=DocumentReadinessResponse)
def get_document_readiness(
    scheme_id: Optional[UUID] = Query(None, description="Optional Scheme ID to compute scheme-specific checklist"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document completeness/readiness score and dynamic checklist based on selected scheme."""
    service = get_document_service(db)
    return service.calculate_readiness_score(user_id=user.id, scheme_id=scheme_id)


@router.post("/auto-fill", response_model=AutoFillProfileResponse)
@router.post("/auto-fill/{doc_id}", response_model=AutoFillProfileResponse)
def auto_fill_profile_from_documents(
    doc_id: Optional[UUID] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Auto-fill citizen and business profile using extracted document OCR metadata."""
    service = get_document_service(db)
    return service.auto_fill_user_profile(user_id=user.id, doc_id=doc_id)


@router.get("")
@router.get("/my-documents")
def list_documents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all user documents with extracted details and verification tiers."""
    service = get_document_service(db)
    docs = service.list_user_documents(user.id)

    return [
        {
            "id": str(d.id),
            "doc_type": d.doc_type,
            "verification_status": d.verification_status,
            "file_format": d.file_format,
            "file_size_bytes": d.file_size_bytes,
            "uploaded_at": d.created_at.isoformat() if d.created_at else None,
            "ocr_preview": d.ocr_extracted_text[:100] + "..." if d.ocr_extracted_text and len(d.ocr_extracted_text) > 100 else d.ocr_extracted_text,
            "extracted_fields": (d.meta_info or {}).get("extracted_fields"),
            "masked_number": (d.meta_info or {}).get("extracted_number"),
            "verification_tier": (d.meta_info or {}).get("verification_tier", "Internal Heuristic OCR (Not Official Govt API)"),
            "duplicate_warning": (d.meta_info or {}).get("duplicate_warning")
        }
        for d in docs
    ]


@router.get("/{doc_id}/download")
def download_document(
    doc_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Securely download a document with IDOR ownership check and path traversal defense."""
    service = get_document_service(db)
    is_privileged = user.role in ["admin", "super_admin", "partner_officer", "nodal_officer"]
    doc_info = service.get_document_for_download(doc_id, user_id=user.id, is_admin_or_officer=is_privileged)

    return FileResponse(
        path=doc_info["file_path"],
        filename=doc_info["filename"],
        media_type=doc_info["media_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{doc_info["filename"]}"',
            "X-Content-Type-Options": "nosniff"
        }
    )


@router.post("/{doc_id}/verify")
def verify_document(
    doc_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify a document with ownership and officer role check."""
    service = get_document_service(db)
    is_admin = user.role in ["admin", "super_admin", "partner_officer", "nodal_officer"]
    doc = service.verify_document(doc_id, user_id=user.id, is_admin=is_admin)
    return {
        "id": str(doc.id),
        "verification_status": doc.verification_status,
        "verification_tier": (doc.meta_info or {}).get("verification_tier", "Internal Heuristic OCR (Not Official Govt API)"),
        "verified_at": doc.verified_at.isoformat() if doc.verified_at else None
    }


@router.delete("/{doc_id}")
def delete_document(
    doc_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document with ownership and officer role check."""
    service = get_document_service(db)
    is_admin = user.role in ["admin", "super_admin", "partner_officer", "nodal_officer"]
    service.delete_user_document(doc_id, user_id=user.id, is_admin=is_admin)
    return {"message": "Document deleted successfully", "document_id": str(doc_id)}

