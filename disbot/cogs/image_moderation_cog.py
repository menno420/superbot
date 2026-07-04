"""Image-moderation cog — wires the image-mod message-pipeline stage + status.

image moderation v1 (owner decision Q-0108): scan uploaded images against
OpenAI's free ``omni-moderation-latest`` endpoint, deleting + warning on a
flagged image.  This cog is glue only — the detection/threshold logic lives in
``services.image_moderation_service`` and the scan + action orchestration in
``cogs.image_moderation.listener``.  Like ``cogs.automod_cog`` (its twin in the
auto-mod tier), it registers a
:class:`~core.runtime.message_pipeline.MessageStage` in ``cog_load`` and the
:class:`SubsystemSchema` so the categories/threshold are operator-editable
through the existing ``!settings`` widget.

Config: ``!settings`` → Image moderation (the four category toggles + threshold
+ exempt lists).  ``!imagemod`` shows the current effective policy.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from cogs.image_moderation.listener import process_message
from core.runtime.message_pipeline import MessagePipelineContext, StageResult
from core.runtime.permission_checks import perms_or_owner
from services import image_moderation_config
from utils.ui_constants import MOD_COLOR

logger = logging.getLogger("bot.cogs.image_moderation")

IMAGE_MOD_STAGE_NAME = "image_moderation"
# Auto-mod tier — runs after the cheap text rules (automod=5, cleanup=10,
# counting=15, chain=20) but before the rewards tier (xp=30), so an external API
# call is made only on a message that survived the free text filters, and a
# flagged image is never rewarded.  See the canonical stage-order table in
# core/runtime/message_pipeline.py.
IMAGE_MOD_STAGE_ORDER = 25


class ImageModerationStage:
    """Message-pipeline stage that applies the per-guild image-moderation policy.

    Auto-mod tier (order=25).  Short-circuits the pipeline on a deletion so
    downstream reward/conversational stages skip a removed message.  Stateless
    across guilds — the per-guild policy is loaded per message; the only state
    (the OpenAI client) lives in the moderation provider (process-local).
    """

    name = IMAGE_MOD_STAGE_NAME
    order = IMAGE_MOD_STAGE_ORDER

    async def process(self, ctx: MessagePipelineContext) -> StageResult:
        return await process_message(ctx.bot, ctx.message)


class ImageModeration(commands.Cog):
    """Automated image-filter layer (sexual · violence · harassment · hate)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        from cogs.image_moderation.schemas import register_schemas
        from core.runtime import message_pipeline

        register_schemas()  # declares the Image-moderation settings group.
        message_pipeline.register(ImageModerationStage())

    async def cog_unload(self) -> None:
        from core.runtime import message_pipeline

        message_pipeline.unregister(IMAGE_MOD_STAGE_NAME)

    @staticmethod
    def _policy_embed(
        policy: image_moderation_config.ImageModerationPolicy,
    ) -> discord.Embed:
        """Render the effective image-moderation policy as a summary embed."""

        def _flag(on: bool) -> str:
            return "🟢 on" if on else "⚫ off"

        lines = [
            f"**Master:** {_flag(policy.enabled)}",
            f"**Action threshold:** ≥ {policy.threshold_percent}% confidence",
            "",
            f"🔞 **Sexual** — {_flag(policy.sexual_enabled)}",
            f"🔪 **Violence** — {_flag(policy.violence_enabled)}",
            f"😠 **Harassment** — {_flag(policy.harassment_enabled)}",
            f"🚫 **Hate** — {_flag(policy.hate_enabled)}",
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
            title="🖼️ Image moderation",
            description="\n".join(lines),
            color=MOD_COLOR,
        )
        embed.set_footer(
            text="Configure in !settings → Image moderation. When on, flagged "
            "images are scanned via OpenAI; actions route through moderation.",
        )
        return embed

    @commands.command(
        name="imagemod",
        help="Show the current image-moderation policy for this server.",
        extras={"classification": "primary_entrypoint"},
    )
    @commands.guild_only()
    @perms_or_owner(manage_guild=True)
    async def imagemod_status(self, ctx: commands.Context) -> None:
        """Render the effective image-moderation policy (manage-guild only)."""
        policy = await image_moderation_config.load_policy(ctx.guild.id)
        await ctx.send(embed=self._policy_embed(policy))

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — the image-mod policy summary.

        Image moderation has no bespoke panel in v1 (config is the !settings
        widget group), so the help dropdown lands on the read-only policy
        summary with the pointer to !settings → Image moderation.
        """
        from views.base import HubView

        policy = await image_moderation_config.load_policy(interaction.guild_id)
        return self._policy_embed(policy), HubView(interaction.user)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ImageModeration(bot))
