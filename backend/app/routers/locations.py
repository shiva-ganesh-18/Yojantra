"""India Locations (States & Districts) Router for Yojantra.
Provides canonical datasets for all 28 States, 8 Union Territories, and districts.
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models import Institution
from app.schemas import StateResponse, DistrictResponse, CityResponse

router = APIRouter(prefix="/locations", tags=["Locations"])

# Canonical All-India States and Union Territories
STATES_DATA = [
    {"code": "AN", "name": "Andaman and Nicobar Islands", "type": "Union Territory", "districts": ["Nicobars", "North and Middle Andaman", "South Andaman"]},
    {"code": "AP", "name": "Andhra Pradesh", "type": "State", "districts": ["Ananthapuramu", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari", "YSR Kadapa", "Nellore", "Tirupati", "NTR", "Kakinada"]},
    {"code": "AR", "name": "Arunachal Pradesh", "type": "State", "districts": ["Changlang", "East Kameng", "East Siang", "Lohit", "Papum Pare", "Tawang", "Tirap", "West Kameng", "West Siang"]},
    {"code": "AS", "name": "Assam", "type": "State", "districts": ["Baksa", "Barpeta", "Cachar", "Darrang", "Dibrugarh", "Goalpara", "Golaghat", "Guwahati (Kamrup Metro)", "Jorhat", "Kamrup", "Nagaon", "Sonitpur", "Tinsukia"]},
    {"code": "BR", "name": "Bihar", "type": "State", "districts": ["Araria", "Bhagalpur", "Darbhanga", "Gaya", "Muzaffarpur", "Nalanda", "Patna", "Purnia", "Rohtas", "Samastipur", "Saran", "Vaishali"]},
    {"code": "CH", "name": "Chandigarh", "type": "Union Territory", "districts": ["Chandigarh"]},
    {"code": "CG", "name": "Chhattisgarh", "type": "State", "districts": ["Bastar", "Bilaspur", "Durg", "Janjgir-Champa", "Korba", "Raigarh", "Raipur", "Rajnandgaon", "Surguja"]},
    {"code": "DN", "name": "Dadra and Nagar Haveli and Daman and Diu", "type": "Union Territory", "districts": ["Dadra and Nagar Haveli", "Daman", "Diu"]},
    {"code": "DL", "name": "Delhi", "type": "Union Territory", "districts": ["Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi"]},
    {"code": "GA", "name": "Goa", "type": "State", "districts": ["North Goa", "South Goa"]},
    {"code": "GJ", "name": "Gujarat", "type": "State", "districts": ["Ahmedabad", "Amreli", "Anand", "Banaskantha", "Bharuch", "Bhavnagar", "Gandhinagar", "Jamnagar", "Junagadh", "Kutch", "Mehsana", "Rajkot", "Surat", "Vadodara", "Valsad"]},
    {"code": "HR", "name": "Haryana", "type": "State", "districts": ["Ambala", "Bhiwani", "Faridabad", "Gurugram", "Hisar", "Karnal", "Kurukshetra", "Panchkula", "Panipat", "Rohtak", "Sonipat", "Yamunanagar"]},
    {"code": "HP", "name": "Himachal Pradesh", "type": "State", "districts": ["Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kullu", "Mandi", "Shimla", "Sirmaur", "Solan", "Una"]},
    {"code": "JK", "name": "Jammu and Kashmir", "type": "Union Territory", "districts": ["Anantnag", "Baramulla", "Budgam", "Jammu", "Kathua", "Pulwama", "Rajouri", "Srinagar", "Udhampur"]},
    {"code": "JH", "name": "Jharkhand", "type": "State", "districts": ["Bokaro", "Deoghar", "Dhanbad", "East Singhbhum (Jamshedpur)", "Hazaribagh", "Ranchi", "West Singhbhum"]},
    {"code": "KA", "name": "Karnataka", "type": "State", "districts": ["Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Dakshina Kannada (Mangaluru)", "Dharwad (Hubballi)", "Kalaburagi", "Mysuru", "Shivamogga", "Tumakuru", "Udupi"]},
    {"code": "KL", "name": "Kerala", "type": "State", "districts": ["Alappuzha", "Ernakulam (Kochi)", "Idukki", "Kannur", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Thiruvananthapuram", "Thrissur"]},
    {"code": "LA", "name": "Ladakh", "type": "Union Territory", "districts": ["Kargil", "Leh"]},
    {"code": "LD", "name": "Lakshadweep", "type": "Union Territory", "districts": ["Lakshadweep"]},
    {"code": "MP", "name": "Madhya Pradesh", "type": "State", "districts": ["Bhopal", "Gwalior", "Indore", "Jabalpur", "Rewa", "Sagar", "Satna", "Ujjain"]},
    {"code": "MH", "name": "Maharashtra", "type": "State", "districts": ["Ahmednagar", "Aurangabad (Chhatrapati Sambhajinagar)", "Kolhapur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nashik", "Navi Mumbai", "Pune", "Solapur", "Thane"]},
    {"code": "MN", "name": "Manipur", "type": "State", "districts": ["Bishnupur", "Churachandpur", "Imphal East", "Imphal West", "Thoubal"]},
    {"code": "ML", "name": "Meghalaya", "type": "State", "districts": ["East Garo Hills", "East Khasi Hills (Shillong)", "Ri Bhoi", "West Garo Hills"]},
    {"code": "MZ", "name": "Mizoram", "type": "State", "districts": ["Aizawl", "Champhai", "Kolasib", "Lunglei"]},
    {"code": "NL", "name": "Nagaland", "type": "State", "districts": ["Dimapur", "Kohima", "Mokokchung", "Tuensang"]},
    {"code": "OD", "name": "Odisha", "type": "State", "districts": ["Balasore", "Bhadrak", "Cuttack", "Ganjam", "Khordha (Bhubaneswar)", "Puri", "Rourkela (Sundargarh)", "Sambalpur"]},
    {"code": "PY", "name": "Puducherry", "type": "Union Territory", "districts": ["Karaikal", "Mahe", "Puducherry", "Yanam"]},
    {"code": "PB", "name": "Punjab", "type": "State", "districts": ["Amritsar", "Bathinda", "Jalandhar", "Ludhiana", "Mohali (SAS Nagar)", "Patiala"]},
    {"code": "RJ", "name": "Rajasthan", "type": "State", "districts": ["Ajmer", "Alwar", "Bikaner", "Jaipur", "Jodhpur", "Kota", "Udaipur"]},
    {"code": "SK", "name": "Sikkim", "type": "State", "districts": ["East Sikkim (Gangtok)", "North Sikkim", "South Sikkim", "West Sikkim"]},
    {"code": "TN", "name": "Tamil Nadu", "type": "State", "districts": ["Chennai", "Coimbatore", "Cuddalore", "Dindigul", "Erode", "Kanchipuram", "Madurai", "Salem", "Thanjavur", "Tiruchirappalli", "Tirunelveli", "Vellore"]},
    {"code": "TS", "name": "Telangana", "type": "State", "districts": ["Hyderabad", "Karimnagar", "Khammam", "Mahabubnagar", "Medchal-Malkajgiri", "Nalgonda", "Nizamabad", "Rangareddy", "Warangal"]},
    {"code": "TR", "name": "Tripura", "type": "State", "districts": ["Dhalai", "Gomati", "North Tripura", "South Tripura", "West Tripura (Agartala)"]},
    {"code": "UP", "name": "Uttar Pradesh", "type": "State", "districts": ["Agra", "Aligarh", "Ayodhya", "Bareilly", "Ghaziabad", "Gorakhpur", "Kanpur Nagar", "Lucknow", "Meerut", "Moradabad", "Noida (Gautam Buddha Nagar)", "Prayagraj", "Varanasi"]},
    {"code": "UK", "name": "Uttarakhand", "type": "State", "districts": ["Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Udham Singh Nagar"]},
    {"code": "WB", "name": "West Bengal", "type": "State", "districts": ["Bankura", "Darjeeling", "Hooghly", "Howrah", "Kolkata", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman (Durgapur/Asansol)", "Siliguri", "South 24 Parganas"]}
]


@router.get("/states", response_model=List[StateResponse])
def get_all_states():
    """Retrieve canonical list of all Indian States and Union Territories."""
    return [
        StateResponse(
            code=s["code"],
            name=s["name"],
            type=s["type"],
            districts_count=len(s["districts"])
        )
        for s in STATES_DATA
    ]


@router.get("/districts", response_model=List[DistrictResponse])
def get_districts_by_state(state: str = Query(..., min_length=2)):
    """Retrieve list of districts for a specified State or Union Territory."""
    state_clean = state.strip().lower()
    matched = None
    for s in STATES_DATA:
        if s["name"].lower() == state_clean or s["code"].lower() == state_clean:
            matched = s
            break

    if not matched:
        # Partial search
        for s in STATES_DATA:
            if state_clean in s["name"].lower():
                matched = s
                break

    if not matched:
        raise HTTPException(status_code=404, detail=f"State '{state}' not found in canonical Indian territory dataset")

    return [
        DistrictResponse(name=d, state=matched["name"])
        for d in matched["districts"]
    ]


@router.get("/cities", response_model=List[CityResponse])
def get_cities(
    state: Optional[str] = Query(None, description="Filter by state"),
    district: Optional[str] = Query(None, description="Filter by district"),
    q: Optional[str] = Query(None, description="Search term for city"),
    db: Session = Depends(get_db)
):
    """
    Retrieve cities and prominent educational/commercial towns.
    Aggregates cities from verified institutions and canonical district centers.
    """
    cities_map = {}  # key: (city_name, district, state)

    # 1. From active institutions in DB
    inst_query = db.query(Institution.city, Institution.district, Institution.state).filter(
        Institution.city != None,
        Institution.city != ""
    )
    if state:
        inst_query = inst_query.filter(func.lower(Institution.state) == state.strip().lower())
    if district:
        inst_query = inst_query.filter(func.lower(Institution.district) == district.strip().lower())
    if q:
        inst_query = inst_query.filter(Institution.city.ilike(f"%{q.strip()}%"))

    for c, d, s in inst_query.distinct().all():
        if c:
            clean_c = c.strip()
            key = (clean_c.lower(), d.lower(), s.lower())
            if key not in cities_map:
                cities_map[key] = CityResponse(name=clean_c, district=d, state=s)

    # 2. If district is specified, add the district headquarter / main city name if not already present
    if district:
        # Find matching state
        parent_state = state
        if not parent_state:
            for s in STATES_DATA:
                for d in s["districts"]:
                    if d.lower() == district.strip().lower():
                        parent_state = s["name"]
                        break
                if parent_state:
                    break

        clean_dist = district.strip()
        # Many Indian districts are named after their main city, or clean parentheses like "Guwahati (Kamrup Metro)"
        base_city = clean_dist.split("(")[0].strip()
        key = (base_city.lower(), clean_dist.lower(), (parent_state or "").lower())
        if key not in cities_map:
            if not q or q.strip().lower() in base_city.lower():
                cities_map[key] = CityResponse(name=base_city, district=clean_dist, state=parent_state or "")

    return sorted(list(cities_map.values()), key=lambda x: x.name)


def validate_state_and_district(state: Optional[str], district: Optional[str]) -> tuple[bool, Optional[str]]:
    """
    Validate whether the provided state and district match canonical Indian territory data.
    Returns (is_valid, error_message).
    """
    if not state and not district:
        return True, None

    if district and not state:
        return False, "State is required when specifying a district."

    state_clean = state.strip().lower() if state else ""
    matched_state = None
    for s in STATES_DATA:
        if s["name"].lower() == state_clean or s["code"].lower() == state_clean:
            matched_state = s
            break

    if not matched_state:
        # Partial fallback match
        for s in STATES_DATA:
            if state_clean in s["name"].lower():
                matched_state = s
                break

    if not matched_state:
        return False, f"State '{state}' is not a recognized Indian State or Union Territory."

    if district:
        dist_clean = district.strip().lower()
        district_found = False
        for d in matched_state["districts"]:
            if d.lower() == dist_clean or dist_clean in d.lower() or d.lower() in dist_clean:
                district_found = True
                break
        if not district_found:
            return False, f"District '{district}' does not belong to {matched_state['name']}."

    return True, None


def is_valid_district_for_state(state: Optional[str], district: Optional[str]) -> bool:
    """Helper returning boolean whether district belongs to state."""
    if not state or not district:
        return True
    valid, _ = validate_state_and_district(state, district)
    return valid
