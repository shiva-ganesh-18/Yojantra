"""CSC (Common Service Center) locator service."""
import math
from typing import List, Optional
from uuid import UUID

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import CSCCenter


class CSCLocatorService:
    """Find nearest CSC centers based on user location."""

    def __init__(self, db: Session):
        self.db = db

    def find_nearby(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float = 10,
        services: Optional[List[str]] = None
    ) -> List[dict]:
        """Find CSC centers within radius using cross-engine Haversine formula."""
        # 1 deg latitude is ~111km
        lat_delta = radius_km / 111.0
        # 1 deg longitude varies with latitude
        cos_lat = max(0.01, math.cos(math.radians(latitude)))
        lon_delta = radius_km / (111.0 * cos_lat)

        candidates = self.db.query(CSCCenter).filter(
            CSCCenter.is_active == True,
            CSCCenter.latitude.between(latitude - lat_delta, latitude + lat_delta),
            CSCCenter.longitude.between(longitude - lon_delta, longitude + lon_delta)
        ).all()

        earth_radius = 6371.0
        phi1 = math.radians(latitude)

        centers = []
        for csc in candidates:
            if csc.latitude is None or csc.longitude is None:
                continue

            phi2 = math.radians(csc.latitude)
            dphi = math.radians(csc.latitude - latitude)
            dlambda = math.radians(csc.longitude - longitude)

            a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
            distance = earth_radius * c

            if distance <= radius_km:
                if services:
                    offered = csc.services_offered or []
                    if not any(s in offered for s in services):
                        continue

                centers.append({
                    "id": str(csc.id),
                    "csc_id": csc.csc_id,
                    "name": csc.name,
                    "state": csc.state,
                    "district": csc.district,
                    "block": csc.block,
                    "address": csc.address,
                    "pincode": csc.pincode,
                    "phone": csc.phone,
                    "latitude": csc.latitude,
                    "longitude": csc.longitude,
                    "services_offered": csc.services_offered or [],
                    "distance_km": round(distance, 2)
                })

        centers.sort(key=lambda x: x["distance_km"])
        return centers[:20]

    def find_by_district(self, state: str, district: str) -> List[CSCCenter]:
        """Find CSCs in a specific district."""
        return self.db.query(CSCCenter).filter(
            CSCCenter.state.ilike(state),
            CSCCenter.district.ilike(district),
            CSCCenter.is_active == True
        ).all()

    def seed_sample_data(self):
        """Seed sample CSC data for testing."""
        sample_csCs = [
            {
                "csc_id": "CSC-KA-BLR-001",
                "name": "Bangalore Rural CSC",
                "state": "Karnataka",
                "district": "Bangalore Rural",
                "block": "Devanahalli",
                "address": "Near Bus Stand, Devanahalli, Bangalore Rural",
                "pincode": "562110",
                "phone": "+919876543210",
                "latitude": 13.2465,
                "longitude": 77.7118,
                "services_offered": ["Aadhaar", "PAN", "UDYAM", "Passport", "Banking"]
            },
            {
                "csc_id": "CSC-TN-CHN-001",
                "name": "Chennai Central CSC",
                "state": "Tamil Nadu",
                "district": "Chennai",
                "block": "Teynampet",
                "address": "Anna Salai, Teynampet, Chennai",
                "pincode": "600018",
                "phone": "+919876543211",
                "latitude": 13.0827,
                "longitude": 80.2707,
                "services_offered": ["Aadhaar", "PAN", "UDYAM", "GST", "Banking"]
            },
            {
                "csc_id": "CSC-MH-PUN-001",
                "name": "Pune District CSC",
                "state": "Maharashtra",
                "district": "Pune",
                "block": "Haveli",
                "address": "Shivaji Nagar, Pune",
                "pincode": "411005",
                "phone": "+919876543212",
                "latitude": 18.5204,
                "longitude": 73.8567,
                "services_offered": ["Aadhaar", "PAN", "UDYAM", "FSSAI", "Banking"]
            },
            {
                "csc_id": "CSC-DL-NDL-001",
                "name": "Delhi North CSC",
                "state": "Delhi",
                "district": "North Delhi",
                "block": "Civil Lines",
                "address": "Mall Road, Civil Lines, Delhi",
                "pincode": "110054",
                "phone": "+919876543213",
                "latitude": 28.7041,
                "longitude": 77.1025,
                "services_offered": ["Aadhaar", "PAN", "UDYAM", "GST", "DigiLocker"]
            },
            {
                "csc_id": "CSC-WB-KOL-001",
                "name": "Kolkata South CSC",
                "state": "West Bengal",
                "district": "Kolkata",
                "block": "Ballygunge",
                "address": "Gariahat Road, Ballygunge, Kolkata",
                "pincode": "700019",
                "phone": "+919876543214",
                "latitude": 22.5726,
                "longitude": 88.3639,
                "services_offered": ["Aadhaar", "PAN", "UDYAM", "Banking"]
            }
        ]

        for csc_data in sample_csCs:
            existing = self.db.query(CSCCenter).filter(
                CSCCenter.csc_id == csc_data["csc_id"]
            ).first()
            if not existing:
                csc = CSCCenter(**csc_data)
                self.db.add(csc)

        self.db.commit()
        print(f"✅ Seeded {len(sample_csCs)} CSC centers")


def get_csc_service(db: Session) -> CSCLocatorService:
    return CSCLocatorService(db)
