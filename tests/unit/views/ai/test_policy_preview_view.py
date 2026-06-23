"""PR4B — preview view runs resolve(dry_run=True) only; no audit / cooldown."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import discord

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
            effective_mode="disabled",
            effective_source="channel",
            precedence_trace=(
                "guild_baseline: natural_language_enabled=True → baseline mode=always_reply",
                "channel_policy: mode=disabled min_level=2 cooldown=30s",
                "mode_gate: mode=disabled → deny CHANNEL_DISABLED",
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
    # Verdict line carries the denial marker + reason value.
    assert "denied" in blob
    assert "channel_disabled" in blob
    # Effective summary line names source + mode.
    assert "effective:" in blob and "source=`channel`" in blob
    assert "mode=`disabled`" in blob
    # Trace bullets are rendered verbatim.
    assert "channel_policy: mode=disabled" in blob
    assert "mode_gate" in blob


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
    interaction.response.edit_message = AsyncMock()
    # In-place navigation (AI nav plan PR 2): the anchor is edited to the
    # effective-policy preview page rather than a new ephemeral.
    await view.preview_btn.callback(interaction)
    _, kwargs = interaction.response.edit_message.call_args
    assert isinstance(kwargs["view"], PreviewChannelSelectView)


def test_chooser_has_preview_button_on_row_one_with_list():
    """The "Effective policy" button (renamed from Preview in PR-2)
    is an admin-only secondary action — same row as List so the
    layout stays predictable. The handler name (``preview_btn``)
    is the persistent custom_id contract and is unchanged.
    """
    from views.ai.policy.chooser import PolicyChooserView

    view = PolicyChooserView()
    btns = {
        item.label: item
        for item in view.children
        if isinstance(item, discord.ui.Button)
    }
    assert "Effective policy" in btns
    assert "List overrides" in btns
    assert btns["Effective policy"].row == btns["List overrides"].row


# ---------------------------------------------------------------------------
# Verdict marker distinguishes hard-kill from baseline-denied (PR 3).
# ---------------------------------------------------------------------------


async def test_build_preview_embed_renders_hard_kill_marker(monkeypatch):
    async def _resolve(ctx, *, dry_run=False):
        return nlp.PolicyDecision(
            allowed=False,
            reason_code=PolicyDenialReason.AI_GLOBALLY_DISABLED,
            effective_min_level=2,
            effective_cooldown=30,
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
    assert "hard-disabled" in blob
    assert "ai_globally_disabled" in blob


async def test_build_preview_embed_renders_baseline_disabled_marker(monkeypatch):
    """``AI_NL_DISABLED_FOR_GUILD`` is the baseline reason — admins
    can override per channel/category, so it renders as baseline-denied
    rather than hard-disabled.
    """
    async def _resolve(ctx, *, dry_run=False):
        return nlp.PolicyDecision(
            allowed=False,
            reason_code=PolicyDenialReason.AI_NL_DISABLED_FOR_GUILD,
            effective_min_level=2,
            effective_cooldown=30,
            effective_mode="disabled",
            effective_source="guild",
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
    assert "baseline-denied" in blob
    assert "ai_nl_disabled_for_guild" in blob
    # Effective summary names guild as the source.
    assert "source=`guild`" in blob


# ---------------------------------------------------------------------------
# Preview ↔ live parity for the inheritance bug case (PR 3).
# ---------------------------------------------------------------------------


async def test_preview_and_live_agree_for_bug_case(monkeypatch):
    """Bug case integration parity test: ``guild natural_language_enabled=false``
    plus ``channel mode=always_reply`` must resolve to allowed via the same
    decision whether the resolver is called with ``dry_run=False`` (live
    runtime) or ``dry_run=True`` (preview). Pins that the dry-run toggle
    only adds bookkeeping; it never changes the decision.
    """
    from utils.db import ai as ai_db

    async def _get_policy(_gid):
        return {
            "guild_id": 1,
            "enabled": True,
            "natural_language_enabled": False,
            "default_provider": "deterministic",
            "default_model": "",
            "minimum_level_default": 2,
            "cooldown_seconds": 30,
            "fresh_user_mention_allowance": 1,
            "guild_instruction_profile_id": None,
            "generation": 1,
        }

    async def _list_channel(_gid):
        return [{
            "channel_id": 555,
            "mode": "always_reply",
            "min_level": 0,
            "cooldown_seconds": 10,
            "instruction_profile_id": None,
        }]

    async def _empty(_gid):
        return []

    monkeypatch.setattr(ai_db, "get_guild_policy", _get_policy)
    monkeypatch.setattr(ai_db, "list_channel_policies", _list_channel)
    monkeypatch.setattr(ai_db, "list_category_policies", _empty)
    monkeypatch.setattr(ai_db, "list_role_policies", _empty)
    nlp._reset_for_tests()

    ctx = nlp.MessageContext(
        guild_id=1,
        channel_id=555,
        category_id=200,
        user_id=99,
        user_level=5,
        user_role_ids=(),
        is_mention=False,
        is_fresh_user=False,
    )
    live = await nlp.resolve(ctx)
    dry = await nlp.resolve(ctx, dry_run=True)

    # Same decision both ways.
    assert live.allowed is True and dry.allowed is True
    assert live.reason_code is dry.reason_code is PolicyDenialReason.NONE
    assert live.effective_min_level == dry.effective_min_level == 0
    assert live.effective_cooldown == dry.effective_cooldown == 10
    assert live.effective_mode == dry.effective_mode == "always_reply"
    assert live.effective_source == dry.effective_source == "channel"
    # Only the trace differs.
    assert live.precedence_trace == ()
    assert any(
        "effective_policy: source=channel" in step for step in dry.precedence_trace
    )
    nlp._reset_for_tests()
