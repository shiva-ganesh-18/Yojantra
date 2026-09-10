"""CSC locator router."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.services.csc_service import get_csc_service

router = APIRouter(prefix="/csc", tags=["CSC Locator"])


@router.get("/nearby")
def find_nearby_csc(
    lat: Optional[float] = Query(None, description="User latitude"),
    lng: Optional[float] = Query(None, description="User longitude"),
    latitude: Optional[float] = Query(None, description="User latitude alias"),
    longitude: Optional[float] = Query(None, description="User longitude alias"),
    radius_km: float = Query(10, ge=1, le=50, description="Search radius in km"),
    services: Optional[List[str]] = Query(None, description="Filter by services offered"),
    db: Session = Depends(get_db)
):
    """Find nearest Common Service Centers."""
    actual_lat = lat if lat is not None else latitude
    actual_lng = lng if lng is not None else longitude
    if actual_lat is None or actual_lng is None:
        raise HTTPException(status_code=422, detail="Missing required coordinates: provide lat & lng or latitude & longitude")
    service = get_csc_service(db)
    centers = service.find_nearby(actual_lat, actual_lng, radius_km, services)
    return {"centers": centers, "count": len(centers)}


@router.get("/by-district")
def find_by_district(
    district: Optional[str] = Query(None, description="District name"),
    state: Optional[str] = Query(None, description="State name"),
    q: Optional[str] = Query(None, description="Search keyword across name, block, address"),
    db: Session = Depends(get_db)
):
    """Find CSCs by district, state, or search keyword."""
    service = get_csc_service(db)
    centers = service.find_by_district(state=state, district=district, query=q)
    return {
        "centers": [
            {
                "id": str(c.id),
                "csc_id": c.csc_id,
                "name": c.name,
                "state": c.state,
                "district": c.district,
                "block": c.block,
                "address": c.address,
                "pincode": c.pincode,
                "phone": c.phone,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "services": c.services_offered or [],
                "services_offered": c.services_offered or [],
            }
            for c in centers
        ],
        "count": len(centers),
        "verified_coverage_available": len(centers) > 0,
        "official_portal_url": "https://findmycsc.nic.in",
        "official_helpline": "1800-3000-3468",
        "query_parameters": {
            "state": state,
            "district": district,
            "q": q
        }
    }


@router.post("/seed")
def seed_csc_data(db: Session = Depends(get_db)):
    """Seed sample CSC data (admin only in production)."""
    service = get_csc_service(db)
    service.seed_sample_data()
    return {"message": "CSC data seeded successfully"}
