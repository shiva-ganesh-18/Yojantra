"""Locales and Multilingual router for Yojantra."""

from fastapi import APIRouter, Header, Query, HTTPException
from typing import Optional, List, Dict, Any

from app.services.localization_service import (
    LocalizationService,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    SYSTEM_MESSAGES
)

router = APIRouter(prefix="/locales", tags=["Locales & Multilingual"])


@router.get("", summary="List all supported Indian scheduled languages")
def list_supported_locales(
    accept_language: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """Returns the list of 12 supported Scheduled Indian languages + English,
    with script metadata and detected language preference.
    """
    detected_lang = LocalizationService.resolve_language(accept_language=accept_language)
    return {
        "default_language": DEFAULT_LANGUAGE,
        "detected_language": detected_lang,
        "total_languages": len(SUPPORTED_LANGUAGES),
        "supported_languages": SUPPORTED_LANGUAGES
    }


@router.get("/{lang}", summary="Get localized system dictionary and messages")
def get_locale_dictionary(
    lang: str,
    accept_language: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """Returns system message templates, error mappings, and metadata for a language."""
    resolved = LocalizationService.resolve_language(query_param=lang, accept_language=accept_language)
    messages = SYSTEM_MESSAGES.get(resolved) or SYSTEM_MESSAGES.get("en", {})
    
    # Locate metadata
    meta = next((item for item in SUPPORTED_LANGUAGES if item["code"] == resolved), None)

    return {
        "language_code": resolved,
        "language_meta": meta,
        "messages": messages
    }
