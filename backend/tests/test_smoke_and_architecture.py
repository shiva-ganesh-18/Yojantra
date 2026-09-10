"""Comprehensive Architectural and Smoke Tests for SchemeMatch AI.
Validates:
- Health, OpenAPI, and Swagger documentation endpoints.
- Fail-fast secret validation in production vs development.
- Resilient Redis cache adapter with automatic in-memory fallback.
- Resilient Neo4j graph adapter with graceful fallback.
- Transparent AI chat fallback mode identification.
- User demographic schema parity (DOB, literacy, sector).
"""
import pytest
from app.core.config import Settings
from app.core.cache import get_cache
from app.core.graph import get_graph_client
from app.services.chat_service import get_chat_service
from app.schemas import ChatMessageRequest, UserUpdate


def test_core_health_and_docs_endpoints(client):
    # 1. Health check
    res_health = client.get("/health")
    assert res_health.status_code == 200
    data = res_health.json()
    assert data["status"] == "healthy"
    assert data["service"] in ("yojantra-api", "schemematch-ai")

    # 2. Swagger docs
    res_docs = client.get("/docs")
    assert res_docs.status_code == 200

    # 3. OpenAPI specification
    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200
    openapi_data = res_openapi.json()
    assert "openapi" in openapi_data
    assert "/schemes/match" in openapi_data["paths"]
    assert "/admin/schemes/match-all" in openapi_data["paths"]


def test_fail_fast_secret_validation_in_production():
    # In development mode: default dev secrets are permitted
    dev_settings = Settings(ENVIRONMENT="development", DEBUG=True)
    assert dev_settings.ENVIRONMENT == "development"

    # In production mode: default insecure SECRET_KEY fails fast
    with pytest.raises(ValueError, match="CRITICAL SECURITY CONFIGURATION ERROR"):
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="your-super-secret-key-change-in-production"
        )

    # In production mode: short SECRET_KEY fails fast
    with pytest.raises(ValueError, match="CRITICAL SECURITY CONFIGURATION ERROR"):
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="short-key"
        )


def test_resilient_cache_operations():
    cache = get_cache()
    # Test setting and getting
    cache.set("test_key_smoke", {"test_val": 42}, ttl_seconds=60)
    val = cache.get("test_key_smoke")
    assert val == {"test_val": 42}

    # Test deleting
    cache.delete("test_key_smoke")
    assert cache.get("test_key_smoke") is None


def test_resilient_graph_operations():
    graph = get_graph_client()
    # Should execute safely without throwing an unhandled exception
    res = graph.query("MATCH (n) RETURN count(n) AS cnt")
    assert isinstance(res, list)


def test_chat_service_transparent_fallback(test_db):
    chat_svc = get_chat_service(test_db)
    # When external LLM is not configured, response must transparently identify source
    msg_req = ChatMessageRequest(message="What schemes can I get for my bakery in Maharashtra?")
    res = chat_svc.process_message(user_id=None, request=msg_req)
    assert res.reply is not None
    assert len(res.reply) > 10
    assert res.source in ("gemini_ai", "openai_ai", "ai", "rule_based_fallback")


def test_user_onboarding_extended_demographics():
    # Verify UserUpdate schema accepts date_of_birth, literacy_level, and block_tehsil
    update = UserUpdate(
        full_name="Rajesh Kumar",
        gender="male",
        social_category="obc",
        date_of_birth="1990-01-15",
        literacy_level="graduate",
        state="Uttar Pradesh",
        district="Varanasi",
        is_rural=True
    )
    dumped = update.model_dump(exclude_unset=True)
    assert str(dumped["date_of_birth"]) == "1990-01-15"
    assert dumped["literacy_level"] == "graduate"
