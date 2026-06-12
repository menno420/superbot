"""Pure embed/component builders shared by UX Lab exhibits.

Everything here is deterministic and side-effect free: builders take plain
arguments (or use the canned sample data below) and return ``discord.Embed``
objects. The embed archetypes double as the candidate "standard library" of
card shapes — when a pattern graduates (plan PR C), real cogs import the
builder rather than re-implementing the layout.

Layer rules: stdlib + discord only (``utils/`` contract). No DB, no services.
"""

from __future__ import annotations

import discord

from utils.ui_constants import (
    ADMIN_COLOR,
    CHANNEL_COLOR,
    ECONOMY_COLOR,
    GAME_COLOR,
    GENERAL_COLOR,
    MINING_COLOR,
    MOD_COLOR,
    ROLE_COLOR,
    UTILITY_COLOR,
)
from utils.ux_patterns.registry import PatternSpec, PatternStatus

# ---------------------------------------------------------------------------
# Sample data (no real users, no real guild state)
# ---------------------------------------------------------------------------

SAMPLE_MEMBERS: tuple[str, ...] = (
    "AstroFox",
    "BananaMage",
    "CinderWolf",
    "DuskRunner",
    "EmberLynx",
    "FrostByte",
    "GlowStick",
    "HexHound",
)

SAMPLE_LEADERBOARD: tuple[tuple[str, int, int], ...] = (
    ("AstroFox", 42, 13_370),
    ("BananaMage", 39, 11_204),
    ("CinderWolf", 35, 9_876),
    ("DuskRunner", 31, 8_545),
    ("EmberLynx", 28, 7_002),
)

_STATUS_COLORS: dict[PatternStatus, discord.Color] = {
    PatternStatus.STABLE: discord.Color.green(),
    PatternStatus.EXPERIMENTAL: discord.Color.orange(),
    PatternStatus.DEPRECATED: discord.Color.dark_grey(),
    PatternStatus.REJECTED: discord.Color.red(),
}

# The named palette every subsystem embed draws from (the colour-strip
# exhibit renders one embed per entry; keep ≤9 so strip + spec card ≤10).
PALETTE: tuple[tuple[str, discord.Color], ...] = (
    ("ADMIN_COLOR", ADMIN_COLOR),
    ("MOD_COLOR", MOD_COLOR),
    ("ECONOMY_COLOR", ECONOMY_COLOR),
    ("GAME_COLOR", GAME_COLOR),
    ("MINING_COLOR", MINING_COLOR),
    ("ROLE_COLOR", ROLE_COLOR),
    ("CHANNEL_COLOR", CHANNEL_COLOR),
    ("UTILITY_COLOR", UTILITY_COLOR),
    ("GENERAL_COLOR", GENERAL_COLOR),
)


def _join(items: tuple[str, ...], *, bullet: str = "• ") -> str:
    return "\n".join(f"{bullet}{i}" for i in items) if items else "—"


def spec_card(spec: PatternSpec) -> discord.Embed:
    """The metadata card shown under every exhibit."""
    flags: list[str] = []
    if spec.uses_components_v2:
        flags.append("Components V2")
    if spec.requires_modal:
        flags.append("modal")
    if spec.requires_pil:
        flags.append("PIL")
    embed = discord.Embed(
        title=f"📐 {spec.title}",
        description=spec.notes or None,
        color=_STATUS_COLORS[spec.status],
    )
    embed.add_field(
        name="Pattern",
        value=f"`{spec.pattern_id}` · {spec.status.value}"
        + (f" · {', '.join(flags)}" if flags else ""),
        inline=False,
    )
    embed.add_field(name="Use for", value=_join(spec.recommended_for), inline=True)
    embed.add_field(name="Avoid for", value=_join(spec.anti_patterns), inline=True)
    embed.add_field(name="Platform limits", value=_join(spec.limits), inline=False)
    embed.add_field(
        name="Adopted by",
        value=_join(spec.adopted_by) if spec.adopted_by else "— (not adopted yet)",
        inline=False,
    )
    return embed


# ---------------------------------------------------------------------------
# Embed archetypes (the embeds wing + reusable card shapes)
# ---------------------------------------------------------------------------


def build_info_card() -> discord.Embed:
    embed = discord.Embed(
        title="ℹ️ Server time settings",
        description=(
            "Short, scannable information with one optional action hint.\n"
            "Keep to ≤3 fields; link the panel for anything deeper."
        ),
        color=GENERAL_COLOR,
    )
    embed.add_field(name="Timezone", value="Europe/Amsterdam", inline=True)
    embed.add_field(name="Quiet hours", value="23:00 – 08:00", inline=True)
    embed.set_footer(text="Use !settings to change these")
    return embed


def build_success_card() -> discord.Embed:
    embed = discord.Embed(
        title="✅ Role created",
        description="**@Night Crew** is live and assignable.",
        color=discord.Color.green(),
    )
    embed.add_field(name="Members", value="0 (new)", inline=True)
    embed.add_field(name="Hoisted", value="Yes", inline=True)
    return embed


def build_warning_card() -> discord.Embed:
    embed = discord.Embed(
        title="⚠️ Approaching channel cap",
        description=(
            "This server has **94 / 100** text channels.\n"
            "Cleanup or archiving is recommended before bulk provisioning."
        ),
        color=discord.Color.orange(),
    )
    embed.set_footer(text="Warnings state the limit AND the next action")
    return embed


def build_error_card() -> discord.Embed:
    embed = discord.Embed(
        title="❌ Couldn't move the channel",
        description=(
            "**Missing permission:** `Manage Channels` in **#archive**.\n"
            "Grant the bot role that permission, then retry."
        ),
        color=discord.Color.red(),
    )
    embed.set_footer(text="Errors name the cause and the fix — never just 'failed'")
    return embed


def build_audit_log_card() -> discord.Embed:
    embed = discord.Embed(color=MOD_COLOR, timestamp=discord.utils.utcnow())
    embed.set_author(name="Audit · settings.warn_threshold.update")
    embed.description = (
        "**AstroFox** changed **Warn threshold** `3` → `5`\n"
        "Scope: guild · Panel: Moderation settings"
    )
    embed.set_footer(text="case 0231 · compact single-line audit shape")
    return embed


def build_moderation_case_card() -> discord.Embed:
    embed = discord.Embed(
        title="🔨 Case #418 — Timeout",
        description="Repeated spam in #general after two warnings.",
        color=MOD_COLOR,
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(name="Member", value="BananaMage", inline=True)
    embed.add_field(name="Moderator", value="AstroFox", inline=True)
    embed.add_field(name="Duration", value="2 hours", inline=True)
    embed.add_field(name="Prior cases", value="#377 warn · #392 warn", inline=False)
    embed.set_footer(text="Everything a reviewing mod needs on one card")
    return embed


def build_user_profile_card() -> discord.Embed:
    embed = discord.Embed(title="🪪 AstroFox", color=ROLE_COLOR)
    embed.add_field(name="Level", value="42", inline=True)
    embed.add_field(name="Coins", value="13,370", inline=True)
    embed.add_field(name="Daily streak", value="17 🔥", inline=True)
    embed.add_field(
        name="Badges",
        value="⛏️ Magma Miner · 🎯 Sharpshooter · 🃏 High Roller",
        inline=False,
    )
    embed.set_footer(text="Profile cards: identity top, numbers middle, flair last")
    return embed


def build_leaderboard_field_card() -> discord.Embed:
    embed = discord.Embed(title="🏆 Top members — field columns", color=ECONOMY_COLOR)
    for rank, (name, level, coins) in enumerate(SAMPLE_LEADERBOARD, start=1):
        embed.add_field(
            name=f"#{rank} {name}",
            value=f"Lv {level} · {coins:,} coins",
            inline=False,
        )
    embed.set_footer(text="Field rows: readable, but ranks wrap on mobile")
    return embed


def build_leaderboard_table_card() -> discord.Embed:
    lines = [f"{'#':<3}{'member':<12}{'lv':>4}{'coins':>9}"]
    lines += [
        f"{i:<3}{name:<12}{level:>4}{coins:>9,}"
        for i, (name, level, coins) in enumerate(SAMPLE_LEADERBOARD, start=1)
    ]
    embed = discord.Embed(
        title="🏆 Top members — code-block table",
        description="```\n" + "\n".join(lines) + "\n```",
        color=ECONOMY_COLOR,
    )
    embed.set_footer(text="Monospace aligns columns; ~40 chars fit on mobile")
    return embed


def build_setup_summary_card() -> discord.Embed:
    embed = discord.Embed(
        title="🧭 Setup review — 3 changes staged",
        description="Nothing is applied until you press **Confirm**.",
        color=ADMIN_COLOR,
    )
    embed.add_field(
        name="1 · Create role",
        value="@Events Crew (hoisted, mentionable)",
        inline=False,
    )
    embed.add_field(
        name="2 · Create channel",
        value="#events under **Community**",
        inline=False,
    )
    embed.add_field(
        name="3 · Bind setting",
        value="`events.announce_channel` → #events",
        inline=False,
    )
    embed.set_footer(text="The draft-lane Final Review shape (numbered, reversible)")
    return embed


def build_ai_answer_card() -> discord.Embed:
    embed = discord.Embed(
        title="🤖 Round 53 cash (ABR)",
        description=(
            "End of round 53 you'll have **$56,318** cumulative.\n\n"
            "**How this was computed**\n"
            "Per-round income table (ABR set) summed r1–r53, no start shift."
        ),
        color=UTILITY_COLOR,
    )
    embed.add_field(
        name="Sources",
        value="• pinned game dump v55.1\n• round-cash workflow (deterministic)",
        inline=False,
    )
    embed.set_footer(text="AI answers carry provenance — answer, method, sources")
    return embed


def build_before_after_cards() -> list[discord.Embed]:
    before = discord.Embed(
        title="Before — #general permissions",
        description="@everyone: ✅ send · ✅ embed · ✅ attach",
        color=discord.Color.dark_grey(),
    )
    after = discord.Embed(
        title="After — #general permissions",
        description="@everyone: ✅ send · ❌ embed · ❌ attach",
        color=CHANNEL_COLOR,
    )
    after.set_footer(text="Two embeds, same fields, diff in bold — scan the delta")
    return [before, after]


def build_color_strip() -> list[discord.Embed]:
    embeds: list[discord.Embed] = []
    for name, color in PALETTE:
        embed = discord.Embed(description=f"**{name}** — `#{color.value:06X}`")
        embed.colour = color
        embeds.append(embed)
    return embeds


def build_budget_edge_card() -> discord.Embed:
    embed = discord.Embed(
        title="🧱 Deliberately maximal embed (25 fields)",
        description=(
            "This is what the 25-field ceiling actually looks like. "
            "If a real panel needs this, it wants pagination instead."
        ),
        color=discord.Color.dark_grey(),
    )
    for i in range(1, 26):
        embed.add_field(
            name=f"Field {i:02d}",
            value="value text that fills the column",
            inline=True,
        )
    embed.set_footer(text="Caps: 25 fields · 1024/field · 6000 chars total")
    return embed
