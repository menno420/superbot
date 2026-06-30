from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands
from discord.ext.commands import MissingPermissions

from core.runtime import resources
from core.runtime.interaction_helpers import help_ctx_shim
from core.runtime.message_pipeline import (
    MessagePipelineContext,
    StageResult,
)
from core.runtime.permission_checks import admin_or_owner
from services import chain_service, moderation_service
from utils import db
from views.base import HubView, interaction_is_admin, send_panel

CHAIN_STAGE_NAME = "chain"
# Auto-mod tier — last within the tier (after cleanup=10, counting=15). See
# the canonical stage-order table in core/runtime/message_pipeline.py.
CHAIN_STAGE_ORDER = 20

logger = logging.getLogger("bot.cogs.chain")


class ChainStage:
    """Message-pipeline stage enforcing chain rules + word limits.

    Auto-mod tier (order=20).  Short-circuits the pipeline when a
    message is deleted so xp / game_input stages skip a removed
    message.

    Holds a cog reference because the rule check requires the bot's
    command-context lookup (so command messages aren't auto-deleted).
    """

    name = CHAIN_STAGE_NAME
    order = CHAIN_STAGE_ORDER

    def __init__(self, cog: ChainCog):
        self.cog = cog

    async def process(self, ctx: MessagePipelineContext) -> StageResult:
        deleted = await self.cog._process_chain_message(ctx.message)
        if deleted:
            return StageResult(deleted=True, short_circuit=True)
        return StageResult()


class ChainCog(commands.Cog):
    """Cog for managing message chains and word limits in specified channels."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self) -> None:
        from core.runtime import message_pipeline

        message_pipeline.register(ChainStage(self))

    def cog_unload(self) -> None:
        from core.runtime import message_pipeline

        message_pipeline.unregister(CHAIN_STAGE_NAME)

    @commands.group(name="chain", invoke_without_command=True)
    async def chain(self, ctx):
        """Manage message chains and word limits in your server.

        Use subcommands to create, delete, set limits, or list chains.
        """
        await ctx.send(
            "❓ Please specify a subcommand. Use `!chain create`, `!chain delete`, `!chain setlimit`, `!chain removelimit`, or `!chain list`.",
        )

    @chain.command(name="create")  # type: ignore[arg-type]
    @admin_or_owner()
    async def create_chain(
        self,
        ctx,
        channel: discord.TextChannel | None = None,
        *,
        word: str = None,
    ):
        """Create a chain in a specified channel or the current channel if none is provided.

        Only the specified word will be allowed in that channel. All other messages will be deleted.

        **Usage:** `!chain create [channel] <word>`
        """
        if word is None:
            await ctx.send(
                "❌ Please specify the word to enforce in the chain.\n**Usage:** `!chain create [channel] <word>`",
            )
            return

        target_channel = channel or ctx.channel

        result = await chain_service.create_chain(
            guild_id=ctx.guild.id,
            channel_id=target_channel.id,
            word=word,
            actor_id=ctx.author.id,
        )
        if result.status == "already_exists":
            await ctx.send(f"❌ A chain is already active in {target_channel.mention}.")
            return
        if result.status == "invalid":
            await ctx.send(
                "❌ Please specify the word to enforce in the chain.\n**Usage:** `!chain create [channel] <word>`",
            )
            return

        await ctx.send(
            f"✅ Chain created in {target_channel.mention}. Only the word `{result.new_value}` is allowed in this channel.",
        )

    @create_chain.error
    async def create_chain_error(self, ctx, error):
        """Handle errors for the create_chain command."""
        if isinstance(error, MissingPermissions):
            await ctx.send("❌ You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                "❌ Invalid channel specified. Please mention a valid text channel.",
            )
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
            logger.error(f"Error in create_chain command: {error}")

    @chain.command(name="delete")  # type: ignore[arg-type]
    @admin_or_owner()
    async def delete_chain(self, ctx, channel: discord.TextChannel = None):
        """Delete a chain from a specified channel or the current channel if none is provided.

        **Usage:** `!chain delete [channel]`
        """
        target_channel = channel or ctx.channel

        result = await chain_service.delete_chain(
            guild_id=ctx.guild.id,
            channel_id=target_channel.id,
            actor_id=ctx.author.id,
        )
        if not result.applied:
            await ctx.send(f"❌ No active chain found in {target_channel.mention}.")
            return

        await ctx.send(f"✅ Chain deleted from {target_channel.mention}.")

    @delete_chain.error
    async def delete_chain_error(self, ctx, error):
        """Handle errors for the delete_chain command."""
        if isinstance(error, MissingPermissions):
            await ctx.send("❌ You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                "❌ Invalid channel specified. Please mention a valid text channel.",
            )
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
            logger.error(f"Error in delete_chain command: {error}")

    @chain.command(name="setlimit")  # type: ignore[arg-type]
    @admin_or_owner()
    async def set_limit(
        self,
        ctx,
        channel: discord.TextChannel = None,
        limit: int = None,
    ):
        """Set a word limit in a specified channel or the current channel if none is provided.

        **Usage:** `!chain setlimit [channel] <number>`
        """
        if limit is None or limit <= 0:
            await ctx.send(
                "❌ Please specify a valid word limit greater than 0.\n**Usage:** `!chain setlimit [channel] <number>`",
            )
            return

        target_channel = channel or ctx.channel

        result = await chain_service.set_word_limit(
            guild_id=ctx.guild.id,
            channel_id=target_channel.id,
            limit=limit,
            actor_id=ctx.author.id,
        )
        if result.status == "not_found":
            await ctx.send(
                f"❌ No active chain found in {target_channel.mention}. Create one first with `!chain create`.",
            )
            return

        await ctx.send(
            f"✅ Word limit of {limit} has been set in {target_channel.mention}.",
        )

    @set_limit.error
    async def set_limit_error(self, ctx, error):
        """Handle errors for the set_limit command."""
        if isinstance(error, MissingPermissions):
            await ctx.send("❌ You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                "❌ Invalid input. Please mention a valid channel and specify a numerical limit.",
            )
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
            logger.error(f"Error in set_limit command: {error}")

    @chain.command(name="removelimit")  # type: ignore[arg-type]
    @admin_or_owner()
    async def remove_limit(self, ctx, channel: discord.TextChannel = None):
        """Remove the word limit from a specified channel or the current channel if none is provided.

        **Usage:** `!chain removelimit [channel]`
        """
        target_channel = channel or ctx.channel

        result = await chain_service.set_word_limit(
            guild_id=ctx.guild.id,
            channel_id=target_channel.id,
            limit=0,
            actor_id=ctx.author.id,
        )
        if result.applied:
            await ctx.send(
                f"✅ Word limit has been removed from {target_channel.mention}.",
            )
        else:
            # not_found / no_change — nothing was set, matching legacy copy.
            await ctx.send(f"ℹ️ No word limit is set in {target_channel.mention}.")

    @remove_limit.error
    async def remove_limit_error(self, ctx, error):
        """Handle errors for the remove_limit command."""
        if isinstance(error, MissingPermissions):
            await ctx.send("❌ You do not have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                "❌ Invalid channel specified. Please mention a valid text channel.",
            )
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
            logger.error(f"Error in remove_limit command: {error}")

    @commands.cooldown(rate=2, per=10, type=commands.BucketType.user)
    @commands.command(name="chainmenu")
    @admin_or_owner()
    async def chain_menu(self, ctx):
        """Open the interactive chain management panel."""
        view = _ChainMenuView(ctx, self)
        embed = await view.build_embed()
        await send_panel(ctx, embed=embed, view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the chain management panel)."""
        view = _ChainMenuView(help_ctx_shim(interaction), self)
        embed = await view.build_embed()
        return embed, view

    @chain.command(name="list")  # type: ignore[arg-type]
    async def list_chains(self, ctx):
        """List all active chains and word limits in the server.

        **Usage:** `!chain list`
        """
        channels = await db.get_all_chain_channels(ctx.guild.id)

        if not channels:
            await ctx.send(
                "ℹ️ There are no active chains or word limits in this server.",
            )
            return

        embed = discord.Embed(
            title="Active Chains and Word Limits",
            color=discord.Color.green(),
        )

        for entry in channels:
            channel = self.bot.get_channel(entry["channel_id"])
            word = entry.get("word")
            limit = entry.get("word_limit")
            description = ""
            if word:
                description += f"Allowed Word: `{word}`\n"
            if limit:
                description += f"Word Limit: `{limit}` words\n"
            if not description:
                description = "No restrictions set."
            if channel:
                embed.add_field(name=channel.name, value=description, inline=False)
            else:
                embed.add_field(
                    name="Unknown Channel",
                    value=f"Channel ID: `{entry['channel_id']}`\n{description}",
                    inline=False,
                )

        await ctx.send(embed=embed)

    async def _process_chain_message(self, message) -> bool:
        """Enforce chain rules and word limits.  Returns True iff deleted.

        Called by :class:`ChainStage` from the message pipeline.
        The pipeline pre-filters bot authors so we don't re-check.

        Command messages (resolved via ``bot.get_context``) are passed
        through unchanged — chain rules apply only to plain content.
        """
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return False  # Don't process command messages

        channel_data = await db.get_chain_channel(message.channel.id)
        if not channel_data:
            return False  # No chain or limit set for this channel

        allowed_word = channel_data.get("word")
        word_limit = channel_data.get("word_limit")

        delete_message = False
        if allowed_word and message.content.strip().lower() != allowed_word.lower():
            delete_message = True
        if word_limit and len(message.content.strip().split()) > word_limit:
            delete_message = True

        if not delete_message:
            await chain_service.record_chain_progress(message.channel.id)
            return False  # Message is allowed

        # Compose the human-readable warning + audit reason.
        warning_message = f"{message.author.mention}, your message was deleted."
        if allowed_word and word_limit:
            warning_message += (
                f" Only the word `{allowed_word}` is allowed, and messages must "
                f"be at most {word_limit} words."
            )
        elif allowed_word:
            warning_message += (
                f" Only the word `{allowed_word}` is allowed in this channel."
            )
        elif word_limit:
            warning_message += f" Messages must be at most {word_limit} words."

        # Route through moderation_service so the removal lands in
        # mod_logs + emits EVT_MOD_ACTION (§2.2 gap closed).
        ok = await moderation_service.auto_delete(
            message,
            reason=warning_message,
            rule="chain.violation",
        )
        if not ok:
            return False

        try:
            warning = await message.channel.send(warning_message)
            await asyncio.sleep(5)
            await warning.delete()
        except discord.Forbidden:
            logger.warning(
                "Missing permissions to post chain warning in %s.",
                message.channel,
            )
        except discord.HTTPException as exc:
            logger.error(
                "Failed to post chain warning in %s: %s",
                message.channel,
                exc,
            )
        return True

    @commands.Cog.listener()
    async def on_ready(self):
        """Event handler when the cog is ready."""
        logger.info(f"{self.__class__.__name__} is ready and operational.")


def _resolve_channel(
    interaction: discord.Interaction,
    raw: str,
) -> discord.TextChannel | None:
    raw = raw.strip()
    if not raw:
        return interaction.channel  # type: ignore[return-value]
    stripped = raw.strip("<#>")
    if stripped.isdigit():
        return resources.resolve_channel(  # type: ignore[return-value]
            interaction.guild,
            channel_id=stripped,
        )
    return resources.resolve_channel(  # type: ignore[return-value]
        interaction.guild,
        name=raw,
        kind="text",
    )


class _CreateChainModal(discord.ui.Modal, title="Create Chain"):  # type: ignore[call-arg]
    channel_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Channel (mention/ID, blank = current)",
        max_length=40,
        required=False,
    )
    word_input = discord.ui.TextInput(label="Allowed word", max_length=100)  # type: ignore[var-annotated]

    def __init__(self, cog: ChainCog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        channel = _resolve_channel(interaction, self.channel_input.value)
        if not channel:
            await interaction.response.send_message(
                "❌ Channel not found.",
                ephemeral=True,
            )
            return
        result = await chain_service.create_chain(
            guild_id=interaction.guild_id,
            channel_id=channel.id,
            word=self.word_input.value,
            actor_id=interaction.user.id,
        )
        if result.status == "already_exists":
            await interaction.response.send_message(
                f"❌ A chain is already active in {channel.mention}.",
                ephemeral=True,
            )
            return
        if result.status == "invalid":
            await interaction.response.send_message(
                "❌ Please provide a non-empty word.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"✅ Chain created in {channel.mention}. Only `{result.new_value}` is allowed.",
            ephemeral=True,
        )


class _DeleteChainModal(discord.ui.Modal, title="Delete Chain"):  # type: ignore[call-arg]
    channel_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Channel (mention/ID, blank = current)",
        max_length=40,
        required=False,
    )

    def __init__(self, cog: ChainCog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        channel = _resolve_channel(interaction, self.channel_input.value)
        if not channel:
            await interaction.response.send_message(
                "❌ Channel not found.",
                ephemeral=True,
            )
            return
        result = await chain_service.delete_chain(
            guild_id=interaction.guild_id,
            channel_id=channel.id,
            actor_id=interaction.user.id,
        )
        if not result.applied:
            await interaction.response.send_message(
                f"❌ No active chain found in {channel.mention}.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"✅ Chain deleted from {channel.mention}.",
            ephemeral=True,
        )


class _SetLimitModal(discord.ui.Modal, title="Set Word Limit"):  # type: ignore[call-arg]
    channel_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Channel (mention/ID, blank = current)",
        max_length=40,
        required=False,
    )
    limit_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Word limit (0 = remove limit)",
        max_length=10,
    )

    def __init__(self, cog: ChainCog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        channel = _resolve_channel(interaction, self.channel_input.value)
        if not channel:
            await interaction.response.send_message(
                "❌ Channel not found.",
                ephemeral=True,
            )
            return
        if not self.limit_input.value.strip().isdigit():
            await interaction.response.send_message(
                "❌ Limit must be a non-negative integer.",
                ephemeral=True,
            )
            return
        limit = int(self.limit_input.value.strip())
        result = await chain_service.set_word_limit(
            guild_id=interaction.guild_id,
            channel_id=channel.id,
            limit=limit,
            actor_id=interaction.user.id,
        )
        if result.status == "not_found":
            await interaction.response.send_message(
                f"❌ No active chain in {channel.mention}. Create one first.",
                ephemeral=True,
            )
            return
        if limit == 0:
            await interaction.response.send_message(
                f"✅ Word limit removed from {channel.mention}.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"✅ Word limit set to {limit} words in {channel.mention}.",
                ephemeral=True,
            )


class _ClearLimitModal(discord.ui.Modal, title="Clear Word Limit"):  # type: ignore[call-arg]
    channel_input = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Channel (mention/ID, blank = current)",
        max_length=40,
        required=False,
    )

    def __init__(self, cog: ChainCog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        channel = _resolve_channel(interaction, self.channel_input.value)
        if not channel:
            await interaction.response.send_message(
                "❌ Channel not found.",
                ephemeral=True,
            )
            return
        result = await chain_service.set_word_limit(
            guild_id=interaction.guild_id,
            channel_id=channel.id,
            limit=0,
            actor_id=interaction.user.id,
        )
        if not result.applied:
            # not_found / no_change — nothing was set, matching legacy copy.
            await interaction.response.send_message(
                f"ℹ️ No word limit is set in {channel.mention}.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"✅ Word limit removed from {channel.mention}.",
            ephemeral=True,
        )


class _ChainMenuView(HubView):
    """Interactive chain channel management panel."""

    def __init__(self, ctx: commands.Context, cog: ChainCog):
        super().__init__(ctx.author)
        self.ctx = ctx
        self.cog = cog

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # The typed chain commands are admin-only; this panel is also reachable
        # via the Help menu (build_help_menu_view), which is not admin-gated, so
        # re-check authority on every button — BaseView only locks to the invoker.
        if not await super().interaction_check(interaction):
            return False
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "Chain management is admin-only.",
                ephemeral=True,
            )
            return False
        return True

    async def build_embed(self) -> discord.Embed:
        channels = await db.get_all_chain_channels(self.ctx.guild.id)
        embed = discord.Embed(title="⛓️ Chain Manager", color=discord.Color.blue())
        if not channels:
            embed.description = "No active chains in this server."
        else:
            lines = []
            for entry in channels:
                ch = self.cog.bot.get_channel(entry["channel_id"])
                name = ch.mention if ch else f"<#{entry['channel_id']}>"
                parts = []
                if entry.get("word"):
                    parts.append(f"word: `{entry['word']}`")
                if entry.get("word_limit"):
                    parts.append(f"limit: `{entry['word_limit']}`")
                lines.append(f"{name} — {', '.join(parts) or 'no restrictions'}")
            embed.description = "\n".join(lines)
        embed.set_footer(text="Use buttons below to manage chains.")
        return embed

    @discord.ui.button(label="➕ Create Chain", style=discord.ButtonStyle.green, row=0)
    async def btn_create(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_CreateChainModal(self.cog))

    @discord.ui.button(label="🗑️ Delete Chain", style=discord.ButtonStyle.danger, row=0)
    async def btn_delete(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_DeleteChainModal(self.cog))

    @discord.ui.button(label="📏 Set Limit", style=discord.ButtonStyle.blurple, row=0)
    async def btn_setlimit(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await interaction.response.send_modal(_SetLimitModal(self.cog))

    @discord.ui.button(
        label="🚫 Clear Limit",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def btn_clearlimit(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await interaction.response.send_modal(_ClearLimitModal(self.cog))

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=1)
    async def btn_refresh(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.edit_message(
            embed=await self.build_embed(),
            view=self,
        )


# Asynchronous setup for discord.py 2.x
async def setup(bot):
    await bot.add_cog(ChainCog(bot))
    logger.info("ChainCog has been loaded.")
