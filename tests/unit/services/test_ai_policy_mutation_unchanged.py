"""PR-C-pre tests for the UNCHANGED sentinel.

Pin the contract:

* ``UNCHANGED`` is the default for every optional column on
  ``set_channel_policy / set_category_policy / set_role_policy``.
* When passed, the mutation function forwards an ``unchanged_fields``
  set to the matching ``ai_db.upsert_*`` helper, which omits those
  fields from the ``EXCLUDED`` SET on conflict (preserve semantics).
* Passing ``None`` explicitly still clears the column (set to NULL).
* Passing a concrete value still sets the column.
* The required ``mode`` (or ``decision``) field cannot be sentinel —
  the row must always carry one.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services import ai_policy_mutation
from utils.db import ai as ai_db


def _admin_actor(actor_id: int = 555):
    return SimpleNamespace(
        id=actor_id,
        guild_permissions=SimpleNamespace(administrator=True),
    )


def _patch_db(monkeypatch):
    captured: dict = {}

    async def _upsert_channel(guild_id, channel_id, **kwargs):
        captured.setdefault("channel", []).append(
            {"guild_id": guild_id, "channel_id": channel_id, **kwargs},
        )

    async def _upsert_category(guild_id, category_id, **kwargs):
        captured.setdefault("category", []).append(
            {"guild_id": guild_id, "category_id": category_id, **kwargs},
        )

    async def _upsert_role(guild_id, role_id, **kwargs):
        captured.setdefault("role", []).append(
            {"guild_id": guild_id, "role_id": role_id, **kwargs},
        )

    async def _bump(_gid):
        return 99

    monkeypatch.setattr(ai_db, "upsert_channel_policy", _upsert_channel)
    monkeypatch.setattr(ai_db, "upsert_category_policy", _upsert_category)
    monkeypatch.setattr(ai_db, "upsert_role_policy", _upsert_role)
    monkeypatch.setattr(ai_db, "bump_generation", _bump)
    monkeypatch.setattr(
        "services.ai_natural_language_policy.invalidate",
        lambda _gid: None,
    )
    monkeypatch.setattr(
        ai_policy_mutation,
        "_emit",
        AsyncMock(return_value=True),
    )
    return captured


# ---------------------------------------------------------------------------
# Channel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_channel_default_unchanged_for_optional_fields(monkeypatch):
    """Calling set_channel_policy with only mode preserves every other
    optional column. This is the PR-C-pre default."""
    captured = _patch_db(monkeypatch)

    await ai_policy_mutation.set_channel_policy(
        guild_id=1,
        channel_id=2,
        mode="always_reply",
        actor=_admin_actor(),
    )

    [call] = captured["channel"]
    assert call["unchanged_fields"] == {
        "min_level",
        "cooldown_seconds",
        "instruction_profile_id",
    }
    # On the INSERT path the value is None (NULL); on conflict the SQL
    # omits the column from EXCLUDED.
    assert call["min_level"] is None
    assert call["cooldown_seconds"] is None
    assert call["instruction_profile_id"] is None


@pytest.mark.asyncio
async def test_channel_explicit_none_still_clears(monkeypatch):
    """Passing ``None`` explicitly must still clear the column."""
    captured = _patch_db(monkeypatch)

    await ai_policy_mutation.set_channel_policy(
        guild_id=1,
        channel_id=2,
        mode="always_reply",
        instruction_profile_id=None,
        actor=_admin_actor(),
    )

    [call] = captured["channel"]
    # instruction_profile_id is NOT in unchanged_fields → SET clause
    # writes NULL → existing value is overwritten.
    assert "instruction_profile_id" not in call["unchanged_fields"]
    assert call["instruction_profile_id"] is None


@pytest.mark.asyncio
async def test_channel_concrete_value_overwrites(monkeypatch):
    captured = _patch_db(monkeypatch)

    await ai_policy_mutation.set_channel_policy(
        guild_id=1,
        channel_id=2,
        mode="mention_only",
        min_level=5,
        instruction_profile_id=42,
        actor=_admin_actor(),
    )

    [call] = captured["channel"]
    assert call["min_level"] == 5
    assert call["instruction_profile_id"] == 42
    # cooldown_seconds left at default UNCHANGED.
    assert call["unchanged_fields"] == {"cooldown_seconds"}


@pytest.mark.asyncio
async def test_channel_mode_required(monkeypatch):
    _patch_db(monkeypatch)

    with pytest.raises(ai_policy_mutation.InvalidAIPolicyValueError, match="mode"):
        await ai_policy_mutation.set_channel_policy(
            guild_id=1,
            channel_id=2,
            actor=_admin_actor(),
        )


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_category_default_unchanged_for_optional_fields(monkeypatch):
    captured = _patch_db(monkeypatch)

    await ai_policy_mutation.set_category_policy(
        guild_id=10,
        category_id=20,
        mode="mention_only",
        actor=_admin_actor(),
    )

    [call] = captured["category"]
    assert call["unchanged_fields"] == {
        "min_level",
        "cooldown_seconds",
        "instruction_profile_id",
    }


@pytest.mark.asyncio
async def test_category_partial_edit_preserves_profile(monkeypatch):
    """The regression scenario that motivated PR-C-pre: an operator
    edits min_level via the modal; instruction_profile_id stays
    untouched.
    """
    captured = _patch_db(monkeypatch)

    await ai_policy_mutation.set_category_policy(
        guild_id=10,
        category_id=20,
        mode="always_reply",
        min_level=3,
        cooldown_seconds=60,
        instruction_profile_id=ai_policy_mutation.UNCHANGED,
        actor=_admin_actor(),
    )

    [call] = captured["category"]
    assert call["min_level"] == 3
    assert call["cooldown_seconds"] == 60
    assert call["unchanged_fields"] == {"instruction_profile_id"}


# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_role_default_unchanged_for_optional_fields(monkeypatch):
    captured = _patch_db(monkeypatch)

    await ai_policy_mutation.set_role_policy(
        guild_id=1,
        role_id=2,
        decision="allow",
        actor=_admin_actor(),
    )

    [call] = captured["role"]
    assert call["unchanged_fields"] == {"min_level_override", "bypass_cooldown"}


@pytest.mark.asyncio
async def test_role_concrete_values_overwrite(monkeypatch):
    captured = _patch_db(monkeypatch)

    await ai_policy_mutation.set_role_policy(
        guild_id=1,
        role_id=2,
        decision="deny",
        min_level_override=7,
        bypass_cooldown=True,
        actor=_admin_actor(),
    )

    [call] = captured["role"]
    assert call["min_level_override"] == 7
    assert call["bypass_cooldown"] is True
    assert call["unchanged_fields"] == set()


# ---------------------------------------------------------------------------
# DB-layer SQL shape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_db_upsert_channel_omits_unchanged_from_excluded(monkeypatch):
    """The DB layer must drop UNCHANGED columns from the EXCLUDED
    SET on conflict — that's the actual mechanism that preserves
    the existing value.
    """
    captured: dict = {}

    class _FakeConn:
        async def execute(self, sql, *args):
            captured["sql"] = sql
            captured["args"] = args

    monkeypatch.setattr("utils.db.ai.pool.get", lambda: _FakeConn())

    await ai_db.upsert_channel_policy(
        1,
        2,
        mode="always_reply",
        min_level=None,
        cooldown_seconds=None,
        instruction_profile_id=None,
        updated_by=99,
        unchanged_fields={"instruction_profile_id"},
    )

    sql = captured["sql"]
    # instruction_profile_id NOT in the EXCLUDED list.
    assert "instruction_profile_id = EXCLUDED.instruction_profile_id" not in sql
    # The non-sentinel columns ARE in the EXCLUDED list.
    assert "mode = EXCLUDED.mode" in sql
    assert "min_level = EXCLUDED.min_level" in sql
    assert "cooldown_seconds = EXCLUDED.cooldown_seconds" in sql
    # Updated_at + updated_by always written.
    assert "updated_at = NOW()" in sql
    assert "updated_by = EXCLUDED.updated_by" in sql
