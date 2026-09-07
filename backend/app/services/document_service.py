"""Document upload, OCR, and verification service."""
import os
import hashlib
import uuid
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.models import Document, User
from app.core.config import get_settings

settings = get_settings()


import tempfile


class DocumentService:
    """Handles document upload, OCR extraction, and verification."""

    def __init__(self, db: Session):
        self.db = db
        base_dir = os.environ.get("UPLOAD_DIR") or os.path.join(tempfile.gettempdir(), "schemematch_uploads")
        self.upload_dir = os.path.abspath(base_dir)
        os.makedirs(self.upload_dir, exist_ok=True)

    async def upload_document(
        self, 
        user_id: uuid.UUID, 
        file: UploadFile, 
        doc_type: str
    ) -> Document:
        """Upload and process a document."""

        # Validate file type
        allowed_types = {
            "pan": ["image/jpeg", "image/png", "application/pdf"],
            "aadhaar": ["image/jpeg", "image/png", "application/pdf"],
            "udyam": ["image/jpeg", "image/png", "application/pdf"],
            "gst": ["image/jpeg", "image/png", "application/pdf"],
            "bank_passbook": ["image/jpeg", "image/png", "application/pdf"],
            "project_report": ["application/pdf"],
            "photo": ["image/jpeg", "image/png"],
        }

        if doc_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Invalid doc_type: {doc_type}")

        if file.content_type not in allowed_types[doc_type]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {allowed_types[doc_type]}"
            )

        # Validate file size (max 10MB)
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        # Save file safely
        filename = os.path.basename(file.filename or "document")
        file_ext = filename.split(".")[-1].lower() if "." in filename else "bin"
        unique_name = f"{user_id}_{doc_type}_{uuid.uuid4().hex[:8]}.{file_ext}"
        file_path = os.path.join(self.upload_dir, unique_name)

        with open(file_path, "wb") as f:
            f.write(contents)

        # Run OCR if image/PDF
        ocr_text = None
        if file.content_type in ["image/jpeg", "image/png"]:
            ocr_text = self._extract_text_from_image(file_path)
        elif file.content_type == "application/pdf":
            ocr_text = self._extract_text_from_pdf(file_path)

        # Extract document number if possible
        doc_number = self._extract_doc_number(doc_type, ocr_text)
        doc_number_hash = hashlib.sha256(doc_number.encode()).hexdigest() if doc_number else None

        # Create DB record
        doc = Document(
            user_id=user_id,
            doc_type=doc_type,
            doc_number_hash=doc_number_hash,
            file_url=file_path,
            file_format=file_ext,
            ocr_extracted_text=ocr_text,
            verification_status="pending",
            metadata={
                "original_filename": file.filename,
                "file_size": len(contents),
                "uploaded_at": datetime.utcnow().isoformat(),
                "extracted_number": doc_number
            }
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        return doc

    def _extract_text_from_image(self, file_path: str) -> Optional[str]:
        """Extract text from image using pytesseract."""
        try:
            from PIL import Image
            import pytesseract

            image = Image.open(file_path)
            # Preprocess: convert to grayscale
            image = image.convert("L")
            text = pytesseract.image_to_string(image, lang="eng+hin")
            return text.strip() if text else None
        except Exception as e:
            print(f"OCR failed: {e}")
            return None

    def _extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """Extract text from PDF."""
        try:
            import pdfplumber

            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip() if text else None
        except Exception as e:
            print(f"PDF extraction failed: {e}")
            return None

    def _extract_doc_number(self, doc_type: str, ocr_text: Optional[str]) -> Optional[str]:
        """Extract document number from OCR text using regex."""
        if not ocr_text:
            return None

        patterns = {
            "pan": r"[A-Z]{5}[0-9]{4}[A-Z]{1}",
            "aadhaar": r"\d{4}\s?\d{4}\s?\d{4}",
            "udyam": r"UDYAM-[A-Z]{2}-\d{2}-\d{7}",
            "gst": r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}",
        }

        import re
        pattern = patterns.get(doc_type)
        if pattern:
            match = re.search(pattern, ocr_text.upper())
            if match:
                return match.group(0).replace(" ", "")
        return None

    def verify_document(self, doc_id: uuid.UUID) -> Document:
        """Mark document as verified (in production: call external APIs)."""
        doc = self.db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # In production: call DigiLocker, UIDAI, GSTN APIs for verification
        doc.verification_status = "verified"
        doc.verified_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def list_user_documents(self, user_id: uuid.UUID):
        """List all documents for a user."""
        return self.db.query(Document).filter(Document.user_id == user_id).all()


def get_document_service(db: Session) -> DocumentService:
    return DocumentService(db)
