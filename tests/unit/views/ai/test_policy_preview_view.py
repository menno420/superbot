"""PR4B — preview view runs resolve(dry_run=True) only; no audit / cooldown."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import PolicyDenialReason  # noqa: E402
from services import ai_natural_language_policy as nlp  # noqa: E402
from views.ai.policy.preview_view import (  # noqa: E402
    PreviewChannelSelectView,
    _build_preview_embed,
)


def _fake_channel(channel_id: int = 555, category_id: int | None = 200) -> MagicMock:
    ch = MagicMock()
    ch.id = channel_id
    ch.name = "general"
    ch.mention = f"<#{channel_id}>"
    ch.category_id = category_id
    return ch


def _fake_member(member_id: int = 99, roles: list[int] | None = None) -> MagicMock:
    member = MagicMock()
    member.id = member_id
    member.mention = f"<@{member_id}>"
    member.guild_permissions.administrator = True
    role_objs = []
    for role_id in roles or []:
        role = MagicMock()
        role.id = role_id
        role_objs.append(role)
    member.roles = role_objs
    return member


def _fake_interaction(*, guild_id: int = 1, member: MagicMock | None = None):
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = guild_id
    interaction.user = member or _fake_member()
    interaction.response.send_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# _build_preview_embed
# ---------------------------------------------------------------------------


async def test_build_preview_embed_calls_resolve_with_dry_run_only(monkeypatch):
    """Both invocations (with/without mention) must pass dry_run=True."""
    captured: list[bool] = []

    async def _resolve(ctx, *, dry_run=False):
        captured.append(dry_run)
        return nlp.PolicyDecision(
            allowed=True,
            reason_code=PolicyDenialReason.NONE,
            effective_min_level=2,
            effective_cooldown=30,
            precedence_trace=("guild: baseline", "final: allowed"),
        )

    monkeypatch.setattr(nlp, "resolve", _resolve)

    async def _xp(_g, _u):
        record = MagicMock()
        record.level = 7
        return record

    monkeypatch.setattr("services.xp_service.get_user_record", _xp)

    interaction = _fake_interaction(member=_fake_member(roles=[42, 99]))
    embed = await _build_preview_embed(interaction, _fake_channel())

    assert captured == [True, True]
    # Embed must have one field per scenario.
    field_names = [f.name for f in embed.fields]
    assert field_names == ["Without mention", "With @mention"]


async def test_build_preview_embed_renders_decision_and_trace(monkeypatch):
    async def _resolve(ctx, *, dry_run=False):
        return nlp.PolicyDecision(
            allowed=False,
            reason_code=PolicyDenialReason.CHANNEL_DISABLED,
            effective_min_level=2,
            effective_cooldown=30,
            precedence_trace=(
                "guild: baseline min_level=2 cooldown=30s",
                "channel 555: mode=disabled → deny CHANNEL_DISABLED",
            ),
        )

    monkeypatch.setattr(nlp, "resolve", _resolve)

    async def _xp(_g, _u):
        record = MagicMock()
        record.level = 7
        return record

    monkeypatch.setattr("services.xp_service.get_user_record", _xp)

    interaction = _fake_interaction()
    embed = await _build_preview_embed(interaction, _fake_channel())
    blob = "\n".join(f"{f.name}\n{f.value}" for f in embed.fields)
    assert "❌" in blob
    assert "denied" in blob
    assert "CHANNEL_DISABLED" in blob
    assert "channel 555: mode=disabled" in blob
    assert "guild: baseline" in blob


async def test_build_preview_embed_uses_resolved_user_level(monkeypatch):
    captured_ctx: list[nlp.MessageContext] = []

    async def _resolve(ctx, *, dry_run=False):
        captured_ctx.append(ctx)
        return nlp.PolicyDecision(
            allowed=True,
            reason_code=PolicyDenialReason.NONE,
            effective_min_level=2,
            effective_cooldown=30,
        )

    monkeypatch.setattr(nlp, "resolve", _resolve)

    async def _xp(_g, _u):
        record = MagicMock()
        record.level = 17
        return record

    monkeypatch.setattr("services.xp_service.get_user_record", _xp)

    interaction = _fake_interaction(member=_fake_member(roles=[101, 202]))
    await _build_preview_embed(interaction, _fake_channel(category_id=200))
    assert captured_ctx[0].user_level == 17
    assert captured_ctx[0].user_role_ids == (101, 202)
    assert captured_ctx[0].category_id == 200
    # is_mention differs between the two scenarios.
    assert captured_ctx[0].is_mention is False
    assert captured_ctx[1].is_mention is True


async def test_build_preview_embed_treats_xp_failure_as_fresh_user(monkeypatch):
    captured_ctx: list[nlp.MessageContext] = []

    async def _resolve(ctx, *, dry_run=False):
        captured_ctx.append(ctx)
        return nlp.PolicyDecision(
            allowed=True,
            reason_code=PolicyDenialReason.NONE,
            effective_min_level=2,
            effective_cooldown=30,
        )

    monkeypatch.setattr(nlp, "resolve", _resolve)

    async def _xp_explodes(_g, _u):
        raise RuntimeError("xp service down")

    monkeypatch.setattr("services.xp_service.get_user_record", _xp_explodes)

    interaction = _fake_interaction()
    embed = await _build_preview_embed(interaction, _fake_channel())
    assert captured_ctx[0].user_level == 0
    assert captured_ctx[0].is_fresh_user is True
    # Embed still renders rather than raising.
    assert "AI policy preview" in (embed.title or "")


# ---------------------------------------------------------------------------
# PreviewChannelSelectView shape + gating.
# ---------------------------------------------------------------------------


def test_preview_select_view_holds_a_text_channel_select():
    view = PreviewChannelSelectView()
    selects = [
        item for item in view.children if isinstance(item, discord.ui.ChannelSelect)
    ]
    assert len(selects) == 1
    assert selects[0].channel_types == [discord.ChannelType.text]


async def test_preview_select_view_rejects_non_admin():
    view = PreviewChannelSelectView()
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = False
    interaction.response.send_message = AsyncMock()
    allowed = await view.interaction_check(interaction)
    assert allowed is False


# ---------------------------------------------------------------------------
# Chooser button wires through to the preview view.
# ---------------------------------------------------------------------------


async def test_chooser_preview_button_opens_preview_view():
    from views.ai.policy.chooser import PolicyChooserView

    view = PolicyChooserView()
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = True
    interaction.response.send_message = AsyncMock()
    await view.preview_btn.callback(interaction)
    _, kwargs = interaction.response.send_message.call_args
    assert isinstance(kwargs["view"], PreviewChannelSelectView)
    assert kwargs.get("ephemeral") is True


def test_chooser_has_preview_button_on_row_one_with_list():
    """Preview is an admin-only secondary action — same row as List
    so the layout stays predictable."""
    from views.ai.policy.chooser import PolicyChooserView

    view = PolicyChooserView()
    btns = {
        item.label: item
        for item in view.children
        if isinstance(item, discord.ui.Button)
    }
    assert "Preview" in btns
    assert "List overrides" in btns
    assert btns["Preview"].row == btns["List overrides"].row
