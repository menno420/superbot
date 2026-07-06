from __future__ import annotations

import asyncio
import datetime as dt
import logging
import re

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import help_ctx_shim, safe_defer
from core.runtime.message_pipeline import (
    MessagePipelineContext,
    StageResult,
)
from core.runtime.permission_checks import admin_or_owner, perms_or_owner
from services import governance_service, moderation_service, prohibited_words_service
from services.governance_service import GovernanceContext
from services.history_cleanup import (
    HISTORY_CLEANUP_MODES,
    build_history_cleanup_plan,
)
from utils import db
from utils.text_obfuscation import find_obfuscated_match
from utils.ui_constants import ADMIN_COLOR
from views.base import HubView, send_panel

CLEANUP_STAGE_NAME = "cleanup"
# Auto-mod tier — runs first within the tier so a banned word is deleted
# before counting/chain try to validate the same message. See the canonical
# stage-order table in core/runtime/message_pipeline.py.
CLEANUP_STAGE_ORDER = 10
MAX_CLEANUP_HISTORY_LIMIT = 1000
HELPER_DELETE_DELAY_SECONDS = 3
# How long the "commands aren't allowed here" notice stays before self-deleting.
_BLOCKED_COMMAND_NOTICE_SECONDS = 8


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


_DURATION_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _parse_duration_seconds(raw: str) -> int | None:
    """Parse a short duration like ``7d`` / ``12h`` / ``30m`` / ``45s`` / ``90``.

    Returns the duration in seconds, or ``None`` if *raw* is not a positive
    duration. A bare integer is read as seconds. Used by the ``!cleanuphistory``
    ``older:<duration>`` age gate.
    """
    raw = raw.strip().lower()
    if not raw:
        return None
    unit_seconds = 1
    if raw[-1] in _DURATION_UNIT_SECONDS:
        unit_seconds = _DURATION_UNIT_SECONDS[raw[-1]]
        raw = raw[:-1]
    if not raw.isdigit():
        return None
    value = int(raw)
    if value <= 0:
        return None
    return value * unit_seconds


async def _resolve_spam_window(guild_id: int) -> int:
    """Resolve the per-guild ``!cleanuphistory`` spam-duplicate window (seconds).

    Reads the ``cleanup_spam_window_seconds`` scalar setting via the canonical
    :func:`services.settings_resolution.resolve_value`, which falls back to the
    declared :class:`SettingSpec` default (15s) when unset or malformed — so a
    fresh guild behaves byte-identically to the old hardcoded constant.
    """
    from cogs.cleanup.schemas import DEFAULT_SPAM_WINDOW_SECONDS
    from services.settings_resolution import resolve_value

    return await resolve_value(
        guild_id,
        "cleanup",
        "spam_window_seconds",
        DEFAULT_SPAM_WINDOW_SECONDS,
    )


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

        # Per-guild caches: guild_id → (words, patterns, strict-mode flag)
        self._word_cache: dict[int, list[str]] = {}
        self._pattern_cache: dict[int, list] = {}
        self._strict_cache: dict[int, bool] = {}

        self.command_prefixes = ["?", "!"]
        self.command_pattern = re.compile(
            rf"^\s*({'|'.join(map(re.escape, self.command_prefixes))})\S+",
            re.IGNORECASE,
        )

    async def cog_load(self) -> None:
        from cogs.cleanup.schemas import register_schemas
        from core.runtime import message_pipeline

        register_schemas()  # Settings Phase 2 — declares the domain panel.
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
        self._strict_cache[guild_id] = await db.get_wordfilter_strict(guild_id)

    async def _get_patterns(self, guild_id: int) -> list:
        if guild_id not in self._pattern_cache:
            await self._load_guild(guild_id)
        return self._pattern_cache[guild_id]

    async def _get_strict(self, guild_id: int) -> bool:
        """Whether obfuscation-resistant (anti-evasion) matching is enabled."""
        if guild_id not in self._strict_cache:
            await self._load_guild(guild_id)
        return self._strict_cache[guild_id]

    async def _delete_if_command_blocked(self, message, command_name: str) -> bool:
        """Delete a command-style message when Command Access denies it here.

        Opt-in per guild via the ``delete_blocked_commands`` toggle on the
        Command Access policy.  Only deletes for a genuine channel/disabled
        denial (``CHANNEL_NOT_ALLOWED`` / ``COMMANDS_DISABLED``) — bootstrap
        commands by operators are admitted by the resolver and never reach
        here, and DM/lifecycle denials are ignored.  A brief notice is posted
        and auto-deleted so the user learns why their message vanished.

        Returns ``True`` when it deleted the message (caller should stop).
        """
        from core.runtime import command_access
        from utils.guild_config_accessors import get_command_access_policy

        try:
            snapshot = await get_command_access_policy(message.guild.id)
        except Exception:  # noqa: BLE001 — never crash auto-mod on a policy read
            self.logger.debug(
                "command-access snapshot read failed; skipping delete-blocked check",
                exc_info=True,
            )
            return False
        if not snapshot.delete_blocked_commands:
            return False

        ctx = await command_access.from_message(
            message,
            command_name,
            bot=self.bot,
        )
        decision = await command_access.resolve_command_access(ctx)
        if decision.allowed:
            return False
        if decision.reason not in (
            command_access.DecisionReason.CHANNEL_NOT_ALLOWED,
            command_access.DecisionReason.COMMANDS_DISABLED,
        ):
            return False

        await moderation_service.auto_delete(
            message,
            reason=f"Command not allowed in this channel: {command_name}",
            rule="cleanup.command_access",
        )
        if decision.feedback:
            try:
                warn = await message.channel.send(decision.feedback)
                await warn.delete(delay=_BLOCKED_COMMAND_NOTICE_SECONDS)
            except discord.DiscordException as e:
                self.logger.error("Cleanup command-access notice error: %s", e)
        return True

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
                # Command Access: if this guild opted in to deleting blocked
                # commands, and Command Access denies this command in this
                # channel, delete it on sight (restores the old-bot behaviour:
                # "instantly delete commands where commands aren't allowed").
                if await self._delete_if_command_blocked(message, command_name):
                    return True
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
            # No guild context or an unparseable command name → we can't make a
            # governance-policy decision, so we don't auto-delete.  (Cleanup is
            # policy-driven: the old hardcoded channel whitelist that used to
            # delete command-style messages here was removed — exempt a channel
            # by setting its cleanup policy to Off instead.)
            return False

        guild_id = message.guild.id if message.guild else 0

        # Exact pass (default, always on): \bword\b on the raw content.
        for pattern in await self._get_patterns(guild_id):
            if pattern.search(message.content):
                return await self._delete_prohibited(message)

        # Anti-evasion pass (opt-in, migration 097): de-obfuscate the message
        # and re-match, catching leet / unicode-confusable / invisible-character
        # / spaced-letter bypasses that walk straight through the exact match.
        # ``_get_patterns`` above already triggered ``_load_guild`` (which
        # populates the strict-mode cache) on the first message per guild, so
        # read the flag directly — no second DB round-trip on the hot path.
        if self._strict_cache.get(guild_id, False):
            words = self._word_cache.get(guild_id) or []
            if find_obfuscated_match(message.content, words) is not None:
                return await self._delete_prohibited(message)

        return False

    async def _delete_prohibited(self, message) -> bool:
        """Remove a prohibited-word match (audited) and post a brief notice.

        Shared by the exact and anti-evasion passes so both route through one
        ``moderation_service.auto_delete`` seam (``mod_logs`` + ``EVT_MOD_ACTION``).
        """
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
            self.logger.error("Failed to post prohibited-word warning: %s", e)
        return True

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        self._word_cache.pop(guild.id, None)
        self._pattern_cache.pop(guild.id, None)
        self._strict_cache.pop(guild.id, None)

    @commands.command(name="cleanuphistory")
    @perms_or_owner(manage_messages=True)
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def cleanup_history(self, ctx, limit: int = 100, *, keyword: str = None):
        """Clean channel history by keyword, commands, prohibited words, spam, embeds, links, or attachments.

        Modes: `keyword <text>` · `commands` · `prohibited` (default) · `spam` ·
        `embeds` · `links` · `attachments`. Add `older:<duration>` (e.g.
        `older:7d`, `older:12h`) to restrict the sweep to messages at least that old.
        """
        if limit <= 0:
            await ctx.send(
                "Please provide a positive number of messages to scan.",
                delete_after=5,
            )
            return

        requested_limit = limit
        effective_limit = min(requested_limit, MAX_CLEANUP_HISTORY_LIMIT)
        if requested_limit > MAX_CLEANUP_HISTORY_LIMIT:
            await ctx.send(
                f"⚠️ Requested {requested_limit} messages. Maximum is "
                f"{MAX_CLEANUP_HISTORY_LIMIT}, so I will scan {effective_limit}.",
                delete_after=7,
            )

        raw_filter = (keyword or "").strip()
        tokens = raw_filter.split() if raw_filter else []

        # Pull out an optional `older:<duration>` age gate (e.g. `older:7d`),
        # composable with any mode. It is removed from the tokens before the
        # mode/keyword are resolved so it never leaks into a keyword search.
        older_than: dt.datetime | None = None
        kept_tokens: list[str] = []
        for token in tokens:
            if token.lower().startswith("older:"):
                seconds = _parse_duration_seconds(token.split(":", 1)[1])
                if seconds is None:
                    await ctx.send(
                        "Usage: `older:<duration>` like `older:7d`, `older:12h`, "
                        "`older:30m` (units d/h/m/s, or plain seconds).",
                        delete_after=7,
                    )
                    return
                older_than = discord.utils.utcnow() - dt.timedelta(seconds=seconds)
            else:
                kept_tokens.append(token)

        mode = "prohibited"
        query: str | None = None
        if kept_tokens and kept_tokens[0].lower() in HISTORY_CLEANUP_MODES:
            mode = kept_tokens[0].lower()
            query = " ".join(kept_tokens[1:]) or None
        elif kept_tokens:
            mode = "keyword"
            query = " ".join(kept_tokens)

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
        spam_window = await _resolve_spam_window(ctx.guild.id)
        plan = await build_history_cleanup_plan(
            ctx.channel,
            limit=effective_limit,
            mode=mode,
            keyword=query,
            command_prefixes=self.command_prefixes,
            prohibited_words=prohibited_words,
            exclude_message_ids={ctx.message.id},
            spam_duplicate_window_seconds=spam_window,
            older_than=older_than,
        )
        final_msg = None
        confirmation_msg = None
        if not plan.matched:
            final_msg = await ctx.send(
                f"Scanned {plan.scanned} message(s) (requested {requested_limit}, "
                f"effective {effective_limit}). Matched 0 messages for `{mode}`.",
            )
            await self._delete_helper_messages_later(ctx, final_msg)
            return

        confirmation_msg = await ctx.send(
            f"Ready to scan up to {effective_limit} message(s)"
            + (
                f" (requested {requested_limit})"
                if requested_limit != effective_limit
                else ""
            )
            + f". Found {len(plan.matched)} candidate message(s) in `{mode}` mode. "
            "Delete matched messages? React ✅ to confirm or ❌ to cancel.",
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
                # Delete mechanics live in the cleanup service (one source of
                # truth shared with the moderation post-action sweep); route
                # through the audited seam so the bulk delete is recorded
                # (Stage-2 walk bug #6).
                apply_result = await moderation_service.apply_channel_cleanup(
                    plan,
                    guild_id=ctx.guild.id,
                    channel_id=ctx.channel.id,
                    actor_id=ctx.author.id,
                    mode=mode,
                )
                deleted = apply_result.deleted
                failed = apply_result.failed
                final_msg = await ctx.send(
                    f"Cleanup completed. Scanned {plan.scanned} message(s) "
                    f"(requested {requested_limit}, effective {effective_limit}). "
                    f"Deleted {deleted} message(s), failed {failed}.",
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
        for msg in [*messages, getattr(ctx, "message", None)]:
            if msg is None:
                continue
            try:
                await msg.delete(delay=HELPER_DELETE_DELAY_SECONDS)
            except discord.NotFound:
                continue
            except discord.Forbidden:
                self.logger.warning(
                    "cleanuphistory could not delete helper message (Forbidden).",
                )
            except discord.HTTPException as exc:
                self.logger.warning("cleanuphistory helper delete failed: %s", exc)

    @commands.group(name="word", invoke_without_command=True)
    @admin_or_owner()
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
    @admin_or_owner()
    async def word_add(self, ctx, *, word: str):
        """Adds a word to the prohibited words list."""
        word = word.lower()
        added = await prohibited_words_service.add_prohibited_word(
            ctx.guild.id,
            word,
            actor_id=ctx.author.id,
        )
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
    @admin_or_owner()
    async def word_remove(self, ctx, *, word: str):
        """Removes a word from the prohibited words list."""
        word = word.lower()
        removed = await prohibited_words_service.remove_prohibited_word(
            ctx.guild.id,
            word,
            actor_id=ctx.author.id,
        )
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
    @admin_or_owner()
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
    @admin_or_owner()
    async def word_menu(self, ctx):
        """Open the interactive prohibited words management panel."""
        if ctx.guild.id not in self._word_cache:
            await self._load_guild(ctx.guild.id)
        view = _WordMenuView(ctx, self)
        await send_panel(ctx, embed=view.build_embed(), view=view)

    @commands.command(name="cleanup")
    @admin_or_owner()
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
        added = await prohibited_words_service.add_prohibited_word(
            interaction.guild_id,
            word,
            actor_id=interaction.user.id,
        )
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
        removed = await prohibited_words_service.remove_prohibited_word(
            interaction.guild_id,
            word,
            actor_id=interaction.user.id,
        )
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
        strict = self.cog._strict_cache.get(self.ctx.guild.id, False)
        embed.add_field(
            name="🛡️ Anti-evasion matching",
            value=(
                "🟢 **On** — also catches leet, unicode look-alikes, "
                "invisible characters, and spaced-out letters"
                if strict
                else "⚫ **Off** — exact word match only"
            ),
            inline=False,
        )
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

    @discord.ui.button(
        label="🛡️ Anti-evasion",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def btn_strict(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        """Toggle obfuscation-resistant matching for this guild."""
        guild_id = self.ctx.guild.id
        new_value = not await self.cog._get_strict(guild_id)
        await prohibited_words_service.set_wordfilter_strict(
            guild_id,
            new_value,
            actor_id=interaction.user.id,
        )
        self.cog._strict_cache[guild_id] = new_value
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


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
