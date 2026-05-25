"""PR-6 — apply_preset_to_guild + guild-scope preset routing.

Pins:

* ``apply_preset_to_guild`` calls ``ai_policy_mutation.set_guild_policy``
  exactly once with the two preset-owned fields
  (``guild_instruction_profile_id``, ``natural_language_enabled``)
  and **every other field preserved verbatim** from the current
  ``ai_guild_policy`` row.
* The same preservation invariant applies when ``apply_preset(scope="guild")``
  is used as a unified dispatcher.
* ``mention_only`` presets raise :class:`GuildScopeNotSupportedError`
  rather than silently mapping to either bool.
* ``_SUPPORTED_SCOPES`` includes ``"guild"`` (PR-6) — channel/category
  also still supported.
* ``ai_behavior_profile_service`` exports the new symbols.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from services import ai_behavior_profile_service as svc


def _admin_actor(actor_id: int = 42):
    actor = MagicMock()
    actor.id = actor_id
    actor.guild_permissions = SimpleNamespace(administrator=True)
    return actor


def _preset_summary(*, key: str, mode: str, preset_id: int = 7):
    return svc.BehaviorPresetSummary(
        preset_id=preset_id,
        key=key,
        headline="test preset",
        recommended_mode=mode,
        body="test body",
    )


def _current_policy_row(**overrides):
    row = {
        "guild_id": 1,
        "enabled": True,
        "natural_language_enabled": False,
        "default_provider": "openai",
        "default_model": "gpt-4o-mini",
        "minimum_level_default": 5,
        "cooldown_seconds": 45,
        "fresh_user_mention_allowance": 2,
        "guild_instruction_profile_id": None,
        "generation": 4,
    }
    row.update(overrides)
    return row


@pytest.fixture
def captured_set_guild(monkeypatch):
    """Replace ``set_guild_policy`` with a kwargs capturer."""
    from services import ai_policy_mutation

    captured: list[dict] = []

    async def _capture(guild_id, **kwargs):
        captured.append({"guild_id": guild_id, **kwargs})
        return ai_policy_mutation.AIPolicyMutationResult(
            mutation_id="mut-1",
            table="ai_guild_policy",
            guild_id=guild_id,
            target_id=None,
            generation=5,
            event_emitted=True,
        )

    monkeypatch.setattr(ai_policy_mutation, "set_guild_policy", _capture)
    return captured


# ---------------------------------------------------------------------------
# _SUPPORTED_SCOPES inventory
# ---------------------------------------------------------------------------


def test_supported_scopes_includes_guild():
    """PR-6 contract: guild is a first-class scope."""
    assert "guild" in svc._SUPPORTED_SCOPES
    assert "channel" in svc._SUPPORTED_SCOPES
    assert "category" in svc._SUPPORTED_SCOPES


def test_module_exports_pr6_symbols():
    assert hasattr(svc, "apply_preset_to_guild")
    assert hasattr(svc, "GuildScopeNotSupportedError")
    assert issubclass(svc.GuildScopeNotSupportedError, svc.BehaviorPresetError)


# ---------------------------------------------------------------------------
# apply_preset_to_guild — happy path + preservation invariant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_preset_to_guild_preserves_all_other_fields(
    monkeypatch, captured_set_guild,
):
    """The preservation invariant: every field NOT owned by the preset
    is passed through unchanged from the current row."""
    monkeypatch.setattr(
        svc,
        "describe_preset",
        AsyncMock(
            return_value=_preset_summary(key="helpful_channel", mode="always_reply"),
        ),
    )
    from utils.db import ai as ai_db

    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(return_value=_current_policy_row()),
    )

    result = await svc.apply_preset_to_guild(
        guild_id=1,
        preset_id=7,
        actor=_admin_actor(),
    )

    assert len(captured_set_guild) == 1
    call = captured_set_guild[0]
    # Preset-owned fields are written.
    assert call["natural_language_enabled"] is True  # always_reply → True
    assert call["guild_instruction_profile_id"] == 7
    # Every other field is preserved verbatim.
    assert call["enabled"] is True
    assert call["default_provider"] == "openai"
    assert call["default_model"] == "gpt-4o-mini"
    assert call["minimum_level_default"] == 5
    assert call["cooldown_seconds"] == 45
    assert call["fresh_user_mention_allowance"] == 2

    assert isinstance(result, svc.BehaviorApplyResult)
    assert result.scope == "guild"
    assert result.preset_key == "helpful_channel"


@pytest.mark.asyncio
async def test_apply_preset_to_guild_disabled_preset_sets_nl_false(
    monkeypatch, captured_set_guild,
):
    """The ``disabled`` preset maps to ``natural_language_enabled=False``."""
    monkeypatch.setattr(
        svc,
        "describe_preset",
        AsyncMock(
            return_value=_preset_summary(key="disabled", mode="disabled"),
        ),
    )
    from utils.db import ai as ai_db

    # Start with NL enabled — the preset must override it to False.
    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(return_value=_current_policy_row(natural_language_enabled=True)),
    )

    await svc.apply_preset_to_guild(
        guild_id=1,
        preset_id=7,
        actor=_admin_actor(),
    )
    assert captured_set_guild[0]["natural_language_enabled"] is False


@pytest.mark.asyncio
async def test_apply_preset_to_guild_with_no_existing_row(
    monkeypatch, captured_set_guild,
):
    """When no ``ai_guild_policy`` row exists yet, set_guild_policy is
    called with sensible defaults — preservation can't preserve what
    doesn't exist, but the write must not raise on None lookups."""
    monkeypatch.setattr(
        svc,
        "describe_preset",
        AsyncMock(
            return_value=_preset_summary(key="helpful_channel", mode="always_reply"),
        ),
    )
    from utils.db import ai as ai_db

    monkeypatch.setattr(ai_db, "get_guild_policy", AsyncMock(return_value=None))

    await svc.apply_preset_to_guild(
        guild_id=1,
        preset_id=7,
        actor=_admin_actor(),
    )
    call = captured_set_guild[0]
    # Preset-owned fields are written.
    assert call["natural_language_enabled"] is True
    assert call["guild_instruction_profile_id"] == 7
    # Unset fields fall back to schema defaults rather than raising.
    assert call["enabled"] is False
    assert call["default_provider"] == "deterministic"


# ---------------------------------------------------------------------------
# mention_only rejection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_preset_to_guild_rejects_mention_only(
    monkeypatch, captured_set_guild,
):
    """``mention_only`` presets must raise — the typed
    natural_language_enabled column has no third state."""
    monkeypatch.setattr(
        svc,
        "describe_preset",
        AsyncMock(
            return_value=_preset_summary(
                key="mention_only_helper", mode="mention_only",
            ),
        ),
    )
    from utils.db import ai as ai_db

    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(return_value=_current_policy_row()),
    )

    with pytest.raises(svc.GuildScopeNotSupportedError):
        await svc.apply_preset_to_guild(
            guild_id=1,
            preset_id=7,
            actor=_admin_actor(),
        )
    # set_guild_policy was never called — the policy is unchanged.
    assert captured_set_guild == []


# ---------------------------------------------------------------------------
# Dispatch via apply_preset(scope="guild")
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_preset_scope_guild_delegates_to_guild_helper(
    monkeypatch, captured_set_guild,
):
    monkeypatch.setattr(
        svc,
        "describe_preset",
        AsyncMock(
            return_value=_preset_summary(key="helpful_channel", mode="always_reply"),
        ),
    )
    from utils.db import ai as ai_db

    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(return_value=_current_policy_row()),
    )

    result = await svc.apply_preset(
        guild_id=1,
        scope="guild",
        target_id=None,  # ignored for guild scope
        preset_id=7,
        actor=_admin_actor(),
    )
    assert result.scope == "guild"
    assert len(captured_set_guild) == 1


@pytest.mark.asyncio
async def test_apply_preset_scope_guild_rejects_mention_only(
    monkeypatch, captured_set_guild,
):
    """The unified dispatcher must surface GuildScopeNotSupportedError
    for ``mention_only`` presets when scope='guild'."""
    monkeypatch.setattr(
        svc,
        "describe_preset",
        AsyncMock(
            return_value=_preset_summary(
                key="mention_only_helper", mode="mention_only",
            ),
        ),
    )
    from utils.db import ai as ai_db

    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(return_value=_current_policy_row()),
    )

    with pytest.raises(svc.GuildScopeNotSupportedError):
        await svc.apply_preset(
            guild_id=1,
            scope="guild",
            target_id=None,
            preset_id=7,
            actor=_admin_actor(),
        )


# ---------------------------------------------------------------------------
# Unknown preset raises before any DB write
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_preset_to_guild_unknown_preset(
    monkeypatch, captured_set_guild,
):
    monkeypatch.setattr(svc, "describe_preset", AsyncMock(return_value=None))

    with pytest.raises(svc.UnknownBehaviorPresetError):
        await svc.apply_preset_to_guild(
            guild_id=1,
            preset_id=9999,
            actor=_admin_actor(),
        )
    assert captured_set_guild == []
