"""Seed all initial data: schemes + CSC centers."""
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append('..')

from app.core.database import SessionLocal, init_db
from app.models import Scheme, CSCCenter, User, Business, EligibilityRule, Benefit
from datetime import date
from decimal import Decimal
import uuid


def seed_users(db):
    """Seed demo admin and demo beneficiary user."""
    # 1. Admin user
    admin = db.query(User).filter(User.phone == "+919999999999").first()
    if not admin:
        admin = User(
            id=uuid.uuid4(),
            phone="+919999999999",
            full_name="System Administrator",
            role="admin",
            gender="prefer_not_to_say",
            social_category="general",
            state="Delhi",
            district="North Delhi",
            is_active=True,
            onboarding_completed=True
        )
        db.add(admin)
        print("  - Seeded demo admin user (+919999999999)")

    # 2. Demo beneficiary user (Woman entrepreneur in food processing)
    demo_user = db.query(User).filter(User.phone == "+919876543210").first()
    if not demo_user:
        demo_user = User(
            id=uuid.uuid4(),
            phone="+919876543210",
            full_name="Priya Sharma",
            role="user",
            gender="female",
            social_category="general",
            state="Karnataka",
            district="Bangalore Rural",
            is_rural=True,
            date_of_birth=date(1992, 5, 15),
            udyam_number="UDYAM-KR-03-0012345",
            gstin="29AAAAA0000A1Z5",
            is_active=True,
            onboarding_completed=True
        )
        db.add(demo_user)
        db.flush()

        # Associated business profile
        business = Business(
            user_id=demo_user.id,
            business_name="Priya Food Crafts & Spices",
            business_type="food_processing",
            business_stage="revenue",
            annual_turnover_inr=Decimal("1500000"),
            num_employees=8,
            num_women_employees=6,
            years_in_operation=Decimal("2.5"),
            sector="Food & Agro Processing",
            is_women_led=True,
            registration_type="proprietorship",
            has_collateral=False,
            funding_needed_inr=Decimal("800000"),
            funding_purpose="Procurement of automatic dehydrator and packaging machinery for micro food unit."
        )
        db.add(business)
        print("  - Seeded demo entrepreneur user (+919876543210) & business profile")

    db.commit()


def seed_schemes(db):
    try:
        from scripts.schemes_data import ALL_SCHEMES
    except ImportError:
        from schemes_data import ALL_SCHEMES

    seeded_count = 0
    updated_count = 0

    for s_raw in ALL_SCHEMES:
        s = dict(s_raw)
        rules_data = s.pop("rules", [])
        benefits_data = s.pop("benefits", [])

        db_scheme = db.query(Scheme).filter(Scheme.name == s["name"]).first()
        if not db_scheme:
            db_scheme = Scheme(**s)
            db.add(db_scheme)
            db.flush()

            # Add rules
            for r in rules_data:
                rule = EligibilityRule(scheme_id=db_scheme.id, **r)
                db.add(rule)

            # Add benefits
            for b in benefits_data:
                benefit = Benefit(scheme_id=db_scheme.id, **b)
                db.add(benefit)
            seeded_count += 1
        else:
            # Update metadata
            for k, v in s.items():
                setattr(db_scheme, k, v)

            # If no rules exist for this scheme, seed them
            if not db_scheme.rules and rules_data:
                for r in rules_data:
                    rule = EligibilityRule(scheme_id=db_scheme.id, **r)
                    db.add(rule)

            # If no benefits exist for this scheme, seed them
            if not db_scheme.benefits and benefits_data:
                for b in benefits_data:
                    benefit = Benefit(scheme_id=db_scheme.id, **b)
                    db.add(benefit)
            updated_count += 1

    db.commit()
    total = db.query(Scheme).count()
    print(f"✅ Schemes: {seeded_count} newly seeded, {updated_count} updated. Total schemes in DB: {total}")


def seed_csc(db):
    centers = [
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

    for c in centers:
        existing = db.query(CSCCenter).filter(CSCCenter.csc_id == c["csc_id"]).first()
        if not existing:
            db.add(CSCCenter(**c))

    db.commit()
    print(f"✅ Seeded {len(centers)} CSC centers")


def seed():
    db = SessionLocal()
    try:
        print("🌱 Seeding database...")
        seed_users(db)
        seed_schemes(db)
        seed_csc(db)
        from scripts.seed_institutions_and_sih import seed_institutions_and_sih
        seed_institutions_and_sih()
        print("\n🎉 All data seeded successfully!")
    except Exception as e:
        print(f"❌ Error during seed: {e}")
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    seed()
