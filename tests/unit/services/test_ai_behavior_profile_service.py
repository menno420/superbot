"""Tests for the AI Behavior preset service (PR-B).

Covers:

* ``list_presets`` reads through ``ai_db.list_preset_profiles`` and
  joins with the in-process catalog.
* ``describe_preset`` rejects rows missing ``is_preset = True``.
* ``apply_preset`` writes through ``ai_policy_mutation`` (never
  directly to ``ai_db``) and selects the correct mutation function
  per scope.
* ``apply_preset`` refuses scopes outside ``{"channel", "category"}``.
* The catalog keys are a stable subset of the seeded preset names.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from services import ai_behavior_profile_service as svc
from utils.db import ai as ai_db


def _preset_row(
    preset_id: int,
    name: str,
    body: str = "preset body",
    *,
    is_preset: bool = True,
):
    return {
        "id": preset_id,
        "guild_id": None,
        "name": name,
        "body": body,
        "scope": "system",
        "feature_key": None,
        "is_preset": is_preset,
    }


def _admin_actor(actor_id: int = 1234):
    return SimpleNamespace(
        id=actor_id,
        guild_permissions=SimpleNamespace(administrator=True),
    )


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


def test_catalog_keys_match_seed_migration():
    """Migration 044 seeds these seven preset names. The Python
    catalog must match — adding or removing a preset is a coordinated
    change across both files.
    """
    expected = {
        "disabled",
        "mention_only_helper",
        "helpful_channel",
        "btd6_focused",
        "quiet_btd6_focused",
        "staff_diagnostics",
        "support_triage",
    }
    assert svc.PRESET_KEYS == expected


# ---------------------------------------------------------------------------
# list_presets
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_presets_reads_through_ai_db(monkeypatch):
    captured = []

    async def _fake(*args, **kwargs):
        captured.append((args, kwargs))
        return [
            _preset_row(11, "disabled"),
            _preset_row(12, "helpful_channel"),
        ]

    monkeypatch.setattr(ai_db, "list_preset_profiles", _fake)

    out = await svc.list_presets()

    assert captured == [((), {})]
    assert [p.preset_id for p in out] == [11, 12]
    assert {p.key for p in out} == {"disabled", "helpful_channel"}
    # Catalog metadata is joined in.
    disabled = next(p for p in out if p.key == "disabled")
    assert disabled.recommended_mode == "disabled"
    helpful = next(p for p in out if p.key == "helpful_channel")
    assert helpful.recommended_mode == "always_reply"


@pytest.mark.asyncio
async def test_list_presets_surfaces_uncatalogued_rows(monkeypatch):
    """A DB row whose name is not in the catalog is still surfaced
    with a fallback entry — the operator should not silently lose
    seeded presets if the Python side falls out of sync.
    """

    async def _fake():
        return [_preset_row(99, "experimental_new_preset", body="hi")]

    monkeypatch.setattr(ai_db, "list_preset_profiles", _fake)

    out = await svc.list_presets()
    assert len(out) == 1
    assert out[0].key == "experimental_new_preset"
    assert "uncatalogued" in out[0].headline


# ---------------------------------------------------------------------------
# describe_preset
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_describe_preset_returns_summary_for_valid_id(monkeypatch):
    async def _fake(pid):
        return _preset_row(42, "btd6_focused", body="prioritise BTD6")

    monkeypatch.setattr(ai_db, "get_instruction_profile", _fake)

    summary = await svc.describe_preset(42)
    assert summary is not None
    assert summary.preset_id == 42
    assert summary.key == "btd6_focused"
    assert summary.recommended_mode == "always_reply"
    assert summary.body == "prioritise BTD6"


@pytest.mark.asyncio
async def test_describe_preset_returns_none_when_not_a_preset(monkeypatch):
    async def _fake(pid):
        return _preset_row(7, "btd6_focused", is_preset=False)

    monkeypatch.setattr(ai_db, "get_instruction_profile", _fake)

    assert await svc.describe_preset(7) is None


@pytest.mark.asyncio
async def test_describe_preset_returns_none_when_row_missing(monkeypatch):
    async def _fake(_pid):
        return None

    monkeypatch.setattr(ai_db, "get_instruction_profile", _fake)

    assert await svc.describe_preset(999) is None


# ---------------------------------------------------------------------------
# apply_preset
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_preset_to_channel_calls_set_channel_policy(monkeypatch):
    captured: dict = {}

    async def _describe(_pid):
        return svc.BehaviorPresetSummary(
            preset_id=42,
            key="btd6_focused",
            headline="BTD6 grounding prioritised",
            recommended_mode="always_reply",
            body="...",
        )

    async def _set_channel_policy(guild_id, channel_id, **kwargs):
        captured["table"] = "channel"
        captured["guild_id"] = guild_id
        captured["channel_id"] = channel_id
        captured.update(kwargs)
        return MagicMock(mutation_id="mid-123")

    monkeypatch.setattr(svc, "describe_preset", _describe)
    monkeypatch.setattr(
        "services.ai_policy_mutation.set_channel_policy",
        _set_channel_policy,
    )

    result = await svc.apply_preset(
        guild_id=999,
        scope="channel",
        target_id=555,
        preset_id=42,
        actor=_admin_actor(),
    )

    assert captured["table"] == "channel"
    assert captured["guild_id"] == 999
    assert captured["channel_id"] == 555
    assert captured["mode"] == "always_reply"
    assert captured["instruction_profile_id"] == 42
    assert result.preset_id == 42
    assert result.preset_key == "btd6_focused"
    assert result.scope == "channel"
    assert result.policy_mutation_id == "mid-123"


@pytest.mark.asyncio
async def test_apply_preset_to_category_calls_set_category_policy(monkeypatch):
    captured: dict = {}

    async def _describe(_pid):
        return svc.BehaviorPresetSummary(
            preset_id=7,
            key="mention_only_helper",
            headline="Concise replies",
            recommended_mode="mention_only",
            body="...",
        )

    async def _set_category_policy(guild_id, category_id, **kwargs):
        captured["table"] = "category"
        captured["category_id"] = category_id
        captured.update(kwargs)
        return MagicMock(mutation_id="mid-cat")

    monkeypatch.setattr(svc, "describe_preset", _describe)
    monkeypatch.setattr(
        "services.ai_policy_mutation.set_category_policy",
        _set_category_policy,
    )

    result = await svc.apply_preset(
        guild_id=10,
        scope="category",
        target_id=20,
        preset_id=7,
        actor=_admin_actor(),
    )

    assert captured["table"] == "category"
    assert captured["category_id"] == 20
    assert captured["mode"] == "mention_only"
    assert captured["instruction_profile_id"] == 7
    assert result.scope == "category"


@pytest.mark.asyncio
async def test_apply_preset_refuses_unsupported_scope():
    """Guild scope is supported as of PR-6 — refuse a genuinely
    invalid scope name instead."""
    with pytest.raises(svc.InvalidBehaviorPresetScopeError):
        await svc.apply_preset(
            guild_id=1,
            scope="role",  # not supported
            target_id=1,
            preset_id=1,
            actor=_admin_actor(),
        )


@pytest.mark.asyncio
async def test_apply_preset_raises_when_preset_missing(monkeypatch):
    async def _describe(_pid):
        return None

    monkeypatch.setattr(svc, "describe_preset", _describe)

    with pytest.raises(svc.UnknownBehaviorPresetError):
        await svc.apply_preset(
            guild_id=1,
            scope="channel",
            target_id=1,
            preset_id=9999,
            actor=_admin_actor(),
        )


# ---------------------------------------------------------------------------
# Boundary: service never touches ai_db.upsert_* helpers directly.
# ---------------------------------------------------------------------------


def test_service_does_not_import_ai_db_write_helpers():
    """The service layer is read-only on ``ai_db``; writes flow
    through ``ai_policy_mutation``.
    """
    import inspect

    src = inspect.getsource(svc)
    forbidden = (
        "ai_db.upsert_channel_policy",
        "ai_db.upsert_category_policy",
        "ai_db.upsert_role_policy",
        "ai_db.upsert_instruction_profile",
        "ai_db.upsert_guild_policy",
    )
    for sym in forbidden:
        assert sym not in src, f"behavior service must not call {sym}"
