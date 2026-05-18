"""Unit tests for ``_PlatformHubView`` — the !platform admin panel.

The view is the read-only hub opened by ``!platform`` with no
subcommand.  These tests cover:

- the overview embed structure;
- the view shape (4 category Selects + 1 Overview button);
- Select option coverage of every grouped subcommand;
- ``_dispatch`` mapping each Select value to its existing builder;
- sessions DB-failure rendering as a red embed (no plain-text path);
- the Overview button returning to the overview embed;
- the canonical invoker-restriction contract from ``BaseView``.

All embeds returned by the panel are produced by the existing
builders in ``cogs.diagnostic._platform_embeds``, so any change in
typed-command rendering propagates to the panel automatically.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.diagnostic.platform_panel import (
    _CATALOGUES_OPTIONS,
    _RESOURCES_OPTIONS,
    _RUNTIME_OPTIONS,
    _VALIDATION_OPTIONS,
    _dispatch,
    _PlatformHubView,
    build_platform_hub_embed,
)


def _author(id_: int = 1) -> MagicMock:
    author = MagicMock()
    author.id = id_
    return author


# ---------------------------------------------------------------------------
# Overview embed
# ---------------------------------------------------------------------------


def test_overview_embed_has_title_and_four_category_fields():
    embed = build_platform_hub_embed()
    assert "Platform hub" in (embed.title or "")
    names = [f.name for f in embed.fields]
    assert names == [
        "Runtime / status",
        "Catalogues",
        "Resources / rollout",
        "Validation",
    ]


def test_overview_embed_describes_read_only_intent():
    embed = build_platform_hub_embed()
    assert "Read-only" in (embed.description or "")


def test_overview_embed_footer_mentions_typed_commands():
    embed = build_platform_hub_embed()
    assert embed.footer is not None
    assert "!platform" in (embed.footer.text or "")


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_view_has_four_selects_and_one_button():
    view = _PlatformHubView(_author())
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 4
    assert len(buttons) == 1
    assert len(view.children) == 5


def test_view_selects_fit_within_discord_row_budget():
    view = _PlatformHubView(_author())
    rows = {c.row for c in view.children}
    # Discord allows rows 0-4 (5 total); 4 selects + 1 button must each
    # claim a unique row so the panel renders without overflow.
    assert rows == {0, 1, 2, 3, 4}


def test_view_select_option_counts_match_category_inventories():
    view = _PlatformHubView(_author())
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    options_by_row = {c.row: c.options for c in selects}
    assert len(options_by_row[0]) == len(_RUNTIME_OPTIONS)
    assert len(options_by_row[1]) == len(_CATALOGUES_OPTIONS)
    assert len(options_by_row[2]) == len(_RESOURCES_OPTIONS)
    assert len(options_by_row[3]) == len(_VALIDATION_OPTIONS)


def test_select_values_cover_every_platform_subcommand():
    view = _PlatformHubView(_author())
    seen: set[str] = set()
    for select in view.children:
        if isinstance(select, discord.ui.Select):
            for opt in select.options:
                seen.add(opt.value)
    expected = {
        # Runtime / status
        "status",
        "runtime",
        "caches",
        "locks",
        "tasks",
        "views",
        "sessions",
        "slow",
        # Catalogues
        "schemas",
        "settings-registry",
        "customization",
        "provisioning",
        "participation-schemas",
        "resource-requirements",
        # Resources / rollout
        "resources",
        "bindings",
        "flags",
        "migrations",
        # Validation
        "identity",
        "consistency",
        "anchors",
    }
    assert seen == expected, seen.symmetric_difference(expected)


def test_overview_button_is_on_last_row_and_secondary_style():
    view = _PlatformHubView(_author())
    button = next(c for c in view.children if isinstance(c, discord.ui.Button))
    assert button.row == 4
    assert button.style == discord.ButtonStyle.secondary
    assert button.label is not None
    assert "Overview" in button.label


# ---------------------------------------------------------------------------
# Dispatch — synchronous builders
# ---------------------------------------------------------------------------


def _fake_interaction(bot: object = None, guild: object = None) -> MagicMock:
    interaction = MagicMock()
    interaction.client = bot or MagicMock()
    interaction.guild = guild
    return interaction


@pytest.mark.asyncio
async def test_dispatch_status_uses_status_builder():
    interaction = _fake_interaction(bot=MagicMock(spec=discord.Client))
    interaction.client.uptime = None
    interaction.client.guilds = []
    interaction.client.cogs = {}
    with patch(
        "views.diagnostic.platform_panel.build_status_embed",
        return_value=discord.Embed(title="status-ok"),
    ) as builder:
        embed = await _dispatch("status", interaction)
    builder.assert_called_once_with(interaction.client)
    assert embed.title == "status-ok"


@pytest.mark.asyncio
async def test_dispatch_runtime_uses_runtime_builder():
    interaction = _fake_interaction()
    with patch(
        "views.diagnostic.platform_panel.build_runtime_embed",
        return_value=discord.Embed(title="rt"),
    ) as builder:
        embed = await _dispatch("runtime", interaction)
    builder.assert_called_once_with()
    assert embed.title == "rt"


@pytest.mark.asyncio
async def test_dispatch_locks_passes_empty_prefix():
    interaction = _fake_interaction()
    with patch(
        "views.diagnostic.platform_panel.build_locks_embed",
        return_value=discord.Embed(title="locks"),
    ) as builder:
        await _dispatch("locks", interaction)
    builder.assert_called_once_with()


@pytest.mark.asyncio
async def test_dispatch_slow_passes_default_limit():
    interaction = _fake_interaction()
    with patch(
        "views.diagnostic.platform_panel.build_slow_embed",
        return_value=discord.Embed(title="slow"),
    ) as builder:
        await _dispatch("slow", interaction)
    builder.assert_called_once_with()


# ---------------------------------------------------------------------------
# Dispatch — async + DB-backed builders
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_sessions_success_returns_embed():
    interaction = _fake_interaction()
    success_embed = discord.Embed(title="🎫 Active sessions")
    with patch(
        "views.diagnostic.platform_panel.build_sessions_embed",
        new_callable=AsyncMock,
        return_value=(success_embed, None),
    ) as builder:
        embed = await _dispatch("sessions", interaction)
    builder.assert_awaited_once_with()
    assert embed.title == "🎫 Active sessions"


@pytest.mark.asyncio
async def test_dispatch_sessions_failure_returns_red_embed():
    """DB failure must surface as a red embed (typed command's plain-text
    fallback would break in-place panel editing)."""
    interaction = _fake_interaction()
    with patch(
        "views.diagnostic.platform_panel.build_sessions_embed",
        new_callable=AsyncMock,
        return_value=(None, "❌ DB query failed: boom"),
    ):
        embed = await _dispatch("sessions", interaction)
    assert "Active sessions" in (embed.title or "")
    assert embed.color == discord.Color.red()
    assert "DB query failed" in (embed.description or "")


@pytest.mark.asyncio
async def test_dispatch_flags_passes_guild_through():
    guild = MagicMock()
    interaction = _fake_interaction(guild=guild)
    with patch(
        "views.diagnostic.platform_panel.build_flags_embed",
        new_callable=AsyncMock,
        return_value=discord.Embed(title="flags"),
    ) as builder:
        await _dispatch("flags", interaction)
    builder.assert_awaited_once_with(guild)


@pytest.mark.asyncio
async def test_dispatch_identity_runs_without_fix_mode():
    """The panel never triggers self-healing; identity always runs in
    read-only mode there (typed `!platform identity --fix` is the only
    way to trigger healing)."""
    interaction = _fake_interaction(bot=MagicMock(spec=discord.Client))
    with patch(
        "views.diagnostic.platform_panel.build_identity_embed",
        new_callable=AsyncMock,
        return_value=discord.Embed(title="identity"),
    ) as builder:
        await _dispatch("identity", interaction)
    # No second positional arg → mode defaults to "" (no --fix).
    builder.assert_awaited_once_with(interaction.client)


@pytest.mark.asyncio
async def test_dispatch_consistency_uses_collect_report():
    interaction = _fake_interaction(
        bot=MagicMock(spec=discord.Client),
        guild=MagicMock(),
    )
    fake_report = MagicMock()
    with patch(
        "services.platform_consistency.collect_report",
        new_callable=AsyncMock,
        return_value=fake_report,
    ) as collector, patch(
        "views.diagnostic.platform_panel.build_consistency_embed",
        return_value=discord.Embed(title="consistency"),
    ) as builder:
        embed = await _dispatch("consistency", interaction)
    collector.assert_awaited_once_with(bot=interaction.client, guild=interaction.guild)
    builder.assert_called_once_with(fake_report)
    assert embed.title == "consistency"


@pytest.mark.asyncio
async def test_dispatch_unknown_returns_error_embed():
    """Defensive: unknown values surface as a visible red embed rather
    than raising and breaking the panel."""
    interaction = _fake_interaction()
    embed = await _dispatch("not_a_real_surface", interaction)
    assert embed.color == discord.Color.red()
    assert "Unknown" in (embed.title or "")


# ---------------------------------------------------------------------------
# Invoker restriction (canonical BaseView contract)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invoker_check_rejects_other_users():
    view = _PlatformHubView(_author(id_=42))
    interaction = MagicMock()
    interaction.user.id = 99
    interaction.response.send_message = AsyncMock()
    result = await view.interaction_check(interaction)
    assert result is False
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_invoker_check_accepts_author():
    view = _PlatformHubView(_author(id_=42))
    interaction = MagicMock()
    interaction.user.id = 42
    result = await view.interaction_check(interaction)
    assert result is True
