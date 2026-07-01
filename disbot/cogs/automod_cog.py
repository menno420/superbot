"""Automod cog — wires the automod message-pipeline stage + operator status.

automod v1 (owner decision Q-0108): the automated message-filter layer beneath
manual moderation.  This cog is glue only — the detection engine lives in
``services.automod_service`` and the action orchestration in
``cogs.automod.listener``.  Like ``cogs.cleanup_cog`` (its twin in the auto-mod
tier), it registers a :class:`~core.runtime.message_pipeline.MessageStage` in
``cog_load`` and the :class:`SubsystemSchema` so the rules are operator-editable
through the existing ``!settings`` widget.

Config: ``!settings`` → Automod (the four rule toggles + thresholds + exempt
lists).  ``!automod`` shows the current effective policy.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from cogs.automod.listener import process_message
from core.runtime.message_pipeline import MessagePipelineContext, StageResult
from core.runtime.permission_checks import perms_or_owner
from services import automod_config
from utils.ui_constants import MOD_COLOR

logger = logging.getLogger("bot.cogs.automod")

AUTOMOD_STAGE_NAME = "automod"
# Auto-mod tier — runs first within the tier (before cleanup=10) so an obvious
# spam/invite burst is removed before the word filter / counting / chain see it.
# See the canonical stage-order table in core/runtime/message_pipeline.py.
AUTOMOD_STAGE_ORDER = 5


class AutomodStage:
    """Message-pipeline stage that applies the per-guild automod policy.

    Auto-mod tier (order=5).  Short-circuits the pipeline on a deletion so
    downstream reward/conversational stages skip a removed message.  Stateless
    across guilds — the per-guild policy is loaded per message and the spam
    sliding-window lives in ``services.automod_service`` (process-local).
    """

    name = AUTOMOD_STAGE_NAME
    order = AUTOMOD_STAGE_ORDER

    async def process(self, ctx: MessagePipelineContext) -> StageResult:
        return await process_message(ctx.bot, ctx.message)


class Automod(commands.Cog):
    """Automated message-filter layer (spam · invites · caps · mass mentions)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        from cogs.automod.schemas import register_schemas
        from core.runtime import message_pipeline

        register_schemas()  # declares the Automod settings group.
        message_pipeline.register(AutomodStage())

    async def cog_unload(self) -> None:
        from core.runtime import message_pipeline

        message_pipeline.unregister(AUTOMOD_STAGE_NAME)

    @staticmethod
    def _policy_embed(policy: automod_config.AutomodPolicy) -> discord.Embed:
        """Render the effective automod policy as a summary embed."""

        def _flag(on: bool) -> str:
            return "🟢 on" if on else "⚫ off"

        lines = [
            f"**Master:** {_flag(policy.enabled)}",
            "",
            f"🛑 **Spam** — {_flag(policy.spam_enabled)} "
            f"(> {policy.spam_count} msgs / {policy.spam_window_seconds}s)",
            f"🔗 **Invite links** — {_flag(policy.invites_enabled)}",
            f"🔠 **Excessive caps** — {_flag(policy.caps_enabled)} "
            f"(>= {policy.caps_percent}% uppercase)",
            f"📣 **Mass mentions** — {_flag(policy.mentions_enabled)} "
            f"(>= {policy.mentions_count} mentions)",
        ]
        if policy.exempt_role_ids:
            lines.append("")
            lines.append(
                "Exempt roles: "
                + ", ".join(f"<@&{rid}>" for rid in sorted(policy.exempt_role_ids)),
            )
        if policy.exempt_channel_ids:
            lines.append(
                "Exempt channels: "
                + ", ".join(f"<#{cid}>" for cid in sorted(policy.exempt_channel_ids)),
            )

        embed = discord.Embed(
            title="🛡️ Automod",
            description="\n".join(lines),
            color=MOD_COLOR,
        )
        embed.set_footer(
            text="Configure in !settings → Automod. Actions route through "
            "moderation (warn → escalation).",
        )
        return embed

    @commands.command(
        name="automod",
        help="Show the current automod policy for this server.",
        extras={"classification": "primary_entrypoint"},
    )
    @commands.guild_only()
    @perms_or_owner(manage_guild=True)
    async def automod_status(self, ctx: commands.Context) -> None:
        """Render the effective automod policy (admin/manage-guild only)."""
        policy = await automod_config.load_policy(ctx.guild.id)
        await ctx.send(embed=self._policy_embed(policy))

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — the automod policy summary.

        automod has no bespoke panel in v1 (config is the !settings widget
        group), so the help dropdown lands on the read-only policy summary
        with the pointer to !settings → Automod.
        """
        from views.base import HubView

        policy = await automod_config.load_policy(interaction.guild_id)
        return self._policy_embed(policy), HubView(interaction.user)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Automod(bot))
