"""Setup-wizard launcher view + channel-selection helpers.

Hosts the persistent ``SetupLauncherView`` that the launcher cog posts
on ``on_guild_join`` and edits in place on ``on_ready``, plus the
deterministic channel-selection helpers used by ``post_launcher``.

Extracted from :mod:`cogs.setup_cog` to keep the cog file under the
S4.6 800-LOC ceiling and to let the launcher view evolve in views/
alongside the rest of the setup wizard panels.
"""

from __future__ import annotations

import logging

import discord

from services import setup_access, setup_session
from services.setup_session import SetupSession

logger = logging.getLogger("bot.views.setup.launcher")

_LAUNCHER_TITLE = "🛰 SuperBot setup"
_LAUNCHER_DESC = (
    "Welcome! I'll help you set SuperBot up for this server.\n\n"
    "Click **Start Setup** for the quick guided setup — a few simple steps, "
    "each saved as you go. The other buttons are optional extras, or "
    "**Dismiss** to defer.\n\n"
    "**Quick commands:** `!setup` / `/setup` for the quick guided setup, "
    "`/setup-advanced` for the full editor, "
    "`/setup-status` for a read-only peek, `/setup-reset` to start over.\n\n"
    "🎫 Setup includes a **Support Tickets** step — enable private "
    "member↔staff tickets there, or run `!ticketsetup @StaffRole [#log]`."
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


# Extends discord.ui.View directly (not BaseView): specialized lifecycle —
# a cross-restart persistent view (timeout=None + static per-button
# custom_id) with per-button owner/admin/apply gating rather than BaseView's
# single invoker lock, and a status-aware label rebind on on_ready.
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

    async def _gate_apply(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        """Gate write-capable actions on the owner-or-delegated ladder.

        Mirrors :func:`services.setup_access.can_apply_setup`, matching the
        wizard / hub / Final Review gates so Smart Suggestions and Choose
        Preset are reachable by delegated setup admins, not just the owner.
        """
        member = interaction.user
        if not isinstance(member, discord.Member):
            await self._deny(
                interaction,
                "This button must be used inside the server.",
            )
            return False
        session = await self._resolve_session(interaction)
        if not setup_access.can_apply_setup(member, session):
            await self._deny(
                interaction,
                "Only the server owner or a delegated setup admin can use "
                "this button. Ask the owner to grant you `/setup-delegate`.",
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
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            await self._deny(interaction, "This can only be used in a server.")
            return

        # Gate on the broad "can use setup" ladder (owner / administrator /
        # delegated setup admin) — same accessibility as the `!setup` command,
        # so a plain admin who joins isn't refused at the launcher.
        session = await self._resolve_session(interaction)
        if not setup_access.is_setup_admin(member, session):
            await self._deny(
                interaction,
                "Only the server owner, an administrator, or a delegated "
                "setup admin can start setup.",
            )
            return

        # Start Setup opens the plain-language Essential Setup spine (the
        # primary `!setup` flow), not the advanced section-list wizard.
        from views.setup.essential_setup import open_essential_setup_in_setup_channel

        channel, message, reason = await open_essential_setup_in_setup_channel(
            guild,
            member,
        )
        if reason == "no_channel" or channel is None:
            await interaction.response.send_message(
                "I couldn't ensure the private `#superbot-setup` channel — "
                "I need the **Manage Channels** permission.  Grant it and "
                "try again.",
                ephemeral=True,
            )
            return
        if reason == "post_failed" or message is None:
            await interaction.response.send_message(
                f"The `#superbot-setup` channel exists ({channel.mention}) "
                "but I couldn't post setup there — check my permissions "
                "in that channel.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"✅ Setup is ready in {channel.mention} — [open it]({message.jump_url}).",
            ephemeral=True,
        )

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
                "This can only be used in a server.",
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
        if not await self._gate_apply(interaction):
            return
        guild = interaction.guild
        if guild is None or interaction.guild_id is None:
            await self._deny(
                interaction,
                "This can only be used in a server.",
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
            logger.exception("setup launcher: advisor flow failed")
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
            logger.exception("setup launcher: mark_in_progress failed")

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
        if not await self._gate_apply(interaction):
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
                "This can only be used in a server.",
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
            logger.exception("setup launcher: summary snapshot build failed")
            await self._deny(
                interaction,
                "Could not build the summary. Try **Run Readiness Scan** "
                "for a deterministic baseline.",
            )
            return

        view = SummaryView(
            interaction.user,
            snapshot=snapshot,
            session=session,
        )
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
                "This can only be used in a server.",
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
                "setup launcher: start_session refresh failed",
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
                "This can only be used in a server.",
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
                "setup launcher: forbidden when posting in #%s (guild=%d)",
                channel.name,
                guild.id,
            )
        except discord.HTTPException as exc:
            logger.warning(
                "setup launcher: HTTP error posting in #%s (guild=%d): %s",
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
                "setup launcher: DMed launcher to owner %d (guild=%d)",
                owner.id,
                guild.id,
            )
            return None, message
        except discord.Forbidden:
            logger.warning(
                "setup launcher: cannot DM owner %d for guild=%d (DMs closed)",
                owner.id,
                guild.id,
            )
        except discord.HTTPException as exc:
            logger.warning(
                "setup launcher: HTTP error DMing owner for guild=%d: %s",
                guild.id,
                exc,
            )

    return None, None


__all__ = [
    "SetupLauncherView",
    "pick_launcher_channel",
    "post_launcher",
]
