"""Contract tests for the audited Help-overlay mutation seam (HLP-3).

Pins the write contract: administrator authority, write-time stable-key
validation against the catalogue, field bounds, partial-edit merge
semantics (``UNSET`` vs ``None``), store-only-deviations (all-``None`` ⇒
row deleted), full guild reset, cache invalidation, and the audit emit.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services import help_overlay as read_model
from services import help_overlay_mutation as mutation
from services.help_overlay_mutation import (
    UNSET,
    InvalidHelpOverlayValueError,
    UnauthorizedHelpOverlayMutationError,
    reset_guild_overlay,
    set_overlay_fields,
)


def _admin(user_id: int = 7):
    return SimpleNamespace(
        id=user_id,
        guild_permissions=SimpleNamespace(administrator=True),
    )


def _member():
    return SimpleNamespace(
        id=8,
        guild_permissions=SimpleNamespace(administrator=False),
    )


@pytest.fixture()
def db(monkeypatch):
    """Mocked DB primitives + spy on cache invalidation and audit emit."""
    from utils.db import help_overlay as db_module

    mocks = SimpleNamespace(
        get_row=AsyncMock(return_value=None),
        upsert_row=AsyncMock(),
        delete_row=AsyncMock(return_value=True),
        delete_guild_rows=AsyncMock(return_value=3),
        invalidate=lambda *a, **k: mocks.invalidated.append(a),
        invalidated=[],
        audit=AsyncMock(return_value=True),
    )
    monkeypatch.setattr(db_module, "get_row", mocks.get_row)
    monkeypatch.setattr(db_module, "upsert_row", mocks.upsert_row)
    monkeypatch.setattr(db_module, "delete_row", mocks.delete_row)
    monkeypatch.setattr(db_module, "delete_guild_rows", mocks.delete_guild_rows)
    monkeypatch.setattr(
        read_model,
        "invalidate_help_overlay_cache",
        mocks.invalidate,
    )
    import services.audit_events as audit_events

    monkeypatch.setattr(audit_events, "emit_audit_action", mocks.audit)
    return mocks


# ---------------------------------------------------------------------------
# Authority
# ---------------------------------------------------------------------------


async def test_actor_is_required(db):
    with pytest.raises(UnauthorizedHelpOverlayMutationError):
        await set_overlay_fields(1, "hub", "games", actor=None, display_hidden=True)


async def test_non_admin_is_rejected(db):
    with pytest.raises(UnauthorizedHelpOverlayMutationError):
        await set_overlay_fields(
            1,
            "hub",
            "games",
            actor=_member(),
            display_hidden=True,
        )
    db.upsert_row.assert_not_awaited()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


async def test_unknown_entity_kind_rejected(db):
    with pytest.raises(InvalidHelpOverlayValueError, match="entity_kind"):
        await set_overlay_fields(
            1,
            "command",
            "ping",
            actor=_admin(),
            display_hidden=True,
        )


async def test_unknown_key_rejected_against_catalogue(db):
    with pytest.raises(InvalidHelpOverlayValueError, match="unknown subsystem key"):
        await set_overlay_fields(
            1,
            "subsystem",
            "not-a-subsystem",
            actor=_admin(),
            display_hidden=True,
        )
    with pytest.raises(InvalidHelpOverlayValueError, match="unknown hub key"):
        await set_overlay_fields(
            1,
            "hub",
            "xp",
            actor=_admin(),
            display_hidden=True,  # xp is no hub
        )


async def test_text_bounds_enforced(db):
    with pytest.raises(InvalidHelpOverlayValueError, match="non-empty"):
        await set_overlay_fields(
            1,
            "subsystem",
            "xp",
            actor=_admin(),
            display_name="   ",
        )
    with pytest.raises(InvalidHelpOverlayValueError, match="exceeds 100"):
        await set_overlay_fields(
            1,
            "subsystem",
            "xp",
            actor=_admin(),
            display_name="x" * 101,
        )


async def test_display_hidden_must_be_bool_or_none(db):
    with pytest.raises(InvalidHelpOverlayValueError, match="bool"):
        await set_overlay_fields(
            1,
            "subsystem",
            "xp",
            actor=_admin(),
            display_hidden="yes",
        )


# ---------------------------------------------------------------------------
# Merge semantics
# ---------------------------------------------------------------------------


async def test_new_override_upserts_and_invalidates_and_audits(db):
    result = await set_overlay_fields(
        1,
        "subsystem",
        "xp",
        actor=_admin(7),
        display_name="  Levels  ",  # stripped before the write
    )
    db.upsert_row.assert_awaited_once_with(
        1,
        "subsystem",
        "xp",
        display_hidden=None,
        display_name="Levels",
        description=None,
        updated_by=7,
    )
    assert db.invalidated == [(1,)]
    db.audit.assert_awaited_once()
    audit_kwargs = db.audit.await_args.kwargs
    assert audit_kwargs["subsystem"] == "help"
    assert audit_kwargs["target"] == "subsystem:xp"
    assert audit_kwargs["prev_value"] is None  # no prior row
    assert result.prev is None
    assert result.new == {
        "display_hidden": None,
        "display_name": "Levels",
        "description": None,
    }
    assert result.audit_emitted


async def test_partial_edit_merges_with_existing_row(db):
    db.get_row.return_value = {
        "entity_kind": "subsystem",
        "entity_key": "xp",
        "display_hidden": True,
        "display_name": "Levels",
        "description": None,
        "updated_by": 7,
        "updated_at": None,
    }
    result = await set_overlay_fields(
        1,
        "subsystem",
        "xp",
        actor=_admin(),
        description="Earn XP by chatting",  # only this field changes
    )
    merged = db.upsert_row.await_args.kwargs
    assert merged["display_hidden"] is True  # UNSET → untouched
    assert merged["display_name"] == "Levels"  # UNSET → untouched
    assert merged["description"] == "Earn XP by chatting"
    assert result.prev == {
        "display_hidden": True,
        "display_name": "Levels",
        "description": None,
    }


async def test_resetting_every_field_deletes_the_row(db):
    db.get_row.return_value = {
        "entity_kind": "hub",
        "entity_key": "games",
        "display_hidden": True,
        "display_name": None,
        "description": None,
        "updated_by": 7,
        "updated_at": None,
    }
    result = await set_overlay_fields(
        1,
        "hub",
        "games",
        actor=_admin(),
        display_hidden=None,  # explicit reset → all fields inherit
    )
    db.delete_row.assert_awaited_once_with(1, "hub", "games")
    db.upsert_row.assert_not_awaited()
    assert result.new is None  # row removed — back to byte-identical default
    assert db.invalidated == [(1,)]


# ---------------------------------------------------------------------------
# Full reset
# ---------------------------------------------------------------------------


async def test_reset_guild_overlay_deletes_all_rows_and_audits(db):
    result = await reset_guild_overlay(1, actor=_admin())
    db.delete_guild_rows.assert_awaited_once_with(1)
    assert db.invalidated == [(1,)]
    assert result.prev == {"rows_removed": 3}
    assert result.new is None
    assert db.audit.await_args.kwargs["target"] == "guild:*"


async def test_reset_requires_admin(db):
    with pytest.raises(UnauthorizedHelpOverlayMutationError):
        await reset_guild_overlay(1, actor=_member())
    db.delete_guild_rows.assert_not_awaited()


# ---------------------------------------------------------------------------
# UNSET sentinel identity
# ---------------------------------------------------------------------------


def test_unset_sentinel_is_module_stable():
    """UNSET must be identity-stable so partial edits are unambiguous."""
    assert mutation.UNSET is UNSET
    assert UNSET is not None
