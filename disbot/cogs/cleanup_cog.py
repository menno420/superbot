from __future__ import annotations

import asyncio
import logging
import re

import discord
from discord.ext import commands

import config as _config
from core.runtime.interaction_helpers import help_ctx_shim, safe_defer
from core.runtime.message_pipeline import (
    MessagePipelineContext,
    StageResult,
)
from services import governance_service, moderation_service
from services.governance_service import GovernanceContext
from services.history_cleanup import build_history_cleanup_plan
from utils import db
from utils.ui_constants import ADMIN_COLOR
from views.base import HubView, send_panel

CLEANUP_STAGE_NAME = "cleanup"
CLEANUP_STAGE_ORDER = 10  # moderation tier per plan §3.2
MAX_CLEANUP_HISTORY_LIMIT = 1000
SPAM_DUPLICATE_WINDOW_SECONDS = 15
HELPER_DELETE_DELAY_SECONDS = 3


def _extract_command_name(content: str, prefixes: list[str]) -> str | None:
    """Extract the bare command name from a prefixed message."""
    for prefix in prefixes:
        if content.startswith(prefix):
            rest = (
                content[len(prefix) :].split()[0]
                if content[len(prefix) :].strip()
                else ""
            )
            return rest.lower() if rest else None
    return None


class CleanupStage:
    """Message-pipeline stage wrapping the existing remove_unwanted_message logic.

    Auto-mod tier (order=10).  Short-circuits the pipeline when a deletion
    happens so downstream stages (XP reward, RPS input) skip a message
    that's already been removed.

    The stage holds a reference to the cog because the auto-mod rules
    depend on per-cog state (compiled command pattern, whitelisted
    channels, per-guild prohibited-word caches).
    """

    name = CLEANUP_STAGE_NAME
    order = CLEANUP_STAGE_ORDER

    def __init__(self, cog: Cleanup):
        self.cog = cog

    async def process(self, ctx: MessagePipelineContext) -> StageResult:
        deleted = await self.cog.remove_unwanted_message(ctx.message)
        if deleted:
            return StageResult(deleted=True, short_circuit=True)
        return StageResult()


class Cleanup(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.logger = logging.getLogger(__name__)

        # Per-guild caches: guild_id → (words, patterns)
        self._word_cache: dict[int, list[str]] = {}
        self._pattern_cache: dict[int, list] = {}

        self.command_prefixes = ["?", "!"]
        self.command_pattern = re.compile(
            rf'^\s*({"|".join(map(re.escape, self.command_prefixes))})\S+',
            re.IGNORECASE,
        )

        self.whitelisted_channels = _config.CLEANUP_WHITELIST_CHANNELS

    async def cog_load(self) -> None:
        from core.runtime import message_pipeline

        message_pipeline.register(CleanupStage(self))

    async def cog_unload(self) -> None:
        from core.runtime import message_pipeline

        message_pipeline.unregister(CLEANUP_STAGE_NAME)

    async def _load_guild(self, guild_id: int) -> None:
        words = await db.get_prohibited_words(guild_id)
        self._word_cache[guild_id] = words
        self._pattern_cache[guild_id] = [
            re.compile(rf"\b{re.escape(w)}\b", re.IGNORECASE) for w in words
        ]

    async def _get_patterns(self, guild_id: int) -> list:
        if guild_id not in self._pattern_cache:
            await self._load_guild(guild_id)
        return self._pattern_cache[guild_id]

    async def remove_unwanted_message(self, message):
        """Delete message if it is a command in a governed channel or contains prohibited content.

        Deletions route through :func:`moderation_service.auto_delete` so the
        ``mod_logs`` audit table and ``EVT_MOD_ACTION`` event bus see every
        auto-mod removal — closing the gap §2.2 of the plan called out
        (CleanupCog deletes were previously invisible to moderation audit).
        """
        if message.author.bot:
            return False

        if self.command_pattern.match(message.content):
            command_name = _extract_command_name(
                message.content.strip(),
                self.command_prefixes,
            )
            if message.guild and command_name:
                # Route through governance_service for policy-driven decision
                gctx = GovernanceContext.from_message(message)
                policy = await governance_service.resolve_command_policy(
                    gctx,
                    command_name,
                )
                if not policy.allowed:
                    if policy.cleanup.delete_message:
                        await moderation_service.auto_delete(
                            message,
                            reason=f"Blocked command: {command_name}",
                            rule="cleanup.command_policy",
                        )
                    if policy.feedback:
                        try:
                            warn = await message.channel.send(policy.feedback)
                            await warn.delete(
                                delay=policy.cleanup.delete_after_seconds,
                            )
                        except discord.DiscordException as e:
                            self.logger.error("Cleanup feedback error: %s", e)
                    return True
                return False
            # DM or unknown guild — fall back to whitelist behavior
            if message.channel.id not in self.whitelisted_channels:
                await moderation_service.auto_delete(
                    message,
                    reason="Command-style message in non-whitelisted channel",
                    rule="cleanup.whitelist",
                )
                return True
            return False

        guild_id = message.guild.id if message.guild else 0
        for pattern in await self._get_patterns(guild_id):
            if pattern.search(message.content):
                await moderation_service.auto_delete(
                    message,
                    reason="Prohibited word match",
                    rule="cleanup.prohibited_words",
                )
                try:
                    warning_msg = await message.channel.send(
                        f"A message from {message.author.mention} was deleted "
                        "because it contained prohibited content.",
                    )
                    await warning_msg.delete(delay=10)
                except discord.DiscordException as e:
                    self.logger.error(
                        "Failed to post prohibited-word warning: %s",
                        e,
                    )
                return True

        return False

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        self._word_cache.pop(guild.id, None)
        self._pattern_cache.pop(guild.id, None)

    @commands.command(name="cleanuphistory")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def cleanup_history(self, ctx, limit: int = 100, *, keyword: str = None):
        """Clean matching channel history by keyword, commands, or prohibited words."""
        if limit <= 0:
            await ctx.send(
                "Please provide a positive number of messages to scan.",
                delete_after=5,
            )
            return

        if limit > MAX_CLEANUP_HISTORY_LIMIT:
            await ctx.send(
                f"⚠️ Limit capped at {MAX_CLEANUP_HISTORY_LIMIT}; scanning that many messages.",
                delete_after=7,
            )
            limit = MAX_CLEANUP_HISTORY_LIMIT

        raw_filter = (keyword or "").strip()
        parts = raw_filter.split(maxsplit=1) if raw_filter else []
        mode = "prohibited"
        query: str | None = None
        if parts and parts[0].lower() in {"keyword", "commands", "prohibited", "spam"}:
            mode = parts[0].lower()
            query = parts[1] if len(parts) > 1 else None
        elif raw_filter:
            mode = "keyword"
            query = raw_filter

        if mode == "keyword" and not query:
            await ctx.send(
                "Usage: `!cleanuphistory <limit> keyword <text>` "
                f"(limit max: {MAX_CLEANUP_HISTORY_LIMIT}).",
                delete_after=7,
            )
            return

        perms = getattr(ctx.channel, "permissions_for", lambda _a: None)(ctx.guild.me)
        if perms is not None and not perms.manage_messages:
            warning_msg = await ctx.send(
                "❌ I need **Manage Messages** in this channel to run cleanuphistory.",
            )
            await self._delete_helper_messages_later(ctx, warning_msg)
            return

        prohibited_words = await db.get_prohibited_words(ctx.guild.id)
        plan = await build_history_cleanup_plan(
            ctx.channel,
            limit=limit,
            mode=mode,
            keyword=query,
            command_prefixes=self.command_prefixes,
            prohibited_words=prohibited_words,
            exclude_message_ids={ctx.message.id},
            spam_duplicate_window_seconds=SPAM_DUPLICATE_WINDOW_SECONDS,
        )
        final_msg = None
        confirmation_msg = None
        if not plan.matched:
            final_msg = await ctx.send(
                f"Scanned {plan.scanned} messages. Matched 0 messages for `{mode}`.",
            )
            await self._delete_helper_messages_later(ctx, final_msg)
            return

        confirmation_msg = await ctx.send(
            f"Scanned {plan.scanned} messages and matched {len(plan.matched)} "
            f"for `{mode}`. Delete matched messages? React ✅ to confirm or ❌ to cancel.",
        )
        await confirmation_msg.add_reaction("✅")
        await confirmation_msg.add_reaction("❌")

        def check(reaction, user):
            return (
                user == ctx.author
                and str(reaction.emoji) in ["✅", "❌"]
                and reaction.message.id == confirmation_msg.id
            )

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add",
                timeout=30.0,
                check=check,
            )
            if str(reaction.emoji) == "✅":
                deleted = 0
                failed = 0
                for message in plan.matched:
                    try:
                        await message.delete()
                        deleted += 1
                    except discord.Forbidden:
                        failed += 1
                        self.logger.warning(
                            "cleanuphistory missing Manage Messages in #%s (%s)",
                            getattr(ctx.channel, "name", "unknown"),
                            getattr(ctx.channel, "id", "unknown"),
                        )
                    except discord.HTTPException:
                        failed += 1
                final_msg = await ctx.send(
                    f"Cleanup completed. Deleted {deleted} message(s), failed {failed}.",
                )
                self.logger.info(
                    "Cleanup history completed in %s: scanned=%s matched=%s deleted=%s failed=%s mode=%s",
                    ctx.channel.name,
                    plan.scanned,
                    len(plan.matched),
                    deleted,
                    failed,
                    mode,
                )
            else:
                final_msg = await ctx.send("Cleanup canceled.")
        except asyncio.TimeoutError:
            final_msg = await ctx.send("Cleanup confirmation timed out.")
        finally:
            await self._delete_helper_messages_later(ctx, confirmation_msg, final_msg)

    async def _delete_helper_messages_later(self, ctx, *messages) -> None:
        await asyncio.sleep(HELPER_DELETE_DELAY_SECONDS)
        for msg in [*messages, getattr(ctx, "message", None)]:
            if msg is None:
                continue
            try:
                await msg.delete()
            except discord.NotFound:
                continue
            except discord.Forbidden:
                self.logger.warning("cleanuphistory could not delete helper message (Forbidden).")
            except discord.HTTPException as exc:
                self.logger.warning("cleanuphistory helper delete failed: %s", exc)

    @commands.group(name="word", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def word_cmd(self, ctx):
        """Manage prohibited words. Subcommands: add, remove, list."""
        guild_id = ctx.guild.id
        if guild_id not in self._word_cache:
            await self._load_guild(guild_id)
        words = self._word_cache[guild_id]
        if words:
            word_list = ", ".join(f"`{w}`" for w in sorted(words))
            await ctx.send(f"Prohibited words: {word_list}", delete_after=15)
        else:
            await ctx.send("No prohibited words are currently set.", delete_after=10)

    @word_cmd.command(name="add")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def word_add(self, ctx, *, word: str):
        """Adds a word to the prohibited words list."""
        word = word.lower()
        added = await db.add_prohibited_word(ctx.guild.id, word)
        if added:
            await self._load_guild(ctx.guild.id)
            await ctx.send(
                f"Added '{word}' to the prohibited words list.",
                delete_after=5,
            )
            self.logger.info(f"Added prohibited word: {word}")
        else:
            await ctx.send(
                f"The word '{word}' is already in the prohibited list.",
                delete_after=5,
            )

    @word_cmd.command(name="remove")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def word_remove(self, ctx, *, word: str):
        """Removes a word from the prohibited words list."""
        word = word.lower()
        removed = await db.remove_prohibited_word(ctx.guild.id, word)
        if removed:
            await self._load_guild(ctx.guild.id)
            await ctx.send(
                f"Removed '{word}' from the prohibited words list.",
                delete_after=5,
            )
            self.logger.info(f"Removed prohibited word: {word}")
        else:
            await ctx.send(
                f"The word '{word}' is not in the prohibited list.",
                delete_after=5,
            )

    @word_cmd.command(name="list")  # type: ignore[arg-type]
    @commands.has_permissions(administrator=True)
    async def word_list(self, ctx):
        """Shows all prohibited words."""
        guild_id = ctx.guild.id
        if guild_id not in self._word_cache:
            await self._load_guild(guild_id)
        words = self._word_cache[guild_id]
        if words:
            word_list = ", ".join(f"`{w}`" for w in sorted(words))
            await ctx.send(f"Prohibited words: {word_list}", delete_after=15)
        else:
            await ctx.send("No prohibited words are currently set.", delete_after=10)

    @commands.command(name="wordmenu")
    @commands.has_permissions(administrator=True)
    async def word_menu(self, ctx):
        """Open the interactive prohibited words management panel."""
        if ctx.guild.id not in self._word_cache:
            await self._load_guild(ctx.guild.id)
        view = _WordMenuView(ctx, self)
        await send_panel(ctx, embed=view.build_embed(), view=view)

    @commands.command(name="cleanup")
    @commands.has_permissions(administrator=True)
    async def cleanup_menu(self, ctx):
        """Open the Cleanup hub panel — overview + routing to subviews."""
        from cogs.cleanup.panel import CleanupPanelView

        if ctx.guild.id not in self._word_cache:
            await self._load_guild(ctx.guild.id)
        view = CleanupPanelView(ctx.author, self, ctx.guild.id)
        await send_panel(ctx, embed=view.build_embed(), view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — returns the Cleanup hub panel.

        Phase 5 replaces the previous direct-to-wordmenu hop. The
        Prohibited Words manager is now reachable as the first button
        of :class:`CleanupPanelView`, alongside Logging Status and
        Settings.
        """
        from cogs.cleanup.panel import CleanupPanelView

        if interaction.guild_id not in self._word_cache:
            await self._load_guild(interaction.guild_id)
        ctx_shim = help_ctx_shim(interaction)
        view = CleanupPanelView(ctx_shim.author, self, interaction.guild_id)
        return view.build_embed(), view


class _AddWordModal(discord.ui.Modal, title="Add Prohibited Word"):  # type: ignore[call-arg]
    word_input = discord.ui.TextInput(label="Word to prohibit", max_length=100)  # type: ignore[var-annotated]

    def __init__(self, cog: Cleanup):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        word = self.word_input.value.lower().strip()
        added = await db.add_prohibited_word(interaction.guild_id, word)
        if added:
            await self.cog._load_guild(interaction.guild_id)
            await interaction.response.send_message(
                f"✅ Added `{word}` to the prohibited list.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ `{word}` is already in the prohibited list.",
                ephemeral=True,
            )


class _RemoveWordModal(discord.ui.Modal, title="Remove Prohibited Word"):  # type: ignore[call-arg]
    word_input = discord.ui.TextInput(label="Word to remove", max_length=100)  # type: ignore[var-annotated]

    def __init__(self, cog: Cleanup):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        word = self.word_input.value.lower().strip()
        removed = await db.remove_prohibited_word(interaction.guild_id, word)
        if removed:
            await self.cog._load_guild(interaction.guild_id)
            await interaction.response.send_message(
                f"✅ Removed `{word}` from the prohibited list.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ `{word}` was not in the prohibited list.",
                ephemeral=True,
            )


class _WordMenuView(HubView):
    """Interactive prohibited-words management panel."""

    def __init__(self, ctx: commands.Context, cog: Cleanup):
        super().__init__(ctx.author)
        self.ctx = ctx
        self.cog = cog

    def build_embed(self) -> discord.Embed:
        words = self.cog._word_cache.get(self.ctx.guild.id, [])
        embed = discord.Embed(title="🔤 Prohibited Words Manager", color=ADMIN_COLOR)
        if words:
            embed.add_field(
                name="Current Words",
                value=", ".join(f"`{w}`" for w in sorted(words))[:1000],
                inline=False,
            )
        else:
            embed.description = "No prohibited words are currently set."
        embed.set_footer(text="Use buttons below to manage prohibited words.")
        return embed

    @discord.ui.button(label="➕ Add Word", style=discord.ButtonStyle.green, row=0)
    async def btn_add(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_AddWordModal(self.cog))

    @discord.ui.button(label="➖ Remove Word", style=discord.ButtonStyle.danger, row=0)
    async def btn_remove(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_RemoveWordModal(self.cog))

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=0)
    async def btn_refresh(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.cog._load_guild(self.ctx.guild.id)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(
        label="🔍 Scan History",
        style=discord.ButtonStyle.blurple,
        row=1,
    )
    async def btn_scan(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_ScanHistoryModal(self.cog))


class _ScanHistoryModal(discord.ui.Modal, title="Scan Channel History"):  # type: ignore[call-arg]
    limit = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Messages to scan (1–500)",
        placeholder="100",
        default="100",
        max_length=3,
    )
    keyword = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Keyword filter (optional)",
        placeholder="Leave blank to scan all messages",
        required=False,
        max_length=100,
    )

    def __init__(self, cog: Cleanup):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:  # type: ignore[union-attr]
            await interaction.response.send_message(
                "❌ You need **Manage Messages** permission to scan history.",
                ephemeral=True,
            )
            return

        try:
            scan_limit = int(self.limit.value.strip())
            if not 1 <= scan_limit <= 500:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Limit must be a number between 1 and 500.",
                ephemeral=True,
            )
            return

        kw = self.keyword.value.strip().lower() if self.keyword.value.strip() else None

        if not await safe_defer(interaction, ephemeral=True):
            return

        scanned = 0
        deleted = 0
        async for message in interaction.channel.history(limit=scan_limit):  # type: ignore[union-attr]
            if message.author.bot:
                continue
            if kw and kw not in message.content.lower():
                continue
            scanned += 1
            if await self.cog.remove_unwanted_message(message):
                deleted += 1

        filter_note = f" (filtered by `{kw}`)" if kw else ""
        await interaction.followup.send(
            f"✅ Scanned **{scanned}** messages{filter_note}. Deleted **{deleted}**.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Cleanup(bot))
