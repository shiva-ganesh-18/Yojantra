"""Scheme discovery and management router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.schemas import SchemeResponse, SchemeSearchParams, SchemeCreate
from app.models import Scheme

router = APIRouter(prefix="/schemes", tags=["Schemes"])


@router.get("", response_model=List[SchemeResponse])
def list_schemes(
    q: Optional[str] = None,
    ministry: Optional[str] = None,
    scheme_type: Optional[str] = None,
    state: Optional[str] = None,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List schemes with filters."""
    query = db.query(Scheme).filter(Scheme.status == "active")

    if q:
        query = query.filter(
            Scheme.name.ilike(f"%{q}%") | Scheme.description.ilike(f"%{q}%")
        )
    if ministry:
        query = query.filter(Scheme.ministry == ministry)
    if scheme_type:
        query = query.filter(Scheme.scheme_type == scheme_type)
    if state:
        query = query.filter(
            (Scheme.is_national == True) | (Scheme.applicable_states.contains([state]))
        )

    total = query.count()
    schemes = query.offset((page - 1) * page_size).limit(page_size).all()

    return [SchemeResponse.model_validate(s) for s in schemes]


@router.get("/{scheme_id}", response_model=SchemeResponse)
def get_scheme(scheme_id: UUID, db: Session = Depends(get_db)):
    """Get scheme details by ID."""
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return SchemeResponse.model_validate(scheme)


@router.post("", response_model=SchemeResponse)
def create_scheme(scheme: SchemeCreate, db: Session = Depends(get_db)):
    """Create a new scheme (admin only in production)."""
    db_scheme = Scheme(**scheme.model_dump())
    db.add(db_scheme)
    db.commit()
    db.refresh(db_scheme)
    return SchemeResponse.model_validate(db_scheme)
