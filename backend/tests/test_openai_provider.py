"""OpenAI provider integration tests (mocked client — no network, no real secrets).

Covers: provider configuration loading, missing-key fallback, OpenAI
failure fallback, RAG grounding of OpenAI input, and API-key non-exposure.
"""
import json
import uuid

import pytest

from app.core.config import Settings, get_settings
from app.models import User, Business, Scheme
from app.schemas import ChatMessageRequest
from app.services.chat_service import ChatService

DUMMY_KEY = "sk-test-dummy-key-not-a-secret"


@pytest.fixture
def ai_settings():
    """The cached global settings object (monkeypatched per-test, auto-reverted)."""
    return get_settings()


@pytest.fixture
def openai_env(monkeypatch, ai_settings):
    """Force deterministic provider selection: OpenAI only, dummy key, no Gemini."""
    monkeypatch.setattr(ai_settings, "AI_PROVIDER", "openai")
    monkeypatch.setattr(ai_settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(ai_settings, "OPENAI_API_KEY", DUMMY_KEY)
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", DUMMY_KEY)
    monkeypatch.setenv("AI_PROVIDER", "openai")
    return ai_settings


@pytest.fixture
def no_keys_env(monkeypatch, ai_settings):
    """Simulate missing API keys for every provider."""
    monkeypatch.setattr(ai_settings, "AI_PROVIDER", "openai")
    monkeypatch.setattr(ai_settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(ai_settings, "OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    return ai_settings


@pytest.fixture
def seeded_registry(test_db):
    user = User(
        id=uuid.uuid4(), phone="+919876500101", full_name="Test Entrepreneur",
        state="Karnataka", district="Bengaluru Rural", gender="female",
        social_category="OBC", is_rural=True, is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    business = Business(
        id=uuid.uuid4(), user_id=user.id, business_name="Test Foods",
        sector="Food Processing", annual_turnover_inr=800000,
        funding_needed_inr=300000, num_employees=3,
    )
    test_db.add(business)
    test_db.commit()
    scheme = Scheme(
        id=uuid.uuid4(),
        name="Prime Minister Employment Generation Programme (PMEGP)",
        ministry="Ministry of Micro, Small and Medium Enterprises",
        description="PMEGP credit-linked subsidy for micro-enterprises.",
        scheme_type="Subsidy", max_benefit_inr=5000000,
        subsidy_percentage=35.0, interest_rate=8.5, collateral_required=False,
        target_social_categories=["All"], target_genders=["All"],
        applicable_states=["All"], official_url="https://www.kviconline.gov.in/pmegpeportal",
        helpline_number="1800-180-1111", status="active",
    )
    test_db.add(scheme)
    test_db.commit()
    return user, business, scheme


def test_openai_model_config_defaults_and_override():
    """OPENAI_MODEL has a sensible default and accepts explicit configuration."""
    assert Settings().OPENAI_MODEL == "gpt-4o-mini"
    assert Settings(OPENAI_MODEL="gpt-4o").OPENAI_MODEL == "gpt-4o"


def test_openai_provider_loads_with_configured_model(test_db, openai_env):
    """OpenAI provider initializes from env key + model without network calls."""
    openai_env.OPENAI_MODEL = "gpt-4o-mini"
    service = ChatService(test_db)
    assert service.provider_name == "openai"
    assert service.llm is not None
    assert service.llm.model_name == "gpt-4o-mini"
    status = service.get_provider_status()
    assert status["provider"] == "openai"
    assert status["is_ai_live"] is True
    assert status["model_name"] == "gpt-4o-mini"


def test_openai_model_override_respected(test_db, openai_env, monkeypatch):
    """A configured OPENAI_MODEL is passed to the client and status."""
    monkeypatch.setattr(openai_env, "OPENAI_MODEL", "gpt-4o")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    service = ChatService(test_db)
    assert service.provider_name == "openai"
    assert service.llm.model_name == "gpt-4o"
    assert service.get_provider_status()["model_name"] == "gpt-4o"


def test_missing_openai_key_falls_back(test_db, no_keys_env, seeded_registry):
    """Missing API key for all providers → deterministic grounded fallback."""
    user, _, _ = seeded_registry
    service = ChatService(test_db)
    assert service.provider_name == "rule_based_fallback"
    res = service.process_message(
        user.id, ChatMessageRequest(message="Which scheme is best for my food business?", language="en", channel="text")
    )
    assert res.source == "rule_based_fallback"
    assert res.reply
    assert "PMEGP" in res.reply or "Prime Minister Employment" in res.reply
    assert len(res.cited_schemes) >= 1


def test_openai_failure_falls_back(test_db, openai_env, seeded_registry):
    """OpenAI runtime failure → existing Gemini/deterministic fallback, still grounded."""
    user, _, _ = seeded_registry
    service = ChatService(test_db)
    assert service.provider_name == "openai"

    class FailingLLM:
        def invoke(self, messages):
            raise RuntimeError("simulated OpenAI outage")

    service.llm = FailingLLM()
    res = service.process_message(
        user.id, ChatMessageRequest(message="What is the maximum loan for PMEGP?", language="en", channel="text")
    )
    assert res.source == "rule_based_fallback"
    assert "PMEGP" in res.reply or "Prime Minister Employment" in res.reply
    assert "5,000,000" in res.reply or "8.5%" in res.reply


def test_openai_input_grounded_in_verified_rag(test_db, openai_env, seeded_registry):
    """Only verified retrieved scheme/RAG context is sent to OpenAI (no invented data)."""
    user, _, _ = seeded_registry
    service = ChatService(test_db)
    captured = {}

    class StubLLM:
        def invoke(self, messages):
            captured["messages"] = [
                {"role": m.type if hasattr(m, "type") else "unknown", "content": m.content} for m in messages
            ]
            class Resp:
                content = (
                    "Based on verified records, Prime Minister Employment Generation "
                    "Programme (PMEGP) offers support. See official portal for details."
                )
            return Resp()

    service.llm = StubLLM()
    res = service.process_message(
        user.id, ChatMessageRequest(message="Tell me about PMEGP support", language="en", channel="text")
    )
    assert res.source == "openai_ai"
    assert "PMEGP" in res.reply
    system_text = next(m["content"] for m in captured["messages"] if "system" in m["role"])
    assert "Prime Minister Employment Generation Programme (PMEGP)" in system_text
    assert "Mars Reactor Yogana" not in system_text
    assert "Statutory Notice" in system_text  # anti-hallucination instructions present
    assert len(res.cited_schemes) >= 1
    assert res.disclaimer is not None


def test_api_key_never_exposed(test_db, openai_env, seeded_registry):
    """API key appears in no model input, response payload, or status payload."""
    user, _, _ = seeded_registry
    service = ChatService(test_db)
    sent = {}

    class CapturingLLM:
        def invoke(self, messages):
            sent["text"] = "\n".join(m.content for m in messages)
            class Resp:
                content = "Namaste! Ask me about PMEGP, MUDRA, documents, or partners."
            return Resp()

    service.llm = CapturingLLM()
    res = service.process_message(
        user.id, ChatMessageRequest(message="Hello", language="en", channel="text")
    )
    assert DUMMY_KEY not in sent["text"]  # key never sent to the model, only RAG context
    blob = json.dumps(res.model_dump(), default=str)
    assert DUMMY_KEY not in blob
    status_blob = json.dumps(service.get_provider_status(), default=str)
    assert DUMMY_KEY not in status_blob
    assert "OPENAI_API_KEY" not in status_blob
