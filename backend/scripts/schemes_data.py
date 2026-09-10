"""Verified Government Schemes Database for Yojantra (60+ Central & State Schemes).

All schemes are sourced from authentic government portals (.gov.in, .nic.in, official boards).
Categories: Women, SC/ST, OBC, Minorities, Youth, Rural, MSMEs, Startups, Agriculture, Food Processing, Handicrafts.
"""
from decimal import Decimal

ALL_SCHEMES = [
    # ==================== 1. CENTRAL FLAGSHIP SCHEMES ====================
    {
        "name": "Stand-Up India",
        "ministry": "Department of Financial Services, Ministry of Finance",
        "description": "Provides bank loans between ₹10 lakh to ₹1 crore to at least one SC/ST borrower and one woman borrower per bank branch for setting up a greenfield enterprise in manufacturing, services, or trading.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("10000000"),
        "min_benefit_inr": Decimal("1000000"),
        "benefit_description": "Composite loan ₹10 lakh to ₹1 crore covering term loan and working capital (up to 85% of project cost)",
        "interest_rate": Decimal("9.50"),
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://www.standupmitra.in",
        "helpline_number": "1800-180-1111",
        "is_national": True,
        "target_genders": ["female"],
        "target_social_categories": ["sc", "st"],
        "target_business_types": ["manufacturing", "service", "trading"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "max_turnover_inr": Decimal("50000000"),
        "women_ownership_min_percent": 51,
        "requires_udyam": True,
        "documents_required": [
            {"name": "PAN Card", "mandatory": True, "format": "pdf"},
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"},
            {"name": "Caste Certificate (for SC/ST)", "mandatory": False, "format": "pdf"},
            {"name": "Detailed Project Report (DPR)", "mandatory": True, "format": "pdf"},
            {"name": "Bank Account Statements (6 months)", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Register on Stand-Up Mitra portal (standupmitra.in) or visit nearest commercial bank", "channel": "both"},
            {"step": 2, "description": "Prepare Detailed Project Report (DPR) and upload required identity and business proofs", "channel": "online"},
            {"step": 3, "description": "Bank assesses credit feasibility and sanctions composite loan", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_genders", "operator": "in", "rule_value": ["female"], "is_mandatory": False, "description": "Women or SC/ST entrepreneurs prioritized"},
            {"field_name": "target_social_categories", "operator": "in", "rule_value": ["sc", "st"], "is_mandatory": False, "description": "SC/ST borrowers eligible"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_min": Decimal("1000000"), "amount_max": Decimal("10000000"), "interest_rate": Decimal("9.50"), "disbursement_mode": "bank_loan", "description": "Composite loan ₹10 Lakh to ₹1 Crore with 7-year repayment"}
        ]
    },
    {
        "name": "PM Mudra Yojana (PMMY)",
        "ministry": "Department of Financial Services, Ministry of Finance",
        "description": "Provides collateral-free institutional loans up to ₹10 lakh to non-corporate, non-farm micro and small enterprises under three categories: Shishu (up to ₹50k), Kishore (₹50k-₹5L), and Tarun (₹5L-₹10L).",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("1000000"),
        "min_benefit_inr": Decimal("10000"),
        "benefit_description": "Collateral-free micro loans up to ₹10 lakh with Mudra Card for working capital",
        "interest_rate": Decimal("10.50"),
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://www.mudra.org.in",
        "helpline_number": "1800-180-1111",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["manufacturing", "service", "trading", "retail", "handicraft"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "max_turnover_inr": Decimal("10000000"),
        "documents_required": [
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"},
            {"name": "PAN Card", "mandatory": True, "format": "pdf"},
            {"name": "Business Address Proof", "mandatory": True, "format": "pdf"},
            {"name": "Quotations of machinery or goods to be purchased", "mandatory": False, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply online at Udyamimitra portal or visit any public/private bank or NBFC", "channel": "both"},
            {"step": 2, "description": "Submit Mudra loan application form with standard KYC and business quotes", "channel": "both"},
            {"step": 3, "description": "Loan sanctioned and disbursed directly to supplier/account with Mudra debit card", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "max_turnover_inr", "operator": "<=", "rule_value": 10000000, "is_mandatory": True, "description": "Turnover within micro-enterprise limits"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_min": Decimal("10000"), "amount_max": Decimal("1000000"), "interest_rate": Decimal("10.50"), "disbursement_mode": "bank_loan", "description": "Mudra micro loan across Shishu, Kishore, Tarun categories"}
        ]
    },
    {
        "name": "PM Formalisation of Micro Food Processing Enterprises (PMFME)",
        "ministry": "Ministry of Food Processing Industries",
        "description": "Centrally sponsored scheme providing 35% credit-linked capital subsidy up to ₹10 lakh for individual micro food processing units to upgrade machinery, packaging, and quality standards.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("1000000"),
        "min_benefit_inr": Decimal("100000"),
        "subsidy_percentage": Decimal("35.0"),
        "benefit_description": "35% credit-linked capital subsidy (max ₹10 lakh) + seed capital of ₹40,000 per SHG member",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://pmfme.mofpi.gov.in",
        "helpline_number": "011-23062118",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["food_processing", "agriculture"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "max_turnover_inr": Decimal("10000000"),
        "requires_udyam": True,
        "documents_required": [
            {"name": "UDYAM Registration Certificate", "mandatory": True, "format": "pdf"},
            {"name": "FSSAI License / Registration", "mandatory": True, "format": "pdf"},
            {"name": "Detailed Project Report (DPR)", "mandatory": True, "format": "pdf"},
            {"name": "Bank Account Details", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Register on the official PMFME portal (pmfme.mofpi.gov.in)", "channel": "online"},
            {"step": 2, "description": "Fill application form with DPR assisted by District Resource Person (DRP)", "channel": "online"},
            {"step": 3, "description": "District Level Committee (DLC) approval and bank loan sanction with direct subsidy credit", "channel": "online"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["food_processing", "agriculture"], "is_mandatory": True, "description": "Must be engaged in agro or food processing"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("35.0"), "amount_max": Decimal("1000000"), "disbursement_mode": "direct_benefit_transfer", "description": "35% capital subsidy up to ₹10 Lakh"}
        ]
    },
    {
        "name": "Startup India Seed Fund Scheme (SISFS)",
        "ministry": "Department for Promotion of Industry and Internal Trade (DPIIT)",
        "description": "Provides financial assistance to DPIIT-recognized startups for proof of concept, prototype development, product trials, market entry, and commercialization through approved incubators.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("5000000"),
        "min_benefit_inr": Decimal("200000"),
        "benefit_description": "Up to ₹20 lakh grant for validation of Proof of Concept/Prototype + up to ₹50 lakh loan/convertible debenture for market entry",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://seedfund.startupindia.gov.in",
        "helpline_number": "1800-115-565",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["technology", "service", "manufacturing"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "max_turnover_inr": Decimal("100000000"),
        "requires_dpiit": True,
        "documents_required": [
            {"name": "DPIIT Startup Recognition Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Pitch Deck & Product Demonstration", "mandatory": True, "format": "pdf"},
            {"name": "Company Incorporation Certificate", "mandatory": True, "format": "pdf"},
            {"name": "12-Month Financial Projections", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Obtain DPIIT Recognition on Startup India portal", "channel": "online"},
            {"step": 2, "description": "Apply on Seed Fund portal selecting up to 3 approved incubators", "channel": "online"},
            {"step": 3, "description": "Incubator Seed Management Committee evaluates presentation and sanctions tranches", "channel": "online"}
        ],
        "rules": [
            {"field_name": "requires_dpiit", "operator": "==", "rule_value": True, "is_mandatory": True, "description": "DPIIT recognition required"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("2000000"), "disbursement_mode": "incubator_grant", "description": "Up to ₹20 Lakh POC validation grant"},
            {"benefit_type": "loan", "amount_max": Decimal("5000000"), "interest_rate": Decimal("5.0"), "disbursement_mode": "debt_or_debenture", "description": "Up to ₹50 Lakh commercialization debt"}
        ]
    },
    {
        "name": "CGTMSE - Credit Guarantee Fund Scheme",
        "ministry": "Ministry of MSME",
        "description": "Facilitates collateral-free institutional credit to new and existing Micro and Small Enterprises (MSEs) by providing guarantee coverage up to ₹5 crore to Member Lending Institutions (MLIs).",
        "scheme_type": "guarantee",
        "max_benefit_inr": Decimal("50000000"),
        "min_benefit_inr": Decimal("500000"),
        "benefit_description": "Credit guarantee coverage up to ₹5 crore with 85% cover for micro enterprises and 90% for women & SC/ST entrepreneurs",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://www.cgtmse.in",
        "helpline_number": "022-61437800",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["manufacturing", "service", "trading"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "max_turnover_inr": Decimal("250000000"),
        "requires_udyam": True,
        "documents_required": [
            {"name": "UDYAM Registration Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Business Financial Statements (2 years if existing)", "mandatory": False, "format": "pdf"},
            {"name": "Loan Proposal Application", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Approach any scheduled commercial bank or eligible NBFC for an MSE business loan", "channel": "offline"},
            {"step": 2, "description": "Lender evaluates credit viability and applies for CGTMSE guarantee cover directly", "channel": "offline"},
            {"step": 3, "description": "Loan disbursed without requiring third-party collateral or mortgage", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "requires_udyam", "operator": "==", "rule_value": True, "is_mandatory": True, "description": "Must have UDYAM registration"}
        ],
        "benefits": [
            {"benefit_type": "guarantee", "amount_max": Decimal("50000000"), "disbursement_mode": "credit_guarantee", "description": "Credit guarantee cover up to ₹5 Crore"}
        ]
    },

    # ==================== 2. WOMEN ENTREPRENEURS ====================
    {
        "name": "Mahila Coir Yojana",
        "ministry": "Coir Board, Ministry of MSME",
        "description": "Women empowerment scheme in the coir industry providing 75% financial subsidy on the cost of motorized ratts and spinning equipment to rural women artisans following stipendiary skill training.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("150000"),
        "min_benefit_inr": Decimal("25000"),
        "subsidy_percentage": Decimal("75.0"),
        "benefit_description": "75% government subsidy on motorized ratts and equipment + 2-month training with ₹3,000 monthly stipend",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://coirboard.gov.in",
        "helpline_number": "0484-2351980",
        "is_national": True,
        "target_genders": ["female"],
        "target_business_types": ["handicraft", "manufacturing"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"},
            {"name": "Coir Board Training Completion Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Bank Passbook Copy", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Complete 2-month coir spinning training at nearest Coir Board Sub-centre", "channel": "offline"},
            {"step": 2, "description": "Submit application with training certificate for motorized ratt subsidy", "channel": "both"},
            {"step": 3, "description": "Coir Board sanctions 75% subsidy directly to designated machinery manufacturer", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_genders", "operator": "in", "rule_value": ["female"], "is_mandatory": True, "description": "Exclusively for women artisans"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("75.0"), "amount_max": Decimal("150000"), "disbursement_mode": "direct_benefit_transfer", "description": "75% subsidy on motorized coir spinning equipment"}
        ]
    },
    {
        "name": "TREAD - Trade Related Entrepreneurship Assistance and Development for Women",
        "ministry": "Ministry of MSME",
        "description": "Provides government grant up to 30% of total project cost (maximum ₹30 lakh) through promoting NGOs and non-profit institutions for poor and marginalized women lacking easy access to formal bank credit.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("3000000"),
        "min_benefit_inr": Decimal("200000"),
        "benefit_description": "Government grant up to 30% of project cost (max ₹30 lakh) with 70% bank credit linkage",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://www.msme.gov.in/",
        "helpline_number": "011-23063800",
        "is_national": True,
        "target_genders": ["female"],
        "women_ownership_min_percent": 51,
        "target_business_types": ["manufacturing", "service", "handicraft", "food_processing"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Women SHG / Entrepreneur KYC", "mandatory": True, "format": "pdf"},
            {"name": "Project Proposal through registered NGO", "mandatory": True, "format": "pdf"},
            {"name": "Bank Consent Letter for 70% Loan", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Prepare project proposal through an empaneled NGO or self-help federations", "channel": "offline"},
            {"step": 2, "description": "Proposal forwarded to Ministry of MSME through state MSME-DI", "channel": "both"},
            {"step": 3, "description": "Grant released to lending bank upon sanction of composite loan", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_genders", "operator": "in", "rule_value": ["female"], "is_mandatory": True, "description": "Women-led enterprises only"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("3000000"), "disbursement_mode": "bank_linked_grant", "description": "Up to 30% capital grant for women enterprises"}
        ]
    },
    {
        "name": "Samarth Scheme for Women Entrepreneurs",
        "ministry": "Ministry of MSME",
        "description": "Dedicated MSME initiative reserving 20% seats in free national skill development programs, 20% MSME delegations sent to international expos, and 20% concession on annual NSIC processing fee for women-led MSEs.",
        "scheme_type": "incentive",
        "max_benefit_inr": Decimal("250000"),
        "min_benefit_inr": Decimal("20000"),
        "benefit_description": "100% free skill training + 20% concession on NSIC commercial registration fee + subsidized expo stalls",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://www.msme.gov.in/",
        "helpline_number": "011-23061544",
        "is_national": True,
        "target_genders": ["female"],
        "women_ownership_min_percent": 51,
        "target_business_types": ["manufacturing", "service", "trading"],
        "requires_udyam": True,
        "documents_required": [
            {"name": "UDYAM Registration showing >51% woman ownership", "mandatory": True, "format": "pdf"},
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Register on UDYAM portal declaring woman-owned enterprise", "channel": "online"},
            {"step": 2, "description": "Apply for Samarth skill training or NSIC concession via msme.gov.in", "channel": "online"},
            {"step": 3, "description": "Avail fee exemption and international trade delegation reservation", "channel": "online"}
        ],
        "rules": [
            {"field_name": "target_genders", "operator": "in", "rule_value": ["female"], "is_mandatory": True, "description": "Women-owned MSMEs only"}
        ],
        "benefits": [
            {"benefit_type": "incentive", "amount_max": Decimal("250000"), "disbursement_mode": "fee_waiver", "description": "Skill development fee waivers and marketing subsidies"}
        ]
    },
    {
        "name": "Annapurna Scheme for Food Catering",
        "ministry": "Ministry of Women & Child Development / State Bank of India",
        "description": "Collateral-free working capital loan up to ₹50,000 for women establishing food catering, lunch tiffin, and packaged snack businesses with a 36-month repayment period and 1-month moratorium.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("50000"),
        "min_benefit_inr": Decimal("10000"),
        "interest_rate": Decimal("11.00"),
        "benefit_description": "Up to ₹50,000 working capital loan for food catering equipment, utensils, and raw ingredients",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://sbi.co.in",
        "helpline_number": "1800-1234",
        "is_national": True,
        "target_genders": ["female"],
        "target_business_types": ["food_processing", "service", "retail"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Identity Proof (Aadhaar/Voter ID)", "mandatory": True, "format": "pdf"},
            {"name": "Residential Proof", "mandatory": True, "format": "pdf"},
            {"name": "List of food items and catering equipment to buy", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Visit nearest SBI branch or apply through nationalized partner banks", "channel": "offline"},
            {"step": 2, "description": "Submit Annapurna application form with guarantor/reference verification", "channel": "offline"},
            {"step": 3, "description": "Loan sanctioned with 36-month EMI repayment schedule", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_genders", "operator": "in", "rule_value": ["female"], "is_mandatory": True, "description": "Women entrepreneurs in catering"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_max": Decimal("50000"), "interest_rate": Decimal("11.00"), "disbursement_mode": "bank_loan", "description": "Up to ₹50,000 collateral-free loan for catering"}
        ]
    },
    {
        "name": "Stree Shakti Package for Women Entrepreneurs",
        "ministry": "Ministry of Finance / Public Sector Banks",
        "description": "Concessional credit package offering a 0.50% interest rate rebate for loans exceeding ₹2 lakh to enterprises where women hold more than 51% share capital, with zero margin requirement for loans up to ₹50,000.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("5000000"),
        "min_benefit_inr": Decimal("50000"),
        "interest_rate": Decimal("9.75"),
        "benefit_description": "0.50% interest rate concession on commercial loans + margin relaxation for women entrepreneurs",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://sbi.co.in",
        "helpline_number": "1800-1234",
        "is_national": True,
        "target_genders": ["female"],
        "women_ownership_min_percent": 51,
        "target_business_types": ["manufacturing", "service", "retail", "trading"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "documents_required": [
            {"name": "UDYAM Registration with female ownership proof", "mandatory": True, "format": "pdf"},
            {"name": "PAN & Aadhaar Card", "mandatory": True, "format": "pdf"},
            {"name": "Bank Statement (6 months)", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply at any State Bank of India or nationalized bank branch", "channel": "offline"},
            {"step": 2, "description": "Submit business plan establishing 51%+ female ownership and control", "channel": "offline"},
            {"step": 3, "description": "Receive 0.50% concessional interest rate on sanctioned credit", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_genders", "operator": "in", "rule_value": ["female"], "is_mandatory": True, "description": "Female ownership >= 51%"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_max": Decimal("5000000"), "interest_rate": Decimal("9.75"), "disbursement_mode": "bank_loan", "description": "Concessional business credit with 0.50% interest discount"}
        ]
    },
    {
        "name": "Dena Shakti Scheme for Women Entrepreneurs",
        "ministry": "Ministry of Finance / Bank of Baroda",
        "description": "Financial assistance up to ₹20 lakh for women entrepreneurs in agriculture, micro-manufacturing, retail stores, and educational/allied services with a 0.25% interest rate discount.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("2000000"),
        "min_benefit_inr": Decimal("50000"),
        "interest_rate": Decimal("9.50"),
        "benefit_description": "Concessional loans up to ₹20 lakh at 0.25% interest concession for women business owners",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://bankofbaroda.bank.in/",
        "helpline_number": "1800-5700",
        "is_national": True,
        "target_genders": ["female"],
        "women_ownership_min_percent": 51,
        "target_business_types": ["manufacturing", "service", "retail", "agriculture"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Aadhaar Card and PAN", "mandatory": True, "format": "pdf"},
            {"name": "UDYAM Registration", "mandatory": True, "format": "pdf"},
            {"name": "Project Proposal & Quotations", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Visit nearest Bank of Baroda branch", "channel": "offline"},
            {"step": 2, "description": "Submit Dena Shakti loan application form with required KYC", "channel": "offline"},
            {"step": 3, "description": "Loan sanctioned under priority sector lending guidelines", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_genders", "operator": "in", "rule_value": ["female"], "is_mandatory": True, "description": "Women entrepreneurs only"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_max": Decimal("2000000"), "interest_rate": Decimal("9.50"), "disbursement_mode": "bank_loan", "description": "Loans up to ₹20 Lakh with 0.25% concession"}
        ]
    },
    {
        "name": "Bharatiya Mahila Bank Business Loan",
        "ministry": "Ministry of Finance / State Bank of India",
        "description": "Large-scale business credit facility up to ₹20 crore for women entrepreneurs setting up large or expanding manufacturing enterprises, with collateral-free options up to ₹2 crore under CGTMSE cover.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("200000000"),
        "min_benefit_inr": Decimal("500000"),
        "interest_rate": Decimal("10.00"),
        "benefit_description": "Working capital and term loans up to ₹20 crore with flexible repayment up to 7 years",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://sbi.co.in",
        "helpline_number": "1800-425-3800",
        "is_national": True,
        "target_genders": ["female"],
        "women_ownership_min_percent": 51,
        "target_business_types": ["manufacturing", "service"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "documents_required": [
            {"name": "UDYAM Registration", "mandatory": True, "format": "pdf"},
            {"name": "Detailed Project Report", "mandatory": True, "format": "pdf"},
            {"name": "Audited Financials (2 years if existing)", "mandatory": False, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Submit loan application at SBI Commercial Branch", "channel": "offline"},
            {"step": 2, "description": "Project feasibility and credit underwriting review", "channel": "offline"},
            {"step": 3, "description": "Sanction with CGTMSE guarantee cover option", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_genders", "operator": "in", "rule_value": ["female"], "is_mandatory": True, "description": "Majority woman-owned unit"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_max": Decimal("200000000"), "interest_rate": Decimal("10.00"), "disbursement_mode": "bank_loan", "description": "Industrial credit up to ₹20 Crore for women"}
        ]
    },
    {
        "name": "Udyam Sakhi Portal Schemes",
        "ministry": "Ministry of MSME",
        "description": "Comprehensive digital service platform providing women entrepreneurs with business plan templates, incubator linkages, financial credit access, mentor networking, and state exhibition participation.",
        "scheme_type": "incentive",
        "max_benefit_inr": Decimal("500000"),
        "min_benefit_inr": Decimal("10000"),
        "benefit_description": "Business incubation support, mentor access, and exhibition stall subsidies for women entrepreneurs",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://udyamsakhi.msme.gov.in",
        "helpline_number": "011-23061544",
        "is_national": True,
        "target_genders": ["female"],
        "target_business_types": ["manufacturing", "service", "handicraft", "trading"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"},
            {"name": "UDYAM Registration Certificate", "mandatory": False, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Sign up on udyamsakhi.msme.gov.in portal", "channel": "online"},
            {"step": 2, "description": "Access business plan tools and match with regional MSME mentors", "channel": "online"},
            {"step": 3, "description": "Avail direct bank linkages and trade fair sponsorship", "channel": "online"}
        ],
        "rules": [
            {"field_name": "target_genders", "operator": "in", "rule_value": ["female"], "is_mandatory": True, "description": "Women entrepreneurs portal"}
        ],
        "benefits": [
            {"benefit_type": "incentive", "amount_max": Decimal("500000"), "disbursement_mode": "mentorship_and_grants", "description": "Incubation, mentoring, and marketing assistance"}
        ]
    },

    # ==================== 3. SC & ST ENTREPRENEURS ====================
    {
        "name": "National SC-ST Hub (NSSH) Special Marketing Assistance",
        "ministry": "Ministry of MSME",
        "description": "Comprehensive scheme providing 100% financial reimbursement of single point registration fee, 80% to 100% space rent subsidy for domestic/international exhibitions, and vendor development linkages for SC/ST MSEs.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("500000"),
        "min_benefit_inr": Decimal("25000"),
        "subsidy_percentage": Decimal("100.0"),
        "benefit_description": "100% reimbursement of NSIC registration + up to 100% stall charges in national exhibitions",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://www.scsthub.in",
        "helpline_number": "1800-110-180",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["sc", "st"],
        "target_business_types": ["manufacturing", "service"],
        "requires_udyam": True,
        "documents_required": [
            {"name": "Caste Certificate (SC/ST) from competent authority", "mandatory": True, "format": "pdf"},
            {"name": "UDYAM Registration with SC/ST ownership declaration", "mandatory": True, "format": "pdf"},
            {"name": "Exhibition participation bills and receipts", "mandatory": False, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Register on National SC-ST Hub portal (scsthub.in)", "channel": "online"},
            {"step": 2, "description": "Apply for tender facilitation, exhibition stall booking, or fee reimbursement", "channel": "both"},
            {"step": 3, "description": "Direct benefit transfer of subsidy into verified bank account", "channel": "online"}
        ],
        "rules": [
            {"field_name": "target_social_categories", "operator": "in", "rule_value": ["sc", "st"], "is_mandatory": True, "description": "Must belong to SC or ST community"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "amount_max": Decimal("500000"), "disbursement_mode": "direct_benefit_transfer", "description": "100% registration and exhibition space subsidies"}
        ]
    },
    {
        "name": "Ambedkar Social Innovation and Incubation Mission (ASIIM)",
        "ministry": "Ministry of Social Justice & Empowerment",
        "description": "Provides equity funding up to ₹30 lakh over 3 years (₹10 lakh per year) to 1,000 SC youth technology and innovation startups incubated in Technology Business Incubators (TBIs) under Venture Capital Fund for SC.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("3000000"),
        "min_benefit_inr": Decimal("1000000"),
        "benefit_description": "Equity funding up to ₹30 lakh over 3 years (₹10 lakh annually) + mentorship from premier TBIs",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://vcfsc.in",
        "helpline_number": "011-45051000",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["sc"],
        "target_business_types": ["technology", "service", "manufacturing"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "SC Caste Certificate", "mandatory": True, "format": "pdf"},
            {"name": "TBI Incubation Recommendation Letter", "mandatory": True, "format": "pdf"},
            {"name": "Pitch Deck & Detailed Technology Business Plan", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Get incubated in any DST/AIM approved Technology Business Incubator", "channel": "offline"},
            {"step": 2, "description": "TBI submits recommendation to Venture Capital Fund for SC (VCF-SC)", "channel": "online"},
            {"step": 3, "description": "Investment Committee sanctions equity disbursement", "channel": "online"}
        ],
        "rules": [
            {"field_name": "target_social_categories", "operator": "in", "rule_value": ["sc"], "is_mandatory": True, "description": "Scheduled Caste youth founders"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("3000000"), "disbursement_mode": "equity_grant", "description": "Up to ₹30 Lakh equity funding for tech startups"}
        ]
    },
    {
        "name": "NSFDC Micro Credit Finance (MCF) Scheme",
        "ministry": "Ministry of Social Justice & Empowerment",
        "description": "Micro credit loan up to ₹1.5 lakh per individual beneficiary at an interest rate of 5% p.a. through State Channelizing Agencies (SCAs) for small business activities and artisan self-employment.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("150000"),
        "min_benefit_inr": Decimal("20000"),
        "interest_rate": Decimal("5.00"),
        "benefit_description": "Concessional micro loan up to ₹1.5 lakh at 5% interest rate per annum with 3-year repayment",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://nsfdc.nic.in",
        "helpline_number": "011-22602770",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["sc"],
        "target_business_types": ["service", "trading", "retail", "handicraft"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "SC Certificate from Revenue Authority", "mandatory": True, "format": "pdf"},
            {"name": "Income Certificate (Family income below ₹3 lakh p.a.)", "mandatory": True, "format": "pdf"},
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply through State SC Development Corporation / SCA office", "channel": "offline"},
            {"step": 2, "description": "SCA forwards application after document verification to NSFDC", "channel": "both"},
            {"step": 3, "description": "Loan disbursed directly to bank account at 5% concessional interest", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_social_categories", "operator": "in", "rule_value": ["sc"], "is_mandatory": True, "description": "Scheduled Caste individuals below poverty limit"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_max": Decimal("150000"), "interest_rate": Decimal("5.00"), "disbursement_mode": "bank_loan", "description": "Micro credit loan at 5% p.a."}
        ]
    },
    {
        "name": "NSTFDC Adivasi Mahila Sashaktikaran Yojana (AMSY)",
        "ministry": "Ministry of Tribal Affairs",
        "description": "Concessional term loan up to ₹2 lakh at an interest rate of only 4% per annum for Scheduled Tribe women entrepreneurs to start or expand micro enterprises and income-generating self-employment.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("200000"),
        "min_benefit_inr": Decimal("25000"),
        "interest_rate": Decimal("4.00"),
        "benefit_description": "Concessional credit up to ₹2 lakh at 4% interest rate per annum with 5-year repayment",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://nstfdc.tribal.gov.in",
        "helpline_number": "011-26713580",
        "is_national": True,
        "target_genders": ["female"],
        "target_social_categories": ["st"],
        "target_business_types": ["handicraft", "agriculture", "retail", "service", "food_processing"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "ST Certificate from Competent Authority", "mandatory": True, "format": "pdf"},
            {"name": "Income Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply through State Tribal Development Cooperative Corporation / SCA", "channel": "offline"},
            {"step": 2, "description": "Evaluation of business feasibility and family background", "channel": "offline"},
            {"step": 3, "description": "Disbursement of loan up to ₹2 lakh at 4% interest rate", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_social_categories", "operator": "in", "rule_value": ["st"], "is_mandatory": True, "description": "Scheduled Tribe community"},
            {"field_name": "target_genders", "operator": "in", "rule_value": ["female"], "is_mandatory": True, "description": "Women beneficiaries only"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_max": Decimal("200000"), "interest_rate": Decimal("4.00"), "disbursement_mode": "bank_loan", "description": "Concessional term loan at 4% p.a. for tribal women"}
        ]
    },
    {
        "name": "NSTFDC Term Loan Scheme for ST Entrepreneurs",
        "ministry": "Ministry of Tribal Affairs",
        "description": "Financial assistance up to ₹50 lakh per unit for viable industrial, service, and agricultural ventures initiated by Scheduled Tribe entrepreneurs at 6% to 8% interest per annum with up to 90% project financing.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("5000000"),
        "min_benefit_inr": Decimal("200000"),
        "interest_rate": Decimal("6.00"),
        "benefit_description": "Term loan up to ₹50 lakh covering up to 90% project cost at 6% to 8% interest rate",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://nstfdc.tribal.gov.in",
        "helpline_number": "011-26713580",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["st"],
        "target_business_types": ["manufacturing", "service", "agriculture", "trading"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Scheduled Tribe Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Project Feasibility Report", "mandatory": True, "format": "pdf"},
            {"name": "UDYAM Registration", "mandatory": False, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Submit business proposal to State Tribal Development Agency", "channel": "offline"},
            {"step": 2, "description": "Technical appraisal by NSTFDC state desk", "channel": "both"},
            {"step": 3, "description": "Sanction and release of funds with quarterly review", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_social_categories", "operator": "in", "rule_value": ["st"], "is_mandatory": True, "description": "Scheduled Tribe entrepreneurs"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_max": Decimal("5000000"), "interest_rate": Decimal("6.00"), "disbursement_mode": "bank_loan", "description": "Term loans up to ₹50 Lakh at 6% p.a."}
        ]
    },
    {
        "name": "Special Credit Linked Capital Subsidy Scheme (SCLCSS) for SC/ST",
        "ministry": "Ministry of MSME",
        "description": "25% upfront capital subsidy (maximum ₹25 lakh) for SC/ST micro and small enterprises on institutional finance availed for procurement of plant and modern machinery without sector restriction.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("2500000"),
        "min_benefit_inr": Decimal("100000"),
        "subsidy_percentage": Decimal("25.0"),
        "benefit_description": "25% upfront capital subsidy up to ₹25 lakh on machinery purchase for SC/ST MSEs",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://www.msme.gov.in/",
        "helpline_number": "011-23063800",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["sc", "st"],
        "target_business_types": ["manufacturing", "service"],
        "requires_udyam": True,
        "documents_required": [
            {"name": "SC/ST Certificate", "mandatory": True, "format": "pdf"},
            {"name": "UDYAM Registration Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Bank Term Loan Sanction Letter for Machinery", "mandatory": True, "format": "pdf"},
            {"name": "Machinery Purchase Invoices and Installation Proof", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Avail term loan for machinery from any commercial bank", "channel": "offline"},
            {"step": 2, "description": "Bank uploads claim on MSME CLCSS portal with SC/ST proof", "channel": "online"},
            {"step": 3, "description": "Subsidy credited to Term Loan Account as fixed deposit / reduction", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_social_categories", "operator": "in", "rule_value": ["sc", "st"], "is_mandatory": True, "description": "SC or ST ownership"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("25.0"), "amount_max": Decimal("2500000"), "disbursement_mode": "bank_linked_subsidy", "description": "25% capital subsidy up to ₹25 Lakh for machinery"}
        ]
    },

    # ==================== 4. OBC & MINORITY ENTREPRENEURS ====================
    {
        "name": "NBCFDC Swavalamban Scheme",
        "ministry": "Ministry of Social Justice & Empowerment",
        "description": "Concessional term loan up to ₹5 lakh at 6% interest rate per annum for Other Backward Classes (OBC) youth and micro entrepreneurs with family income below ₹3 lakh per annum.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("500000"),
        "min_benefit_inr": Decimal("50000"),
        "interest_rate": Decimal("6.00"),
        "benefit_description": "Concessional business loan up to ₹5 lakh at 6% interest rate per annum with 5-year repayment",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://www.nbcfdc.gov.in",
        "helpline_number": "011-45854400",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["obc"],
        "target_business_types": ["manufacturing", "service", "retail", "trading", "handicraft"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "OBC Certificate (Non-Creamy Layer)", "mandatory": True, "format": "pdf"},
            {"name": "Family Income Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Submit application to State Backward Classes Development Corporation (SCA)", "channel": "offline"},
            {"step": 2, "description": "Verification of OBC non-creamy layer certificate and proposed trade", "channel": "offline"},
            {"step": 3, "description": "Disbursement through partnering public sector bank or RRB", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_social_categories", "operator": "in", "rule_value": ["obc"], "is_mandatory": True, "description": "Other Backward Classes (OBC)"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_max": Decimal("500000"), "interest_rate": Decimal("6.00"), "disbursement_mode": "bank_loan", "description": "Low-interest business credit at 6% p.a."}
        ]
    },
    {
        "name": "NBCFDC New Swarnima Scheme for OBC Women",
        "ministry": "Ministry of Social Justice & Empowerment",
        "description": "Concessional term loans up to ₹2 lakh at an interest rate of 5% p.a. for women belonging to backward classes without requiring collateral security to foster financial independence.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("200000"),
        "min_benefit_inr": Decimal("25000"),
        "interest_rate": Decimal("5.00"),
        "benefit_description": "Collateral-free loan up to ₹2 lakh at 5% interest rate per annum for OBC women",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://www.nbcfdc.gov.in",
        "helpline_number": "011-45854400",
        "is_national": True,
        "target_genders": ["female"],
        "target_social_categories": ["obc"],
        "target_business_types": ["handicraft", "retail", "service", "food_processing"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "OBC Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Income Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply through District Backward Classes Welfare Office or SCA", "channel": "offline"},
            {"step": 2, "description": "Eligibility audit by district committee", "channel": "offline"},
            {"step": 3, "description": "Loan sanction with 5-year repayment tenure", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_social_categories", "operator": "in", "rule_value": ["obc"], "is_mandatory": True, "description": "OBC category"},
            {"field_name": "target_genders", "operator": "in", "rule_value": ["female"], "is_mandatory": True, "description": "Women only"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_max": Decimal("200000"), "interest_rate": Decimal("5.00"), "disbursement_mode": "bank_loan", "description": "Concessional term loan up to ₹2 Lakh at 5% p.a."}
        ]
    },
    {
        "name": "NMDFC Term Loan Scheme for Minorities",
        "ministry": "Ministry of Minority Affairs",
        "description": "Financial credit up to ₹30 lakh for individual minority community entrepreneurs (Muslim, Christian, Sikh, Buddhist, Jain, Parsi) at a concessional interest rate of 6% p.a. covering up to 90% project cost.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("3000000"),
        "min_benefit_inr": Decimal("100000"),
        "interest_rate": Decimal("6.00"),
        "benefit_description": "Concessional term loan up to ₹30 lakh at 6% interest rate for minority entrepreneurs",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://www.nmdfc.org",
        "helpline_number": "011-26210086",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["minority"],
        "target_business_types": ["manufacturing", "service", "trading", "retail"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Minority Community Declaration / Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Income Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Project DPR and Bank Details", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply through State Minority Financial Corporation / SCA", "channel": "offline"},
            {"step": 2, "description": "Project review and NMDFC quota allocation", "channel": "both"},
            {"step": 3, "description": "Loan sanctioned with 5-year repayment schedule", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_social_categories", "operator": "in", "rule_value": ["minority"], "is_mandatory": True, "description": "Notified minority community"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_max": Decimal("3000000"), "interest_rate": Decimal("6.00"), "disbursement_mode": "bank_loan", "description": "Term loan up to ₹30 Lakh at 6% p.a."}
        ]
    },
    {
        "name": "NMDFC Virasat Scheme for Minority Artisans",
        "ministry": "Ministry of Minority Affairs",
        "description": "Concessional credit up to ₹10 lakh for master craftspersons and artisans belonging to notified minorities at 5% p.a. for male artisans and 4% p.a. for female artisans to purchase raw materials and modern hand tools.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("1000000"),
        "min_benefit_inr": Decimal("50000"),
        "interest_rate": Decimal("5.00"),
        "benefit_description": "Concessional credit up to ₹10 lakh at 4%-5% interest rate for traditional minority artisans",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://www.nmdfc.org",
        "helpline_number": "011-26210086",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["minority"],
        "target_business_types": ["handicraft", "manufacturing"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Artisan Identity Card (Pehchan) / Proof of Craft", "mandatory": True, "format": "pdf"},
            {"name": "Minority Community Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Submit application with craft portfolio to State Minority Development Agency", "channel": "offline"},
            {"step": 2, "description": "Verification of artisan credentials and credit history", "channel": "offline"},
            {"step": 3, "description": "Release of loan with 5-year repayment", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_social_categories", "operator": "in", "rule_value": ["minority"], "is_mandatory": True, "description": "Minority community artisan"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_max": Decimal("1000000"), "interest_rate": Decimal("5.00"), "disbursement_mode": "bank_loan", "description": "Artisan loan up to ₹10 Lakh at 4-5% p.a."}
        ]
    },
    {
        "name": "NMDFC Mahila Samridhi Yojana",
        "ministry": "Ministry of Minority Affairs",
        "description": "Micro-finance scheme providing collateral-free loans up to ₹1 lakh per woman at an interest rate of 4% per annum for women from minority communities organized into Self Help Groups (SHGs).",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("100000"),
        "min_benefit_inr": Decimal("15000"),
        "interest_rate": Decimal("4.00"),
        "benefit_description": "Micro finance loan up to ₹1 lakh at 4% interest rate per annum for minority women",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://www.nmdfc.org",
        "helpline_number": "011-26210086",
        "is_national": True,
        "target_genders": ["female"],
        "target_social_categories": ["minority"],
        "target_business_types": ["service", "trading", "retail", "handicraft"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Minority Community Declaration", "mandatory": True, "format": "pdf"},
            {"name": "SHG Membership Record", "mandatory": True, "format": "pdf"},
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply through Women SHG Federation or designated State Channelizing Agency", "channel": "offline"},
            {"step": 2, "description": "Direct bank group appraisal", "channel": "offline"},
            {"step": 3, "description": "Disbursement of micro-loan at 4% interest", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_social_categories", "operator": "in", "rule_value": ["minority"], "is_mandatory": True, "description": "Minority community"},
            {"field_name": "target_genders", "operator": "in", "rule_value": ["female"], "is_mandatory": True, "description": "Women only"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_max": Decimal("100000"), "interest_rate": Decimal("4.00"), "disbursement_mode": "bank_loan", "description": "Micro credit at 4% p.a. for minority women"}
        ]
    },

    # ==================== 5. YOUTH, RURAL & MICRO ENTERPRISES ====================
    {
        "name": "Prime Minister's Employment Generation Programme (PMEGP)",
        "ministry": "Ministry of MSME / KVIC",
        "description": "Major credit-linked subsidy scheme offering 15% to 35% margin money subsidy on project costs up to ₹50 lakh for manufacturing and ₹20 lakh for service units for first-time micro-entrepreneurs and youth.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("1750000"),
        "min_benefit_inr": Decimal("50000"),
        "subsidy_percentage": Decimal("35.0"),
        "benefit_description": "15% to 35% margin money capital subsidy (up to ₹17.5 lakh) on institutional bank loan",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://www.kviconline.gov.in",
        "helpline_number": "1800-3000-0034",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["manufacturing", "service"],
        "target_business_stages": ["idea", "pre_revenue"],
        "max_turnover_inr": Decimal("10000000"),
        "min_age": 18,
        "documents_required": [
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"},
            {"name": "Detailed Project Report (DPR)", "mandatory": True, "format": "pdf"},
            {"name": "Special Category Certificate (for 35% subsidy: SC/ST/OBC/Women/Minority/Rural)", "mandatory": False, "format": "pdf"},
            {"name": "Educational Certificate (8th pass for projects >₹10L)", "mandatory": False, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply online on KVIC e-portal (kviconline.gov.in)", "channel": "online"},
            {"step": 2, "description": "District Task Force Committee scrutinizes application and forwards to selected bank", "channel": "online"},
            {"step": 3, "description": "Bank sanctions loan; subsidy kept in 3-year term deposit and adjusted after verification", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "min_age", "operator": ">=", "rule_value": 18, "is_mandatory": True, "description": "Applicant must be at least 18 years old"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("35.0"), "amount_max": Decimal("1750000"), "disbursement_mode": "bank_linked_subsidy", "description": "Up to 35% margin money subsidy on project cost"}
        ]
    },
    {
        "name": "PM Vishwakarma Scheme",
        "ministry": "Ministry of MSME & Ministry of Skill Development",
        "description": "Comprehensive scheme providing end-to-end support to traditional craftspersons across 18 artisan trades: ₹15,000 modern toolkit grant, ₹500/day training stipend, and up to ₹3 lakh collateral-free enterprise loan at 5% interest.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("300000"),
        "min_benefit_inr": Decimal("15000"),
        "interest_rate": Decimal("5.00"),
        "benefit_description": "₹15,000 e-voucher toolkit grant + ₹3 lakh credit in two tranches (₹1L + ₹2L) at 5% interest",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://pmvishwakarma.gov.in",
        "helpline_number": "1800-267-7777",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["handicraft", "manufacturing", "service"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "min_age": 18,
        "documents_required": [
            {"name": "Aadhaar Card with biometric verification", "mandatory": True, "format": "pdf"},
            {"name": "Mobile Number linked with Aadhaar", "mandatory": True, "format": "pdf"},
            {"name": "Bank Passbook Copy", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Register with biometric authentication at nearest Common Service Center (CSC)", "channel": "csc"},
            {"step": 2, "description": "Gram Panchayat / Urban Local Body 3-tier verification of trade practice", "channel": "online"},
            {"step": 3, "description": "Complete 5-7 days basic skill training with ₹500/day stipend, receive ₹15k toolkit & loan", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "min_age", "operator": ">=", "rule_value": 18, "is_mandatory": True, "description": "18 years or older"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("15000"), "disbursement_mode": "e_voucher", "description": "₹15,000 modern toolkit e-voucher"},
            {"benefit_type": "loan", "amount_max": Decimal("300000"), "interest_rate": Decimal("5.00"), "disbursement_mode": "bank_loan", "description": "Up to ₹3 Lakh collateral-free loan at 5% p.a."}
        ]
    },
    {
        "name": "ASPIRE - Rural Business Incubation Scheme",
        "ministry": "Ministry of MSME",
        "description": "Financial grant up to ₹1 crore (100% of plant & machinery cost for govt agencies / 50% for private) to establish Livelihood Business Incubators (LBIs) and Technology Business Incubators in rural districts.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("10000000"),
        "min_benefit_inr": Decimal("500000"),
        "benefit_description": "Grant up to ₹1 crore for setting up rural livelihood incubators for agri-business and rural micro enterprises",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://aspire.msme.gov.in",
        "helpline_number": "011-23063800",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["agriculture", "manufacturing", "food_processing"],
        "target_business_stages": ["idea", "pre_revenue"],
        "documents_required": [
            {"name": "Incubator Entity Registration", "mandatory": True, "format": "pdf"},
            {"name": "Detailed Project Report on Rural Incubation", "mandatory": True, "format": "pdf"},
            {"name": "Land and Building Availability Proof", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Submit proposal on ASPIRE portal (aspire.msme.gov.in)", "channel": "online"},
            {"step": 2, "description": "Screening by Project Screening Committee of Ministry of MSME", "channel": "online"},
            {"step": 3, "description": "Funds released in 3 tranches for machinery installation and incubation setup", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["agriculture", "manufacturing", "food_processing"], "is_mandatory": True, "description": "Rural industry & agro-processing"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("10000000"), "disbursement_mode": "incubator_grant", "description": "Up to ₹1 Crore capital grant for rural business incubators"}
        ]
    },
    {
        "name": "SFURTI - Traditional Industries Regeneration Fund",
        "ministry": "Ministry of MSME",
        "description": "Cluster development grant up to ₹2.5 crore for regular clusters (up to 500 artisans) and up to ₹5 crore for major clusters (more than 500 artisans) to build Common Facility Centers (CFC), packaging units, and design banks.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("50000000"),
        "min_benefit_inr": Decimal("25000000"),
        "benefit_description": "Grant up to ₹5 crore covering 90% hard and soft interventions for artisan clusters",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://sfurti.msme.gov.in/SFURTI/Home.aspx",
        "helpline_number": "011-23061544",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["handicraft", "manufacturing", "food_processing"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Cluster Diagnostic Study Report (DSR)", "mandatory": True, "format": "pdf"},
            {"name": "Implementing Agency (IA) Registration Details", "mandatory": True, "format": "pdf"},
            {"name": "Technical Agency (TA) Consent", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Implementing agency submits cluster DSR through Nodal Agency", "channel": "online"},
            {"step": 2, "description": "Scheme Steering Committee reviews and sanctions DPR", "channel": "online"},
            {"step": 3, "description": "Common Facility Center construction and machinery procurement", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["handicraft", "manufacturing", "food_processing"], "is_mandatory": True, "description": "Traditional craft/agro clusters"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("50000000"), "disbursement_mode": "cluster_grant", "description": "Up to ₹5 Crore grant for artisan cluster infrastructure"}
        ]
    },
    {
        "name": "Deendayal Antyodaya Yojana - NRLM / Aajeevika",
        "ministry": "Ministry of Rural Development",
        "description": "Interest subvention on bank loans up to ₹3 lakh down to 7% per annum for rural Women Self Help Groups (SHGs), alongside revolving fund assistance of ₹15,000 and Community Investment Fund for micro-enterprises.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("300000"),
        "min_benefit_inr": Decimal("15000"),
        "interest_rate": Decimal("7.00"),
        "benefit_description": "Interest subvention down to 7% on bank credit up to ₹3 lakh + ₹15,000 revolving fund",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://aajeevika.gov.in",
        "helpline_number": "1800-111-555",
        "is_national": True,
        "target_genders": ["female"],
        "target_social_categories": ["all"],
        "target_business_types": ["handicraft", "agriculture", "retail", "food_processing"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "SHG Panchasutra compliance record", "mandatory": True, "format": "pdf"},
            {"name": "SHG Bank Passbook Copy", "mandatory": True, "format": "pdf"},
            {"name": "Aadhaar Card of members", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Form or join village level SHG under NRLM", "channel": "offline"},
            {"step": 2, "description": "Avail Revolving Fund and Village Organization micro-investment fund", "channel": "offline"},
            {"step": 3, "description": "Credit-linked bank loan with 7% interest subvention", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_genders", "operator": "in", "rule_value": ["female"], "is_mandatory": True, "description": "Rural women SHG members"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "amount_max": Decimal("300000"), "interest_rate": Decimal("7.00"), "disbursement_mode": "interest_subvention", "description": "Interest subvention down to 7% on micro-loans"}
        ]
    },
    {
        "name": "Deen Dayal Upadhyaya Grameen Kaushalya Yojana (DDU-GKY)",
        "ministry": "Ministry of Rural Development",
        "description": "Placement-linked skill development scheme for rural poor youth aged 15-35 years, offering 100% subsidized residential training, free uniform/books, tablet computers, and post-placement self-employment stipends.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("75000"),
        "min_benefit_inr": Decimal("15000"),
        "benefit_description": "100% free residential skill training, meals, transport allowance, and startup placement support",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://ddugky.gov.in",
        "helpline_number": "011-24660300",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["service", "manufacturing", "technology"],
        "target_business_stages": ["idea"],
        "min_age": 15,
        "max_age": 35,
        "documents_required": [
            {"name": "BPL / SECC Ration Card", "mandatory": True, "format": "pdf"},
            {"name": "Age Proof (Aadhaar / School Leaving)", "mandatory": True, "format": "pdf"},
            {"name": "Bank Account Details", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Register at nearest Gram Panchayat or Kaushal Panjee portal", "channel": "both"},
            {"step": 2, "description": "Counseling and trade allocation at training center", "channel": "offline"},
            {"step": 3, "description": "Certified skill training with post-placement stipend", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "min_age", "operator": ">=", "rule_value": 15, "is_mandatory": True, "description": "Age between 15 and 35"},
            {"field_name": "max_age", "operator": "<=", "rule_value": 35, "is_mandatory": True, "description": "Age between 15 and 35"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("75000"), "disbursement_mode": "training_grant", "description": "Free residential skill training & equipment"}
        ]
    },
    {
        "name": "PM SVANidhi - Street Vendor's AtmaNirbhar Nidhi",
        "ministry": "Ministry of Housing and Urban Affairs",
        "description": "Special micro-credit facility providing urban and peri-urban street vendors collateral-free working capital loans of ₹10,000 (1st tranche), ₹20,000 (2nd tranche), and ₹50,000 (3rd tranche) with 7% interest subsidy.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("50000"),
        "min_benefit_inr": Decimal("10000"),
        "interest_rate": Decimal("7.00"),
        "benefit_description": "Collateral-free working capital loan up to ₹50,000 with 7% interest subsidy + up to ₹1,200 annual digital cashback",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://pmsvanidhi.mohua.gov.in",
        "helpline_number": "1800-111-979",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["retail", "trading", "service", "food_processing"],
        "target_business_stages": ["idea", "revenue"],
        "documents_required": [
            {"name": "Vending Certificate / Identity Card issued by ULB", "mandatory": True, "format": "pdf"},
            {"name": "Aadhaar linked Mobile Number", "mandatory": True, "format": "pdf"},
            {"name": "Bank Account Passbook", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Check name in Urban Local Body street vendor survey list or get Letter of Recommendation", "channel": "both"},
            {"step": 2, "description": "Apply online at pmsvanidhi.mohua.gov.in or through nearest Common Service Center (CSC)", "channel": "both"},
            {"step": 3, "description": "Direct disbursement into bank account within 7 days", "channel": "online"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["retail", "trading", "service", "food_processing"], "is_mandatory": True, "description": "Street vending activities"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_max": Decimal("50000"), "interest_rate": Decimal("7.00"), "disbursement_mode": "bank_loan", "description": "Collateral-free working capital loan up to ₹50,000"}
        ]
    },
    {
        "name": "Gramodyog Vikas Yojana (KVIC)",
        "ministry": "Ministry of MSME / KVIC",
        "description": "Comprehensive village industry scheme distributing free modern production equipment kits (potter wheels, bee boxes, agarbatti making machines, leather toolkits) alongside specialized technical training.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("100000"),
        "min_benefit_inr": Decimal("15000"),
        "benefit_description": "Free electric pottery wheels, bee boxes, or agarbatti machinery kits + 10-day stipendiary training",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://www.kvic.gov.in",
        "helpline_number": "022-26711586",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["handicraft", "manufacturing", "agriculture"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"},
            {"name": "Traditional artisan declaration from Panchayat", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Register with nearest KVIC State / Divisional Office", "channel": "offline"},
            {"step": 2, "description": "Attend free equipment operation and skill training", "channel": "offline"},
            {"step": 3, "description": "Receive modern toolkit equipment kit with raw material linkage", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["handicraft", "manufacturing", "agriculture"], "is_mandatory": True, "description": "Traditional village crafts"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("100000"), "disbursement_mode": "equipment_grant", "description": "Free village industry production equipment kits"}
        ]
    },

    # ==================== 6. MSME QUALITY, TECHNOLOGY & CREDIT ====================
    {
        "name": "MSME Champions - ZED (Zero Defect Zero Effect) Certification",
        "ministry": "Ministry of MSME",
        "description": "Financial subsidy up to 80% on certification cost for Bronze, Silver, and Gold ZED certifications (80% for Micro, 60% for Small, 50% for Medium; additional 10% for women/SC/ST owned MSEs) plus ₹5 lakh consulting support.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("500000"),
        "min_benefit_inr": Decimal("10000"),
        "subsidy_percentage": Decimal("80.0"),
        "benefit_description": "Up to 80% certification fee subsidy + up to ₹5 lakh handholding and consulting assistance",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://zed.msme.gov.in",
        "helpline_number": "011-23063800",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["manufacturing"],
        "target_business_stages": ["revenue"],
        "requires_udyam": True,
        "documents_required": [
            {"name": "UDYAM Registration Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Factory pollution & safety compliance documents", "mandatory": False, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Take free digital ZED pledge on zed.msme.gov.in", "channel": "online"},
            {"step": 2, "description": "Apply for desktop/onsite assessment for Bronze/Silver/Gold level", "channel": "online"},
            {"step": 3, "description": "Receive official ZED certificate and fee subsidy directly", "channel": "online"}
        ],
        "rules": [
            {"field_name": "requires_udyam", "operator": "==", "rule_value": True, "is_mandatory": True, "description": "UDYAM registration required"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("80.0"), "amount_max": Decimal("500000"), "disbursement_mode": "direct_benefit_transfer", "description": "Up to 80% subsidy on ZED green certification"}
        ]
    },
    {
        "name": "MSME Competitive (Lean) Scheme",
        "ministry": "Ministry of MSME",
        "description": "Provides 90% financial contribution from Central Government towards consultant and expert fees for implementing 5S, Kaizen, Kanban, TPM, and Lean manufacturing tools in MSME clusters (up to ₹2.5 lakh per unit).",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("250000"),
        "min_benefit_inr": Decimal("50000"),
        "subsidy_percentage": Decimal("90.0"),
        "benefit_description": "90% government contribution for Lean consultant implementation fees (up to ₹2.5 lakh per unit)",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://lean.msme.gov.in",
        "helpline_number": "011-23063800",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["manufacturing"],
        "target_business_stages": ["revenue"],
        "requires_udyam": True,
        "documents_required": [
            {"name": "UDYAM Registration Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Lean Cluster formation agreement", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Form a mini cluster of 4-10 MSMEs and register on lean.msme.gov.in", "channel": "online"},
            {"step": 2, "description": "Empaneled QCI/NPC Lean consultant conducts diagnostic study", "channel": "offline"},
            {"step": 3, "description": "90% consultant fees reimbursed by Ministry upon milestone signoff", "channel": "online"}
        ],
        "rules": [
            {"field_name": "requires_udyam", "operator": "==", "rule_value": True, "is_mandatory": True, "description": "UDYAM registration required"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("90.0"), "amount_max": Decimal("250000"), "disbursement_mode": "consultant_fee_subsidy", "description": "90% Lean manufacturing consulting subsidy"}
        ]
    },
    {
        "name": "MSME Innovative Scheme - Incubation, Design & IPR",
        "ministry": "Ministry of MSME",
        "description": "Financial grant up to ₹15 lakh per approved idea for incubation in Host Institutes, up to ₹40 lakh for prototype equipment in design centers, and financial assistance up to ₹5 lakh for international and ₹1 lakh for domestic patent filing.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("1500000"),
        "min_benefit_inr": Decimal("100000"),
        "benefit_description": "Up to ₹15 lakh incubation grant for prototype development + up to ₹5 lakh patent reimbursement",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://innovative.msme.gov.in",
        "helpline_number": "011-23061544",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["technology", "manufacturing", "service"],
        "target_business_stages": ["idea", "pre_revenue"],
        "requires_udyam": True,
        "documents_required": [
            {"name": "UDYAM Registration Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Idea Innovation Proposal with Budget Breakdown", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Submit innovation idea on innovative.msme.gov.in during national hackathon window", "channel": "online"},
            {"step": 2, "description": "Evaluation by Host Institute (IIT/NIT/recognized engineering college)", "channel": "online"},
            {"step": 3, "description": "Direct grant disbursement up to ₹15 lakh in tranches for prototyping", "channel": "online"}
        ],
        "rules": [
            {"field_name": "requires_udyam", "operator": "==", "rule_value": True, "is_mandatory": True, "description": "UDYAM registration required"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("1500000"), "disbursement_mode": "incubator_grant", "description": "Up to ₹15 Lakh prototyping innovation grant"}
        ]
    },
    {
        "name": "Credit Linked Capital Subsidy Scheme (CLCSS)",
        "ministry": "Ministry of MSME",
        "description": "15% upfront capital subsidy (maximum ₹15 lakh) on institutional credit availed by micro and small enterprises for inducting well-established and improved technology in 51 specified sub-sectors.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("1500000"),
        "min_benefit_inr": Decimal("100000"),
        "subsidy_percentage": Decimal("15.0"),
        "benefit_description": "15% upfront capital subsidy up to ₹15 lakh on machinery loan for tech upgradation",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://www.msme.gov.in/",
        "helpline_number": "011-23063800",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["manufacturing"],
        "target_business_stages": ["revenue"],
        "requires_udyam": True,
        "documents_required": [
            {"name": "UDYAM Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Term Loan Sanction Letter for eligible technology machinery", "mandatory": True, "format": "pdf"},
            {"name": "Machinery Invoices & Bank Inspection Report", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply for term loan for modern plant machinery at participating bank", "channel": "offline"},
            {"step": 2, "description": "Nodal bank uploads subsidy claim on Ministry online portal", "channel": "online"},
            {"step": 3, "description": "15% subsidy kept in Term Deposit for 3 years, then adjusted against loan principal", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "requires_udyam", "operator": "==", "rule_value": True, "is_mandatory": True, "description": "UDYAM required"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("15.0"), "amount_max": Decimal("1500000"), "disbursement_mode": "bank_linked_subsidy", "description": "15% capital subsidy up to ₹15 Lakh"}
        ]
    },
    {
        "name": "Raising and Accelerating MSME Performance (RAMP)",
        "ministry": "Ministry of MSME / World Bank",
        "description": "World Bank-assisted flagship program improving MSME access to finance, market development, supplier integration, delayed payment monitoring, and green technology adoption grants.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("2000000"),
        "min_benefit_inr": Decimal("100000"),
        "benefit_description": "Institutional grants for green transition, digital tools, and supplier integration",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://ramp.msme.gov.in/ramp/",
        "helpline_number": "011-23063800",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["manufacturing", "service"],
        "target_business_stages": ["revenue"],
        "requires_udyam": True,
        "documents_required": [
            {"name": "UDYAM Registration Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Audited balance sheet (previous 2 years)", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Register on ramp.msme.gov.in through state implementation desk", "channel": "online"},
            {"step": 2, "description": "Enroll in Strategic Investment Plan (SIP) supplier development tracks", "channel": "online"},
            {"step": 3, "description": "Avail capacity grants and delayed payment dispute resolution", "channel": "online"}
        ],
        "rules": [
            {"field_name": "requires_udyam", "operator": "==", "rule_value": True, "is_mandatory": True, "description": "UDYAM registration required"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("2000000"), "disbursement_mode": "institutional_grant", "description": "Green and digital transition matching grants"}
        ]
    },
    {
        "name": "Procurement and Marketing Support (PMS) Scheme",
        "ministry": "Ministry of MSME",
        "description": "Financial assistance covering 80% to 100% of stall charges in national/international exhibitions, retail trade fairs, modern barcode adoption reimbursement, and e-commerce platform onboarding.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("300000"),
        "min_benefit_inr": Decimal("15000"),
        "subsidy_percentage": Decimal("100.0"),
        "benefit_description": "100% reimbursement of stall rent for women/SC/ST (80% for general) in approved trade expos",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://www.msme.gov.in/",
        "helpline_number": "011-23063800",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["manufacturing", "service", "handicraft"],
        "target_business_stages": ["revenue"],
        "requires_udyam": True,
        "documents_required": [
            {"name": "UDYAM Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Trade fair stall allotment letter and fee receipt", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply online on MSME PMS portal prior to trade fair participation", "channel": "online"},
            {"step": 2, "description": "Participate in exhibition and collect participation certificate", "channel": "offline"},
            {"step": 3, "description": "Upload rent receipt for direct bank transfer reimbursement", "channel": "online"}
        ],
        "rules": [
            {"field_name": "requires_udyam", "operator": "==", "rule_value": True, "is_mandatory": True, "description": "UDYAM registration required"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "amount_max": Decimal("300000"), "disbursement_mode": "direct_benefit_transfer", "description": "100% trade fair stall reimbursement"}
        ]
    },
    {
        "name": "Interest Subvention Scheme for Incremental Credit to MSMEs",
        "ministry": "Ministry of MSME / Reserve Bank of India",
        "description": "Provides 2% per annum interest subvention on fresh or incremental working capital and term loan facilities extended to eligible MSMEs holding valid UDYAM and GST registrations.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("2000000"),
        "min_benefit_inr": Decimal("20000"),
        "interest_rate": Decimal("8.00"),
        "benefit_description": "2% per annum interest rebate on incremental working capital and term loans",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://www.rbi.org.in",
        "helpline_number": "14440",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["manufacturing", "service"],
        "target_business_stages": ["revenue"],
        "requires_udyam": True,
        "requires_gst": True,
        "documents_required": [
            {"name": "UDYAM Registration Certificate", "mandatory": True, "format": "pdf"},
            {"name": "GST Returns (GSTR-3B)", "mandatory": True, "format": "pdf"},
            {"name": "Bank loan account statements", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Submit UDYAM and GSTIN to lending bank branch", "channel": "offline"},
            {"step": 2, "description": "Lender verifies active account and submits claim to RBI/SIDBI nodal portal", "channel": "online"},
            {"step": 3, "description": "2% interest rebate credited quarterly to loan account", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "requires_udyam", "operator": "==", "rule_value": True, "is_mandatory": True, "description": "UDYAM registration required"},
            {"field_name": "requires_gst", "operator": "==", "rule_value": True, "is_mandatory": True, "description": "GST registration required"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "amount_max": Decimal("2000000"), "disbursement_mode": "interest_subvention", "description": "2% interest subvention credited directly"}
        ]
    },

    # ==================== 7. STARTUPS, INNOVATION & DEEP TECH ====================
    {
        "name": "MeitY TIDE 2.0 - Tech Incubation & Development",
        "ministry": "Ministry of Electronics and Information Technology (MeitY)",
        "description": "Financial and incubation support to ICT and deep-tech startups: Entrepreneur-in-Residence (EiR) fellowship up to ₹4 lakh and Grant-in-Aid up to ₹7 lakh for prototype development in AI, IoT, and Blockchain.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("700000"),
        "min_benefit_inr": Decimal("100000"),
        "benefit_description": "EiR fellowship up to ₹4 lakh + prototype grant up to ₹7 lakh via empaneled TBIs",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://www.meity.gov.in",
        "helpline_number": "011-24301100",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["technology"],
        "target_business_stages": ["idea", "pre_revenue"],
        "documents_required": [
            {"name": "Technical Proposal & Working Architecture", "mandatory": True, "format": "pdf"},
            {"name": "Founder Resume & Identity Proof", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply to any of 51 TIDE 2.0 incubation centers across India", "channel": "online"},
            {"step": 2, "description": "Technical screening by expert review panel", "channel": "online"},
            {"step": 3, "description": "Grant sanctioned with access to lab facilities and compute resources", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["technology"], "is_mandatory": True, "description": "ICT and tech startups"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("700000"), "disbursement_mode": "incubator_grant", "description": "Up to ₹7 Lakh prototype grant"}
        ]
    },
    {
        "name": "MeitY SAMRIDH Accelerator Scheme",
        "ministry": "Ministry of Electronics and Information Technology (MeitY)",
        "description": "Matched funding investment up to ₹40 lakh per tech startup alongside selected partner accelerators to scale software products with proven customer traction, domestic IP, and growth potential.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("4000000"),
        "min_benefit_inr": Decimal("1000000"),
        "benefit_description": "Matching government co-investment up to ₹40 lakh per startup with customized accelerator cohort support",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://meitystartuphub.in",
        "helpline_number": "011-24301100",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["technology"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "requires_dpiit": True,
        "documents_required": [
            {"name": "DPIIT Startup Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Working Software Demo / Product Metrics", "mandatory": True, "format": "pdf"},
            {"name": "Accelerator Cohort Admission Offer", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply through MeitY Startup Hub (MSH) portal for SAMRIDH cohort", "channel": "online"},
            {"step": 2, "description": "Accelerator partner selects startup and commits matching seed capital", "channel": "online"},
            {"step": 3, "description": "MeitY releases matching grant-to-equity funds up to ₹40 lakh", "channel": "online"}
        ],
        "rules": [
            {"field_name": "requires_dpiit", "operator": "==", "rule_value": True, "is_mandatory": True, "description": "DPIIT recognition required"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("4000000"), "disbursement_mode": "accelerator_seed", "description": "Up to ₹40 Lakh matching accelerator capital"}
        ]
    },
    {
        "name": "BIRAC Biotechnology Ignition Grant (BIG)",
        "ministry": "Department of Biotechnology, Ministry of Science & Technology",
        "description": "Prestigious grant-in-aid up to ₹50 lakh for up to 18 months for early-stage entrepreneurs, medical innovators, and biotech startups to establish commercial proof-of-concept in healthcare, diagnostics, and agritech.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("5000000"),
        "min_benefit_inr": Decimal("1000000"),
        "benefit_description": "Grant-in-aid up to ₹50 lakh for 18 months without equity dilution",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://www.birac.nic.in",
        "helpline_number": "011-47744500",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["technology", "food_processing", "agriculture"],
        "target_business_stages": ["idea", "pre_revenue"],
        "documents_required": [
            {"name": "Detailed Scientific Research Proposal", "mandatory": True, "format": "pdf"},
            {"name": "Company Incorporation / Individual Bio-profile", "mandatory": True, "format": "pdf"},
            {"name": "Milestone Gantt Chart & Budget Justification", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Submit proposal online on BIRAC portal during bi-annual call (Jan & July)", "channel": "online"},
            {"step": 2, "description": "Presentation before Technical Expert Committee (TEC)", "channel": "online"},
            {"step": 3, "description": "Funds disbursed in 4 milestones through designated BIG Partner incubator", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["technology", "food_processing", "agriculture"], "is_mandatory": True, "description": "Biotech, medtech, or agritech"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("5000000"), "disbursement_mode": "equity_free_grant", "description": "Up to ₹50 Lakh equity-free grant-in-aid"}
        ]
    },
    {
        "name": "BIRAC SEED Fund (Sustainable Entrepreneurship)",
        "ministry": "Department of Biotechnology / BIRAC",
        "description": "Financial equity and debt support up to ₹30 lakh per startup through bio-incubators to bridge the gap between discovery and commercialization of bio-innovations and clinical testing.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("3000000"),
        "min_benefit_inr": Decimal("500000"),
        "benefit_description": "Equity/debt financing up to ₹30 lakh per enterprise via bio-incubators",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://www.birac.nic.in",
        "helpline_number": "011-47744500",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["technology", "agriculture"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Incubation Agreement with BIRAC bio-incubator", "mandatory": True, "format": "pdf"},
            {"name": "Commercialization Business Plan", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Join an empaneled BIRAC Bio-NEST incubator", "channel": "offline"},
            {"step": 2, "description": "Apply to the Incubator Seed Investment Committee", "channel": "online"},
            {"step": 3, "description": "Sanction of seed capital for clinical trials or market entry", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["technology", "agriculture"], "is_mandatory": True, "description": "Bio-innovations"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("3000000"), "disbursement_mode": "incubator_seed", "description": "Up to ₹30 Lakh seed financing"}
        ]
    },
    {
        "name": "MeitY GENESIS - Tier-II & III Startup Support",
        "ministry": "Ministry of Electronics and Information Technology (MeitY)",
        "description": "Venture discovery, mentorship, and seed grants up to ₹20 lakh for tech startups originating from Tier-II, Tier-III cities, and rural districts across India to decentralize tech innovation.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("2000000"),
        "min_benefit_inr": Decimal("200000"),
        "benefit_description": "Seed grants up to ₹20 lakh + national mentor network access for Tier-2/3 tech founders",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://www.meity.gov.in",
        "helpline_number": "011-24301100",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["technology", "service"],
        "target_business_stages": ["idea", "pre_revenue"],
        "documents_required": [
            {"name": "Address proof located in Tier-2/3 City / District", "mandatory": True, "format": "pdf"},
            {"name": "Software Architecture / Prototype details", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply through MeitY Startup Hub GENESIS regional challenges", "channel": "online"},
            {"step": 2, "description": "Regional hackathon & screening evaluation", "channel": "online"},
            {"step": 3, "description": "Seed grant disbursement with venture scaling support", "channel": "online"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["technology", "service"], "is_mandatory": True, "description": "Tech startups in non-metro areas"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("2000000"), "disbursement_mode": "seed_grant", "description": "Up to ₹20 Lakh Tier-2/3 seed capital"}
        ]
    },
    {
        "name": "NIDHI-PRAYAS - Prototyping Hardware Grant",
        "ministry": "Department of Science & Technology (DST)",
        "description": "Proof-of-concept prototype grant up to ₹10 lakh for young innovators to convert physical hardware and tech ideas into workable prototypes within 18 months in recognized PRAYAS centers.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("1000000"),
        "min_benefit_inr": Decimal("100000"),
        "benefit_description": "Grant up to ₹10 lakh for hardware fabrication, component procurement, and 3D prototyping",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://www.nstdbtc.dst.gov.in",
        "helpline_number": "011-26590300",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["technology", "manufacturing"],
        "target_business_stages": ["idea"],
        "documents_required": [
            {"name": "Hardware Proof-of-Concept Design Document", "mandatory": True, "format": "pdf"},
            {"name": "Bill of Materials (BOM) Estimate", "mandatory": True, "format": "pdf"},
            {"name": "Founder Identity Proof", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply to any DST-recognized PRAYAS Centre (PC)", "channel": "online"},
            {"step": 2, "description": "PRAYAS Monitoring Committee (PMC) presentation", "channel": "online"},
            {"step": 3, "description": "Disbursement of prototype grant with fabrication lab access", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["technology", "manufacturing"], "is_mandatory": True, "description": "Hardware and engineering tech"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("1000000"), "disbursement_mode": "prototyping_grant", "description": "Up to ₹10 Lakh hardware prototyping grant"}
        ]
    },
    {
        "name": "NIDHI-EIR - Entrepreneur-in-Residence Fellowship",
        "ministry": "Department of Science & Technology (DST)",
        "description": "Monthly subsistence fellowship of ₹30,000 for up to 18 months for aspiring technology innovators to work full-time on commercially promising technology ventures without financial stress.",
        "scheme_type": "fellowship",
        "max_benefit_inr": Decimal("540000"),
        "min_benefit_inr": Decimal("180000"),
        "benefit_description": "Monthly fellowship of ₹30,000 for up to 18 months + lab workspace access",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://www.nidhi-eir.in",
        "helpline_number": "011-26590300",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["technology", "service", "manufacturing"],
        "target_business_stages": ["idea"],
        "documents_required": [
            {"name": "Engineering / Science Degree Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Innovative Technology Business Concept Note", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply on nidhi-eir.uk to an empaneled Technology Business Incubator", "channel": "online"},
            {"step": 2, "description": "Selection committee interview on full-time commitment and technology novelty", "channel": "online"},
            {"step": 3, "description": "Monthly fellowship of ₹30,000 credited directly to personal bank account", "channel": "online"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["technology", "service", "manufacturing"], "is_mandatory": True, "description": "Science & technology innovations"}
        ],
        "benefits": [
            {"benefit_type": "fellowship", "amount_max": Decimal("540000"), "disbursement_mode": "monthly_stipend", "description": "₹30,000 monthly fellowship for up to 18 months"}
        ]
    },

    # ==================== 8. AGRICULTURE, FOOD PROCESSING & ALLIED ====================
    {
        "name": "Agriculture Infrastructure Fund (AIF)",
        "ministry": "Ministry of Agriculture and Farmers Welfare",
        "description": "3% per annum interest subvention on bank loans up to ₹2 crore for up to 7 years, plus CGTMSE fee coverage, for post-harvest management infrastructure, cold chains, assaying units, and community farming assets.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("20000000"),
        "min_benefit_inr": Decimal("500000"),
        "interest_rate": Decimal("6.00"),
        "benefit_description": "3% interest subvention on loans up to ₹2 crore + credit guarantee coverage under CGTMSE",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://agriinfra.dac.gov.in",
        "helpline_number": "1800-180-1551",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["agriculture", "food_processing", "service"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Land ownership / lease agreement for infrastructure", "mandatory": True, "format": "pdf"},
            {"name": "Detailed Project Report (DPR)", "mandatory": True, "format": "pdf"},
            {"name": "Bank account details and registration proof", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Register and submit project report on agriinfra.dac.gov.in", "channel": "online"},
            {"step": 2, "description": "Ministry review and digital forwarding to chosen lending bank", "channel": "online"},
            {"step": 3, "description": "Loan sanctioned with 3% interest subvention auto-credited by NABARD/DA&FW", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["agriculture", "food_processing", "service"], "is_mandatory": True, "description": "Post-harvest and agri-logistics"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "amount_max": Decimal("20000000"), "interest_rate": Decimal("6.00"), "disbursement_mode": "interest_subvention", "description": "3% interest subvention on loans up to ₹2 Crore"}
        ]
    },
    {
        "name": "PM Kisan Sampada - Food Processing Capacities (CEFPPC)",
        "ministry": "Ministry of Food Processing Industries",
        "description": "Capital subsidy of 35% of eligible project cost in general areas and 50% in difficult/hilly areas (maximum ₹5 crore) for setting up or modernizing food processing and packaging plants.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("50000000"),
        "min_benefit_inr": Decimal("5000000"),
        "subsidy_percentage": Decimal("35.0"),
        "benefit_description": "35% to 50% capital subsidy (up to ₹5 crore) on food processing plant and machinery",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://mofpi.gov.in",
        "helpline_number": "011-23062118",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["food_processing", "manufacturing"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "requires_udyam": True,
        "documents_required": [
            {"name": "UDYAM Registration Certificate", "mandatory": True, "format": "pdf"},
            {"name": "FSSAI License / Application", "mandatory": True, "format": "pdf"},
            {"name": "Bank Term Loan Appraisal Report", "mandatory": True, "format": "pdf"},
            {"name": "Detailed Project Report (DPR)", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply online on MoFPI Sampada portal in response to Expression of Interest", "channel": "online"},
            {"step": 2, "description": "Technical Committee reviews DPR and bank appraisal", "channel": "online"},
            {"step": 3, "description": "Grant released in 3 milestone installments linked to bank disbursement", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["food_processing", "manufacturing"], "is_mandatory": True, "description": "Food processing enterprises"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("35.0"), "amount_max": Decimal("50000000"), "disbursement_mode": "bank_linked_subsidy", "description": "Up to ₹5 Crore capital subsidy for food processing"}
        ]
    },
    {
        "name": "Agricultural Marketing Infrastructure (AMI)",
        "ministry": "Ministry of Agriculture and Farmers Welfare",
        "description": "25% to 33.33% capital subsidy (up to ₹3 crore for registered farmer enterprises and women/SC/ST entrepreneurs) on modern agricultural storage, godowns, and cleaning/grading units.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("30000000"),
        "min_benefit_inr": Decimal("500000"),
        "subsidy_percentage": Decimal("33.33"),
        "benefit_description": "25% to 33.33% back-ended capital subsidy on agricultural godowns and marketing infrastructure",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://agricoop.nic.in",
        "helpline_number": "011-23381501",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["agriculture", "service"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Land Title / Registered Lease for warehouse", "mandatory": True, "format": "pdf"},
            {"name": "Bank Term Loan Sanction Letter", "mandatory": True, "format": "pdf"},
            {"name": "Technical Blueprint approved by chartered engineer", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Obtain term loan from commercial bank or RRB", "channel": "offline"},
            {"step": 2, "description": "Bank submits subsidy claim to NABARD / DMI within 90 days of first disbursement", "channel": "online"},
            {"step": 3, "description": "NABARD inspects site and credits subsidy to borrower's Subsidy Reserve Fund account", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["agriculture", "service"], "is_mandatory": True, "description": "Agri storage and marketing"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("33.33"), "amount_max": Decimal("30000000"), "disbursement_mode": "nabard_subsidy", "description": "Up to ₹3 Crore storage infrastructure subsidy"}
        ]
    },
    {
        "name": "Mission for Integrated Development of Horticulture (MIDH)",
        "ministry": "Ministry of Agriculture and Farmers Welfare",
        "description": "40% to 50% credit-linked back-ended capital subsidy for cold storage facilities, ripening chambers, pack houses, tissue culture labs, and modern nursery infrastructure for horticultural entrepreneurs.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("25000000"),
        "min_benefit_inr": Decimal("500000"),
        "subsidy_percentage": Decimal("50.0"),
        "benefit_description": "40% to 50% credit-linked capital subsidy for cold chains and pack houses",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://midh.gov.in",
        "helpline_number": "011-23381012",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["agriculture", "food_processing"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Land ownership proof and layout", "mandatory": True, "format": "pdf"},
            {"name": "Detailed Project Report for cold storage / pack house", "mandatory": True, "format": "pdf"},
            {"name": "Bank term loan sanction letter", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply through State Horticulture Mission (SHM) or National Horticulture Board (NHB)", "channel": "both"},
            {"step": 2, "description": "In-principle approval issued for bank loan processing", "channel": "online"},
            {"step": 3, "description": "Joint inspection and release of back-ended subsidy", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["agriculture", "food_processing"], "is_mandatory": True, "description": "Horticulture and cold chain"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("50.0"), "amount_max": Decimal("25000000"), "disbursement_mode": "bank_linked_subsidy", "description": "Up to ₹2.5 Crore cold chain & pack house subsidy"}
        ]
    },
    {
        "name": "Pradhan Mantri Matsya Sampada Yojana (PMMSY)",
        "ministry": "Department of Fisheries, Ministry of Fisheries, Animal Husbandry and Dairying",
        "description": "40% government subsidy for general category and 60% for women, SC, and ST beneficiaries for setting up fish processing units, insulated cold chain vans, biofloc units, and freshwater aquaculture.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("5000000"),
        "min_benefit_inr": Decimal("100000"),
        "subsidy_percentage": Decimal("60.0"),
        "benefit_description": "40% to 60% government subsidy (up to ₹50 lakh) for aquaculture, fish processing, and cold vans",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://pmmsy.dof.gov.in",
        "helpline_number": "1800-425-1660",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["agriculture", "food_processing", "manufacturing"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Water body lease / Land ownership document", "mandatory": True, "format": "pdf"},
            {"name": "Fisheries Department Registration", "mandatory": True, "format": "pdf"},
            {"name": "Detailed Project Report", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Submit DPR on PMMSY portal or to District Fisheries Officer", "channel": "both"},
            {"step": 2, "description": "District Level Committee (DLC) reviews and approves proposal", "channel": "online"},
            {"step": 3, "description": "Subsidy disbursed in milestone-based DBT tranches", "channel": "online"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["agriculture", "food_processing", "manufacturing"], "is_mandatory": True, "description": "Fisheries and aquaculture enterprises"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("60.0"), "amount_max": Decimal("5000000"), "disbursement_mode": "direct_benefit_transfer", "description": "40%-60% subsidy up to ₹50 Lakh for fisheries"}
        ]
    },
    {
        "name": "Animal Husbandry Infrastructure Development Fund (AHIDF)",
        "ministry": "Department of Animal Husbandry and Dairying",
        "description": "3% interest subvention for dairy processing plants, meat processing facilities, and animal feed manufacturing units, with loan coverage up to 90% from commercial banks and credit guarantee options.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("30000000"),
        "min_benefit_inr": Decimal("1000000"),
        "interest_rate": Decimal("6.50"),
        "benefit_description": "3% interest subvention on commercial bank loans covering up to 90% of dairy/meat plant project cost",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://ahidf.udyamimitra.in",
        "helpline_number": "1800-180-1111",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["food_processing", "manufacturing", "agriculture"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "requires_udyam": True,
        "documents_required": [
            {"name": "UDYAM Registration Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Detailed Project Report on Dairy/Meat/Feed processing", "mandatory": True, "format": "pdf"},
            {"name": "Land and FSSAI documentation", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply online at ahidf.udyamimitra.in", "channel": "online"},
            {"step": 2, "description": "Digital appraisal and sanction by partnering commercial bank", "channel": "online"},
            {"step": 3, "description": "Quarterly interest subvention of 3% credited to loan account", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["food_processing", "manufacturing", "agriculture"], "is_mandatory": True, "description": "Animal husbandry & dairy units"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "amount_max": Decimal("30000000"), "interest_rate": Decimal("6.50"), "disbursement_mode": "interest_subvention", "description": "3% interest subvention for animal husbandry units"}
        ]
    },
    {
        "name": "National Beekeeping & Honey Mission (NBHM)",
        "ministry": "Ministry of Agriculture and Farmers Welfare",
        "description": "Up to 80% financial subsidy for procurement of bee colonies, modern beehives, honey extraction units, and custom hiring centers for beekeeping entrepreneurs, youth, and women SHGs.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("500000"),
        "min_benefit_inr": Decimal("30000"),
        "subsidy_percentage": Decimal("80.0"),
        "benefit_description": "Up to 80% subsidy on beehives, honey extraction equipment, and training",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://nbhm.gov.in",
        "helpline_number": "011-23381501",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["agriculture", "food_processing"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "National Bee Board (NBB) Registration", "mandatory": True, "format": "pdf"},
            {"name": "Aadhaar Card and Bank Account", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Register on Madhukranti portal (nbhm.gov.in)", "channel": "online"},
            {"step": 2, "description": "Submit equipment purchase quotation for bee colonies & hives", "channel": "both"},
            {"step": 3, "description": "Direct subsidy transfer upon field verification by State Horticulture Dept", "channel": "online"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["agriculture", "food_processing"], "is_mandatory": True, "description": "Apiculture & honey processing"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("80.0"), "amount_max": Decimal("500000"), "disbursement_mode": "direct_benefit_transfer", "description": "Up to 80% subsidy on beekeeping equipment"}
        ]
    },

    # ==================== 9. HANDICRAFTS, HANDLOOMS & TEXTILES ====================
    {
        "name": "National Handicrafts Development Programme (NHDP)",
        "ministry": "Ministry of Textiles",
        "description": "Skill upgradation, distribution of modern toolkits up to ₹10,000, design development workshops, and financial assistance up to ₹10 lakh for master artisans to participate in national and international craft expos.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("1000000"),
        "min_benefit_inr": Decimal("10000"),
        "benefit_description": "₹10,000 toolkit assistance + design workshops + 100% expo travel/stall sponsorship",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://handicrafts.nic.in",
        "helpline_number": "1800-208-4800",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["handicraft", "manufacturing"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Pehchan Artisan Identity Card", "mandatory": True, "format": "pdf"},
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"},
            {"name": "Bank Passbook Copy", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Obtain Pehchan ID Card from nearest Field Facilitation Centre", "channel": "offline"},
            {"step": 2, "description": "Apply for design workshop or marketing event stall online", "channel": "online"},
            {"step": 3, "description": "Receive modern toolkits and marketing allowances directly", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["handicraft", "manufacturing"], "is_mandatory": True, "description": "Handicrafts and traditional arts"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("1000000"), "disbursement_mode": "artisan_grant", "description": "Marketing grants and modern toolkit distribution"}
        ]
    },
    {
        "name": "Ambedkar Hastshilp Vikas Yojana (AHVY)",
        "ministry": "Ministry of Textiles",
        "description": "Mobilization and financial grant assistance up to ₹50 lakh per project for community empowerment, Self Help Group formation, design intervention, and technology upgradation in traditional craft clusters.",
        "scheme_type": "grant",
        "max_benefit_inr": Decimal("5000000"),
        "min_benefit_inr": Decimal("500000"),
        "benefit_description": "Grant up to ₹50 lakh for cluster mobilization, design training, and common facility centers",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://handicrafts.nic.in",
        "helpline_number": "1800-208-4800",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["handicraft"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Cluster Baseline Survey Report", "mandatory": True, "format": "pdf"},
            {"name": "SHG / Producer Company Registration Proof", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Implementing Agency prepares baseline survey of craft cluster", "channel": "offline"},
            {"step": 2, "description": "Proposal submission to Development Commissioner (Handicrafts)", "channel": "both"},
            {"step": 3, "description": "Sanction and release of funds for community mobilization & design", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["handicraft"], "is_mandatory": True, "description": "Traditional craft clusters"}
        ],
        "benefits": [
            {"benefit_type": "grant", "amount_max": Decimal("5000000"), "disbursement_mode": "cluster_grant", "description": "Up to ₹50 Lakh cluster mobilization grant"}
        ]
    },
    {
        "name": "National Handloom Development Programme - Weavers Mudra",
        "ministry": "Ministry of Textiles",
        "description": "Concessional loan up to ₹2 lakh at 6% interest rate with margin money assistance of up to ₹25,000 per weaver and credit guarantee coverage under CGTMSE for three years without third-party collateral.",
        "scheme_type": "loan",
        "max_benefit_inr": Decimal("200000"),
        "min_benefit_inr": Decimal("25000"),
        "interest_rate": Decimal("6.00"),
        "benefit_description": "Subsidized loan up to ₹2 lakh at 6% interest + ₹25,000 margin money assistance",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://handlooms.nic.in",
        "helpline_number": "1800-208-9988",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["handicraft", "manufacturing"],
        "target_business_stages": ["idea", "pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Weaver Identity Card issued by DC (Handlooms)", "mandatory": True, "format": "pdf"},
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"},
            {"name": "Bank Account Details", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply through Weavers Service Centre (WSC) or commercial bank branch", "channel": "offline"},
            {"step": 2, "description": "Weavers Mudra loan sanctioned with ₹25,000 margin money credit", "channel": "offline"},
            {"step": 3, "description": "7% interest subvention credited directly by Ministry to bank", "channel": "online"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["handicraft", "manufacturing"], "is_mandatory": True, "description": "Handloom weaving"}
        ],
        "benefits": [
            {"benefit_type": "loan", "amount_max": Decimal("200000"), "interest_rate": Decimal("6.00"), "disbursement_mode": "bank_loan", "description": "Concessional loan up to ₹2 Lakh at 6% p.a."}
        ]
    },
    {
        "name": "Silk Samagra 2 - Integrated Silk Development",
        "ministry": "Central Silk Board, Ministry of Textiles",
        "description": "50% to 75% financial subsidy for automatic reeling machines, silkworm rearing houses, solar lighting, and modern handlooms/powerlooms for silk farmers and sericulture micro-enterprises.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("1500000"),
        "min_benefit_inr": Decimal("50000"),
        "subsidy_percentage": Decimal("75.0"),
        "benefit_description": "50% to 75% subsidy on rearing houses, automatic reeling units, and mulberry nurseries",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://csb.gov.in",
        "helpline_number": "080-26282699",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["agriculture", "manufacturing", "handicraft"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "documents_required": [
            {"name": "Sericulture Farmer / Reelers Registration", "mandatory": True, "format": "pdf"},
            {"name": "Land Records for mulberry plantation / shed", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply through District Sericulture Officer or CSB regional office", "channel": "offline"},
            {"step": 2, "description": "Joint technical inspection and subsidy sanction", "channel": "offline"},
            {"step": 3, "description": "Subsidy credited directly to bank account upon machine installation", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["agriculture", "manufacturing", "handicraft"], "is_mandatory": True, "description": "Sericulture and silk production"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("75.0"), "amount_max": Decimal("1500000"), "disbursement_mode": "direct_benefit_transfer", "description": "50%-75% subsidy on sericulture machinery"}
        ]
    },
    {
        "name": "Coir Vikas Yojana - Science & Technology Upgradation",
        "ministry": "Coir Board, Ministry of MSME",
        "description": "Up to 25% capital subsidy on modern machinery, computerized design looms, and skill upgradation training for micro-enterprises in coir production and eco-friendly geo-textiles.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("2500000"),
        "min_benefit_inr": Decimal("100000"),
        "subsidy_percentage": Decimal("25.0"),
        "benefit_description": "25% capital subsidy (up to ₹25 lakh) for establishing modern coir processing units",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://coirboard.gov.in",
        "helpline_number": "0484-2351980",
        "is_national": True,
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["manufacturing", "handicraft"],
        "target_business_stages": ["pre_revenue", "revenue"],
        "requires_udyam": True,
        "documents_required": [
            {"name": "UDYAM Registration Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Detailed Project Report for coir unit", "mandatory": True, "format": "pdf"},
            {"name": "Bank Term Loan Sanction Letter", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Submit application to Coir Board regional office with bank loan sanction", "channel": "both"},
            {"step": 2, "description": "Technical appraisal by Coir Board engineering team", "channel": "offline"},
            {"step": 3, "description": "Release of 25% capital subsidy into Term Loan account", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "target_business_types", "operator": "in", "rule_value": ["manufacturing", "handicraft"], "is_mandatory": True, "description": "Coir and natural fiber production"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("25.0"), "amount_max": Decimal("2500000"), "disbursement_mode": "bank_linked_subsidy", "description": "25% capital subsidy up to ₹25 Lakh for coir units"}
        ]
    },

    # ==================== 10. PROMINENT STATE GOVERNMENT SCHEMES ====================
    {
        "name": "Mukhyamantri Udyami Yojana (Bihar)",
        "ministry": "Department of Industries, Government of Bihar",
        "description": "Financial support of ₹10 lakh (₹5 lakh non-refundable grant + ₹5 lakh interest-free loan) for SC, ST, EBC, Women, and Youth entrepreneurs in Bihar to establish new manufacturing and service units.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("1000000"),
        "min_benefit_inr": Decimal("500000"),
        "subsidy_percentage": Decimal("50.0"),
        "interest_rate": Decimal("0.00"),
        "benefit_description": "₹5 lakh government grant + ₹5 lakh interest-free loan (repayable in 84 monthly installments)",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://udyami.bihar.gov.in",
        "helpline_number": "1800-345-6214",
        "is_national": False,
        "applicable_states": ["Bihar"],
        "target_genders": ["all"],
        "target_social_categories": ["sc", "st", "ebc", "women", "all"],
        "target_business_types": ["manufacturing", "service"],
        "target_business_stages": ["idea", "pre_revenue"],
        "min_age": 18,
        "max_age": 50,
        "documents_required": [
            {"name": "Permanent Resident Certificate of Bihar (Domicile)", "mandatory": True, "format": "pdf"},
            {"name": "Caste Certificate (for SC/ST/EBC categories)", "mandatory": False, "format": "pdf"},
            {"name": "Intermediate (10+2) or ITI / Diploma Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Current Bank Account Proof in firm name", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply online on udyami.bihar.gov.in portal during annual intake window", "channel": "online"},
            {"step": 2, "description": "Computerized lottery selection followed by 2-week mandatory entrepreneurship training", "channel": "online"},
            {"step": 3, "description": "Disbursement of ₹10 lakh in 3 tranches directly into business bank account", "channel": "online"}
        ],
        "rules": [
            {"field_name": "applicable_states", "operator": "in", "rule_value": ["Bihar"], "is_mandatory": True, "description": "Bihar residents only"},
            {"field_name": "min_age", "operator": ">=", "rule_value": 18, "is_mandatory": True, "description": "Age 18 to 50"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "amount_max": Decimal("500000"), "disbursement_mode": "direct_benefit_transfer", "description": "₹5 Lakh direct grant"},
            {"benefit_type": "loan", "amount_max": Decimal("500000"), "interest_rate": Decimal("0.00"), "disbursement_mode": "interest_free_loan", "description": "₹5 Lakh interest-free loan (84 EMIs)"}
        ]
    },
    {
        "name": "Mukhyamantri Yuva Swarozgar Yojana (Uttar Pradesh)",
        "ministry": "Directorate of Industries, Government of Uttar Pradesh",
        "description": "25% margin money subsidy (up to ₹6.25 lakh for industry projects up to ₹25 lakh, and up to ₹2.5 lakh for service sector up to ₹10 lakh) for educated unemployed youth in UP.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("625000"),
        "min_benefit_inr": Decimal("50000"),
        "subsidy_percentage": Decimal("25.0"),
        "benefit_description": "25% margin money subsidy (up to ₹6.25 lakh) converted to grant after 2 years successful operation",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://diupmsme.upsdc.gov.in",
        "helpline_number": "1800-180-0888",
        "is_national": False,
        "applicable_states": ["Uttar Pradesh"],
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["manufacturing", "service"],
        "target_business_stages": ["idea", "pre_revenue"],
        "min_age": 18,
        "max_age": 40,
        "documents_required": [
            {"name": "UP Domicile Certificate", "mandatory": True, "format": "pdf"},
            {"name": "High School (10th pass) marksheet", "mandatory": True, "format": "pdf"},
            {"name": "Detailed Project Report (DPR)", "mandatory": True, "format": "pdf"},
            {"name": "Notarized affidavit of no prior government loan default", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply on diupmsme.upsdc.gov.in selecting target bank branch", "channel": "online"},
            {"step": 2, "description": "District Level Task Force interview and bank forwarding", "channel": "both"},
            {"step": 3, "description": "Loan sanction with 25% margin money subsidy deposited in bank", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "applicable_states", "operator": "in", "rule_value": ["Uttar Pradesh"], "is_mandatory": True, "description": "Uttar Pradesh domicile"},
            {"field_name": "min_age", "operator": ">=", "rule_value": 18, "is_mandatory": True, "description": "Age 18 to 40"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("25.0"), "amount_max": Decimal("625000"), "disbursement_mode": "bank_linked_subsidy", "description": "25% margin money subsidy up to ₹6.25 Lakh"}
        ]
    },
    {
        "name": "Chief Minister's Employment Generation Programme - CMEGP (Maharashtra)",
        "ministry": "Directorate of Industries, Government of Maharashtra",
        "description": "15% to 35% capital subsidy (up to ₹12.5 lakh for SC/ST/Women/Rural) on project costs up to ₹50 lakh for manufacturing and ₹20 lakh for service units for micro-enterprises in Maharashtra.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("1250000"),
        "min_benefit_inr": Decimal("50000"),
        "subsidy_percentage": Decimal("35.0"),
        "benefit_description": "15% to 35% capital subsidy on manufacturing and service projects up to ₹50 lakh",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://cmegp.maharashtra.gov.in",
        "helpline_number": "022-22026217",
        "is_national": False,
        "applicable_states": ["Maharashtra"],
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["manufacturing", "service"],
        "target_business_stages": ["idea", "pre_revenue"],
        "min_age": 18,
        "max_age": 45,
        "documents_required": [
            {"name": "Maharashtra Domicile Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Detailed Project Report (DPR)", "mandatory": True, "format": "pdf"},
            {"name": "Special Category Certificate (for 35% subsidy rate)", "mandatory": False, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Register on cmegp.maharashtra.gov.in portal", "channel": "online"},
            {"step": 2, "description": "District Task Force Committee reviews and forwards to bank", "channel": "online"},
            {"step": 3, "description": "Bank loan sanction with capital subsidy deposit", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "applicable_states", "operator": "in", "rule_value": ["Maharashtra"], "is_mandatory": True, "description": "Maharashtra resident"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("35.0"), "amount_max": Decimal("1250000"), "disbursement_mode": "bank_linked_subsidy", "description": "Up to 35% capital subsidy (max ₹12.5 Lakh)"}
        ]
    },
    {
        "name": "New Entrepreneur-cum-Enterprise Development Scheme - NEEDS (Tamil Nadu)",
        "ministry": "MSME Department, Government of Tamil Nadu",
        "description": "25% capital subsidy up to ₹75 lakh with 3% interest subvention for first-generation educated youth entrepreneurs setting up manufacturing or service enterprises in Tamil Nadu.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("7500000"),
        "min_benefit_inr": Decimal("500000"),
        "subsidy_percentage": Decimal("25.0"),
        "benefit_description": "25% capital subsidy up to ₹75 lakh + 3% interest rebate for first-generation entrepreneurs",
        "collateral_required": False,
        "application_mode": "online",
        "official_url": "https://msmeonline.tn.gov.in",
        "helpline_number": "044-22501550",
        "is_national": False,
        "applicable_states": ["Tamil Nadu"],
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["manufacturing", "service"],
        "target_business_stages": ["idea", "pre_revenue"],
        "min_age": 21,
        "max_age": 45,
        "documents_required": [
            {"name": "Tamil Nadu Native / Domicile Certificate", "mandatory": True, "format": "pdf"},
            {"name": "Degree / Diploma Certificate (First Generation Entrepreneur)", "mandatory": True, "format": "pdf"},
            {"name": "Bank Term Loan Appraisal Report", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply online at msmeonline.tn.gov.in", "channel": "online"},
            {"step": 2, "description": "District Industries Centre (DIC) interviews and recommends to TIIC / Bank", "channel": "both"},
            {"step": 3, "description": "Entrepreneurship Development Institute (EDII) training & subsidy release", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "applicable_states", "operator": "in", "rule_value": ["Tamil Nadu"], "is_mandatory": True, "description": "Tamil Nadu resident"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("25.0"), "amount_max": Decimal("7500000"), "disbursement_mode": "bank_linked_subsidy", "description": "25% subsidy up to ₹75 Lakh with 3% interest rebate"}
        ]
    },
    {
        "name": "Karnataka Rajiv Gandhi Self-Employment Scheme",
        "ministry": "Department of Industries & Commerce, Government of Karnataka",
        "description": "Up to 25% seed capital subsidy (maximum ₹2.5 lakh) and interest subvention for rural youth, women, and backward class entrepreneurs setting up micro enterprises in Karnataka.",
        "scheme_type": "subsidy",
        "max_benefit_inr": Decimal("250000"),
        "min_benefit_inr": Decimal("25000"),
        "subsidy_percentage": Decimal("25.0"),
        "benefit_description": "25% seed capital margin money subsidy up to ₹2.5 lakh for rural youth in Karnataka",
        "collateral_required": False,
        "application_mode": "both",
        "official_url": "https://karnataka.gov.in",
        "helpline_number": "080-22252443",
        "is_national": False,
        "applicable_states": ["Karnataka"],
        "target_genders": ["all"],
        "target_social_categories": ["all"],
        "target_business_types": ["manufacturing", "service", "retail", "food_processing"],
        "target_business_stages": ["idea", "pre_revenue"],
        "min_age": 18,
        "max_age": 45,
        "documents_required": [
            {"name": "Karnataka Domicile Proof", "mandatory": True, "format": "pdf"},
            {"name": "Aadhaar Card", "mandatory": True, "format": "pdf"},
            {"name": "Project Proposal for micro enterprise", "mandatory": True, "format": "pdf"}
        ],
        "application_steps": [
            {"step": 1, "description": "Apply through District Industries Centre (DIC) Karnataka", "channel": "offline"},
            {"step": 2, "description": "Joint appraisal by DIC and Lead District Bank", "channel": "offline"},
            {"step": 3, "description": "25% subsidy credited directly to loan account", "channel": "offline"}
        ],
        "rules": [
            {"field_name": "applicable_states", "operator": "in", "rule_value": ["Karnataka"], "is_mandatory": True, "description": "Karnataka domicile"}
        ],
        "benefits": [
            {"benefit_type": "subsidy", "percentage": Decimal("25.0"), "amount_max": Decimal("250000"), "disbursement_mode": "bank_linked_subsidy", "description": "25% seed margin subsidy up to ₹2.5 Lakh"}
        ]
    }
]
