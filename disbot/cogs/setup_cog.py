"""Setup-wizard launcher cog.

Posts a persistent owner-gated launcher when the bot joins a guild and
on every subsequent ``on_ready`` for guilds whose launcher is still
``pending`` / ``in_progress``.

Wires:
* :mod:`services.setup_session` for the lifecycle row.
* :mod:`services.setup_access` for owner / admin / non-admin gating.
* :func:`services.setup_readiness.collect` for readiness scans.
* :class:`views.setup.hub.SetupHubView` for the guided setup hub.
* :mod:`services.setup_ai_advisor` and
  :class:`views.setup.ai_review.main_panel.AIReviewPanelView` for Smart
  Suggestions.
* :class:`views.setup.template_picker.TemplatePickerView` for preset
  selection.
* :mod:`views.setup.summary` for completed-setup summaries and drift review.

Interactive launcher actions:
* **Start Setup** opens the guided setup hub and marks the session in progress.
* **Run Readiness Scan** renders the deterministic setup-readiness snapshot.
* **Smart Suggestions** collects a guild snapshot and opens the AI/deterministic
  recommendation review panel.
* **Choose Preset** opens the automation-template picker.
* **View Summary** opens the completed setup summary when setup is complete.
* **Dismiss** flips ``setup_status`` to ``dismissed``; never deletes Discord
  resources or DB rows.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from services import setup_access, setup_session
from services.setup_session import SetupSession

logger = logging.getLogger("bot.cogs.setup")

_LAUNCHER_TITLE = "🛰 SuperBot setup"
_LAUNCHER_DESC = (
    "Welcome! I'll help you wire SuperBot up to this server.\n\n"
    "Use **Start Setup** for the guided walkthrough, **Run Readiness Scan** "
    "to see what's already configured, or **Dismiss** to defer."
)


def _build_launcher_embed(session: SetupSession | None) -> discord.Embed:
    color = discord.Color.blurple()
    if session is not None and session.setup_status == "complete":
        color = discord.Color.green()
    elif session is not None and session.setup_status == "dismissed":
        color = discord.Color.dark_grey()

    description = _LAUNCHER_DESC
    if session is not None:
        description = f"{_LAUNCHER_DESC}\n\n**Status:** `{session.setup_status}`"
        if session.last_readiness_score is not None:
            description += f" · readiness `{session.last_readiness_score}%`"
        if session.current_step:
            description += f" · step `{session.current_step}`"

    embed = discord.Embed(
        title=_LAUNCHER_TITLE,
        description=description,
        color=color,
    )
    embed.set_footer(
        text="Owner-gated for write actions. Admins can run the readiness scan.",
    )
    return embed


_START_LABELS_BY_STATUS = {
    "pending": "Start Setup",
    "in_progress": "Resume Setup",
    "complete": "Re-run Setup",
    "dismissed": "Start Setup",
}


class SetupLauncherView(discord.ui.View):
    """Persistent owner-gated launcher view.

    ``timeout=None`` + static ``custom_id`` per button = the message
    survives bot restarts; :meth:`SetupCog._resume_launchers` rebinds
    in-flight launcher messages with a status-aware label set on
    ``on_ready``.

    Labels:

    * ``status="pending"`` / ``None`` / ``"dismissed"`` — default
      "Start Setup".
    * ``status="in_progress"`` — "Resume Setup".
    * ``status="complete"`` — "Re-run Setup".

    Custom IDs never change; discord.py routes interactions by id,
    not by label, so the rebound message keeps working against the
    cog-load-registered view.
    """

    def __init__(self, *, status: str | None = None) -> None:
        super().__init__(timeout=None)
        self.status = status
        if status is not None:
            self._apply_status_labels(status)

    def _apply_status_labels(self, status: str) -> None:
        start_label = _START_LABELS_BY_STATUS.get(status, "Start Setup")
        for child in self.children:
            if (
                isinstance(child, discord.ui.Button)
                and getattr(child, "custom_id", None) == "setup:start"
            ):
                child.label = start_label

    async def _resolve_session(
        self,
        interaction: discord.Interaction,
    ) -> SetupSession | None:
        if interaction.guild_id is None:
            return None
        return await setup_session.resume_session(interaction.guild_id)

    async def _deny(
        self,
        interaction: discord.Interaction,
        message: str,
    ) -> None:
        await interaction.response.send_message(message, ephemeral=True)

    async def _gate_owner(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        member = interaction.user
        if not isinstance(member, discord.Member):
            await self._deny(
                interaction,
                "This button must be used inside the server.",
            )
            return False
        if not setup_access.is_server_owner(member):
            await self._deny(
                interaction,
                "Only the server owner can start setup or change presets.",
            )
            return False
        return True

    async def _gate_admin(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        member = interaction.user
        if not isinstance(member, discord.Member):
            await self._deny(
                interaction,
                "This button must be used inside the server.",
            )
            return False
        session = await self._resolve_session(interaction)
        if not setup_access.is_setup_admin(member, session):
            await self._deny(
                interaction,
                "Only the server owner, an administrator, or a delegated "
                "setup admin can use this button.",
            )
            return False
        return True

    @discord.ui.button(
        label="Start Setup",
        style=discord.ButtonStyle.success,
        custom_id="setup:start",
    )
    async def _start(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        if not await self._gate_owner(interaction):
            return
        if interaction.guild_id is None:
            await self._deny(
                interaction,
                "Setup requires a guild context.",
            )
            return

        from services import setup_draft
        from views.setup.hub import SetupHubView, build_hub_embed

        session = await self._resolve_session(interaction)
        try:
            draft_ops = await setup_draft.list_ops(interaction.guild_id)
        except Exception:
            logger.exception("setup_cog._start: setup_draft.list_ops failed")
            draft_ops = []
        pending_ops = len(draft_ops)
        hub = SetupHubView(interaction.user, session=session)
        await interaction.response.send_message(
            embed=build_hub_embed(
                session,
                pending_ops=pending_ops,
                draft_ops=draft_ops,
            ),
            view=hub,
            ephemeral=True,
        )
        try:
            await setup_session.mark_in_progress(interaction.guild_id, step="hub")
        except Exception:
            logger.exception("setup_cog._start: mark_in_progress failed")

    @discord.ui.button(
        label="Run Readiness Scan",
        style=discord.ButtonStyle.primary,
        custom_id="setup:readiness",
    )
    async def _readiness(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        if not await self._gate_admin(interaction):
            return
        guild = interaction.guild
        if guild is None:
            await self._deny(
                interaction,
                "Readiness scan requires a guild context.",
            )
            return
        from cogs.diagnostic._platform_embeds import build_setup_readiness_embed

        embed = await build_setup_readiness_embed(guild.id, guild=guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Smart Suggestions",
        style=discord.ButtonStyle.secondary,
        custom_id="setup:smart_suggestions",
    )
    async def _suggestions(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        if not await self._gate_owner(interaction):
            return
        guild = interaction.guild
        if guild is None or interaction.guild_id is None:
            await self._deny(
                interaction,
                "Smart Suggestions requires a guild context.",
            )
            return

        from services.guild_snapshot import collect as collect_snapshot
        from services.setup_ai_advisor import build_advisor
        from views.setup.ai_review.main_panel import (
            AIReviewPanelView,
            build_ai_review_embed,
        )

        try:
            snapshot = await collect_snapshot(guild)
            advisor = build_advisor()
            draft = await advisor.suggest(snapshot)
        except Exception:
            logger.exception("setup_cog._suggestions: advisor flow failed")
            await self._deny(
                interaction,
                "Smart Suggestions failed. Run **Run Readiness Scan** for "
                "a deterministic baseline.",
            )
            return

        panel = AIReviewPanelView(interaction.user, draft=draft, snapshot=snapshot)
        await interaction.response.send_message(
            embed=build_ai_review_embed(draft),
            view=panel,
            ephemeral=True,
        )
        try:
            await setup_session.mark_in_progress(
                interaction.guild_id,
                step="suggestions",
            )
        except Exception:
            logger.exception("setup_cog._suggestions: mark_in_progress failed")

    @discord.ui.button(
        label="Choose Preset",
        style=discord.ButtonStyle.secondary,
        custom_id="setup:preset",
    )
    async def _preset(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        if not await self._gate_owner(interaction):
            return

        from views.setup.template_picker import TemplatePickerView, build_picker_embed

        picker = TemplatePickerView(interaction.user)
        await interaction.response.send_message(
            embed=build_picker_embed(),
            view=picker,
            ephemeral=True,
        )

    @discord.ui.button(
        label="View Summary",
        style=discord.ButtonStyle.secondary,
        custom_id="setup:summary",
        row=1,
    )
    async def _view_summary(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        if not await self._gate_admin(interaction):
            return
        guild = interaction.guild
        if guild is None or interaction.guild_id is None:
            await self._deny(
                interaction,
                "View Summary requires a guild context.",
            )
            return
        session = await self._resolve_session(interaction)
        if session is None or session.setup_status != "complete":
            await self._deny(
                interaction,
                "Setup is not complete yet. Run **Start Setup** to finish "
                "the wizard before viewing the summary.",
            )
            return

        from views.setup.summary import (
            SummaryView,
            build_summary_embed,
            build_summary_snapshot,
        )

        try:
            snapshot = await build_summary_snapshot(
                session=session,
                guild=guild,
            )
        except Exception:
            logger.exception("setup_cog._view_summary: snapshot build failed")
            await self._deny(
                interaction,
                "Could not build the summary. Try **Run Readiness Scan** "
                "for a deterministic baseline.",
            )
            return

        view = SummaryView(interaction.user, snapshot=snapshot)
        await interaction.response.send_message(
            embed=build_summary_embed(snapshot),
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(
        label="Repost launcher",
        style=discord.ButtonStyle.secondary,
        custom_id="setup:repost_launcher",
        row=1,
    )
    async def _repost_launcher(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        if not await self._gate_admin(interaction):
            return
        guild = interaction.guild
        if guild is None:
            await self._deny(
                interaction,
                "Repost launcher requires a guild context.",
            )
            return

        channel, message = await post_launcher(guild)
        if message is None:
            await self._deny(
                interaction,
                "Could not post the launcher anywhere — bot has no sendable "
                "channel and the owner has DMs closed.",
            )
            return

        try:
            await setup_session.start_session(
                guild_id=guild.id,
                guild_name=guild.name,
                owner_id=guild.owner_id or 0,
                setup_channel_id=channel.id if channel is not None else None,
                setup_message_id=message.id,
            )
        except Exception:
            logger.exception(
                "setup_cog._repost_launcher: start_session refresh failed",
            )

        where = f"<#{channel.id}>" if channel is not None else "your DMs"
        await interaction.response.send_message(
            f"Launcher reposted in {where}.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Dismiss",
        style=discord.ButtonStyle.danger,
        custom_id="setup:dismiss",
        row=1,
    )
    async def _dismiss(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        if not await self._gate_owner(interaction):
            return
        if interaction.guild_id is None:
            await self._deny(
                interaction,
                "Dismiss requires a guild context.",
            )
            return
        await setup_session.dismiss(interaction.guild_id)
        await interaction.response.send_message(
            "Setup dismissed. Use the setup launcher later to resume.",
            ephemeral=True,
        )


# ---------------------------------------------------------------------------
# Channel selection — pick the safest place to post the launcher.
# ---------------------------------------------------------------------------


def _bot_can_send_in(channel: discord.TextChannel, me: discord.Member) -> bool:
    perms = channel.permissions_for(me)
    return bool(perms.view_channel and perms.send_messages and perms.embed_links)


def pick_launcher_channel(guild: discord.Guild) -> discord.TextChannel | None:
    """Return the safest text channel to post the launcher in.

    Order:
      1. ``guild.system_channel`` if the bot can send + embed there.
      2. First channel whose name contains ``admin`` / ``mod`` /
         ``staff`` that the bot can send in.
      3. First channel whose name contains ``bot`` that the bot can
         send in.
      4. First text channel in the guild the bot can send in.
      5. ``None`` — caller should DM the owner instead.
    """
    me = guild.me
    if me is None:
        return None

    system = guild.system_channel
    if isinstance(system, discord.TextChannel) and _bot_can_send_in(system, me):
        return system

    keyword_groups: tuple[tuple[str, ...], ...] = (
        ("admin", "mod", "staff"),
        ("bot",),
    )
    for needles in keyword_groups:
        for channel in guild.text_channels:
            name = (channel.name or "").lower()
            if any(needle in name for needle in needles) and _bot_can_send_in(
                channel,
                me,
            ):
                return channel

    for channel in guild.text_channels:
        if _bot_can_send_in(channel, me):
            return channel
    return None


async def post_launcher(
    guild: discord.Guild,
) -> tuple[discord.TextChannel | None, discord.Message | None]:
    """Pick a channel + post the launcher message.

    Returns ``(channel, message)`` on success, ``(None, None)`` when
    no channel is sendable and the owner-DM fallback also failed.
    The caller is responsible for updating ``setup_session`` with the
    resulting ids.
    """
    embed = _build_launcher_embed(None)
    view = SetupLauncherView()

    channel = pick_launcher_channel(guild)
    if channel is not None:
        try:
            message = await channel.send(embed=embed, view=view)
            return channel, message
        except discord.Forbidden:
            logger.warning(
                "setup_cog: forbidden when posting launcher in #%s (guild=%d)",
                channel.name,
                guild.id,
            )
        except discord.HTTPException as exc:
            logger.warning(
                "setup_cog: HTTP error posting launcher in #%s (guild=%d): %s",
                channel.name,
                guild.id,
                exc,
            )

    # Channel fallback: DM the owner.
    owner = guild.owner
    if owner is not None:
        try:
            message = await owner.send(embed=embed, view=view)
            logger.info(
                "setup_cog: DMed launcher to owner %d (guild=%d)",
                owner.id,
                guild.id,
            )
            return None, message
        except discord.Forbidden:
            logger.warning(
                "setup_cog: cannot DM owner %d for guild=%d (DMs closed)",
                owner.id,
                guild.id,
            )
        except discord.HTTPException as exc:
            logger.warning(
                "setup_cog: HTTP error DMing owner for guild=%d: %s",
                guild.id,
                exc,
            )

    return None, None


# ---------------------------------------------------------------------------
# Shared hub-entry helper for direct commands (!setup / /setup).
# ---------------------------------------------------------------------------


async def _resolve_hub_entry(
    member: discord.Member,
    guild: discord.Guild,
) -> (
    tuple[discord.Embed, discord.ui.View, str]
    | tuple[discord.Embed, None, str]
    | tuple[None, None, str]
):
    """Resolve the hub-entry response for ``member`` in ``guild``.

    Returns one of three shapes:

    * ``(hub_embed, hub_view, "hub")`` — member can apply setup; full
      hub is rendered. Caller marks the session in progress.
    * ``(readiness_embed, None, "readiness")`` — member is a setup
      admin without apply authority; render the deterministic
      readiness embed instead.
    * ``(None, None, "denied")`` — member is not a setup admin.

    The helper performs no Discord send; the calling command decides
    whether to reply ephemerally (slash) or to ``ctx.send`` (prefix).
    """
    session = await setup_session.resume_session(guild.id)

    if setup_access.can_apply_setup(member, session):
        if session is None:
            try:
                session = await setup_session.start_session(
                    guild_id=guild.id,
                    guild_name=guild.name,
                    owner_id=guild.owner_id or 0,
                )
            except Exception:
                logger.exception(
                    "setup_cog._resolve_hub_entry: start_session failed",
                )
                session = None

        from services import setup_draft
        from views.setup.hub import SetupHubView, build_hub_embed

        try:
            draft_ops = await setup_draft.list_ops(guild.id)
        except Exception:
            logger.exception(
                "setup_cog._resolve_hub_entry: setup_draft.list_ops failed",
            )
            draft_ops = []
        hub = SetupHubView(member, session=session)
        embed = build_hub_embed(
            session,
            pending_ops=len(draft_ops),
            draft_ops=draft_ops,
        )
        return embed, hub, "hub"

    if setup_access.is_setup_admin(member, session):
        from cogs.diagnostic._platform_embeds import build_setup_readiness_embed

        embed = await build_setup_readiness_embed(guild.id, guild=guild)
        return embed, None, "readiness"

    return None, None, "denied"


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class SetupCog(commands.Cog):
    """Setup-wizard launcher.

    Listens for ``on_guild_join`` and ``on_ready`` and keeps the
    launcher message in sync with the ``setup_session`` row:

    * ``on_guild_join`` — fresh launcher posted, session row upserted
      in ``pending``.
    * ``on_ready`` — for every guild with a recorded launcher
      message, the message is edited in place with a status-aware
      embed + view (e.g. ``Start Setup`` becomes ``Resume Setup``
      when the row is mid-flow).

    The base ``SetupLauncherView`` is registered at ``cog_load`` so
    discord.py can dispatch interactions even before the resume
    sweep finishes (the rebound message has the same custom_ids).
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        # Register the persistent view so discord.py can match
        # interactions to it after restart. The base instance has
        # the default labels; ``_resume_launchers`` later edits
        # individual messages with status-aware label sets.
        self.bot.add_view(SetupLauncherView())

    @commands.command(name="setup")
    @commands.guild_only()
    async def setup_cmd(self, ctx: commands.Context) -> None:
        """Open or resume the setup wizard from any channel.

        Owners and delegated setup admins get the hub; administrators
        without delegation get a read-only readiness embed; everyone
        else is denied. Recovery path when the launcher message has
        been deleted.
        """
        guild = ctx.guild
        member = ctx.author
        if guild is None or not isinstance(member, discord.Member):
            await ctx.send("Run `!setup` from inside the server.")
            return

        embed, view, mode = await _resolve_hub_entry(member, guild)
        if mode == "denied":
            await ctx.send(
                "Only the server owner, an administrator, or a delegated "
                "setup admin can open the setup wizard.",
            )
            return
        if mode == "readiness":
            if embed is None:
                await ctx.send("Could not build the readiness scan.")
                return
            await ctx.send(embed=embed)
            return

        if embed is None or view is None:
            await ctx.send("Could not build the setup hub. See logs.")
            return
        await ctx.send(embed=embed, view=view)
        try:
            await setup_session.mark_in_progress(guild.id, step="hub")
        except Exception:
            logger.exception("setup_cog.setup_cmd: mark_in_progress failed")

    @app_commands.command(
        name="setup",
        description="Open the setup wizard (owner, delegated admin, or admin).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def setup_slash(self, interaction: discord.Interaction) -> None:
        """Slash front door for the setup wizard — ephemeral.

        Mirrors the access ladder of the prefix command: owner /
        delegated admin → hub; administrator → readiness; otherwise
        denied (the ``has_permissions`` decorator will already have
        short-circuited the deny case for non-admins).
        """
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Use `/setup` from inside the server.",
                ephemeral=True,
            )
            return

        embed, view, mode = await _resolve_hub_entry(member, guild)
        if mode == "denied":
            await interaction.response.send_message(
                "Only the server owner, an administrator, or a delegated "
                "setup admin can open the setup wizard.",
                ephemeral=True,
            )
            return
        if mode == "readiness":
            if embed is None:
                await interaction.response.send_message(
                    "Could not build the readiness scan.",
                    ephemeral=True,
                )
                return
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if embed is None or view is None:
            await interaction.response.send_message(
                "Could not build the setup hub. See logs.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )
        try:
            await setup_session.mark_in_progress(guild.id, step="hub")
        except Exception:
            logger.exception("setup_cog.setup_slash: mark_in_progress failed")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self._handle_join(guild)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self._resume_launchers()

    async def _handle_join(self, guild: discord.Guild) -> None:
        """Internal entry point — split out for direct testing."""
        try:
            channel, message = await post_launcher(guild)
            channel_id = channel.id if channel is not None else None
            message_id = message.id if message is not None else None
            await setup_session.start_session(
                guild_id=guild.id,
                guild_name=guild.name,
                owner_id=guild.owner_id or 0,
                setup_channel_id=channel_id,
                setup_message_id=message_id,
            )
        except Exception:
            logger.exception(
                "setup_cog.on_guild_join: handler failed for guild=%d",
                guild.id,
            )

    async def _resume_launchers(self) -> None:
        """Walk ``self.bot.guilds`` and refresh each launcher message.

        For every guild whose ``setup_session`` row carries both a
        ``setup_channel_id`` and a ``setup_message_id``, the message
        is edited in place with the right status-aware label set.
        Stale channel / message ids are detected via ``Forbidden`` /
        ``NotFound`` / ``HTTPException`` and the corresponding row
        fields are NOT cleared here (Track 4 PR 9 keeps the cog
        non-destructive; an explicit teardown is the only path that
        removes session state).
        """
        for guild in list(self.bot.guilds):
            try:
                await self._resume_one_launcher(guild)
            except Exception:
                logger.exception(
                    "setup_cog.on_ready: resume failed for guild=%d",
                    guild.id,
                )

    async def _resume_one_launcher(self, guild: discord.Guild) -> bool:
        """Refresh one guild's launcher message.

        Returns ``True`` when the message was edited, ``False`` when
        no row exists, the row has no channel/message ids, or the
        original message could not be fetched.
        """
        session = await setup_session.resume_session(guild.id)
        if session is None:
            return False
        if session.setup_channel_id is None or session.setup_message_id is None:
            return False

        channel = guild.get_channel(session.setup_channel_id)
        if not isinstance(
            channel,
            (discord.TextChannel, discord.Thread),
        ):
            logger.debug(
                "setup_cog.on_ready: channel %s not in guild %d cache; "
                "skipping resume.",
                session.setup_channel_id,
                guild.id,
            )
            return False

        try:
            message = await channel.fetch_message(session.setup_message_id)
        except discord.NotFound:
            logger.info(
                "setup_cog.on_ready: launcher message %s in guild %d is "
                "gone; skipping resume (next on_guild_join will re-post).",
                session.setup_message_id,
                guild.id,
            )
            return False
        except discord.Forbidden:
            logger.warning(
                "setup_cog.on_ready: cannot fetch launcher message in "
                "#%s (guild=%d) — missing read_message_history.",
                channel.name,
                guild.id,
            )
            return False
        except discord.HTTPException as exc:
            logger.warning(
                "setup_cog.on_ready: HTTP error fetching launcher in guild=%d: %s",
                guild.id,
                exc,
            )
            return False

        view = SetupLauncherView(status=session.setup_status)
        embed = _build_launcher_embed(session)
        try:
            await message.edit(embed=embed, view=view)
        except discord.HTTPException as exc:
            logger.warning(
                "setup_cog.on_ready: edit_message failed for launcher in guild=%d: %s",
                guild.id,
                exc,
            )
            return False
        return True


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetupCog(bot))


__all__ = [
    "SetupCog",
    "SetupLauncherView",
    "pick_launcher_channel",
    "post_launcher",
    "setup",
]
