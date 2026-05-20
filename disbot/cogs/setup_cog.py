"""Setup-wizard launcher cog — Phase 9e / Track 4 PR 9.

Posts a persistent owner-gated launcher when the bot joins a guild and
on every subsequent ``on_ready`` for guilds whose launcher is still
``pending`` / ``in_progress``.

Wires:
* :mod:`services.setup_session` for the lifecycle row.
* :mod:`services.setup_access` for owner / admin / non-admin gating.
* :func:`services.setup_readiness.collect` for the readiness scan.

This PR ships the launcher entry point only:
* **Start Setup** and **Smart Suggestions** stub to "Coming soon"
  (Tracks 5 + 8 fill them).
* **Choose Preset** stub to "Coming soon" (Track 7 fills it).
* **Run Readiness Scan** runs ``setup_readiness.collect`` and renders
  the existing
  :func:`cogs.diagnostic._platform_embeds.build_setup_readiness_embed`.
* **Dismiss** flips ``setup_status`` to ``dismissed``; never deletes
  Discord resources or DB rows.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from services import setup_access, setup_session
from services.setup_session import SetupSession

if TYPE_CHECKING:
    pass

logger = logging.getLogger("bot.cogs.setup")

_LAUNCHER_TITLE = "🛰 SuperBot setup"
_LAUNCHER_DESC = (
    "Welcome! I'll help you wire SuperBot up to this server.\n\n"
    "Use **Start Setup** for the guided walkthrough, **Run Readiness Scan** "
    "to see what's already configured, or **Dismiss** to defer."
)
_COMING_SOON = (
    "This step is not wired up yet — it lands in an upcoming PR. "
    "Run **Run Readiness Scan** to see the current configuration."
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
        await interaction.response.send_message(_COMING_SOON, ephemeral=True)

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
        await interaction.response.send_message(_COMING_SOON, ephemeral=True)

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
        await interaction.response.send_message(_COMING_SOON, ephemeral=True)

    @discord.ui.button(
        label="Dismiss",
        style=discord.ButtonStyle.danger,
        custom_id="setup:dismiss",
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
            "Setup dismissed. Run `/setup` later to resume.",
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
                "setup_cog.on_ready: edit_message failed for launcher in "
                "guild=%d: %s",
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
