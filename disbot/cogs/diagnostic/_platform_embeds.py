"""Embed builders for the ``!platform <subcommand>`` admin surface.

Extracted from ``cogs/diagnostic_cog.py`` to keep the cog under the
800-LOC fail threshold enforced by
``tests/unit/invariants/test_cog_size.py``.  Each builder is a pure
async function that fetches its data (via ``services.diagnostics_service``
and/or ``utils.db.*``) and returns a single :class:`discord.Embed`
ready to send.  The cog methods become thin wrappers that delegate
here.

Phase 2a + 2b builders covered:

* :func:`build_resources_embed` — ``!platform resources``
* :func:`build_bindings_embed`  — ``!platform bindings``

Earlier-phase platform commands stay inline in the cog for now.  When
the next batch of platform commands lands and pushes the cog back
toward the ceiling, those should migrate here too.
"""

from __future__ import annotations

import discord


async def build_resources_embed(guild: discord.Guild | None) -> discord.Embed:
    """Build the embed for ``!platform resources`` (Phase 2a)."""
    from services import diagnostics_service
    from utils.db import resource_cache

    snap = diagnostics_service.snapshot("resources")
    embed = discord.Embed(
        title="🧱 Resources",
        description=(
            f"package: `{snap['package']}`  ·  "
            f"kinds: {', '.join(f'`{k}`' for k in snap['kinds'])}"
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Submodules",
        value=", ".join(f"`{m}`" for m in snap["submodules"]),
        inline=False,
    )
    if guild is not None:
        try:
            histogram = await resource_cache.count_by_status(guild.id)
        except Exception as exc:  # noqa: BLE001 — DB outage shouldn't crash command
            embed.add_field(
                name="Cached status",
                value=f"❌ {exc}",
                inline=False,
            )
        else:
            if histogram:
                lines = [
                    f"`{status}` — {count}"
                    for status, count in sorted(histogram.items())
                ]
                embed.add_field(
                    name=f"Cached status (guild {guild.id})",
                    value="\n".join(lines),
                    inline=False,
                )
            else:
                embed.add_field(
                    name=f"Cached status (guild {guild.id})",
                    value="*(no cached rows)*",
                    inline=False,
                )
    return embed


async def build_bindings_embed(guild: discord.Guild | None) -> discord.Embed:
    """Build the embed for ``!platform bindings`` (Phase 2b)."""
    from services import diagnostics_service
    from utils.db import bindings as bindings_db

    snap = diagnostics_service.snapshot("bindings")
    embed = discord.Embed(
        title="🔗 Subsystem bindings",
        description=f"kinds: {', '.join(f'`{k}`' for k in snap['kinds'])}",
        color=discord.Color.blurple(),
    )
    dispatch_lines = [
        f"`{kind}` → `{validator}`"
        for kind, validator in sorted(snap["validator_dispatch"].items())
    ]
    embed.add_field(
        name="Validator dispatch",
        value="\n".join(dispatch_lines),
        inline=False,
    )
    if guild is not None:
        try:
            by_status = await bindings_db.count_by_status(guild.id)
            by_sub = await bindings_db.count_by_subsystem(guild.id)
        except Exception as exc:  # noqa: BLE001 — DB outage shouldn't crash command
            embed.add_field(
                name="Per-guild counts",
                value=f"❌ DB query failed: {exc}",
                inline=False,
            )
            return embed

        status_lines = (
            "\n".join(
                f"`{status}` — {count}" for status, count in sorted(by_status.items())
            )
            or "*(no bindings)*"
        )
        embed.add_field(
            name=f"Status (guild {guild.id})",
            value=status_lines,
            inline=False,
        )
        sub_lines = (
            "\n".join(f"`{sub}` — {count}" for sub, count in sorted(by_sub.items()))
            or "*(no bindings)*"
        )
        embed.add_field(
            name=f"By subsystem (guild {guild.id})",
            value=sub_lines,
            inline=False,
        )
    return embed


__all__ = ["build_bindings_embed", "build_resources_embed"]
