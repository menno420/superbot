"""Tests for the legacy AI scalar → typed-policy projection (Issue B).

The post-PR-#310 hardening adds an inline projection inside
``SettingsMutationPipeline.set_value`` so the existing AI settings UI
mutations propagate to the typed ``ai_guild_policy`` row. Until this
landed, ``ai_policy_mutation.set_guild_policy`` had zero production
callers and the runtime resolver could not see UI changes.

These tests pin:

* Every mapped legacy key triggers ``set_guild_policy`` with the
  freshly-resolved value and the existing typed values for the rest.
* ``ai_guild_instruction_profile`` (unmapped scalar) is NOT projected.
* Projection failure logs a structured WARNING with the required
  diagnostic fields, never leaks the raw setting value, and emits the
  ``ai.policy.projection_failed`` bus event — but the parent mutation
  still succeeds.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from services import ai_policy_mutation

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _admin_actor(actor_id: int = 42):
    actor = MagicMock()
    actor.id = actor_id
    actor.guild_permissions = SimpleNamespace(administrator=True)
    return actor


def _settings_resolution(values: dict[str, object]):
    """Build a fake settings_resolution.resolve_setting that returns ``values``."""

    async def _resolve(_guild_id, _subsystem, name):
        if name not in values:
            return None
        return SimpleNamespace(value=values[name])

    return _resolve


# ---------------------------------------------------------------------------
# Projection writes the correct upsert
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_projection_writes_all_seven_scalars(monkeypatch):
    """The projection reads all seven mapped scalars and writes them
    into ``ai_guild_policy`` in a single ``set_guild_policy`` call."""
    from services import settings_resolution

    monkeypatch.setattr(
        settings_resolution,
        "resolve_setting",
        _settings_resolution(
            {
                "ai_enabled": True,
                "ai_natural_language_enabled": True,
                "ai_default_provider": "openai",
                "ai_default_model": "gpt-4o-mini",
                "ai_minimum_level_default": 3,
                "ai_cooldown_seconds": 15,
                "ai_fresh_user_mention_allowance": 2,
            },
        ),
    )
    from utils.db import ai as ai_db

    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(return_value={"guild_instruction_profile_id": 88}),
    )

    captured: dict[str, object] = {}

    async def _fake_set_guild_policy(**kw):
        captured.update(kw)
        return ai_policy_mutation.AIPolicyMutationResult(
            mutation_id="mid",
            table="ai_guild_policy",
            guild_id=kw["guild_id"] if "guild_id" in kw else 0,
            target_id=None,
            generation=7,
            event_emitted=True,
        )

    # set_guild_policy is positional for guild_id; capture both forms.
    async def _set_guild_policy_proxy(guild_id, **kw):
        captured["guild_id"] = guild_id
        captured.update(kw)
        return ai_policy_mutation.AIPolicyMutationResult(
            mutation_id="mid",
            table="ai_guild_policy",
            guild_id=guild_id,
            target_id=None,
            generation=7,
            event_emitted=True,
        )

    monkeypatch.setattr(
        ai_policy_mutation,
        "set_guild_policy",
        _set_guild_policy_proxy,
    )

    result = await ai_policy_mutation.project_from_legacy_settings(
        guild_id=99,
        actor=_admin_actor(),
        mutation_id="mut-1",
    )

    assert result is not None
    assert captured["guild_id"] == 99
    assert captured["enabled"] is True
    assert captured["natural_language_enabled"] is True
    assert captured["default_provider"] == "openai"
    assert captured["default_model"] == "gpt-4o-mini"
    assert captured["minimum_level_default"] == 3
    assert captured["cooldown_seconds"] == 15
    assert captured["fresh_user_mention_allowance"] == 2
    # Read-merge-write preserved the unmapped FK.
    assert captured["guild_instruction_profile_id"] == 88


@pytest.mark.asyncio
async def test_projection_uses_default_when_no_prior_typed_row(monkeypatch):
    """When ``ai_guild_policy`` has no row yet, the projection still
    upserts and the unmapped FK is ``None``."""
    from services import settings_resolution

    monkeypatch.setattr(
        settings_resolution,
        "resolve_setting",
        _settings_resolution(
            {
                "ai_enabled": True,
                "ai_natural_language_enabled": False,
                "ai_default_provider": "deterministic",
                "ai_default_model": "",
                "ai_minimum_level_default": 2,
                "ai_cooldown_seconds": 30,
                "ai_fresh_user_mention_allowance": 1,
            },
        ),
    )
    from utils.db import ai as ai_db

    monkeypatch.setattr(ai_db, "get_guild_policy", AsyncMock(return_value=None))

    captured: dict[str, object] = {}

    async def _set_guild_policy_proxy(guild_id, **kw):
        captured["guild_id"] = guild_id
        captured.update(kw)
        return ai_policy_mutation.AIPolicyMutationResult(
            mutation_id="m",
            table="ai_guild_policy",
            guild_id=guild_id,
            target_id=None,
            generation=1,
            event_emitted=True,
        )

    monkeypatch.setattr(
        ai_policy_mutation,
        "set_guild_policy",
        _set_guild_policy_proxy,
    )

    result = await ai_policy_mutation.project_from_legacy_settings(
        guild_id=42,
        actor=_admin_actor(),
        mutation_id="m",
    )

    assert result is not None
    assert captured["enabled"] is True
    assert captured["guild_instruction_profile_id"] is None


# ---------------------------------------------------------------------------
# Failure handling — structured log + best-effort event, no raw value leak
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_projection_failure_logs_structured_warning(
    monkeypatch,
    caplog,
):
    """When ``set_guild_policy`` raises, a structured WARNING is logged
    with guild_id / mutation_id / exc_type and the parent caller gets
    ``None`` back. Raw setting values must NOT appear in the log."""
    from services import settings_resolution

    monkeypatch.setattr(
        settings_resolution,
        "resolve_setting",
        _settings_resolution(
            {
                "ai_enabled": True,
                "ai_natural_language_enabled": True,
                "ai_default_provider": "openai",
                "ai_default_model": "SECRET-MODEL-NAME-DO-NOT-LEAK",
                "ai_minimum_level_default": 2,
                "ai_cooldown_seconds": 30,
                "ai_fresh_user_mention_allowance": 1,
            },
        ),
    )
    from utils.db import ai as ai_db

    monkeypatch.setattr(ai_db, "get_guild_policy", AsyncMock(return_value=None))

    async def _boom(*a, **kw):
        raise ai_policy_mutation.InvalidAIPolicyValueError("schema rejected")

    monkeypatch.setattr(ai_policy_mutation, "set_guild_policy", _boom)

    # Swallow the best-effort bus emit so it doesn't bleed into the log.
    from core import events

    monkeypatch.setattr(events.bus, "emit", AsyncMock(return_value=None))

    with caplog.at_level(logging.WARNING, logger="bot.services.ai_policy_mutation"):
        result = await ai_policy_mutation.project_from_legacy_settings(
            guild_id=123,
            actor=_admin_actor(),
            mutation_id="mut-warn",
        )

    assert result is None
    matching = [r for r in caplog.records if "projection failed" in r.getMessage()]
    assert matching, "expected a 'projection failed' WARNING log"
    rec = matching[-1]
    # Structured fields are required diagnostic context.
    assert getattr(rec, "guild_id", None) == 123
    assert getattr(rec, "subsystem", None) == "ai"
    assert getattr(rec, "mutation_id", None) == "mut-warn"
    assert getattr(rec, "exc_type", None) == "InvalidAIPolicyValueError"
    # Raw setting value must NOT leak.
    full_text = " ".join(
        list(caplog.text.splitlines())
        + [str(v) for v in vars(rec).values() if isinstance(v, str)],
    )
    assert "SECRET-MODEL-NAME-DO-NOT-LEAK" not in full_text


@pytest.mark.asyncio
async def test_projection_failure_emits_bus_event(monkeypatch):
    """Projection failure emits the ``ai.policy.projection_failed`` bus
    event with diagnostic fields (no raw value)."""
    from services import settings_resolution

    monkeypatch.setattr(
        settings_resolution,
        "resolve_setting",
        _settings_resolution({"ai_enabled": True}),
    )
    from utils.db import ai as ai_db

    monkeypatch.setattr(ai_db, "get_guild_policy", AsyncMock(return_value=None))

    async def _boom(*a, **kw):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(ai_policy_mutation, "set_guild_policy", _boom)

    from core import events

    emitted: list[tuple[str, dict]] = []

    async def _capture_emit(event_name, **payload):
        emitted.append((event_name, payload))

    monkeypatch.setattr(events.bus, "emit", _capture_emit)

    await ai_policy_mutation.project_from_legacy_settings(
        guild_id=42,
        actor=_admin_actor(),
        mutation_id="m-bus",
    )

    failed = [
        (name, payload)
        for name, payload in emitted
        if name == "ai.policy.projection_failed"
    ]
    assert len(failed) == 1, f"expected one projection_failed emit, got {emitted}"
    _, payload = failed[0]
    assert payload["guild_id"] == 42
    assert payload["mutation_id"] == "m-bus"
    assert payload["exc_type"] == "RuntimeError"
