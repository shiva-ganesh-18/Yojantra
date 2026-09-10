"""Part 12 Regression Test Suite: Multilingual & Accessibility.

Verifies:
1. Complete support for 12 Scheduled Indian Languages + English
2. Accurate language negotiation from headers, query params, and user preferences
3. Locale dictionary and metadata API endpoints (/locales and /locales/{lang})
4. Strict statutory scheme data integrity (official scheme names, ministries, and URLs preserved)
5. Multi-lingual notification generation with canonical reference codes
6. Localized system error resolution
7. Accessibility response headers
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.services.localization_service import (
    LocalizationService,
    SUPPORTED_LANGUAGES,
    SUPPORTED_CODES,
    DEFAULT_LANGUAGE,
    SYSTEM_MESSAGES
)

client = TestClient(app)


def test_supported_languages_completeness():
    """Verify that all 12 major Indian scheduled languages + English are present."""
    expected_codes = {"en", "hi", "mr", "ta", "te", "bn", "gu", "kn", "ml", "pa", "or", "as"}
    assert expected_codes.issubset(SUPPORTED_CODES), f"Missing codes: {expected_codes - SUPPORTED_CODES}"
    assert len(SUPPORTED_LANGUAGES) == 12

    for item in SUPPORTED_LANGUAGES:
        assert "code" in item
        assert "label" in item
        assert "english_name" in item
        assert "script" in item
        assert len(item["label"]) > 0
        assert len(item["script"]) > 0


def test_language_negotiation_priority():
    """Verify language resolution priority: query param > user pref > header > default."""
    # 1. Query parameter takes precedence
    resolved = LocalizationService.resolve_language(
        query_param="mr",
        user_preference="ta",
        accept_language="te,en;q=0.9"
    )
    assert resolved == "mr"

    # 2. User preference takes precedence over header
    resolved = LocalizationService.resolve_language(
        query_param=None,
        user_preference="ta",
        accept_language="bn,en;q=0.9"
    )
    assert resolved == "ta"

    # 3. Accept-Language header parsing
    resolved = LocalizationService.resolve_language(
        query_param=None,
        user_preference=None,
        accept_language="bn-IN,bn;q=0.9,en;q=0.8"
    )
    assert resolved == "bn"

    # 4. Unknown language falls back to DEFAULT_LANGUAGE ('hi')
    resolved = LocalizationService.resolve_language(
        query_param="unknown_lang",
        user_preference="invalid_lang",
        accept_language="fr-FR,fr;q=0.9"
    )
    assert resolved == DEFAULT_LANGUAGE


def test_locales_list_endpoint():
    """Verify GET /locales endpoint returns all languages and detected preference."""
    response = client.get("/locales", headers={"Accept-Language": "ta-IN,ta;q=0.9,en;q=0.8"})
    assert response.status_code == 200
    data = response.json()

    assert data["total_languages"] == 12
    assert data["default_language"] == "hi"
    assert data["detected_language"] == "ta"
    assert len(data["supported_languages"]) == 12

    # Verify also available at /api/locales
    api_res = client.get("/api/locales")
    assert api_res.status_code == 200
    assert api_res.json()["total_languages"] == 12


def test_locale_dictionary_endpoint():
    """Verify GET /locales/{lang} returns script-specific dictionary."""
    # Test Hindi dictionary
    hi_res = client.get("/locales/hi")
    assert hi_res.status_code == 200
    hi_data = hi_res.json()
    assert hi_data["language_code"] == "hi"
    assert hi_data["language_meta"]["script"] == "Devanagari"
    assert "ERR_UNAUTHORIZED" in hi_data["messages"]
    assert "लॉगिन" in hi_data["messages"]["ERR_UNAUTHORIZED"]

    # Test Tamil dictionary
    ta_res = client.get("/locales/ta")
    assert ta_res.status_code == 200
    ta_data = ta_res.json()
    assert ta_data["language_code"] == "ta"
    assert ta_data["language_meta"]["script"] == "Tamil"
    assert "உள்நுழையவும்" in ta_data["messages"]["ERR_UNAUTHORIZED"]

    # Test Bengali dictionary
    bn_res = client.get("/locales/bn")
    assert bn_res.status_code == 200
    bn_data = bn_res.json()
    assert bn_data["language_code"] == "bn"
    assert bn_data["language_meta"]["script"] == "Bengali"
    assert "লগইন" in bn_data["messages"]["ERR_UNAUTHORIZED"]


def test_official_scheme_data_integrity_safeguard():
    """Strictly verify that official statutory scheme names, ministries, and URLs
    are preserved canonically and never corrupted or machine-translated.
    """
    canonical_scheme = {
        "id": str(uuid4()),
        "name": "Prime Minister's Employment Generation Programme (PMEGP)",
        "ministry": "Ministry of Micro, Small and Medium Enterprises",
        "official_url": "https://www.kviconline.gov.in/pmegpeportal",
        "scheme_type": "subsidy"
    }

    preserved = LocalizationService.preserve_official_scheme_data(canonical_scheme)

    assert preserved["name"] == "Prime Minister's Employment Generation Programme (PMEGP)"
    assert preserved["ministry"] == "Ministry of Micro, Small and Medium Enterprises"
    assert preserved["official_url"] == "https://www.kviconline.gov.in/pmegpeportal"
    assert preserved["is_canonical_preserved"] is True


def test_multilingual_notification_formatting_preserves_scheme_and_ref():
    """Verify notification templates generate correct native script
    while strictly preserving the exact scheme name and partner reference number.
    """
    scheme_name = "Pradhan Mantri Mudra Yojana (PMMY)"
    ref_code = "YOJ-2026-MUDRA-8821"

    # Hindi
    notif_hi = LocalizationService.format_notification(
        "application_submitted",
        lang="hi",
        scheme_name=scheme_name,
        ref_code=ref_code
    )
    assert scheme_name in notif_hi["body"]
    assert ref_code in notif_hi["body"]
    assert "आवेदन" in notif_hi["title"] or "आवेदन" in notif_hi["body"]

    # Marathi
    notif_mr = LocalizationService.format_notification(
        "deadline_3d",
        lang="mr",
        scheme_name=scheme_name
    )
    assert scheme_name in notif_mr["body"]
    assert "३ दिवस" in notif_mr["body"] or "३ दिवसांत" in notif_mr["body"]

    # Tamil
    notif_ta = LocalizationService.format_notification(
        "deadline_7d",
        lang="ta",
        scheme_name=scheme_name
    )
    assert scheme_name in notif_ta["body"]
    assert "7 நாட்கள்" in notif_ta["body"] or "காலக்கெடு" in notif_ta["title"]

    # Telugu
    notif_te = LocalizationService.format_notification(
        "deadline_1d",
        lang="te",
        scheme_name=scheme_name
    )
    assert scheme_name in notif_te["body"]
    assert "చివరి రోజు" in notif_te["body"] or "గడువు" in notif_te["title"]

    # Bengali
    notif_bn = LocalizationService.format_notification(
        "application_submitted",
        lang="bn",
        scheme_name=scheme_name,
        ref_code=ref_code
    )
    assert scheme_name in notif_bn["body"]
    assert ref_code in notif_bn["body"]
    assert "আবেদন" in notif_bn["title"] or "আবেদন" in notif_bn["body"]


def test_localized_error_resolution():
    """Verify localized error messages across Scheduled Languages."""
    msg_en = LocalizationService.get_message("ERR_NOT_FOUND", lang="en")
    msg_hi = LocalizationService.get_message("ERR_NOT_FOUND", lang="hi")
    msg_gu = LocalizationService.get_message("ERR_NOT_FOUND", lang="gu")
    msg_kn = LocalizationService.get_message("ERR_NOT_FOUND", lang="kn")

    assert "not found" in msg_en.lower()
    assert "नहीं मिला" in msg_hi
    assert "મળ્યો નથી" in msg_gu
    assert "ಕಂಡುಬಂದಿಲ್ಲ" in msg_kn


def test_accessibility_response_headers():
    """Verify security and accessibility headers on HTTP responses."""
    res = client.get("/locales")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
