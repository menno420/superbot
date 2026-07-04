"""Unified BTD6 command tree — one ``/btd6`` (and ``!btd6``) for everything.

Owner request (2026-06-24): collapse the five separate BTD6 command groups
(``btd6`` / ``btd6ref`` / ``btd6ops`` / ``btd6strat`` / ``btd6events``) into a
single ``/btd6`` so users no longer have to remember which prefix owns which
action. The maintainer picked the **"Flattest"** layout:

* everyday lookups sit **flat**: ``/btd6 income``, ``/btd6 round``, ``/btd6 rbe``,
  ``/btd6 tower``, ``/btd6 hero``, ``/btd6 relic``, ``/btd6 ct``, ``/btd6 ask``,
  ``/btd6 status``, ``/btd6 diagnostics``, ``/btd6 test-intent`` (+ ``ctteam``
  on the prefix surface only);
* the bigger buckets **nest** one level: ``/btd6 strat …`` (strategy memory),
  ``/btd6 ops …`` (ingestion ops), ``/btd6 events …`` (live events).

Discord allows a top-level command to mix flat subcommands with nested
subcommand-groups (max 25 per level, one level of nesting), so this is valid.

**Why a module-level tree, not a cog.** discord.py can't cleanly share one
``app_commands.Group`` across multiple cogs, and folding 33 actions into a
single ``*_cog.py`` would blow the 800-LOC ceiling. Defining the tree at module
level (registered once by the mother :mod:`cogs.btd6_cog`) is the supported
pattern and keeps every ``*_cog.py`` small. Handlers stay **thin** — they
delegate to the existing :mod:`cogs.btd6._builders` / services, so the verified
numbers and gating logic are unchanged; only the command *path* moves.

The old ``!btd6ref`` / ``!btd6ops`` / … **prefix** groups remain as hidden
aliases (in their original cogs) so existing muscle-memory keeps working; the
old **slash** groups are removed in favour of this tree.

Subcommand caveat (Discord limitation): ``guild_only`` / ``default_permissions``
only take effect on a *top-level* command, not on subcommands. The ops actions
therefore can't hide themselves from non-staff via the picker — but every ops
handler re-checks ``is_staff_member`` / ``is_administrator_member`` inline (the
same defense-in-depth the standalone cog used), so this is a UI-hint change
only, never a privilege change.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs.btd6 import _builders, _event_helpers, _ops_helpers
from cogs.btd6._embeds import (
    build_diagnostics_embed,
    build_status_embed,
    build_test_intent_embed,
)
from cogs.btd6._embeds import response_to_embed as _response_to_embed
from cogs.btd6._reply import reply_ephemeral
from core.runtime.interaction_helpers import safe_defer, safe_followup
from core.runtime.permission_checks import perms_or_owner
from services import btd6_ai_service
from utils.discord_permissions import is_administrator_member, is_staff_member
from views.btd6 import strategy_browse
from views.btd6.panel import BTD6PanelView, build_btd6_panel_embed

logger = logging.getLogger("bot.cogs.btd6")


# ===========================================================================
# Root groups
# ===========================================================================

btd6_app = app_commands.Group(
    name="btd6",
    description="BTD6 Assistant — lookups, strategy, live events, and ops.",
)


@commands.group(name="btd6", invoke_without_command=True)
async def btd6_prefix(ctx: commands.Context) -> None:
    """BTD6 Assistant — open the panel, or run a subcommand (income/round/…)."""
    await ctx.send(embed=await build_btd6_panel_embed(), view=BTD6PanelView())


# ===========================================================================
# Flat lookups — the everyday commands
# ===========================================================================

# --- income ----------------------------------------------------------------


@btd6_app.command(
    name="income",
    description="Verified cash earned per round (single round or a range).",
)
@app_commands.describe(
    start_round="The round (or first round of a range).",
    end_round="Last round of an inclusive range (omit for a single round).",
    roundset="Round set: 'default' (standard) or 'abr' (alternate).",
)
async def income_slash(
    interaction: discord.Interaction,
    start_round: int,
    end_round: int | None = None,
    roundset: str = "default",
) -> None:
    embed = await _builders.build_income_embed(start_round, end_round, roundset)
    await interaction.response.send_message(embed=embed)


@btd6_prefix.command(name="income")  # type: ignore[arg-type]
async def income_prefix(
    ctx: commands.Context,
    start_round: int,
    end_round: int | None = None,
) -> None:
    """Verified cash per round — single round or an inclusive range."""
    await ctx.send(embed=await _builders.build_income_embed(start_round, end_round))


# --- rbe -------------------------------------------------------------------


@btd6_app.command(
    name="rbe",
    description="RBE per round — base + freeplay-scaled (single round or a range).",
)
@app_commands.describe(
    start_round="The round (or first round of a range).",
    end_round="Last round of an inclusive range (omit for a single round).",
)
async def rbe_slash(
    interaction: discord.Interaction,
    start_round: int,
    end_round: int | None = None,
) -> None:
    embed = await _builders.build_rbe_embed(start_round, end_round)
    await interaction.response.send_message(embed=embed)


@btd6_prefix.command(name="rbe")  # type: ignore[arg-type]
async def rbe_prefix(
    ctx: commands.Context,
    start_round: int,
    end_round: int | None = None,
) -> None:
    """RBE per round (base + freeplay-scaled) — single round or a range."""
    await ctx.send(embed=await _builders.build_rbe_embed(start_round, end_round))


# --- round -----------------------------------------------------------------


@btd6_app.command(
    name="round",
    description="Look up a round, or a values table across a range of rounds.",
)
@app_commands.describe(
    number="The round (or first round of a range).",
    end_round="Last round of an inclusive range (omit for a single round).",
)
async def round_slash(
    interaction: discord.Interaction,
    number: int,
    end_round: int | None = None,
) -> None:
    embed = await _builders.build_round_embed(number, end_round)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@btd6_prefix.command(name="round")  # type: ignore[arg-type]
async def round_prefix(
    ctx: commands.Context,
    number: int,
    end_round: int | None = None,
) -> None:
    """A single round's detail, or a values table across a round range."""
    await ctx.send(embed=await _builders.build_round_embed(number, end_round))


# --- tower -----------------------------------------------------------------


@btd6_app.command(name="tower", description="Look up a tower.")
async def tower_slash(interaction: discord.Interaction, name: str) -> None:
    await reply_ephemeral(interaction, _builders.build_tower_embed(name))


@btd6_prefix.command(name="tower")  # type: ignore[arg-type]
async def tower_prefix(ctx: commands.Context, *, name: str) -> None:
    await ctx.send(embed=await _builders.build_tower_embed(name))


# --- estimate --------------------------------------------------------------


@btd6_app.command(
    name="estimate",
    description="Estimate a boss fight from HP/DPS/cost (tower vs boss, or counters).",
)
@app_commands.describe(
    query="e.g. 'super monkey 0-4-0 vs bloonarius t5' or 'counters bloonarius'",
)
async def estimate_slash(interaction: discord.Interaction, query: str) -> None:
    await reply_ephemeral(interaction, _builders.build_estimate_embed(query))


@btd6_prefix.command(name="estimate")  # type: ignore[arg-type]
async def estimate_prefix(ctx: commands.Context, *, query: str = "") -> None:
    """Estimate a boss fight: `<tower> vs <boss> [tier]`, or `counters <boss>`."""
    await ctx.send(embed=await _builders.build_estimate_embed(query))


# --- hero ------------------------------------------------------------------


@btd6_app.command(name="hero", description="Look up a hero.")
async def hero_slash(interaction: discord.Interaction, name: str) -> None:
    if not await safe_defer(interaction, ephemeral=True):
        return
    embed = await _builders.build_hero_embed(name)
    await safe_followup(interaction, embed=embed, ephemeral=True)


@btd6_prefix.command(name="hero")  # type: ignore[arg-type]
async def hero_prefix(ctx: commands.Context, *, name: str) -> None:
    await ctx.send(embed=await _builders.build_hero_embed(name))


# --- relic -----------------------------------------------------------------


@btd6_app.command(
    name="relic",
    description="Look up a Contested Territory relic's effect and tile.",
)
async def relic_slash(interaction: discord.Interaction, name: str) -> None:
    await reply_ephemeral(interaction, _builders.build_ct_relic_embed(name))


@btd6_prefix.command(name="relic")  # type: ignore[arg-type]
async def relic_prefix(ctx: commands.Context, *, name: str) -> None:
    """CT relic effect + current tile (by name / abbrev e.g. SMS / alias)."""
    await ctx.send(embed=await _builders.build_ct_relic_embed(name))


# --- ct --------------------------------------------------------------------


@btd6_app.command(
    name="ct",
    description="Browse active Contested Territory events and relic tiles.",
)
async def ct_slash(interaction: discord.Interaction) -> None:
    await reply_ephemeral(interaction, _builders.build_ct_browser_embed())


@btd6_prefix.command(name="ct")  # type: ignore[arg-type]
async def ct_prefix(ctx: commands.Context) -> None:
    """Browse active Contested Territory events and their relic tiles."""
    await ctx.send(embed=await _builders.build_ct_browser_embed())


# --- ask -------------------------------------------------------------------


@btd6_app.command(name="ask", description="Ask a BTD6 question.")
async def ask_slash(interaction: discord.Interaction, question: str) -> None:
    if not await safe_defer(interaction, ephemeral=True):
        return
    response = await btd6_ai_service.answer_question(question)
    await safe_followup(
        interaction,
        embed=_response_to_embed(response),
        ephemeral=True,
    )


@btd6_prefix.command(name="ask")  # type: ignore[arg-type]
async def ask_prefix(ctx: commands.Context, *, question: str) -> None:
    """Deterministic Q&A (with optional AI augmentation)."""
    response = await btd6_ai_service.answer_question(question)
    await ctx.send(embed=_response_to_embed(response))


# --- status ----------------------------------------------------------------


@btd6_app.command(name="status", description="BTD6 assistant status.")
async def status_slash(interaction: discord.Interaction) -> None:
    await reply_ephemeral(interaction, build_status_embed())


@btd6_prefix.command(name="status")  # type: ignore[arg-type]
async def status_prefix(ctx: commands.Context) -> None:
    await ctx.send(embed=await build_status_embed())


# --- diagnostics -----------------------------------------------------------


@btd6_app.command(name="diagnostics", description="BTD6 dataset diagnostics.")
async def diagnostics_slash(interaction: discord.Interaction) -> None:
    # Sync builder — safe to respond directly without defer.
    await interaction.response.send_message(
        embed=build_diagnostics_embed(),
        ephemeral=True,
    )


@btd6_prefix.command(name="diagnostics")  # type: ignore[arg-type]
async def diagnostics_prefix(ctx: commands.Context) -> None:
    await ctx.send(embed=build_diagnostics_embed())


# --- test-intent -----------------------------------------------------------


@btd6_app.command(
    name="test-intent",
    description="Show what the resolver extracted from a message.",
)
async def test_intent_slash(interaction: discord.Interaction, text: str) -> None:
    # Sync resolver work — safe to respond directly without defer.
    await interaction.response.send_message(
        embed=build_test_intent_embed(text),
        ephemeral=True,
    )


@btd6_prefix.command(name="test-intent")  # type: ignore[arg-type]
async def test_intent_prefix(ctx: commands.Context, *, text: str) -> None:
    await ctx.send(embed=build_test_intent_embed(text))


# --- ctteam (prefix-only: pasting a long bracket URL suits the prefix surface)


@btd6_prefix.command(name="ctteam")  # type: ignore[arg-type]
async def ctteam_prefix(ctx: commands.Context, *, arg: str = "") -> None:
    """View or set this server's CT team (paste the bracket group id / URL)."""
    embed, view = await _builders.handle_ctteam(ctx, arg)
    if view is None:
        await ctx.send(embed=embed)
        return
    message = await ctx.send(embed=embed, view=view)
    view.message = message  # disable-on-timeout edits the right message


# ===========================================================================
# /btd6 strat … — strategy memory
# ===========================================================================

strat_app = app_commands.Group(
    name="strat",
    parent=btd6_app,
    description="BTD6 strategy memory — browse, submit, review.",
)


@btd6_prefix.group(name="strat", invoke_without_command=True)  # type: ignore[arg-type]
async def strat_prefix(ctx: commands.Context) -> None:
    """BTD6 strategy memory (browse / submit / review)."""
    await ctx.send_help(ctx.command)


@strat_app.command(name="browse", description="Browse published BTD6 strategies.")
async def strat_browse_slash(
    interaction: discord.Interaction,
    limit: int = 10,
) -> None:
    await reply_ephemeral(interaction, strategy_browse.build_browse_embed(limit=limit))


@strat_prefix.command(name="browse")  # type: ignore[arg-type]
async def strat_browse_prefix(ctx: commands.Context, limit: int = 10) -> None:
    """Browse published BTD6 strategies."""
    await ctx.send(embed=await strategy_browse.build_browse_embed(limit=limit))


@strat_app.command(
    name="mine",
    description="List my own strategy submissions in this guild.",
)
async def strat_mine_slash(
    interaction: discord.Interaction,
    limit: int = 10,
) -> None:
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command requires a guild context.",
            ephemeral=True,
        )
        return
    await reply_ephemeral(
        interaction,
        strategy_browse.build_mine_embed(
            interaction.guild.id,
            interaction.user.id,
            limit=limit,
        ),
    )


@strat_prefix.command(name="mine")  # type: ignore[arg-type]
async def strat_mine_prefix(ctx: commands.Context, limit: int = 10) -> None:
    """List my own strategy submissions in this guild."""
    if not ctx.guild:
        await ctx.send("This command requires a guild context.")
        return
    await ctx.send(
        embed=await strategy_browse.build_mine_embed(
            ctx.guild.id,
            ctx.author.id,
            limit=limit,
        ),
    )


@strat_app.command(name="strategy", description="Show one strategy in detail.")
async def strat_strategy_slash(
    interaction: discord.Interaction,
    strategy_id: int,
) -> None:
    viewer_guild = interaction.guild.id if interaction.guild else None
    await reply_ephemeral(
        interaction,
        strategy_browse.build_detail_embed(strategy_id, viewer_guild_id=viewer_guild),
    )


@strat_prefix.command(name="strategy")  # type: ignore[arg-type]
async def strat_strategy_prefix(ctx: commands.Context, strategy_id: int) -> None:
    """Show one strategy in detail."""
    viewer_guild = ctx.guild.id if ctx.guild else None
    payload = await strategy_browse.build_detail_embed(
        strategy_id,
        viewer_guild_id=viewer_guild,
    )
    if isinstance(payload, str):
        await ctx.send(payload)
    else:
        await ctx.send(embed=payload)


@strat_app.command(name="strategy-audit", description="Per-strategy audit log.")
async def strat_audit_slash(
    interaction: discord.Interaction,
    strategy_id: int,
) -> None:
    if not await safe_defer(interaction, ephemeral=True):
        return
    embed = await strategy_browse.build_audit_embed(strategy_id)
    await safe_followup(interaction, embed=embed, ephemeral=True)


@strat_prefix.command(name="strategy-audit")  # type: ignore[arg-type]
async def strat_audit_prefix(ctx: commands.Context, strategy_id: int) -> None:
    """Show the per-strategy audit log."""
    await ctx.send(embed=await strategy_browse.build_audit_embed(strategy_id))


@strat_app.command(name="submit", description="Submit a BTD6 strategy.")
async def strat_submit_slash(interaction: discord.Interaction) -> None:
    from views.btd6.strategy_submit import StrategySubmitModal

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Submitting a strategy requires a guild context.",
            ephemeral=True,
        )
        return
    await interaction.response.send_modal(StrategySubmitModal())


@strat_prefix.command(name="submit")  # type: ignore[arg-type]
async def strat_submit_prefix(ctx: commands.Context) -> None:
    """Open a strategy submission modal (slash-only on Discord)."""
    await ctx.send(
        "Strategy submission opens a Discord modal — use `/btd6 strat submit` "
        "to fill it in.",
    )


@strat_app.command(
    name="pending",
    description="List pending strategy submissions (staff-only).",
)
@app_commands.default_permissions(manage_guild=True)
async def strat_pending_slash(
    interaction: discord.Interaction,
    limit: int = 5,
) -> None:
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command requires a guild context.",
            ephemeral=True,
        )
        return
    if not await safe_defer(interaction, ephemeral=True):
        return
    payload = await _builders.build_pending_review_payload(
        interaction.guild.id,
        limit=limit,
    )
    if isinstance(payload, str):
        await safe_followup(interaction, payload, ephemeral=True)
        return
    for embed, view in payload:
        await safe_followup(interaction, embed=embed, view=view, ephemeral=True)


@strat_prefix.command(name="pending")  # type: ignore[arg-type]
@perms_or_owner(manage_guild=True)
async def strat_pending_prefix(ctx: commands.Context, limit: int = 5) -> None:
    """List pending strategy submissions with review buttons (staff-only)."""
    if not ctx.guild:
        await ctx.send("This command requires a guild context.")
        return
    payload = await _builders.build_pending_review_payload(ctx.guild.id, limit=limit)
    if isinstance(payload, str):
        await ctx.send(payload)
        return
    for embed, view in payload:
        await ctx.send(embed=embed, view=view)


@strat_app.command(
    name="strategies",
    description="List strategy memory entries available in this guild.",
)
async def strat_strategies_slash(interaction: discord.Interaction) -> None:
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command requires a guild context.",
            ephemeral=True,
        )
        return
    if not await safe_defer(interaction, ephemeral=True):
        return
    payload = await _builders.build_strategies_payload(interaction.guild.id)
    await safe_followup(interaction, content=payload, ephemeral=True)


@strat_prefix.command(name="strategies")  # type: ignore[arg-type]
async def strat_strategies_prefix(ctx: commands.Context) -> None:
    """List strategy memory entries available in this guild."""
    if not ctx.guild:
        await ctx.send("This command requires a guild context.")
        return
    await ctx.send(await _builders.build_strategies_payload(ctx.guild.id))


@strat_app.command(
    name="why-no-response",
    description="Recent BTD6 denials/skips for this guild.",
)
async def strat_why_no_response_slash(
    interaction: discord.Interaction,
    limit: int = 10,
) -> None:
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command requires a guild context.",
            ephemeral=True,
        )
        return
    await reply_ephemeral(
        interaction,
        _builders.build_why_no_response_payload(interaction.guild.id, limit=limit),
    )


@strat_prefix.command(name="why-no-response")  # type: ignore[arg-type]
async def strat_why_no_response_prefix(
    ctx: commands.Context,
    limit: int = 10,
) -> None:
    """Show the most recent BTD6 denials / skips for this guild."""
    if not ctx.guild:
        await ctx.send("This command requires a guild context.")
        return
    payload = await _builders.build_why_no_response_payload(ctx.guild.id, limit=limit)
    if isinstance(payload, str):
        await ctx.send(payload)
    else:
        await ctx.send(embed=payload)


# ===========================================================================
# /btd6 ops … — ingestion operations (staff readable; toggles are admin)
# ===========================================================================

ops_app = app_commands.Group(
    name="ops",
    parent=btd6_app,
    description="BTD6 ingestion operations (staff readable; toggles are admin).",
)


@btd6_prefix.group(name="ops", invoke_without_command=True)  # type: ignore[arg-type]
@commands.guild_only()
async def ops_prefix(ctx: commands.Context) -> None:
    """BTD6 ingestion operations (staff readable; toggles are admin)."""
    await ctx.send_help(ctx.command)


@ops_app.command(name="readiness", description="Show BTD6 ingestion readiness.")
async def ops_readiness_slash(interaction: discord.Interaction) -> None:
    if not is_staff_member(interaction.user):
        await interaction.response.send_message(
            _ops_helpers.STAFF_DENIED,
            ephemeral=True,
        )
        return
    await interaction.response.send_message(embed=await _ops_helpers.readiness_embed())


@ops_prefix.command(name="readiness")  # type: ignore[arg-type]
async def ops_readiness_prefix(ctx: commands.Context) -> None:
    if not is_staff_member(ctx.author):
        await ctx.send(_ops_helpers.STAFF_DENIED)
        return
    await ctx.send(embed=await _ops_helpers.readiness_embed())


@ops_app.command(name="runs", description="Show recent BTD6 ingestion runs.")
@app_commands.describe(
    source_key="Limit to one source key (optional).",
    limit="How many runs to show (max 25).",
)
async def ops_runs_slash(
    interaction: discord.Interaction,
    source_key: str | None = None,
    limit: int = _ops_helpers.RUNS_DEFAULT_LIMIT,
) -> None:
    if not is_staff_member(interaction.user):
        await interaction.response.send_message(
            _ops_helpers.STAFF_DENIED,
            ephemeral=True,
        )
        return
    await interaction.response.send_message(
        embed=await _ops_helpers.runs_embed(source_key, limit),
    )


@ops_prefix.command(name="runs")  # type: ignore[arg-type]
async def ops_runs_prefix(
    ctx: commands.Context,
    source_key: str | None = None,
    limit: int = _ops_helpers.RUNS_DEFAULT_LIMIT,
) -> None:
    if not is_staff_member(ctx.author):
        await ctx.send(_ops_helpers.STAFF_DENIED)
        return
    await ctx.send(embed=await _ops_helpers.runs_embed(source_key, limit))


@ops_app.command(
    name="source_enable",
    description="Enable a BTD6 ingestion source (administrator only).",
)
async def ops_source_enable_slash(
    interaction: discord.Interaction,
    source_key: str,
) -> None:
    if not is_administrator_member(interaction.user):
        await interaction.response.send_message(
            _ops_helpers.ADMIN_DENIED,
            ephemeral=True,
        )
        return
    msg = await _ops_helpers.toggle_source(interaction.user, source_key, enabled=True)
    await interaction.response.send_message(msg, ephemeral=True)


@ops_prefix.command(name="source_enable")  # type: ignore[arg-type]
async def ops_source_enable_prefix(ctx: commands.Context, source_key: str) -> None:
    if not is_administrator_member(ctx.author):
        await ctx.send(_ops_helpers.ADMIN_DENIED)
        return
    await ctx.send(
        await _ops_helpers.toggle_source(ctx.author, source_key, enabled=True),
    )


@ops_app.command(
    name="source_disable",
    description="Disable a BTD6 ingestion source (administrator only).",
)
async def ops_source_disable_slash(
    interaction: discord.Interaction,
    source_key: str,
) -> None:
    if not is_administrator_member(interaction.user):
        await interaction.response.send_message(
            _ops_helpers.ADMIN_DENIED,
            ephemeral=True,
        )
        return
    msg = await _ops_helpers.toggle_source(interaction.user, source_key, enabled=False)
    await interaction.response.send_message(msg, ephemeral=True)


@ops_prefix.command(name="source_disable")  # type: ignore[arg-type]
async def ops_source_disable_prefix(ctx: commands.Context, source_key: str) -> None:
    if not is_administrator_member(ctx.author):
        await ctx.send(_ops_helpers.ADMIN_DENIED)
        return
    await ctx.send(
        await _ops_helpers.toggle_source(ctx.author, source_key, enabled=False),
    )


@ops_app.command(
    name="seed-data",
    description="Seed the Postgres data store from the bundled files (admin).",
)
async def ops_seed_data_slash(interaction: discord.Interaction) -> None:
    if not is_administrator_member(interaction.user):
        await interaction.response.send_message(
            _ops_helpers.ADMIN_DENIED,
            ephemeral=True,
        )
        return
    # Reading files + upserting can take a moment — defer first.
    if not await safe_defer(interaction, ephemeral=True):
        return
    await safe_followup(
        interaction,
        embed=await _ops_helpers.seed_embed(),
        ephemeral=True,
    )


@ops_prefix.command(name="seed-data")  # type: ignore[arg-type]
async def ops_seed_data_prefix(ctx: commands.Context) -> None:
    """Seed the Postgres data store from the bundled files (administrator)."""
    if not is_administrator_member(ctx.author):
        await ctx.send(_ops_helpers.ADMIN_DENIED)
        return
    await ctx.send(embed=await _ops_helpers.seed_embed())


@ops_app.command(
    name="announcechannel",
    description="Set/clear the BTD6 new-version announcement channel (admin).",
)
async def ops_announce_channel_slash(
    interaction: discord.Interaction,
    channel: discord.TextChannel | None = None,
) -> None:
    if not is_administrator_member(interaction.user):
        await interaction.response.send_message(
            _ops_helpers.ADMIN_DENIED,
            ephemeral=True,
        )
        return
    if interaction.guild is None:
        await interaction.response.send_message(
            "🚫 This command must be used in a server.",
            ephemeral=True,
        )
        return
    msg = await _ops_helpers.set_announce_channel(interaction.guild.id, channel)
    await interaction.response.send_message(msg, ephemeral=True)


@ops_prefix.command(name="announcechannel")  # type: ignore[arg-type]
async def ops_announce_channel_prefix(
    ctx: commands.Context,
    channel: discord.TextChannel | None = None,
) -> None:
    """Set/clear the BTD6 new-version announcement channel (administrator)."""
    if not is_administrator_member(ctx.author):
        await ctx.send(_ops_helpers.ADMIN_DENIED)
        return
    if ctx.guild is None:
        return
    await ctx.send(await _ops_helpers.set_announce_channel(ctx.guild.id, channel))


# ===========================================================================
# /btd6 events … — live events, leaderboards, source diagnostics
# ===========================================================================

events_app = app_commands.Group(
    name="events",
    parent=btd6_app,
    description="BTD6 live events, leaderboards, and data sources.",
)


@btd6_prefix.group(name="events", invoke_without_command=True)  # type: ignore[arg-type]
async def events_prefix(ctx: commands.Context) -> None:
    """BTD6 live events, leaderboards, and data-source diagnostics."""
    await ctx.send_help(ctx.command)


@events_app.command(
    name="live",
    description="Show recent live events (race/boss/ct/odyssey/event).",
)
async def events_live_slash(
    interaction: discord.Interaction,
    kind: str = "race",
    limit: int = 5,
) -> None:
    await reply_ephemeral(
        interaction,
        _builders.build_live_events_embed(kind, limit=limit),
    )


@events_prefix.command(name="live")  # type: ignore[arg-type]
async def events_live_prefix(
    ctx: commands.Context,
    kind: str = "race",
    limit: int = 5,
) -> None:
    """Show recent live events for ``kind`` (race / boss / ct / odyssey / event)."""
    await ctx.send(embed=await _builders.build_live_events_embed(kind, limit=limit))


@events_app.command(
    name="event",
    description="Show one specific BTD6 event with tower restrictions.",
)
async def events_event_slash(
    interaction: discord.Interaction,
    kind: str,
    entity_key: str,
) -> None:
    await reply_ephemeral(
        interaction,
        _event_helpers.build_event_payload(kind, entity_key),
    )


@events_prefix.command(name="event")  # type: ignore[arg-type]
async def events_event_prefix(
    ctx: commands.Context,
    kind: str,
    entity_key: str,
) -> None:
    """Show one specific BTD6 event with its tower restrictions."""
    await ctx.send(embed=await _event_helpers.build_event_payload(kind, entity_key))


@events_app.command(name="leaderboard", description="Show race / boss leaderboard.")
async def events_leaderboard_slash(
    interaction: discord.Interaction,
    kind: str,
    event_id: str | None = None,
    limit: int = 10,
) -> None:
    await reply_ephemeral(
        interaction,
        _builders.build_leaderboard_embed(kind, event_id, limit=limit),
    )


@events_prefix.command(name="leaderboard")  # type: ignore[arg-type]
async def events_leaderboard_prefix(
    ctx: commands.Context,
    kind: str,
    event_id: str | None = None,
    limit: int = 10,
) -> None:
    """Top-N race or boss leaderboard. No event_id = newest active."""
    await ctx.send(
        embed=await _builders.build_leaderboard_embed(kind, event_id, limit=limit),
    )


@events_app.command(name="sources", description="List BTD6 source registry rows.")
async def events_sources_slash(interaction: discord.Interaction) -> None:
    if not await safe_defer(interaction, ephemeral=True):
        return
    payload = await _builders.build_sources_payload()
    await safe_followup(interaction, content=payload, ephemeral=True)


@events_prefix.command(name="sources")  # type: ignore[arg-type]
async def events_sources_prefix(ctx: commands.Context) -> None:
    """List BTD6 source registry rows."""
    await ctx.send(await _builders.build_sources_payload())


@events_app.command(
    name="source-health",
    description="BTD6 source registry freshness overview.",
)
async def events_source_health_slash(
    interaction: discord.Interaction,
    limit: int = 25,
) -> None:
    await reply_ephemeral(
        interaction,
        _builders.build_source_health_embed(limit=limit),
    )


@events_prefix.command(name="source-health")  # type: ignore[arg-type]
async def events_source_health_prefix(ctx: commands.Context, limit: int = 25) -> None:
    """Show source registry freshness."""
    await ctx.send(embed=await _builders.build_source_health_embed(limit=limit))


@events_app.command(
    name="latest-data",
    description="Newest fact envelope per entity_kind.",
)
async def events_latest_data_slash(interaction: discord.Interaction) -> None:
    await reply_ephemeral(interaction, _builders.build_latest_data_embed())


@events_prefix.command(name="latest-data")  # type: ignore[arg-type]
async def events_latest_data_prefix(ctx: commands.Context) -> None:
    """Show newest fact envelope per entity_kind."""
    await ctx.send(embed=await _builders.build_latest_data_embed())


@events_app.command(
    name="refresh-source",
    description="Manually refresh one Ninja Kiwi source (staff-only).",
)
@app_commands.default_permissions(manage_guild=True)
async def events_refresh_source_slash(
    interaction: discord.Interaction,
    source_key: str,
) -> None:
    await reply_ephemeral(
        interaction,
        _event_helpers.build_refresh_source_payload(
            source_key,
            started_by_user_id=interaction.user.id,
            include_exception_detail=True,
        ),
    )


@events_prefix.command(name="refresh-source")  # type: ignore[arg-type]
@perms_or_owner(manage_guild=True)
async def events_refresh_source_prefix(
    ctx: commands.Context,
    source_key: str,
) -> None:
    """Manually refresh one Ninja Kiwi source (staff-only)."""
    embed = await _event_helpers.build_refresh_source_payload(
        source_key,
        started_by_user_id=ctx.author.id,
        include_exception_detail=False,
    )
    await ctx.send(embed=embed)


@events_app.command(
    name="grounding",
    description="Grounding facts that fed an AI response.",
)
async def events_grounding_slash(
    interaction: discord.Interaction,
    message_id: str,
) -> None:
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command requires a guild context.",
            ephemeral=True,
        )
        return
    try:
        mid = int(message_id)
    except ValueError:
        await interaction.response.send_message(
            f"❌ Invalid message_id: {message_id!r}",
            ephemeral=True,
        )
        return
    if not await safe_defer(interaction, ephemeral=True):
        return
    payload = await _builders.build_grounding_embed(interaction.guild.id, mid)
    if isinstance(payload, str):
        await safe_followup(interaction, content=payload, ephemeral=True)
    else:
        await safe_followup(interaction, embed=payload, ephemeral=True)


@events_prefix.command(name="grounding")  # type: ignore[arg-type]
async def events_grounding_prefix(ctx: commands.Context, message_id: int) -> None:
    """Show the grounding facts that fed an AI response."""
    if not ctx.guild:
        await ctx.send("This command requires a guild context.")
        return
    payload = await _builders.build_grounding_embed(ctx.guild.id, message_id)
    if isinstance(payload, str):
        await ctx.send(payload)
    else:
        await ctx.send(embed=payload)


# ===========================================================================
# Registration — called once by the mother cog (cogs.btd6_cog)
# ===========================================================================


def register(bot: commands.Bot) -> None:
    """Add the unified ``/btd6`` app group + ``!btd6`` prefix group to the bot.

    Idempotent: guarded so a re-run (extension reload / test re-setup) doesn't
    raise ``CommandAlreadyRegistered``.
    """
    if bot.tree.get_command("btd6") is None:
        bot.tree.add_command(btd6_app)
    if bot.get_command("btd6") is None:
        bot.add_command(btd6_prefix)  # type: ignore[arg-type]


def teardown(bot: commands.Bot) -> None:
    """Remove the unified groups (mirror of :func:`register`) for clean reloads."""
    if bot.tree.get_command("btd6") is not None:
        bot.tree.remove_command("btd6")
    if bot.get_command("btd6") is not None:
        bot.remove_command("btd6")
