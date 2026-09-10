"""Scheme discovery and management router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.schemas import (
    SchemeResponse,
    SchemeSearchParams,
    SchemeCreate,
    LoanSimulationRequest,
    LoanSimulationResponse
)
from app.models import Scheme, User
from app.services.financial_calculator_service import FinancialCalculatorService

router = APIRouter(prefix="/schemes", tags=["Schemes"])


@router.get("", response_model=List[SchemeResponse])
def list_schemes(
    q: Optional[str] = None,
    ministry: Optional[str] = None,
    scheme_type: Optional[str] = None,
    state: Optional[str] = None,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
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


@router.post("/calculate-emi", response_model=LoanSimulationResponse)
def calculate_generic_emi(payload: LoanSimulationRequest):
    """Generic financial simulation and monthly payment breakdown."""
    try:
        result = FinancialCalculatorService.simulate_loan(
            principal=payload.principal_amount,
            tenure_months=payload.tenure_months or 60,
            moratorium_months=payload.moratorium_months or 0,
            interest_rate_percent=payload.interest_rate_percent or 9.50,
            scheme=None,
            include_schedule=payload.include_schedule
        )
        return LoanSimulationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{scheme_id}", response_model=SchemeResponse)
def get_scheme(scheme_id: UUID, db: Session = Depends(get_db)):
    """Get scheme details by ID."""
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return SchemeResponse.model_validate(scheme)




@router.post("/{scheme_id}/simulate-loan", response_model=LoanSimulationResponse)
def simulate_scheme_loan(
    scheme_id: UUID,
    payload: LoanSimulationRequest,
    db: Session = Depends(get_db)
):
    """Scheme-grounded loan simulation using real database rates, moratorium, and loan limits."""
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    try:
        result = FinancialCalculatorService.simulate_loan(
            principal=payload.principal_amount,
            tenure_months=payload.tenure_months,
            moratorium_months=payload.moratorium_months,
            interest_rate_percent=payload.interest_rate_percent,
            scheme=scheme,
            include_schedule=payload.include_schedule
        )
        return LoanSimulationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("", response_model=SchemeResponse)
def create_scheme(
    scheme: SchemeCreate, 
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Create a new scheme (strict admin authorization required)."""
    db_scheme = Scheme(**scheme.model_dump())
    db.add(db_scheme)
    db.commit()
    db.refresh(db_scheme)
    return SchemeResponse.model_validate(db_scheme)


@router.put("/{scheme_id}", response_model=SchemeResponse)
def update_scheme(
    scheme_id: UUID,
    scheme_update: SchemeCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Update a scheme (strict admin authorization required)."""
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    for key, value in scheme_update.model_dump(exclude_unset=True).items():
        setattr(scheme, key, value)
    db.commit()
    db.refresh(scheme)
    return SchemeResponse.model_validate(scheme)


@router.delete("/{scheme_id}")
def delete_scheme(
    scheme_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Delete a scheme (strict admin authorization required)."""
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    scheme.status = "archived"
    db.commit()
    return {"message": "Scheme successfully archived", "scheme_id": str(scheme_id)}
