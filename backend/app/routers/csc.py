"""CSC locator router."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.services.csc_service import get_csc_service

router = APIRouter(prefix="/csc", tags=["CSC Locator"])


@router.get("/nearby")
def find_nearby_csc(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    radius_km: float = Query(10, ge=1, le=50, description="Search radius in km"),
    services: Optional[List[str]] = Query(None, description="Filter by services offered"),
    db: Session = Depends(get_db)
):
    """Find nearest Common Service Centers."""
    service = get_csc_service(db)
    centers = service.find_nearby(lat, lng, radius_km, services)
    return {"centers": centers, "count": len(centers)}


@router.get("/by-district")
def find_by_district(
    state: str = Query(..., description="State name"),
    district: str = Query(..., description="District name"),
    db: Session = Depends(get_db)
):
    """Find CSCs by district."""
    service = get_csc_service(db)
    centers = service.find_by_district(state, district)
    return {
        "centers": [
            {
                "id": str(c.id),
                "name": c.name,
                "address": c.address,
                "phone": c.phone,
                "services": c.services_offered
            }
            for c in centers
        ]
    }


@router.post("/seed")
def seed_csc_data(db: Session = Depends(get_db)):
    """Seed sample CSC data (admin only in production)."""
    service = get_csc_service(db)
    service.seed_sample_data()
    return {"message": "CSC data seeded successfully"}
