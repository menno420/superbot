"""BTD6 ingestion operations surface (``!btd6ops`` / ``/btd6ops``).

Thin operator cog. Readiness + recent-runs are staff-readable; source
enable/disable is **administrator-only**, matching
``services.btd6_source_mutation._check_admin`` so the UI gate and the
mutation service agree on who may toggle live ingestion sources. All embed
formatting lives in ``cogs/btd6/_builders.py``; every write goes through
``services.btd6_source_mutation``.

Kept as its own small cog (not a ``btd6_cog`` subcommand) so ``btd6_cog.py``
stays under the 800-LOC ceiling (``tests/unit/invariants/test_cog_size.py``).

Gating is intentionally mixed and enforced inline (friendly denial message)
*and* re-checked server-side by the mutation service (defense in depth):

* ``readiness`` / ``runs``  — staff  (``is_staff_member``: admin OR manage_guild)
* ``source_enable`` / ``source_disable`` — admin (``is_administrator_member``)
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs.btd6 import _builders
from core.runtime.interaction_helpers import safe_defer, safe_followup
from services import btd6_ops_readiness_service, btd6_source_mutation
from utils.db import btd6_sources as btd6_db
from utils.discord_permissions import is_administrator_member, is_staff_member

logger = logging.getLogger("bot.cogs.btd6_ops")

_RUNS_DEFAULT_LIMIT = 10
_RUNS_MAX_LIMIT = 25

_STAFF_DENIED = "🚫 This is a staff-only command (requires Manage Server)."
_ADMIN_DENIED = "🚫 Toggling BTD6 sources requires the Administrator permission."


async def _readiness_embed() -> discord.Embed:
    verdict = await btd6_ops_readiness_service.evaluate()
    return _builders.build_readiness_embed(verdict)


async def _runs_embed(source_key: str | None, limit: int) -> discord.Embed:
    safe_limit = max(1, min(int(limit), _RUNS_MAX_LIMIT))
    runs = await btd6_db.list_ingestion_runs(source_key=source_key, limit=safe_limit)
    return _builders.build_ingestion_runs_embed(runs, source_key=source_key)


async def _toggle_source(actor: object, source_key: str, *, enabled: bool) -> str:
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
        return _ADMIN_DENIED
    except btd6_source_mutation.InvalidSourceValueError as exc:
        return f"⚠️ {exc}"
    except btd6_source_mutation.BTD6SourceMutationError as exc:  # pragma: no cover
        logger.warning("btd6 source toggle failed: %s", exc)
        return f"⚠️ {exc}"
    verb = "enabled" if enabled else "disabled"
    return f"✅ Source `{result.source_key}` {verb}."


async def _seed_embed() -> discord.Embed:
    """Seed the Postgres data store from the bundled files; report the result."""
    from services import btd6_data_service

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
    return discord.Embed(
        title="🌱 BTD6 data seeded",
        description=(
            f"Upserted **{count}** blobs into the `btd6_data_blobs` table and "
            f"**reloaded the live dataset** — the new data is being served "
            f"now; no restart needed.{serving_line}\n\n"
            "First-time setup only: set `BTD6_DATA_BACKEND` = `postgres` in "
            "Railway → Variables, then confirm `!btd6 status` reads "
            "`Data source: postgres (…)`.\n\n"
            "Safe to re-run any time (it upserts)."
        ),
        color=discord.Color.green(),
    )


async def _set_announce_channel(
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


class BTD6OpsCog(commands.Cog):
    """Operator surface for BTD6 ingestion readiness + source control."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------
    # Prefix surface — !btd6ops ...
    # ------------------------------------------------------------------

    @commands.group(name="btd6ops", invoke_without_command=True)
    @commands.guild_only()
    async def btd6ops(self, ctx: commands.Context) -> None:
        """BTD6 ingestion operations (staff readable; toggles are admin)."""
        await ctx.send_help(ctx.command)

    @btd6ops.command(name="readiness")  # type: ignore[arg-type]
    async def readiness_prefix(self, ctx: commands.Context) -> None:
        if not is_staff_member(ctx.author):
            await ctx.send(_STAFF_DENIED)
            return
        await ctx.send(embed=await _readiness_embed())

    @btd6ops.command(name="runs")  # type: ignore[arg-type]
    async def runs_prefix(
        self,
        ctx: commands.Context,
        source_key: str | None = None,
        limit: int = _RUNS_DEFAULT_LIMIT,
    ) -> None:
        if not is_staff_member(ctx.author):
            await ctx.send(_STAFF_DENIED)
            return
        await ctx.send(embed=await _runs_embed(source_key, limit))

    @btd6ops.command(name="source_enable")  # type: ignore[arg-type]
    async def source_enable_prefix(
        self,
        ctx: commands.Context,
        source_key: str,
    ) -> None:
        if not is_administrator_member(ctx.author):
            await ctx.send(_ADMIN_DENIED)
            return
        await ctx.send(await _toggle_source(ctx.author, source_key, enabled=True))

    @btd6ops.command(name="source_disable")  # type: ignore[arg-type]
    async def source_disable_prefix(
        self,
        ctx: commands.Context,
        source_key: str,
    ) -> None:
        if not is_administrator_member(ctx.author):
            await ctx.send(_ADMIN_DENIED)
            return
        await ctx.send(await _toggle_source(ctx.author, source_key, enabled=False))

    @btd6ops.command(name="seed-data")  # type: ignore[arg-type]
    async def seed_data_prefix(self, ctx: commands.Context) -> None:
        """Seed the Postgres data store from the bundled files (administrator)."""
        if not is_administrator_member(ctx.author):
            await ctx.send(_ADMIN_DENIED)
            return
        await ctx.send(embed=await _seed_embed())

    @btd6ops.command(name="announcechannel")  # type: ignore[arg-type]
    async def announce_channel_prefix(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel | None = None,
    ) -> None:
        """Set/clear the BTD6 new-version announcement channel (administrator).

        ``!btd6ops announcechannel #updates`` routes new-version
        announcements there; with no channel it clears (disables) them.
        """
        if not is_administrator_member(ctx.author):
            await ctx.send(_ADMIN_DENIED)
            return
        if ctx.guild is None:
            return
        await ctx.send(await _set_announce_channel(ctx.guild.id, channel))

    # ------------------------------------------------------------------
    # Slash surface — /btd6ops ... (mirrors the prefix surface)
    # ------------------------------------------------------------------

    btd6ops_app = app_commands.Group(
        name="btd6ops",
        description="BTD6 ingestion operations (staff readable; toggles are admin).",
        guild_only=True,
    )

    @btd6ops_app.command(name="readiness", description="Show BTD6 ingestion readiness.")
    async def readiness_slash(self, interaction: discord.Interaction) -> None:
        if not is_staff_member(interaction.user):
            await interaction.response.send_message(_STAFF_DENIED, ephemeral=True)
            return
        await interaction.response.send_message(embed=await _readiness_embed())

    @btd6ops_app.command(name="runs", description="Show recent BTD6 ingestion runs.")
    @app_commands.describe(
        source_key="Limit to one source key (optional).",
        limit="How many runs to show (max 25).",
    )
    async def runs_slash(
        self,
        interaction: discord.Interaction,
        source_key: str | None = None,
        limit: int = _RUNS_DEFAULT_LIMIT,
    ) -> None:
        if not is_staff_member(interaction.user):
            await interaction.response.send_message(_STAFF_DENIED, ephemeral=True)
            return
        await interaction.response.send_message(
            embed=await _runs_embed(source_key, limit),
        )

    @btd6ops_app.command(
        name="source_enable",
        description="Enable a BTD6 ingestion source (administrator only).",
    )
    @app_commands.default_permissions(administrator=True)
    async def source_enable_slash(
        self,
        interaction: discord.Interaction,
        source_key: str,
    ) -> None:
        if not is_administrator_member(interaction.user):
            await interaction.response.send_message(_ADMIN_DENIED, ephemeral=True)
            return
        msg = await _toggle_source(interaction.user, source_key, enabled=True)
        await interaction.response.send_message(msg, ephemeral=True)

    @btd6ops_app.command(
        name="source_disable",
        description="Disable a BTD6 ingestion source (administrator only).",
    )
    @app_commands.default_permissions(administrator=True)
    async def source_disable_slash(
        self,
        interaction: discord.Interaction,
        source_key: str,
    ) -> None:
        if not is_administrator_member(interaction.user):
            await interaction.response.send_message(_ADMIN_DENIED, ephemeral=True)
            return
        msg = await _toggle_source(interaction.user, source_key, enabled=False)
        await interaction.response.send_message(msg, ephemeral=True)

    @btd6ops_app.command(
        name="seed-data",
        description="Seed the Postgres data store from the bundled files (admin).",
    )
    @app_commands.default_permissions(administrator=True)
    async def seed_data_slash(self, interaction: discord.Interaction) -> None:
        if not is_administrator_member(interaction.user):
            await interaction.response.send_message(_ADMIN_DENIED, ephemeral=True)
            return
        # Reading files + upserting can take a moment — defer first.
        if not await safe_defer(interaction, ephemeral=True):
            return
        await safe_followup(interaction, embed=await _seed_embed(), ephemeral=True)

    @btd6ops_app.command(
        name="announcechannel",
        description="Set/clear the BTD6 new-version announcement channel (admin).",
    )
    @app_commands.default_permissions(administrator=True)
    async def announce_channel_slash(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | None = None,
    ) -> None:
        if not is_administrator_member(interaction.user):
            await interaction.response.send_message(_ADMIN_DENIED, ephemeral=True)
            return
        if interaction.guild is None:
            await interaction.response.send_message(
                "🚫 This command must be used in a server.",
                ephemeral=True,
            )
            return
        msg = await _set_announce_channel(interaction.guild.id, channel)
        await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BTD6OpsCog(bot))
