"""Phase 9f / Track 5 PR 13 — AI advisor tests.

Pins:

* ``build_advisor`` returns ``DeterministicAdvisor`` by default
  (the CI/dev safe fallback).
* Unknown provider strings fall back to deterministic with a
  warn-level log.
* ``OpenAISetupAdvisor.suggest`` parses a valid OpenAI response
  through the JSON schema and emits matching
  :class:`SetupRecommendation` records.
* Invalid recommendations are dropped with a reason:
  * unknown subsystem;
  * binding name not declared;
  * kind mismatch;
  * bad confidence string;
  * non-JSON content.
* The advisor never makes a real network call in tests; CI has no
  ``OPENAI_API_KEY``.
* AST-level invariants:
  * ``setup_ai_advisor`` does not import ``utils.db``.
  * ``setup_ai_advisor`` does not reference ``guild.create_*``.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SubsystemSchema,
)
from services.guild_snapshot import GuildSnapshot
from services.setup_ai_advisor import (
    ANTHROPIC,
    DETERMINISTIC,
    OPENAI,
    OpenAISetupAdvisor,
    SetupAdvisor,
    build_advisor,
)
from services.setup_plan import (
    DeterministicAdvisor,
    SetupPlanDraft,
    SetupRecommendation,
)


def _snap() -> GuildSnapshot:
    return GuildSnapshot(
        guild_id=1,
        guild_name="Test",
        owner_id=99,
    )


@pytest.fixture
def _logging_schema():
    schemas = {
        "logging": SubsystemSchema(
            subsystem="logging",
            bindings=(
                BindingSpec(
                    name="mod_channel",
                    kind=BindingKind.CHANNEL,
                    required=True,
                    hint="",
                    capability_required="logging.mod_channel.bind",
                ),
            ),
        ),
    }
    with patch(
        "core.runtime.subsystem_schema.all_schemas",
        return_value=schemas,
    ):
        yield schemas


@pytest.fixture
def _no_openai_env(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SETUP_ADVISOR_PROVIDER", raising=False)
    yield


# ---------------------------------------------------------------------------
# build_advisor — provider resolution
# ---------------------------------------------------------------------------


def test_build_advisor_defaults_to_deterministic(_no_openai_env):
    advisor = build_advisor()
    assert isinstance(advisor, DeterministicAdvisor)


def test_build_advisor_explicit_deterministic(_no_openai_env):
    advisor = build_advisor(provider="deterministic")
    assert isinstance(advisor, DeterministicAdvisor)


def test_build_advisor_unknown_provider_falls_back(_no_openai_env, caplog):
    with caplog.at_level("WARNING", logger="bot.services.setup_ai_advisor"):
        advisor = build_advisor(provider="totally_made_up")
    assert isinstance(advisor, DeterministicAdvisor)
    assert any(
        "unknown SETUP_ADVISOR_PROVIDER" in record.getMessage()
        for record in caplog.records
    )


def test_build_advisor_openai_without_api_key_falls_back(_no_openai_env, caplog):
    with caplog.at_level("WARNING", logger="bot.services.setup_ai_advisor"):
        advisor = build_advisor(provider="openai")
    assert isinstance(advisor, DeterministicAdvisor)
    assert any(
        "OPENAI_API_KEY not set" in record.getMessage()
        for record in caplog.records
    )


def test_build_advisor_anthropic_is_reserved_and_falls_back(_no_openai_env, caplog):
    with caplog.at_level("WARNING", logger="bot.services.setup_ai_advisor"):
        advisor = build_advisor(provider="anthropic")
    assert isinstance(advisor, DeterministicAdvisor)
    assert any(
        "ANTHROPIC adapter is not implemented" in record.getMessage()
        for record in caplog.records
    )


def test_build_advisor_openai_with_key_returns_openai_adapter(_no_openai_env):
    advisor = build_advisor(provider="openai", api_key="sk-test")
    assert isinstance(advisor, OpenAISetupAdvisor)
    assert isinstance(advisor, SetupAdvisor)


def test_known_providers_set():
    from services.setup_ai_advisor import KNOWN_PROVIDERS

    assert KNOWN_PROVIDERS == frozenset({DETERMINISTIC, OPENAI, ANTHROPIC})


# ---------------------------------------------------------------------------
# OpenAISetupAdvisor — happy path
# ---------------------------------------------------------------------------


def _fake_openai_response(payload: dict) -> MagicMock:
    """Build a chat.completions response that contains ``payload`` as
    the assistant message JSON string."""
    message = MagicMock()
    message.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.mark.asyncio
async def test_openai_advisor_emits_validated_recommendation(_logging_schema):
    payload = {
        "recommendations": [
            {
                "subsystem": "logging",
                "binding_name": "mod_channel",
                "target_kind": "channel",
                "target_id": 100,
                "target_name": "mod-log",
                "confidence": "high",
                "reason": "exact name match",
            },
        ],
    }
    fake_client = MagicMock()
    fake_client.chat = MagicMock()
    fake_client.chat.completions = MagicMock()
    fake_client.chat.completions.create = AsyncMock(
        return_value=_fake_openai_response(payload),
    )

    advisor = OpenAISetupAdvisor(client=fake_client, api_key="sk-test")
    draft = await advisor.suggest(_snap())

    fake_client.chat.completions.create.assert_awaited_once()
    assert isinstance(draft, SetupPlanDraft)
    assert len(draft.recommendations) == 1
    rec = draft.recommendations[0]
    assert rec.source == "openai"
    assert rec.subsystem == "logging"
    assert rec.binding_name == "mod_channel"


@pytest.mark.asyncio
async def test_openai_advisor_drops_unknown_subsystem(_logging_schema):
    payload = {
        "recommendations": [
            {
                "subsystem": "vibes",
                "binding_name": "mod_channel",
                "target_kind": "channel",
                "target_id": 100,
                "target_name": "x",
                "confidence": "high",
                "reason": "y",
            },
        ],
    }
    fake_client = MagicMock()
    fake_client.chat = MagicMock()
    fake_client.chat.completions = MagicMock()
    fake_client.chat.completions.create = AsyncMock(
        return_value=_fake_openai_response(payload),
    )

    advisor = OpenAISetupAdvisor(client=fake_client, api_key="sk-test")
    draft = await advisor.suggest(_snap())

    assert draft.recommendations == ()
    assert any("not registered" in r for r in draft.dropped)


@pytest.mark.asyncio
async def test_openai_advisor_drops_kind_mismatch(_logging_schema):
    payload = {
        "recommendations": [
            {
                "subsystem": "logging",
                "binding_name": "mod_channel",
                "target_kind": "role",  # schema says CHANNEL
                "target_id": 100,
                "target_name": "x",
                "confidence": "high",
                "reason": "y",
            },
        ],
    }
    fake_client = MagicMock()
    fake_client.chat = MagicMock()
    fake_client.chat.completions = MagicMock()
    fake_client.chat.completions.create = AsyncMock(
        return_value=_fake_openai_response(payload),
    )

    advisor = OpenAISetupAdvisor(client=fake_client, api_key="sk-test")
    draft = await advisor.suggest(_snap())

    assert draft.recommendations == ()
    assert any("AI proposed role" in r for r in draft.dropped)


@pytest.mark.asyncio
async def test_openai_advisor_drops_bad_confidence(_logging_schema):
    payload = {
        "recommendations": [
            {
                "subsystem": "logging",
                "binding_name": "mod_channel",
                "target_kind": "channel",
                "target_id": 100,
                "target_name": "x",
                "confidence": "totally_made_up",
                "reason": "y",
            },
        ],
    }
    fake_client = MagicMock()
    fake_client.chat = MagicMock()
    fake_client.chat.completions = MagicMock()
    fake_client.chat.completions.create = AsyncMock(
        return_value=_fake_openai_response(payload),
    )

    advisor = OpenAISetupAdvisor(client=fake_client, api_key="sk-test")
    draft = await advisor.suggest(_snap())

    assert draft.recommendations == ()
    assert any("bad confidence" in r for r in draft.dropped)


@pytest.mark.asyncio
async def test_openai_advisor_drops_missing_field(_logging_schema):
    payload = {
        "recommendations": [
            {
                # missing target_id
                "subsystem": "logging",
                "binding_name": "mod_channel",
                "target_kind": "channel",
                "target_name": "x",
                "confidence": "high",
                "reason": "y",
            },
        ],
    }
    fake_client = MagicMock()
    fake_client.chat = MagicMock()
    fake_client.chat.completions = MagicMock()
    fake_client.chat.completions.create = AsyncMock(
        return_value=_fake_openai_response(payload),
    )

    advisor = OpenAISetupAdvisor(client=fake_client, api_key="sk-test")
    draft = await advisor.suggest(_snap())

    assert draft.recommendations == ()
    assert any("KeyError" in r for r in draft.dropped)


@pytest.mark.asyncio
async def test_openai_advisor_handles_invalid_json():
    message = MagicMock()
    message.content = "not json at all {{"
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]

    fake_client = MagicMock()
    fake_client.chat = MagicMock()
    fake_client.chat.completions = MagicMock()
    fake_client.chat.completions.create = AsyncMock(return_value=response)

    advisor = OpenAISetupAdvisor(client=fake_client, api_key="sk-test")
    draft = await advisor.suggest(_snap())

    assert draft.recommendations == ()
    assert any("invalid JSON" in r for r in draft.dropped)


@pytest.mark.asyncio
async def test_openai_advisor_swallows_network_failure():
    fake_client = MagicMock()
    fake_client.chat = MagicMock()
    fake_client.chat.completions = MagicMock()
    fake_client.chat.completions.create = AsyncMock(
        side_effect=RuntimeError("rate limited"),
    )

    advisor = OpenAISetupAdvisor(client=fake_client, api_key="sk-test")
    draft = await advisor.suggest(_snap())

    assert draft.recommendations == ()
    assert any("rate limited" in r for r in draft.dropped)


@pytest.mark.asyncio
async def test_openai_advisor_handles_empty_response():
    response = MagicMock()
    response.choices = []
    fake_client = MagicMock()
    fake_client.chat = MagicMock()
    fake_client.chat.completions = MagicMock()
    fake_client.chat.completions.create = AsyncMock(return_value=response)

    advisor = OpenAISetupAdvisor(client=fake_client, api_key="sk-test")
    draft = await advisor.suggest(_snap())

    assert draft.recommendations == ()
    assert any("empty response" in r for r in draft.dropped)


# ---------------------------------------------------------------------------
# Module invariants
# ---------------------------------------------------------------------------


def test_module_has_no_db_imports():
    import services.setup_ai_advisor as mod

    src = mod.__file__
    assert src is not None
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    for forbidden in ("from utils.db import", "import utils.db"):
        assert forbidden not in text, (
            f"services.setup_ai_advisor must not import {forbidden}; "
            "the AI advisor must remain read-only."
        )


def test_module_has_no_discord_create_calls():
    import services.setup_ai_advisor as mod

    src = mod.__file__
    assert src is not None
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    for forbidden in (
        "guild.create_text_channel",
        "guild.create_role",
        "guild.create_category",
        "create_text_channel(",
        "create_role(",
        "create_category(",
    ):
        assert forbidden not in text, (
            f"services.setup_ai_advisor must not call {forbidden}; "
            "the AI advisor must never create Discord resources."
        )


def test_setup_advisor_protocol_accepts_deterministic_and_openai():
    """Both implementations satisfy the Protocol."""
    assert isinstance(DeterministicAdvisor(), SetupAdvisor)
    assert isinstance(OpenAISetupAdvisor(api_key="sk-test"), SetupAdvisor)


def test_protocol_is_runtime_checkable():
    """``isinstance`` check works for arbitrary objects implementing
    ``async def suggest(snapshot) -> SetupPlanDraft``."""

    class _Custom:
        async def suggest(self, snapshot):
            return SetupPlanDraft()

    assert isinstance(_Custom(), SetupAdvisor)


def test_recommendation_source_field_marks_origin():
    """Sanity: the deterministic baseline marks ``source="deterministic"``,
    OpenAI marks ``source="openai"``. Tests above already exercise the
    OpenAI side; this one pins the deterministic default."""
    rec = SetupRecommendation(
        subsystem="logging",
        binding_name="mod_channel",
        target_kind="channel",
        target_id=1,
        target_name="mod-log",
        confidence="high",
        reason="x",
    )
    assert rec.source == "deterministic"
