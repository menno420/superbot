"""Unit tests for :class:`AccessExplorerView` (Phase 6).

Covers:

* Overview embed renders with the invoker, subsystem placeholder,
  and scope placeholder.
* Constructed view exposes exactly the expected components (one
  subsystem select, one scope select, Explain + Reset buttons).
* The subsystem select only lists subsystems the invoker can see —
  the read-only explorer must not leak policies the invoker is not
  authorised to inspect.
* Scope select cycles between channel/category/guild.
* Explain button before subsystem selection sends an ephemeral and
  does not call governance.
* Explain button after selection routes through
  ``governance.resolve_subsystem_state`` and renders the decision
  chain in the embed.
* Explain handles a governance-resolution exception by surfacing an
  ephemeral fallback (no message edit, no crash).
* Reset clears the selected subsystem and restores the placeholder
  scope label.

The view never mutates governance state — these tests pin that
contract.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from utils.subsystem_registry import SUBSYSTEMS
from views.access.explorer import (
    _SCOPE_LABELS,
    AccessExplorerView,
    _build_context_for_scope,
    _resolve_default_subsystem_options,
    build_explanation_embed,
    build_explorer_overview_embed,
)


def _author(id_: int = 7) -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.id = id_
    member.display_name = "Test Admin"
    member.mention = f"<@{id_}>"
    return member


def _visible_all() -> set[str]:
    return set(SUBSYSTEMS.keys())


# ---------------------------------------------------------------------------
# Subsystem options + tier filtering
# ---------------------------------------------------------------------------


def test_subsystem_options_excludes_invisible_subsystems():
    visible_subset = {"settings", "logging"}
    options = _resolve_default_subsystem_options(visible_subset)
    values = {o.value for o in options}
    assert values == visible_subset


def test_subsystem_options_are_not_front_truncated():
    # Lane A2: the subsystem select is now windowed (◀/▶ nav), so the option
    # builder no longer front-truncates at Discord's 25 cap — it returns one
    # option per *real* visible subsystem (fake names aren't in the registry).
    options = _resolve_default_subsystem_options(set(SUBSYSTEMS))
    assert len(options) == len(SUBSYSTEMS)
    # More than the 25 cap is fine now — windowing reaches the tail.
    assert len(options) > 25


def test_subsystem_options_carries_emoji_and_description():
    options = _resolve_default_subsystem_options({"settings"})
    assert len(options) == 1
    only = options[0]
    meta = SUBSYSTEMS["settings"]
    if meta.get("emoji"):
        actual_emoji = (
            only.emoji.name if only.emoji is not None else None
        )
        assert actual_emoji == meta["emoji"]
    if meta.get("description"):
        assert only.description == meta["description"][:100]


# ---------------------------------------------------------------------------
# Overview embed
# ---------------------------------------------------------------------------


def test_overview_embed_lists_subsystem_and_scope_placeholders():
    embed = build_explorer_overview_embed(_author())
    field_names = [f.name for f in embed.fields]
    assert "Subsystem" in field_names
    assert "Scope" in field_names


def test_overview_embed_mentions_read_only_intent():
    embed = build_explorer_overview_embed(_author())
    text = (embed.description or "") + (embed.footer.text or "")
    assert "read-only" in text.lower() or "diagnostic" in text.lower()


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_view_has_two_selects_and_explain_reset_buttons():
    view = AccessExplorerView(_author(), visible_subsystems=_visible_all())
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    # Subsystem (windowed) select + scope select.  Windowing keeps the visible
    # select count at one per band regardless of how many subsystems there are.
    assert len(selects) == 2
    # The action buttons remain (windowed ◀/▶ nav buttons may also be present
    # when the subsystem list spans >25, so assert by custom_id, not count).
    button_ids = {
        c.custom_id  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    assert {"access:explain", "access:reset"} <= button_ids


def test_view_action_buttons_use_recognisable_custom_ids():
    view = AccessExplorerView(_author(), visible_subsystems=_visible_all())
    # The windowed nav buttons carry an auto-generated custom_id; the action
    # buttons use the stable ``access:*`` ids.
    button_ids = {
        c.custom_id  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and (c.custom_id or "").startswith("access:")
    }
    assert button_ids == {"access:explain", "access:reset"}


def test_view_initial_scope_defaults_to_channel():
    view = AccessExplorerView(_author(), visible_subsystems=_visible_all())
    assert view.selected_scope == "channel"
    assert view.selected_subsystem is None


# ---------------------------------------------------------------------------
# Explain button
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_explain_without_selection_sends_ephemeral():
    view = AccessExplorerView(_author(), visible_subsystems=_visible_all())
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "access:explain"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_explain_invisible_subsystem_blocks_explanation():
    """Mid-session governance may shrink visible_subsystems. The explain
    handler must re-check against the original visible set so an admin
    can't trick the explorer by mutating ``selected_subsystem``.
    """
    view = AccessExplorerView(_author(), visible_subsystems={"settings"})
    view.selected_subsystem = "moderation"  # not in the visible set

    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "access:explain"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_explain_routes_through_resolve_subsystem_state():
    view = AccessExplorerView(_author(), visible_subsystems=_visible_all())
    view.selected_subsystem = "settings"
    view.selected_scope = "guild"

    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild = MagicMock()
    interaction.guild_id = 42
    interaction.channel = MagicMock()
    interaction.user = view._author
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()

    fake_effective = MagicMock()
    fake_effective.state = MagicMock()
    fake_effective.state.value = "enabled"
    fake_effective.visibility_source = MagicMock()
    fake_effective.visibility_source.value = "registry_default"
    fake_effective.dependency_blocks = []
    fake_trace = MagicMock()
    fake_trace.checked_scopes = ["guild", "category", "channel"]
    fake_trace.matched_scope = None
    fake_effective.trace = fake_trace

    with patch(
        "governance.resolve_subsystem_state",
        AsyncMock(return_value=fake_effective),
    ) as fake_resolve:
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and c.custom_id == "access:explain"
        )
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    fake_resolve.assert_awaited_once()
    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    embed: discord.Embed = kwargs["embed"]
    rendered = (embed.title or "") + (embed.description or "")
    assert "Settings Manager" in rendered
    assert "enabled" in rendered.lower()


@pytest.mark.asyncio
async def test_explain_governance_failure_sends_ephemeral():
    view = AccessExplorerView(_author(), visible_subsystems=_visible_all())
    view.selected_subsystem = "settings"

    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild = MagicMock()
    interaction.guild_id = 42
    interaction.channel = MagicMock()
    interaction.user = view._author
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    with patch(
        "governance.resolve_subsystem_state",
        AsyncMock(side_effect=RuntimeError("governance unavailable")),
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and c.custom_id == "access:explain"
        )
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


# ---------------------------------------------------------------------------
# Reset button
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reset_clears_state():
    view = AccessExplorerView(_author(), visible_subsystems=_visible_all())
    view.selected_subsystem = "moderation"
    view.selected_scope = "guild"

    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()

    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "access:reset"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]

    assert view.selected_subsystem is None
    assert view.selected_scope == "channel"
    interaction.response.edit_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# Scope-context builder
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_context_for_scope_guild_drops_channel_and_category():
    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild_id = 100
    interaction.channel = MagicMock()
    interaction.channel.id = 200
    interaction.channel.category_id = 300
    # Not a thread.
    interaction.user = MagicMock(spec=discord.Member)
    interaction.user.roles = []

    with patch(
        "governance.models.GovernanceContext.from_interaction",
    ) as fake_from:
        from governance.models import GovernanceContext

        fake_from.return_value = GovernanceContext(
            guild_id=100,
            channel_id=200,
            category_id=300,
            thread_id=None,
            member=None,
            role_ids=set(),
        )
        ctx = await _build_context_for_scope(interaction, "guild")

    assert ctx.channel_id is None
    assert ctx.category_id is None
    assert ctx.guild_id == 100


@pytest.mark.asyncio
async def test_build_context_for_scope_category_drops_only_channel():
    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild_id = 100
    interaction.user = MagicMock(spec=discord.Member)
    interaction.user.roles = []

    with patch(
        "governance.models.GovernanceContext.from_interaction",
    ) as fake_from:
        from governance.models import GovernanceContext

        fake_from.return_value = GovernanceContext(
            guild_id=100,
            channel_id=200,
            category_id=300,
            thread_id=None,
            member=None,
            role_ids=set(),
        )
        ctx = await _build_context_for_scope(interaction, "category")

    assert ctx.channel_id is None
    assert ctx.category_id == 300


# ---------------------------------------------------------------------------
# Explanation embed
# ---------------------------------------------------------------------------


def test_explanation_embed_includes_required_tier_and_visibility_mode():
    fake_effective = MagicMock()
    fake_effective.state = MagicMock(value="enabled")
    fake_effective.visibility_source = MagicMock(value="guild")
    fake_effective.dependency_blocks = []
    fake_effective.trace = MagicMock(
        checked_scopes=["guild"],
        matched_scope=MagicMock(value="guild"),
    )
    embed = build_explanation_embed(
        invoker=_author(),
        subsystem="settings",
        scope="guild",
        effective=fake_effective,
    )
    field_names = [f.name for f in embed.fields]
    assert "Required tier" in field_names
    assert "Visibility mode" in field_names
    assert "Decision source" in field_names
    assert "Scopes inspected" in field_names


def test_scope_labels_cover_three_scopes():
    assert set(_SCOPE_LABELS) == {"channel", "category", "guild"}
