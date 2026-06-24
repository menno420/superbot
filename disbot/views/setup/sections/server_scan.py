"""Server scan section — read-only snapshot of the guild's structure.

Opens at the top of the wizard hub (``order=5`` so it sorts before
Readiness).  Calls :func:`services.guild_snapshot.collect` and hands
the result to :func:`views.setup.scan_panel.build_scan_embed`, which
renders categories / channels / roles / bot perms / likely matches /
missing-permission blockers.

The section is strictly read-only — no draft writes, no apply path.
It exists so the operator can see the bot's view of the server
before deciding which setup mode to use (keep existing / create
only missing / preset / manual).  Subsequent sections (PRs 7-10)
consume the cached snapshot to propose drafts; this PR only
renders the scan.

The snapshot is cached on the ``SetupHubView`` instance via
:func:`set_cached_snapshot` so sibling sections can re-use it
without re-collecting.  The cache is per-hub-view (an in-memory
attribute on the View), so it lives only for the duration of one
wizard run.  A fresh ``Start Setup`` click rebuilds the snapshot.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services import setup_session
from services.guild_snapshot import GuildSnapshot, collect
from services.setup_sections import REGISTRY, SetupSection
from views.setup.scan_panel import build_scan_embed

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.server_scan")

SLUG = "server_scan"

_CACHE_ATTR = "_cached_snapshot"


def set_cached_snapshot(hub: SetupHubView, snapshot: GuildSnapshot) -> None:
    """Attach ``snapshot`` to ``hub`` so subsequent sections can read it.

    The attribute name is shared with :func:`get_cached_snapshot` so
    later sections (channels, roles, presets) can pick it up without
    re-collecting.  A fresh wizard launch creates a fresh hub view
    with no cached snapshot, which is the desired behaviour.
    """
    setattr(hub, _CACHE_ATTR, snapshot)


def get_cached_snapshot(hub: SetupHubView) -> GuildSnapshot | None:
    """Return the cached snapshot for ``hub`` or ``None`` if absent."""
    return getattr(hub, _CACHE_ATTR, None)


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This can only be used in a server.",
            ephemeral=True,
        )
        return

    try:
        snapshot = await collect(guild)
    except Exception:
        logger.exception("server_scan: guild_snapshot.collect failed")
        await interaction.response.send_message(
            "❌ Server scan failed — see logs.",
            ephemeral=True,
        )
        return

    set_cached_snapshot(hub, snapshot)
    embed = build_scan_embed(snapshot)
    await interaction.response.send_message(embed=embed, ephemeral=True)

    try:
        await setup_session.mark_in_progress(guild.id, step=SLUG)
    except Exception:
        logger.exception("server_scan: mark_in_progress failed")


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Scan server",
        style=discord.ButtonStyle.primary,
        run=run,
        emoji="🛰",
        order=5,
    ),
)


__all__ = [
    "SLUG",
    "get_cached_snapshot",
    "run",
    "set_cached_snapshot",
]
