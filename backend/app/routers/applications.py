"""Application management router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.models import User, Application, Scheme

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=ApplicationResponse)
def create_application(
    app_data: ApplicationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new application."""
    scheme = db.query(Scheme).filter(Scheme.id == app_data.scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    # Count total steps from scheme
    total_steps = len(scheme.application_steps) if scheme.application_steps else 3

    application = Application(
        user_id=user.id,
        scheme_id=app_data.scheme_id,
        channel=app_data.channel,
        total_steps=total_steps,
        next_action="Complete Step 1: Fill basic information"
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    # Enrich response with scheme name
    response = ApplicationResponse.model_validate(application)
    response.scheme_name = scheme.name
    return response


@router.get("", response_model=List[ApplicationResponse])
def list_applications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all user applications."""
    applications = db.query(Application).filter(Application.user_id == user.id).all()

    results = []
    for app in applications:
        resp = ApplicationResponse.model_validate(app)
        resp.scheme_name = app.scheme.name if app.scheme else None
        results.append(resp)

    return results


@router.get("/{app_id}", response_model=ApplicationResponse)
def get_application(
    app_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get application details."""
    application = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == user.id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    response = ApplicationResponse.model_validate(application)
    response.scheme_name = application.scheme.name if application.scheme else None
    return response


@router.put("/{app_id}", response_model=ApplicationResponse)
def update_application(
    app_id: UUID,
    update: ApplicationUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update application."""
    application = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == user.id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)

    response = ApplicationResponse.model_validate(application)
    response.scheme_name = application.scheme.name if application.scheme else None
    return response


@router.post("/{app_id}/submit")
def submit_application(
    app_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit application."""
    application = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == user.id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.status != "draft":
        raise HTTPException(status_code=400, detail="Application already submitted")

    application.status = "submitted"
    application.next_action = "Under review by authorities"
    db.commit()

    return {
        "message": "Application submitted successfully",
        "reference": str(application.id),
        "status": application.status
    }
