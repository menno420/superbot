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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BTD6OpsCog(bot))
