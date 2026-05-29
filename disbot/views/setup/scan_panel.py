"""Read-only server scan panel — renders ``GuildSnapshot`` for the wizard.

The Setup Wizard's server scan section calls
:func:`services.guild_snapshot.collect` and hands the snapshot to
:func:`build_scan_embed`, which renders an operator-facing summary of:

* category + channel + voice + role counts and a few salient names;
* member count;
* bot permission flags relevant to setup (manage_channels /
  manage_roles / manage_guild);
* likely existing bot/log/mod/admin/games channels — name-pattern
  matches against ``ChannelMeta.name``; the result is opinionated
  but pure-read, so a mismatch is a UI suggestion only;
* role hierarchy notes — surfaces any non-manageable role positions
  that would block role-create / role-bind operations;
* missing permissions that would block setup.

The classifier is in this module so tests can pin its name patterns
without going through the section's interaction surface.  No DB I/O,
no Discord create calls — strictly view-rendering.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import discord

from services.guild_snapshot import (
    ChannelMeta,
    GuildSnapshot,
)
from utils.channel_classify import classify_channel_name

# ---------------------------------------------------------------------------
# Scan classification — aggregates per-channel hits
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClassifiedChannel:
    """One channel + the classifier tags it matched."""

    channel: ChannelMeta
    tags: tuple[str, ...]


def classify_snapshot(snapshot: GuildSnapshot) -> tuple[ClassifiedChannel, ...]:
    """Return every channel paired with its classifier tags.

    Channels with no tag matches still appear in the result with an
    empty tag tuple — callers filter as needed.
    """
    return tuple(
        ClassifiedChannel(channel=ch, tags=classify_channel_name(ch.name))
        for ch in snapshot.channels
    )


def first_match(
    classified: Iterable[ClassifiedChannel],
    tag: str,
) -> ChannelMeta | None:
    """Return the first ``ClassifiedChannel.channel`` whose tags contain
    ``tag``, or ``None`` if no match.

    Useful for the wizard's "what looks like a log channel?" probe.
    """
    for c in classified:
        if tag in c.tags:
            return c.channel
    return None


# ---------------------------------------------------------------------------
# Bot permission probe — surfaces missing perms that would block setup
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MissingPermission:
    """One permission the bot is missing for a planned setup action."""

    name: str
    why: str


def missing_permissions(snapshot: GuildSnapshot) -> tuple[MissingPermission, ...]:
    """Inspect the snapshot for permissions the bot would need at apply.

    The probe is heuristic — the canonical permission check happens
    inside the mutation pipelines at apply time.  Surfacing missing
    perms during the scan lets the operator fix the bot's role before
    they spend time staging drafts that will fail apply.
    """
    findings: list[MissingPermission] = []

    # No category is manageable — manage_channels is missing or every
    # category sits above the bot's role.
    if snapshot.categories and not any(c.bot_can_manage for c in snapshot.categories):
        findings.append(
            MissingPermission(
                name="manage_channels",
                why=(
                    "No category is manageable by the bot.  Channel/category "
                    "create + bind ops would fail at apply."
                ),
            ),
        )

    # No role is manageable — manage_roles is missing or the bot's
    # highest role sits below every role in the guild.
    if snapshot.roles and not any(r.bot_can_manage for r in snapshot.roles):
        findings.append(
            MissingPermission(
                name="manage_roles",
                why=(
                    "No role is manageable by the bot.  Role create + bind "
                    "ops would fail at apply."
                ),
            ),
        )

    # Bot can't send in any text channel — message-based features and
    # automation actions would never reach the operator.
    text_channels = [c for c in snapshot.channels if c.type == "text"]
    if text_channels and not any(c.bot_can_send for c in text_channels):
        findings.append(
            MissingPermission(
                name="send_messages",
                why=(
                    "Bot cannot send in any text channel.  Bot/log/mod "
                    "channels need send + embed perms before apply."
                ),
            ),
        )

    return tuple(findings)


# ---------------------------------------------------------------------------
# Embed builder
# ---------------------------------------------------------------------------


_FIELD_VALUE_CAP = 1000


def _truncate(text: str, *, limit: int = _FIELD_VALUE_CAP) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _format_match_block(
    classified: Iterable[ClassifiedChannel],
    tag: str,
    *,
    max_items: int = 5,
) -> str:
    matches = [c.channel for c in classified if tag in c.tags]
    if not matches:
        return "_no match_"
    lines = [f"• `#{m.name}` (id `{m.id}`)" for m in matches[:max_items]]
    if len(matches) > max_items:
        lines.append(f"_+{len(matches) - max_items} more_")
    return "\n".join(lines)


def build_scan_embed(snapshot: GuildSnapshot) -> discord.Embed:
    """Render the snapshot as an operator-facing wizard embed.

    Three sections:

    * **Inventory** — counts + sample names so the operator knows the
      bot sees what they expect.
    * **Likely matches** — channels the classifier flagged for the
      highest-priority setup outputs (log / bot-cmd / mod-log /
      admin / general).
    * **Setup blockers** — missing bot permissions that would prevent
      apply from succeeding.

    Channel / role hierarchy notes ride along inside the inventory
    block; we don't dedicate a separate field so the embed stays
    inside Discord's six-field threshold across diverse guild shapes.
    """
    classified = classify_snapshot(snapshot)
    blockers = missing_permissions(snapshot)

    color = discord.Color.red() if blockers else discord.Color.blurple()
    embed = discord.Embed(
        title=f"🛰 Server scan · {snapshot.guild_name}",
        description=(
            "Read-only snapshot of this server's structure.  Use it to "
            "decide which setup mode fits — keep existing, create only "
            "missing, load a preset, or customize manually.  Nothing "
            "applies from this view."
        ),
        color=color,
    )

    embed.add_field(
        name="Inventory",
        value=_inventory_block(snapshot),
        inline=False,
    )

    likely_value = _likely_matches_block(classified)
    if likely_value:
        embed.add_field(
            name="Likely matches",
            value=_truncate(likely_value),
            inline=False,
        )

    if blockers:
        embed.add_field(
            name="⚠️ Setup blockers (missing bot permissions)",
            value="\n".join(f"• **{b.name}** — {b.why}" for b in blockers),
            inline=False,
        )

    embed.set_footer(
        text=(
            f"guild_id={snapshot.guild_id} · "
            f"{len(snapshot.channels)} channel(s), "
            f"{len(snapshot.categories)} category(ies), "
            f"{len(snapshot.roles)} role(s)"
        ),
    )
    return embed


def _inventory_block(snapshot: GuildSnapshot) -> str:
    text_channels = [c for c in snapshot.channels if c.type == "text"]
    voice_channels = [c for c in snapshot.channels if c.type == "voice"]
    stage_channels = [c for c in snapshot.channels if c.type == "stage"]
    bot_manageable_roles = sum(1 for r in snapshot.roles if r.bot_can_manage)
    bot_manageable_cats = sum(1 for c in snapshot.categories if c.bot_can_manage)
    return (
        f"`channels`: text={len(text_channels)} · voice={len(voice_channels)} · "
        f"stage={len(stage_channels)}\n"
        f"`categories`: {len(snapshot.categories)} ({bot_manageable_cats} manageable)\n"
        f"`roles`: {len(snapshot.roles)} ({bot_manageable_roles} manageable)\n"
        f"`bindings declared`: {len(snapshot.bindings_snapshot)} · "
        f"`settings declared`: {len(snapshot.settings_snapshot)}\n"
        f"`readiness findings`: {len(snapshot.readiness_findings)}"
    )


_LIKELY_PROBES: tuple[tuple[str, str], ...] = (
    ("likely_log", "Log channel"),
    ("likely_mod_log", "Moderation log"),
    ("likely_bot_cmd", "Bot command channel"),
    ("likely_admin", "Admin / staff channel"),
    ("likely_general", "General chat"),
)


def _likely_matches_block(classified: tuple[ClassifiedChannel, ...]) -> str:
    lines: list[str] = []
    for tag, label in _LIKELY_PROBES:
        match = first_match(classified, tag)
        if match is None:
            continue
        lines.append(f"**{label}** → `#{match.name}` (id `{match.id}`)")
    return "\n".join(lines)


__all__ = [
    "ClassifiedChannel",
    "MissingPermission",
    "build_scan_embed",
    "classify_channel_name",
    "classify_snapshot",
    "first_match",
    "missing_permissions",
]
