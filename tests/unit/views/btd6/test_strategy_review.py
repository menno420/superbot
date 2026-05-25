"""PR5 — strategy review view drives every action through ai_strategy_mutation."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_strategy_mutation  # noqa: E402
from utils.db import btd6_strategies as db  # noqa: E402
from views.btd6.strategy_review import (  # noqa: E402
    StrategyReviewView,
    build_strategy_embed,
)


def _strategy(
    *,
    sid: int = 42,
    visibility: str = "guild",
    approval_status: str = "draft",
    title: str = "Round 100 push",
    summary: str = "Drop dart at corner, upgrade to 4xx, etc.",
    submitter_display: str = "alice#1234",
) -> dict:
    return {
        "id": sid,
        "title": title,
        "summary": summary,
        "map": "TreeStump",
        "mode": "Standard",
        "difficulty": "Medium",
        "hero": "Quincy",
        "origin_guild_id": 100,
        "current_guild_id": 100,
        "visibility": visibility,
        "approval_status": approval_status,
        "version": 1,
        "submitter_display_snapshot": submitter_display,
        "submitted_by": 12345,
    }


def _staff_interaction(*, manage_guild: bool = True) -> MagicMock:
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = False
    interaction.user.guild_permissions.manage_guild = manage_guild
    interaction.user.id = 7777
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# build_strategy_embed
# ---------------------------------------------------------------------------


def test_embed_includes_title_summary_and_state():
    embed = build_strategy_embed(_strategy())
    assert "Round 100 push" in (embed.title or "")
    assert "Drop dart" in (embed.description or "")
    fields = {f.name: f.value for f in embed.fields}
    assert "Map" in fields and "TreeStump" in fields["Map"]
    assert "Hero" in fields and "Quincy" in fields["Hero"]
    assert "State" in fields
    assert "approval=`draft`" in fields["State"]
    assert "visibility=`guild`" in fields["State"]


def test_embed_footer_carries_id_and_submitter():
    embed = build_strategy_embed(_strategy())
    assert "id=42" in (embed.footer.text or "")
    assert "alice#1234" in (embed.footer.text or "")


def test_embed_handles_long_title_and_summary():
    strategy = _strategy(title="X" * 500, summary="Y" * 5000)
    embed = build_strategy_embed(strategy)
    # Discord caps the title at 256 and description at 4096; the
    # renderer must not break.
    assert len(embed.title) <= 256
    assert embed.description is not None
    assert len(embed.description) <= 2048


# ---------------------------------------------------------------------------
# StrategyReviewView — button matrix + staff gate
# ---------------------------------------------------------------------------


def test_guild_strategy_does_not_show_unpublish_button():
    view = StrategyReviewView(_strategy(visibility="guild"))
    labels = {item.label for item in view.children if hasattr(item, "label")}
    assert "Unpublish" not in labels
    # The other three actions are always available.
    assert "Approve (guild)" in labels
    assert "Publish (global)" in labels
    assert "Reject" in labels


def test_published_strategy_shows_unpublish_button():
    view = StrategyReviewView(_strategy(visibility="published"))
    labels = {item.label for item in view.children if hasattr(item, "label")}
    assert "Unpublish" in labels
    assert "Approve (guild)" in labels


async def test_view_rejects_non_staff():
    view = StrategyReviewView(_strategy())
    interaction = _staff_interaction(manage_guild=False)
    allowed = await view.interaction_check(interaction)
    assert allowed is False
    interaction.response.send_message.assert_awaited_once()
    args, kwargs = interaction.response.send_message.call_args
    assert "manage_guild" in args[0] or "administrator" in args[0]
    assert kwargs.get("ephemeral") is True


async def test_view_admits_admin_even_without_manage_guild():
    view = StrategyReviewView(_strategy())
    interaction = _staff_interaction(manage_guild=False)
    interaction.user.guild_permissions.administrator = True
    allowed = await view.interaction_check(interaction)
    assert allowed is True


# ---------------------------------------------------------------------------
# Button callbacks route to mutation service ONLY (no direct DB writes).
# ---------------------------------------------------------------------------


async def test_approve_guild_button_calls_staff_approve_guild(monkeypatch):
    captured: dict = {}

    async def _capture(strategy_id, *, staff_actor, detail=None):
        captured["id"] = strategy_id
        captured["actor"] = staff_actor
        result = MagicMock()
        result.action = "staff_approved_guild"
        return result

    monkeypatch.setattr(
        btd6_strategy_mutation,
        "staff_approve_guild",
        _capture,
    )

    async def _refresh(sid):
        return _strategy(sid=sid, approval_status="approved")

    monkeypatch.setattr(db, "get_strategy", _refresh)

    view = StrategyReviewView(_strategy(sid=42))
    interaction = _staff_interaction()
    await view.approve_guild_btn.callback(interaction)
    assert captured["id"] == 42
    assert captured["actor"] is interaction.user
    interaction.response.edit_message.assert_awaited_once()
    interaction.followup.send.assert_awaited_once()
    args, _ = interaction.followup.send.call_args
    assert "Approved" in args[0]
    assert "#42" in args[0]


async def test_publish_button_calls_staff_publish(monkeypatch):
    captured: dict = {}

    async def _capture(strategy_id, *, staff_actor, detail=None):
        captured["id"] = strategy_id
        result = MagicMock()
        result.action = "published"
        return result

    monkeypatch.setattr(btd6_strategy_mutation, "staff_publish", _capture)

    async def _refresh(sid):
        return _strategy(sid=sid, visibility="published")

    monkeypatch.setattr(db, "get_strategy", _refresh)

    view = StrategyReviewView(_strategy(sid=11))
    interaction = _staff_interaction()
    await view.publish_btn.callback(interaction)
    assert captured["id"] == 11
    args, _ = interaction.followup.send.call_args
    assert "Published" in args[0]


async def test_reject_button_calls_reject_with_staff_actor_kind(monkeypatch):
    captured: dict = {}

    async def _capture(strategy_id, *, actor, actor_kind, reason=None):
        captured["id"] = strategy_id
        captured["actor"] = actor
        captured["actor_kind"] = actor_kind
        result = MagicMock()
        result.action = "rejected"
        return result

    monkeypatch.setattr(btd6_strategy_mutation, "reject", _capture)

    async def _refresh(sid):
        return _strategy(sid=sid, approval_status="rejected")

    monkeypatch.setattr(db, "get_strategy", _refresh)

    view = StrategyReviewView(_strategy(sid=5))
    interaction = _staff_interaction()
    await view.reject_btn.callback(interaction)
    assert captured["id"] == 5
    assert captured["actor_kind"] == "staff"


async def test_unpublish_button_calls_unpublish_on_published_strategy(monkeypatch):
    captured: dict = {}

    async def _capture(strategy_id, *, staff_actor, reason=None):
        captured["id"] = strategy_id
        result = MagicMock()
        result.action = "unpublished"
        return result

    monkeypatch.setattr(btd6_strategy_mutation, "unpublish", _capture)

    async def _refresh(sid):
        return _strategy(sid=sid, visibility="guild", approval_status="unpublished")

    monkeypatch.setattr(db, "get_strategy", _refresh)

    view = StrategyReviewView(_strategy(sid=99, visibility="published"))
    interaction = _staff_interaction()
    await view.unpublish_btn.callback(interaction)
    assert captured["id"] == 99
    args, _ = interaction.followup.send.call_args
    assert "Unpublished" in args[0]


async def test_mutation_error_surfaces_as_typed_ephemeral_reply(monkeypatch):
    async def _raise(strategy_id, **kw):
        raise btd6_strategy_mutation.InvalidStrategyValueError("bad value")

    monkeypatch.setattr(btd6_strategy_mutation, "staff_publish", _raise)

    view = StrategyReviewView(_strategy(sid=42))
    interaction = _staff_interaction()
    await view.publish_btn.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    args, kwargs = interaction.response.send_message.call_args
    assert "InvalidStrategyValueError" in args[0]
    assert "bad value" in args[0]
    assert kwargs.get("ephemeral") is True
    # No refresh / followup happened because the mutation failed.
    interaction.response.edit_message.assert_not_awaited()
    interaction.followup.send.assert_not_awaited()


async def test_unauthorized_mutation_error_uses_ephemeral_branch(monkeypatch):
    """Server-side gate (mutation service) is the source of truth; the
    view's interaction_check is just a UX courtesy."""
    async def _raise(strategy_id, **kw):
        raise btd6_strategy_mutation.UnauthorizedStrategyMutationError("nope")

    monkeypatch.setattr(
        btd6_strategy_mutation,
        "staff_approve_guild",
        _raise,
    )

    view = StrategyReviewView(_strategy(sid=42))
    interaction = _staff_interaction()
    await view.approve_guild_btn.callback(interaction)
    args, _ = interaction.response.send_message.call_args
    assert "UnauthorizedStrategyMutationError" in args[0]


# ---------------------------------------------------------------------------
# Pin: every button calls THROUGH btd6_strategy_mutation, never the DB
# directly. Catches accidental future regressions where someone wires a
# button to utils.db.btd6_strategies for "convenience".
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("button_attr", "mutation_attr"),
    [
        ("approve_guild_btn", "staff_approve_guild"),
        ("publish_btn", "staff_publish"),
        ("reject_btn", "reject"),
    ],
)
async def test_button_only_writes_via_mutation_service(
    monkeypatch,
    button_attr,
    mutation_attr,
):
    called_mutation = {"hit": False}

    async def _capture(strategy_id, **kw):
        called_mutation["hit"] = True
        result = MagicMock()
        result.action = mutation_attr
        return result

    monkeypatch.setattr(btd6_strategy_mutation, mutation_attr, _capture)

    # If anyone writes to update_strategy_state or record_strategy_audit
    # directly from the view, this AsyncMock raises before the test ends.
    db_explode = AsyncMock(side_effect=AssertionError("view must not call DB directly"))
    monkeypatch.setattr(db, "update_strategy_state", db_explode)
    monkeypatch.setattr(db, "record_strategy_audit", db_explode)

    async def _refresh(sid):
        return _strategy(sid=sid)

    monkeypatch.setattr(db, "get_strategy", _refresh)

    view = StrategyReviewView(_strategy(sid=7))
    interaction = _staff_interaction()
    handler = getattr(view, button_attr)
    await handler.callback(interaction)
    assert called_mutation["hit"] is True
    db_explode.assert_not_awaited()
