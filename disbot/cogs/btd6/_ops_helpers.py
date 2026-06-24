"""Shared BTD6 ingestion-ops helpers (readiness / runs / source toggle / seed).

Extracted from ``btd6_ops_cog`` when the BTD6 command surface was unified under
one ``/btd6`` tree (owner request, 2026-06-24). Both the legacy ``!btd6ops``
prefix alias group (in :mod:`cogs.btd6_ops_cog`) and the unified
``/btd6 ops …`` subgroup (in :mod:`cogs.btd6._unified`) call these, so the
formatting + mutation seam lives in exactly one place rather than being
duplicated across the two surfaces (helper-policy: a function needed by more
than one cog in the same domain belongs in the shared ``cogs/btd6`` package).

Every write still funnels through ``services.btd6_source_mutation`` /
``services.btd6_data_service`` — these helpers only format the result.
"""

from __future__ import annotations

import logging

import discord

from cogs.btd6 import _builders
from services import btd6_ops_readiness_service, btd6_source_mutation
from utils.db import btd6_sources as btd6_db

logger = logging.getLogger("bot.cogs.btd6_ops")

RUNS_DEFAULT_LIMIT = 10
RUNS_MAX_LIMIT = 25

STAFF_DENIED = "🚫 This is a staff-only command (requires Manage Server)."
ADMIN_DENIED = "🚫 Toggling BTD6 sources requires the Administrator permission."


async def readiness_embed() -> discord.Embed:
    verdict = await btd6_ops_readiness_service.evaluate()
    return _builders.build_readiness_embed(verdict)


async def runs_embed(source_key: str | None, limit: int) -> discord.Embed:
    safe_limit = max(1, min(int(limit), RUNS_MAX_LIMIT))
    runs = await btd6_db.list_ingestion_runs(source_key=source_key, limit=safe_limit)
    return _builders.build_ingestion_runs_embed(runs, source_key=source_key)


async def toggle_source(actor: object, source_key: str, *, enabled: bool) -> str:
    """Flip a source's enabled flag; return a human result/error message.

    The mutation service re-checks administrator permission and validates the
    source (e.g. refuses to enable a NULL-base_url row), so both failure modes
    surface as a friendly line rather than an unhandled exception.
    """
    try:
        result = await btd6_source_mutation.set_enabled(
            source_key.strip(),
            enabled=enabled,
            actor=actor,
            reason="btd6ops command",
        )
    except btd6_source_mutation.UnauthorizedSourceMutationError:
        return ADMIN_DENIED
    except btd6_source_mutation.InvalidSourceValueError as exc:
        return f"⚠️ {exc}"
    except btd6_source_mutation.BTD6SourceMutationError as exc:  # pragma: no cover
        logger.warning("btd6 source toggle failed: %s", exc)
        return f"⚠️ {exc}"
    verb = "enabled" if enabled else "disabled"
    return f"✅ Source `{result.source_key}` {verb}."


async def seed_embed() -> discord.Embed:
    """Seed the Postgres data store from the bundled files; report the result."""
    from services import btd6_data_service

    # Capture what's about to change BEFORE seeding, so the receipt confirms which
    # files the seed applied (postgres only; None for the file backend / in sync).
    changed = btd6_data_service.content_drift()
    count = await btd6_data_service.seed_postgres_from_files()
    if count == 0:
        return discord.Embed(
            title="🌱 BTD6 data seed",
            description=(
                "No bundled data files were found to seed. If the repo data has "
                "already been removed, re-generate the fixtures first."
            ),
            color=discord.Color.orange(),
        )
    served = ""
    try:
        served = btd6_data_service.get_dataset().game_version
    except Exception:  # noqa: BLE001 — version is decoration on the receipt
        pass
    serving_line = f"\n**Now serving:** game version `{served}`." if served else ""
    changed_line = ""
    if changed:
        shown = ", ".join(f"`{name}`" for name in changed[:8])
        more = f" +{len(changed) - 8} more" if len(changed) > 8 else ""
        changed_line = f"\n**Applied {len(changed)} changed file(s):** {shown}{more}."
    return discord.Embed(
        title="🌱 BTD6 data seeded",
        description=(
            f"Upserted **{count}** blobs into the `btd6_data_blobs` table and "
            f"**reloaded the live dataset** — the new data is being served "
            f"now; no restart needed.{serving_line}{changed_line}\n\n"
            "First-time setup only: set `BTD6_DATA_BACKEND` = `postgres` in "
            "Railway → Variables, then confirm `!btd6 status` reads "
            "`Data source: postgres (…)`.\n\n"
            "Safe to re-run any time (it upserts)."
        ),
        color=discord.Color.green(),
    )


async def set_announce_channel(
    guild_id: int,
    channel: discord.TextChannel | None,
) -> str:
    """Set or clear the BTD6 version-announcement channel; return a result line.

    The setting is owned by ``services.btd6_version_announce`` (no raw key
    string here, mirroring ``btd6_ct_team_service``). A ``None`` channel
    clears it — disabling the announcement for the guild.

    This command writes the **legacy KV lane**; a bound
    ``btd6.version_announce_channel`` binding takes precedence (Q-0064
    read order), so the result line warns when a binding shadows the
    write instead of silently confirming a channel that won't be used.
    """
    from services import btd6_version_announce

    if channel is None:
        await btd6_version_announce.clear_channel(guild_id)
        return "✅ BTD6 version announcements disabled (no channel set)."
    await btd6_version_announce.set_channel(guild_id, channel.id)
    bound = await btd6_version_announce.binding_channel_id(guild_id)
    if bound is not None and bound != channel.id:
        return (
            f"⚠️ Saved, but the Settings **binding** currently points "
            f"announcements at <#{bound}> and takes precedence — change or "
            f"clear the `version_announce_channel` binding to use "
            f"{channel.mention}."
        )
    return f"✅ New BTD6 versions will be announced in {channel.mention}."
