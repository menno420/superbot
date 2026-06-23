"""Tests for the natural-language setup wedge.

Pins ``suggest_from_description``'s routing:

* an OpenAI advisor + a non-empty description folds the description into the
  prompt (``operator_description`` + the text reach the provider call);
* an empty/whitespace description does NOT fold (plain snapshot-only suggest);
* a non-OpenAI (deterministic) advisor ignores the description entirely;
* with no injected advisor it builds the configured one (deterministic in CI).
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.guild_snapshot import GuildSnapshot
from services.setup_ai_advisor import OpenAISetupAdvisor
from services.setup_natural_language_advisor import suggest_from_description
from services.setup_plan import DeterministicAdvisor, SetupPlanDraft


def _snap() -> GuildSnapshot:
    return GuildSnapshot(guild_id=1, guild_name="Test", owner_id=99)


def _fake_openai_client(payload: dict) -> MagicMock:
    message = MagicMock()
    message.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=response)
    return client


@pytest.mark.asyncio
async def test_description_folded_into_openai_prompt():
    client = _fake_openai_client({"recommendations": []})
    advisor = OpenAISetupAdvisor(client=client, api_key="sk-test")

    draft = await suggest_from_description(
        _snap(),
        "a competitive gaming server with mod logs",
        advisor=advisor,
    )

    assert isinstance(draft, SetupPlanDraft)
    client.chat.completions.create.assert_awaited_once()
    sent = str(client.chat.completions.create.call_args)
    # The directive (carrying the field name) + the operator's words both
    # reach the provider — the prompt is genuinely description-informed.
    assert "operator_description" in sent
    assert "competitive gaming server" in sent


@pytest.mark.asyncio
async def test_blank_description_is_not_folded():
    client = _fake_openai_client({"recommendations": []})
    advisor = OpenAISetupAdvisor(client=client, api_key="sk-test")

    draft = await suggest_from_description(_snap(), "   ", advisor=advisor)

    assert isinstance(draft, SetupPlanDraft)
    client.chat.completions.create.assert_awaited_once()
    sent = str(client.chat.completions.create.call_args)
    assert "operator_description" not in sent


@pytest.mark.asyncio
async def test_deterministic_advisor_ignores_description():
    draft = await suggest_from_description(
        _snap(),
        "any description at all",
        advisor=DeterministicAdvisor(),
    )

    assert isinstance(draft, SetupPlanDraft)
    # Deterministic can't use free text — it stays snapshot-only.
    assert draft.source == "deterministic"


@pytest.mark.asyncio
async def test_defaults_to_built_advisor_in_ci(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SETUP_ADVISOR_PROVIDER", raising=False)

    draft = await suggest_from_description(_snap(), "desc")

    assert isinstance(draft, SetupPlanDraft)
    assert draft.source == "deterministic"
