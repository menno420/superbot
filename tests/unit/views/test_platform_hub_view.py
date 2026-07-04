"""Unit tests for ``_PlatformHubView`` — the !platform admin panel.

The view is the hub opened by ``!platform`` with no subcommand.
These tests cover:

- the overview embed structure (4 read-only sections + 1 mutations section);
- the view shape (4 category Selects on rows 0-3 + buttons on row 4);
- Select option coverage of every grouped read-only subcommand;
- ``_dispatch`` mapping each Select value to its existing builder;
- sessions DB-failure rendering as a red embed (no plain-text path);
- the Overview button returning to the overview embed;
- the Flag-manager button opening the editable manager;
- the canonical invoker-restriction contract from ``BaseView``.

All embeds returned by the panel are produced by the existing
builders in ``cogs.diagnostic._platform_embeds``, so any change in
typed-command rendering propagates to the panel automatically.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.ext import commands

from views.diagnostic.platform_panel import (
    _CATALOGUES_OPTIONS,
    _MUTATION_BUTTONS,
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


def test_overview_embed_has_title_and_five_section_fields():
    embed = build_platform_hub_embed()
    assert "Platform hub" in (embed.title or "")
    names = [f.name for f in embed.fields]
    assert names == [
        "Runtime / status",
        "Catalogues",
        "Resources / rollout",
        "Validation",
        "Mutations / managers",
    ]


def test_overview_embed_separates_readonly_from_mutations():
    embed = build_platform_hub_embed()
    description = embed.description or ""
    assert "read-only" in description.lower()
    assert "Mutations" in description


def test_overview_embed_footer_mentions_typed_commands():
    embed = build_platform_hub_embed()
    assert embed.footer is not None
    assert "!platform" in (embed.footer.text or "")


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_view_has_four_selects_overview_and_mutation_buttons():
    view = _PlatformHubView(_author())
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 4
    # One Overview button + one button per mutation entry.
    assert len(buttons) == 1 + len(_MUTATION_BUTTONS)


def test_view_selects_fit_within_discord_row_budget():
    view = _PlatformHubView(_author())
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    # Discord allows rows 0-4 (5 total); 4 selects must each claim a
    # unique row (0-3) and all buttons share the bottom row 4.
    assert {c.row for c in selects} == {0, 1, 2, 3}
    assert {c.row for c in buttons} == {4}


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
        "health",
        "startup",
        "findings",
        "status",
        "runtime",
        "lifecycle",
        "caches",
        "media",
        "locks",
        "tasks",
        "views",
        "sessions",
        "slow",
        "automation",
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
        "setup-readiness",
    }
    assert seen == expected, seen.symmetric_difference(expected)


def test_finding_mutation_is_excluded_from_readonly_hub():
    """The ``finding`` *lifecycle mutation* must never appear in the read-only
    category Selects — the only write surface is the segregated Mutations row.

    ``startup``/``findings`` (both read-only reports) were grouped into
    Runtime/status on 2026-06-30 (diagnostic completion cert punch #1), so they
    are no longer excluded; this test now pins only the mutation exclusion. If a
    future session changes what is grouped, update both this test and the module
    docstring together.
    """
    view = _PlatformHubView(_author())
    grouped = {
        opt.value
        for child in view.children
        if isinstance(child, discord.ui.Select)
        for opt in child.options
    }
    assert "finding" not in grouped, (
        "the `finding` lifecycle mutation leaked into the read-only hub: "
        f"{grouped}"
    )
    # The read-only health reports are now intentionally reachable.
    assert {"startup", "findings"} <= grouped


def test_overview_button_is_on_last_row_and_secondary_style():
    view = _PlatformHubView(_author())
    overview = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and (c.label or "").endswith("Overview")
    )
    assert overview.row == 4
    assert overview.style == discord.ButtonStyle.secondary


def test_flag_manager_button_is_primary_on_last_row():
    view = _PlatformHubView(_author())
    flag_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and "Flag manager" in (c.label or "")
    )
    assert flag_btn.row == 4
    assert flag_btn.style == discord.ButtonStyle.primary
    assert flag_btn.custom_id == "platform_hub.flag_manager"


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
    interaction = _fake_interaction(bot=MagicMock(spec=commands.Bot))
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
async def test_dispatch_lifecycle_uses_lifecycle_builder():
    interaction = _fake_interaction()
    with patch(
        "views.diagnostic.platform_panel.build_lifecycle_embed",
        return_value=discord.Embed(title="lc"),
    ) as builder:
        embed = await _dispatch("lifecycle", interaction)
    builder.assert_called_once_with()
    assert embed.title == "lc"


@pytest.mark.asyncio
async def test_dispatch_setup_readiness_passes_guild_and_id():
    guild = MagicMock()
    guild.id = 4242
    interaction = _fake_interaction(guild=guild)
    with patch(
        "views.diagnostic.platform_panel.build_setup_readiness_embed",
        new_callable=AsyncMock,
        return_value=discord.Embed(title="setup"),
    ) as builder:
        embed = await _dispatch("setup-readiness", interaction)
    builder.assert_awaited_once_with(4242, guild=guild)
    assert embed.title == "setup"


@pytest.mark.asyncio
async def test_dispatch_setup_readiness_falls_back_to_zero_in_dm():
    interaction = _fake_interaction(guild=None)
    with patch(
        "views.diagnostic.platform_panel.build_setup_readiness_embed",
        new_callable=AsyncMock,
        return_value=discord.Embed(title="setup-dm"),
    ) as builder:
        await _dispatch("setup-readiness", interaction)
    builder.assert_awaited_once_with(0, guild=None)


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
    fallback would break in-place panel editing).
    """
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
    way to trigger healing).
    """
    interaction = _fake_interaction(bot=MagicMock(spec=commands.Bot))
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
        bot=MagicMock(spec=commands.Bot),
        guild=MagicMock(),
    )
    fake_report = MagicMock()
    with (
        patch(
            "services.platform_consistency.collect_report",
            new_callable=AsyncMock,
            return_value=fake_report,
        ) as collector,
        patch(
            "views.diagnostic.platform_panel.build_consistency_embed",
            return_value=discord.Embed(title="consistency"),
        ) as builder,
    ):
        embed = await _dispatch("consistency", interaction)
    collector.assert_awaited_once_with(bot=interaction.client, guild=interaction.guild)
    builder.assert_called_once_with(fake_report)
    assert embed.title == "consistency"


@pytest.mark.asyncio
async def test_dispatch_startup_prefers_stored_snapshot_projected_to_audience():
    """The hub mirrors `!platform startup`: a stored settled snapshot is
    re-projected to the caller's audience (no fresh collection)."""
    guild = MagicMock()
    guild.id = 7
    interaction = _fake_interaction(bot=MagicMock(spec=commands.Bot), guild=guild)
    interaction.user = MagicMock()
    stored = MagicMock()
    projected = MagicMock()
    with (
        patch(
            "services.health_snapshot_service.resolve_audience",
            new_callable=AsyncMock,
            return_value="admin",
        ),
        patch(
            "services.health_snapshot_service.get_last_startup_snapshot",
            return_value=stored,
        ),
        patch(
            "services.health_snapshot_service.project_for_audience",
            return_value=projected,
        ) as projector,
        patch(
            "services.health_snapshot_service.collect_snapshot",
            new_callable=AsyncMock,
        ) as collector,
        patch(
            "views.diagnostic.platform_panel.build_startup_health_embed",
            return_value=discord.Embed(title="🚀 Startup health"),
        ) as builder,
    ):
        embed = await _dispatch("startup", interaction)
    projector.assert_called_once_with(stored, "admin")
    collector.assert_not_awaited()  # stored snapshot → no fresh collection
    builder.assert_called_once_with(projected)
    assert "Startup health" in (embed.title or "")


@pytest.mark.asyncio
async def test_dispatch_findings_lists_open_with_audience_redaction():
    """The hub mirrors `!platform findings` defaulting to the open status;
    owner detail is gated on the resolved audience."""
    from services.health_contracts import HealthAudience

    guild = MagicMock()
    interaction = _fake_interaction(bot=MagicMock(spec=commands.Bot), guild=guild)
    interaction.user = MagicMock()
    rows = [{"category": "db", "message": "x", "status": "open"}]
    with (
        patch(
            "services.health_snapshot_service.resolve_audience",
            new_callable=AsyncMock,
            return_value=HealthAudience.GUILD_ADMIN,
        ),
        patch(
            "services.health_findings_service.list_by_status",
            new_callable=AsyncMock,
            return_value=rows,
        ) as lister,
        patch(
            "services.health_findings_service.count_by_status",
            new_callable=AsyncMock,
            return_value={"open": 1},
        ),
        patch(
            "views.diagnostic.platform_panel.build_findings_embed",
            return_value=discord.Embed(title="🩺 Health findings — open"),
        ) as builder,
    ):
        embed = await _dispatch("findings", interaction)
    lister.assert_awaited_once_with("open", limit=15)
    builder.assert_called_once_with(rows, status="open", counts={"open": 1}, is_owner=False)
    assert "Health findings" in (embed.title or "")


@pytest.mark.asyncio
async def test_dispatch_unknown_returns_error_embed():
    """Defensive: unknown values surface as a visible red embed rather
    than raising and breaking the panel.
    """
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
