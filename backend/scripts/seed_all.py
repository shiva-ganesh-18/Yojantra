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
    schemes = [
        {
            "name": "Stand-Up India",
            "ministry": "DFS, Ministry of Finance",
            "description": "Provides bank loans between ₹10 lakh to ₹1 crore to at least one SC/ST borrower and one woman borrower per bank branch for setting up a greenfield enterprise.",
            "scheme_type": "loan",
            "max_benefit_inr": Decimal("10000000"),
            "min_benefit_inr": Decimal("1000000"),
            "benefit_description": "Bank loan ₹10 lakh - ₹1 crore with composite loan facility",
            "interest_rate": Decimal("10.0"),
            "collateral_required": False,
            "application_mode": "offline",
            "official_url": "https://www.standupmitra.in",
            "helpline_number": "1800-180-1111",
            "target_genders": ["female"],
            "target_social_categories": ["sc", "st"],
            "target_business_types": ["manufacturing", "service", "trading"],
            "target_business_stages": ["pre_revenue", "revenue"],
            "max_turnover_inr": Decimal("10000000"),
            "max_employees": 50,
            "women_ownership_min_percent": 51,
            "requires_udyam": True,
            "documents_required": [
                {"name": "PAN Card", "mandatory": True, "format": "pdf"},
                {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"},
                {"name": "Caste Certificate", "mandatory": True, "format": "pdf"},
                {"name": "Project Report", "mandatory": True, "format": "pdf"},
                {"name": "Bank Statement", "mandatory": True, "format": "pdf"}
            ],
            "application_steps": [
                {"step": 1, "description": "Visit nearest bank branch", "channel": "offline"},
                {"step": 2, "description": "Submit application with project report", "channel": "offline"},
                {"step": 3, "description": "Bank evaluates and sanctions loan", "channel": "offline"}
            ],
            "rules": [
                {"field_name": "target_genders", "operator": "in", "rule_value": ["female"], "is_mandatory": False, "description": "Preference for women or SC/ST entrepreneurs"},
                {"field_name": "target_social_categories", "operator": "in", "rule_value": ["sc", "st"], "is_mandatory": False, "description": "SC/ST borrowers eligible"}
            ],
            "benefits": [
                {"benefit_type": "loan", "amount_min": Decimal("1000000"), "amount_max": Decimal("10000000"), "interest_rate": Decimal("10.0"), "disbursement_mode": "bank_loan", "description": "Bank loan ₹10 lakh to ₹1 crore for greenfield enterprise"}
            ]
        },
        {
            "name": "PM Mudra Yojana (PMMY)",
            "ministry": "Ministry of Finance",
            "description": "Provides loans up to ₹10 lakh to non-corporate, non-farm small/micro enterprises. Shishu: up to ₹50,000, Kishore: ₹50,001-₹5 lakh, Tarun: ₹5-10 lakh.",
            "scheme_type": "loan",
            "max_benefit_inr": Decimal("1000000"),
            "min_benefit_inr": Decimal("10000"),
            "benefit_description": "Collateral-free loans up to ₹10 lakh under Shishu, Kishore, Tarun categories",
            "interest_rate": Decimal("12.0"),
            "collateral_required": False,
            "application_mode": "both",
            "official_url": "https://www.mudra.org.in",
            "helpline_number": "1800-180-1111",
            "target_genders": None,
            "target_social_categories": None,
            "target_business_types": ["manufacturing", "service", "trading", "retail", "handicraft"],
            "target_business_stages": ["idea", "pre_revenue", "revenue"],
            "max_turnover_inr": Decimal("5000000"),
            "max_employees": 10,
            "documents_required": [
                {"name": "Identity Proof", "mandatory": True, "format": "pdf"},
                {"name": "Address Proof", "mandatory": True, "format": "pdf"},
                {"name": "Business Proof", "mandatory": True, "format": "pdf"}
            ],
            "application_steps": [
                {"step": 1, "description": "Approach bank/NBFC/MFI", "channel": "both"},
                {"step": 2, "description": "Fill Mudra application form", "channel": "both"},
                {"step": 3, "description": "Submit with business details", "channel": "both"}
            ],
            "rules": [
                {"field_name": "max_turnover_inr", "operator": "<=", "rule_value": 5000000, "is_mandatory": True, "description": "Annual turnover under ₹50 lakh"}
            ],
            "benefits": [
                {"benefit_type": "loan", "amount_min": Decimal("10000"), "amount_max": Decimal("1000000"), "interest_rate": Decimal("12.0"), "disbursement_mode": "bank_loan", "description": "Collateral-free micro loans up to ₹10 Lakh"}
            ]
        },
        {
            "name": "PM Formalisation of Micro Food Processing Enterprises (PMFME)",
            "ministry": "Ministry of Food Processing Industries",
            "description": "Provides 35% capital subsidy up to ₹10 lakh for micro food processing units. Also supports branding, marketing, and common infrastructure.",
            "scheme_type": "subsidy",
            "max_benefit_inr": Decimal("1000000"),
            "min_benefit_inr": Decimal("100000"),
            "benefit_description": "35% capital subsidy up to ₹10 lakh + credit-linked grant",
            "application_mode": "online",
            "official_url": "https://pmfme.mofpi.gov.in",
            "helpline_number": "011-23062118",
            "target_genders": None,
            "target_social_categories": None,
            "target_business_types": ["food_processing"],
            "target_business_stages": ["pre_revenue", "revenue"],
            "max_turnover_inr": Decimal("5000000"),
            "max_employees": 10,
            "requires_udyam": True,
            "documents_required": [
                {"name": "UDYAM Registration", "mandatory": True, "format": "pdf"},
                {"name": "FSSAI License", "mandatory": True, "format": "pdf"},
                {"name": "Project Report", "mandatory": True, "format": "pdf"},
                {"name": "Bank Details", "mandatory": True, "format": "pdf"}
            ],
            "application_steps": [
                {"step": 1, "description": "Register on PMFME portal", "channel": "online"},
                {"step": 2, "description": "Fill application with project details", "channel": "online"},
                {"step": 3, "description": "Upload documents and submit", "channel": "online"}
            ],
            "rules": [
                {"field_name": "target_business_types", "operator": "in", "rule_value": ["food_processing"], "is_mandatory": True, "description": "Must be in food processing or allied sector"}
            ],
            "benefits": [
                {"benefit_type": "subsidy", "percentage": Decimal("35.0"), "amount_max": Decimal("1000000"), "disbursement_mode": "direct_benefit_transfer", "description": "35% credit-linked capital subsidy up to ₹10 Lakh"}
            ]
        },
        {
            "name": "Startup India Seed Fund Scheme (SISFS)",
            "ministry": "DPIIT",
            "description": "Provides financial assistance to startups for proof of concept, prototype development, product trials, market entry, and commercialization.",
            "scheme_type": "grant",
            "max_benefit_inr": Decimal("2000000"),
            "min_benefit_inr": Decimal("100000"),
            "benefit_description": "Up to ₹20 lakh grant for POC + up to ₹50 lakh loan for market entry",
            "application_mode": "online",
            "official_url": "https://seedfund.startupindia.gov.in",
            "helpline_number": "1800-115-565",
            "target_genders": None,
            "target_social_categories": None,
            "target_business_types": ["technology"],
            "target_business_stages": ["pre_revenue", "revenue"],
            "max_turnover_inr": Decimal("100000000"),
            "max_employees": 100,
            "requires_dpiit": True,
            "documents_required": [
                {"name": "DPIIT Recognition", "mandatory": True, "format": "pdf"},
                {"name": "Pitch Deck", "mandatory": True, "format": "pdf"},
                {"name": "Financial Projections", "mandatory": True, "format": "pdf"}
            ],
            "application_steps": [
                {"step": 1, "description": "Apply through Startup India portal", "channel": "online"},
                {"step": 2, "description": "Submit pitch and documents", "channel": "online"},
                {"step": 3, "description": "Evaluation by expert panel", "channel": "online"}
            ],
            "rules": [
                {"field_name": "requires_dpiit", "operator": "==", "rule_value": True, "is_mandatory": True, "description": "Must have valid DPIIT Startup Recognition"}
            ],
            "benefits": [
                {"benefit_type": "grant", "amount_max": Decimal("2000000"), "disbursement_mode": "incubator_grant", "description": "Up to ₹20 Lakh POC validation grant"}
            ]
        },
        {
            "name": "CGTMSE - Credit Guarantee Fund",
            "ministry": "Ministry of MSME",
            "description": "Provides credit guarantee coverage to Member Lending Institutions for collateral-free credit facilities extended to MSEs. Women-led MSMEs get 90% guarantee coverage.",
            "scheme_type": "guarantee",
            "max_benefit_inr": Decimal("50000000"),
            "benefit_description": "Collateral-free credit guarantee up to ₹5 crore. 90% for women-led MSMEs.",
            "application_mode": "both",
            "official_url": "https://www.cgtmse.in",
            "helpline_number": "1800-180-1111",
            "target_genders": None,
            "target_social_categories": None,
            "target_business_types": ["manufacturing", "service", "trading"],
            "target_business_stages": ["revenue", "growth"],
            "max_turnover_inr": Decimal("500000000"),
            "max_employees": 500,
            "requires_udyam": True,
            "documents_required": [
                {"name": "UDYAM Certificate", "mandatory": True, "format": "pdf"},
                {"name": "Loan Application", "mandatory": True, "format": "pdf"}
            ],
            "application_steps": [
                {"step": 1, "description": "Apply for loan at bank", "channel": "both"},
                {"step": 2, "description": "Bank applies for CGTMSE cover", "channel": "offline"},
                {"step": 3, "description": "Guarantee issued", "channel": "offline"}
            ],
            "rules": [
                {"field_name": "requires_udyam", "operator": "==", "rule_value": True, "is_mandatory": True, "description": "Active UDYAM registration is required"}
            ],
            "benefits": [
                {"benefit_type": "guarantee", "amount_max": Decimal("50000000"), "disbursement_mode": "credit_guarantee", "description": "Credit guarantee cover up to ₹5 Crore"}
            ]
        }
    ]

    for s in schemes:
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

    db.commit()
    print(f"✅ Seeded {len(schemes)} schemes with rules and benefits")


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
