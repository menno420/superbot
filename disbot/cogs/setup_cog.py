"""Advanced setup-wizard launcher cog.

Discord-facing surface only. The persistent launcher view, embed
builder, and channel-selection helpers live in
:mod:`views.setup.launcher`; this file holds:

* the cog class with lifecycle listeners and slash/prefix entry
  commands (``!setupadvanced`` / ``/setup-advanced``);
* a shared ``_resolve_hub_entry`` helper that branches between the
  guided hub (owner / delegated admin) and the deterministic
  readiness embed (plain administrator).

The plain-language **Essential Setup** spine is now the primary
``!setup`` / ``/setup`` front door (:mod:`cogs.quicksetup_cog`); this
cog is the power-user / advanced section-list + draft → Final Review
path, plus the ``/setup-*`` helper commands and the on-join launcher.

Re-exports the launcher view + post helpers so callers that imported
``cogs.setup_cog.SetupLauncherView`` / ``post_launcher`` /
``pick_launcher_channel`` keep working.

Wires:
* :mod:`services.setup_session` for the lifecycle row.
* :mod:`services.setup_access` for owner / admin / non-admin gating.
* :func:`services.setup_readiness.collect` for readiness scans.
* :class:`views.setup.hub.SetupHubView` for the guided setup hub.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

# Imported for its registration side effect: section modules register into
# services.setup_sections.REGISTRY at import time. Without this the registry is
# empty at startup and the wizard renders "No setup sections available for this
# depth" until the hub (the only other importer) is opened.
import views.setup.sections  # noqa: F401
from cogs.setup._helpers import build_status_embed as _build_status_embed
from cogs.setup._helpers import resolve_hub_entry as _resolve_hub_entry
from cogs.setup._helpers import toggle_delegate as _toggle_delegate
from core.runtime.permission_checks import admin_or_owner, app_admin_or_owner
from services import setup_access, setup_session
from views.setup.essential_setup import EssentialSetupResumeView, revive_essential_flows
from views.setup.launcher import (
    SetupLauncherView,
    pick_launcher_channel,
    post_launcher,
)
from views.setup.launcher import _build_launcher_embed as _build_launcher_embed

logger = logging.getLogger("bot.cogs.setup")


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class SetupCog(commands.Cog):
    """Setup-wizard launcher.

    Listens for ``on_guild_join`` and ``on_ready`` and keeps the
    launcher message in sync with the ``setup_session`` row.
    Exposes ``!setup`` and ``/setup`` as direct entry / recovery
    commands; both route through ``_resolve_hub_entry``.

    The base ``SetupLauncherView`` is registered at ``cog_load`` so
    discord.py can dispatch interactions even before the resume
    sweep finishes (the rebound message has the same custom_ids).
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.bot.add_view(SetupLauncherView())
        # Resume button for restart-revive (migration 099); shown by on_ready sweep.
        self.bot.add_view(EssentialSetupResumeView())

    @commands.command(name="setupadvanced", aliases=["advancedsetup"])
    @commands.guild_only()
    async def setupadvanced_cmd(self, ctx: commands.Context) -> None:
        """Open or resume the advanced (linear) setup wizard.

        The power-user path: the full section-list + draft → Final
        Review editor.  Most operators want the plain-language
        ``!setup`` (Essential Setup) instead.

        Routes through :func:`views.setup.wizard.open_setup_workspace`
        so the wizard message lives in ``#superbot-setup`` and the
        invoking channel only receives a transient pointer reply.
        Owners and delegated setup admins get the wizard; administrators
        without delegation get a read-only readiness embed; everyone
        else is denied.
        """
        from cogs.setup._wizard_entry import open_wizard_from_prefix

        await open_wizard_from_prefix(ctx)

    @app_commands.command(
        name="setup-advanced",
        description="Open the advanced setup wizard (power users; "
        "/setup is the quick one).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.guild_only()
    async def setupadvanced_slash(self, interaction: discord.Interaction) -> None:
        """Ephemeral slash front door for the advanced (linear) setup wizard.

        Routes through :func:`views.setup.wizard.open_setup_workspace`
        so the wizard message lives in ``#superbot-setup`` and the
        slash response is a transient ephemeral pointer reply.
        """
        from cogs.setup._wizard_entry import open_wizard_from_slash

        await open_wizard_from_slash(interaction)

    @commands.command(name="setupdescribe", aliases=["describesetup"])
    @commands.guild_only()
    @admin_or_owner()
    async def setup_describe_cmd(
        self,
        ctx: commands.Context,
        *,
        description: str = "",
    ) -> None:
        """Describe your server in words; propose how to wire it to the bot.

        Natural-language setup wedge: the configured advisor reads your
        description **and** the live server, then proposes which channels/roles
        bind to which subsystems. Read-only — nothing changes until you accept
        and apply in the review panel (still gated by setup access).
        """
        from cogs.setup._describe_entry import open_describe_from_prefix

        await open_describe_from_prefix(ctx, description)

    @app_commands.command(
        name="setup-describe",
        description="Describe your server; the AI proposes a setup plan to review.",
    )
    @app_commands.describe(
        description="What your server is for and how it's organised.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.guild_only()
    async def setup_describe_slash(
        self,
        interaction: discord.Interaction,
        description: str,
    ) -> None:
        """Ephemeral natural-language setup proposal (admin-gated)."""
        from cogs.setup._describe_entry import open_describe_from_slash

        await open_describe_from_slash(interaction, description)

    @app_commands.command(
        name="setup-hub",
        description="Open the legacy section-list hub (compat).",
        extras={"classification": "legacy_duplicate"},
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.guild_only()
    async def setup_hub_slash(self, interaction: discord.Interaction) -> None:
        """Legacy section-list hub.

        Preserved as a compatibility command for operators (and tests)
        that want the registry-driven section list as the entry point
        instead of the linear wizard.  Same access ladder as ``/setup``
        used to use: owner / delegated admin → hub; plain admin →
        readiness; otherwise denied.
        """
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Use `/setup-hub` from inside the server.",
                ephemeral=True,
            )
            return

        embed, view, mode = await _resolve_hub_entry(member, guild)
        if mode == "denied":
            await interaction.response.send_message(
                "Only the server owner, an administrator, or a delegated "
                "setup admin can open the setup hub.",
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
        if mode == "hub":
            try:
                await setup_session.mark_in_progress(guild.id, step="hub")
            except Exception:
                logger.exception("setup_cog.setup_hub_slash: mark_in_progress failed")

    @app_commands.command(
        name="setup-depth",
        description="Pick the wizard depth (owner/delegated admin only).",
    )
    @app_commands.describe(depth="Setup depth: quick, standard, or advanced.")
    @app_commands.choices(
        depth=[
            app_commands.Choice(name="Quick (3 steps)", value="quick"),
            app_commands.Choice(name="Standard (5–6 steps)", value="standard"),
            app_commands.Choice(name="Advanced (all sections)", value="advanced"),
        ],
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.guild_only()
    async def setup_depth_slash(
        self,
        interaction: discord.Interaction,
        depth: app_commands.Choice[str],
    ) -> None:
        """Set the persisted wizard depth without opening the hub.

        The hub's section list and the "Apply all recommended" button
        re-filter by the new depth on the next open. The skip set and
        any staged draft ops are preserved — only the depth pick is
        replaced.
        """
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Use `/setup-depth` from inside the server.",
                ephemeral=True,
            )
            return

        try:
            session = await setup_session.resume_session(guild.id)
        except Exception:
            logger.exception("setup_cog.setup_depth_slash: resume failed")
            session = None

        if not setup_access.can_apply_setup(member, session):
            await interaction.response.send_message(
                "Only the server owner or a delegated setup admin can "
                "change the wizard depth.",
                ephemeral=True,
            )
            return

        if session is None:
            # No session yet — create one so the depth choice persists.
            try:
                await setup_session.start_session(
                    guild_id=guild.id,
                    guild_name=guild.name,
                    owner_id=guild.owner_id or 0,
                )
            except Exception:
                logger.exception(
                    "setup_cog.setup_depth_slash: start_session failed",
                )
                await interaction.response.send_message(
                    "Could not initialise the setup session — see logs.",
                    ephemeral=True,
                )
                return

        try:
            await setup_session.set_depth(guild.id, depth.value)
        except Exception:
            logger.exception("setup_cog.setup_depth_slash: set_depth failed")
            await interaction.response.send_message(
                "Could not save the depth choice — see logs.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ Depth set to **{depth.name}**. Run `!setupadvanced` / "
            f"`/setup-advanced` to see the filtered section list.",
            ephemeral=True,
        )

    @app_commands.command(
        name="setup-skip",
        description="Mark a setup section as skipped (owner/delegated admin only).",
    )
    @app_commands.describe(
        section="Section slug (e.g. cleanup, channels, cog_routing).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.guild_only()
    async def setup_skip_slash(
        self,
        interaction: discord.Interaction,
        section: str,
    ) -> None:
        """Add ``section`` to the session's skipped_sections set.

        The hub renders the section with a ⚠️ Skipped badge and the
        ``Apply all recommended`` button skips it. Use
        ``/setup-unskip`` to revert.
        """
        await self._toggle_skip(interaction, section, skipped=True)

    @app_commands.command(
        name="setup-unskip",
        description="Remove a section from the skipped set (owner/delegated admin only).",
    )
    @app_commands.describe(
        section="Section slug (e.g. cleanup, channels, cog_routing).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.guild_only()
    async def setup_unskip_slash(
        self,
        interaction: discord.Interaction,
        section: str,
    ) -> None:
        """Drop ``section`` from the session's skipped_sections set."""
        await self._toggle_skip(interaction, section, skipped=False)

    async def _toggle_skip(
        self,
        interaction: discord.Interaction,
        slug: str,
        *,
        skipped: bool,
    ) -> None:
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            cmd = "skip" if skipped else "unskip"
            await interaction.response.send_message(
                f"Use `/setup-{cmd}` from inside the server.",
                ephemeral=True,
            )
            return

        try:
            session = await setup_session.resume_session(guild.id)
        except Exception:
            logger.exception("setup_cog._toggle_skip: resume failed")
            session = None

        if not setup_access.can_apply_setup(member, session):
            await interaction.response.send_message(
                "Only the server owner or a delegated setup admin can "
                "change a section's skipped state.",
                ephemeral=True,
            )
            return

        from services.setup_sections import REGISTRY

        if REGISTRY.get(slug) is None:
            available = ", ".join(f"`{s.slug}`" for s in REGISTRY.all())
            await interaction.response.send_message(
                f"Unknown section `{slug}`. Available: {available}",
                ephemeral=True,
            )
            return

        try:
            if skipped:
                await setup_session.mark_section_skipped(guild.id, slug)
            else:
                await setup_session.unmark_section_skipped(guild.id, slug)
        except Exception:
            verb = "mark" if skipped else "unmark"
            logger.exception("setup_cog._toggle_skip: %s failed", verb)
            await interaction.response.send_message(
                "Could not update the skip state — see logs.",
                ephemeral=True,
            )
            return

        verb = "skipped" if skipped else "un-skipped"
        await interaction.response.send_message(
            f"✅ Section `{slug}` {verb}.",
            ephemeral=True,
        )

    @app_commands.command(
        name="setup-reset",
        description="Clear all staged setup operations (owner/delegated admin only).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.guild_only()
    async def setup_reset_slash(self, interaction: discord.Interaction) -> None:
        """Clear the per-guild setup draft without dismissing the session.

        Useful when the operator made mistakes while staging ops and
        wants a clean slate without flipping the session to
        ``dismissed`` (which would also clear the depth pick and
        skipped-section set).
        """
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Use `/setup-reset` from inside the server.",
                ephemeral=True,
            )
            return

        try:
            session = await setup_session.resume_session(guild.id)
        except Exception:
            logger.exception("setup_cog.setup_reset_slash: resume failed")
            session = None

        if not setup_access.can_apply_setup(member, session):
            await interaction.response.send_message(
                "Only the server owner or a delegated setup admin can "
                "reset staged setup operations.",
                ephemeral=True,
            )
            return

        from services import setup_draft

        try:
            pending_before = await setup_draft.count(guild.id)
        except Exception:
            logger.exception("setup_cog.setup_reset_slash: count failed")
            pending_before = 0

        if pending_before == 0:
            await interaction.response.send_message(
                "No staged operations to clear — the draft is already empty.",
                ephemeral=True,
            )
            return

        try:
            await setup_draft.clear(guild.id)
        except Exception:
            logger.exception("setup_cog.setup_reset_slash: clear failed")
            await interaction.response.send_message(
                "Could not clear staged operations — see logs.",
                ephemeral=True,
            )
            return

        word = "operation" if pending_before == 1 else "operations"
        await interaction.response.send_message(
            f"✅ Cleared **{pending_before}** staged {word}. The session "
            f"keeps its status and depth — run `!setupadvanced` or "
            f"`/setup-advanced` to continue.",
            ephemeral=True,
        )

    @app_commands.command(
        name="setup-delegate",
        description="Grant a member delegated setup-admin authority (owner only).",
    )
    @app_commands.describe(
        member="Member to grant delegated setup-admin authority.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.guild_only()
    async def setup_delegate_slash(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ) -> None:
        """Add ``member`` to the guild's ``delegated_admins`` set.

        Owner-only on purpose: delegation is a capability-significant
        change and must not be self-granted by other administrators.
        Idempotent — re-granting an existing delegate is a no-op at
        the DB layer.  After the grant succeeds the private setup
        channel's overwrites are recomputed so the new delegate gets
        explicit channel access.

        Body lives in :func:`cogs.setup._helpers.toggle_delegate` so
        the cog file stays under the S4.6 LOC ceiling.
        """
        await _toggle_delegate(interaction, member, grant=True)

    @app_commands.command(
        name="setup-undelegate",
        description="Revoke delegated setup-admin authority (owner only).",
    )
    @app_commands.describe(
        member="Member to revoke delegated setup-admin authority from.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.guild_only()
    async def setup_undelegate_slash(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ) -> None:
        """Drop ``member`` from the guild's ``delegated_admins`` set.

        Owner-only.  Idempotent.  After the revoke succeeds the private
        setup channel's overwrites are recomputed so the revoked
        delegate loses explicit channel access (Discord administrator
        permissions may still let them view — see PRIVACY_NOTE on
        :mod:`services.setup_channel`).

        Body lives in :func:`cogs.setup._helpers.toggle_delegate`.
        """
        await _toggle_delegate(interaction, member, grant=False)

    @app_commands.command(
        name="setup-status",
        description="Quick at-a-glance setup state (read-only).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.guild_only()
    async def setup_status_slash(self, interaction: discord.Interaction) -> None:
        """Ephemeral read-only status view.

        Surfaces the session lifecycle, depth choice, pending op
        count, and skipped section list without opening the
        interactive hub. Useful for "where am I?" peeks that don't
        want to enter the wizard.
        """
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Use `/setup-status` from inside the server.",
                ephemeral=True,
            )
            return

        try:
            session = await setup_session.resume_session(guild.id)
        except Exception:
            logger.exception("setup_cog.setup_status_slash: resume failed")
            session = None

        if not setup_access.is_setup_admin(member, session):
            await interaction.response.send_message(
                "Only the server owner, an administrator, or a delegated "
                "setup admin can view setup status.",
                ephemeral=True,
            )
            return

        from services import setup_draft

        try:
            pending_ops = await setup_draft.count(guild.id)
        except Exception:
            logger.exception("setup_cog.setup_status_slash: draft.count failed")
            pending_ops = 0

        embed = _build_status_embed(session, pending_ops=pending_ops)
        # Aggressive ephemeral policy: post the status snapshot to the
        # workspace as a durable notice (event log) rather than a
        # per-user ephemeral. The wizard anchor stays in place, so
        # running /setup-status mid-wizard does not clobber state.
        # Reply with a short ephemeral pointer.
        from views.setup._anchor import push_setup_notice

        posted = await push_setup_notice(guild, embed=embed)
        if posted:
            channel_id = session.setup_channel_id if session is not None else None
            ref = f"<#{channel_id}>" if channel_id else "the setup workspace"
            await interaction.response.send_message(
                f"📋 Setup status posted in {ref}.",
                ephemeral=True,
            )
        else:
            # Fall back to the historic ephemeral when the workspace is
            # unreachable so the operator still sees the snapshot.
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self._handle_join(guild)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self._resume_launchers()
        await revive_essential_flows(self.bot)  # restart-revive sweep (migration 099)

    async def _handle_join(self, guild: discord.Guild) -> None:
        """Internal entry point — split out for direct testing.

        Tries to auto-create a private ``#superbot-setup`` channel and
        post the launcher there with an owner ping. If the bot lacks
        Manage Channels (or the create fails), falls back to
        :func:`post_launcher` which picks the safest existing channel
        or DMs the owner.
        """
        try:
            channel_id, message_id = await self._post_launcher_in_setup_channel(
                guild,
            )
            if channel_id is None:
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

    async def _post_launcher_in_setup_channel(
        self,
        guild: discord.Guild,
    ) -> tuple[int | None, int | None]:
        """Try the private-setup-channel path; return ``(channel_id,
        message_id)`` on success or ``(None, None)`` to signal the
        caller should fall back to :func:`post_launcher`.

        Resuming on bot restart hits the same path and is idempotent
        (``ensure_setup_channel`` returns the existing channel without
        recreating, and the cog keeps the prior message id when the
        existing launcher message is still posted).
        """
        from services.setup_channel import ensure_setup_channel

        existing_session = await setup_session.resume_session(guild.id)
        existing_channel_id = (
            existing_session.setup_channel_id if existing_session else None
        )
        try:
            channel, was_created = await ensure_setup_channel(
                guild,
                existing_channel_id=existing_channel_id,
            )
        except Exception:
            logger.exception(
                "setup_cog._post_launcher_in_setup_channel: ensure failed (guild=%d)",
                guild.id,
            )
            return None, None
        if channel is None:
            return None, None

        # On a restart where the channel already existed and we already
        # posted a launcher, do not double-post — the existing message
        # gets edited in place by ``_resume_launchers`` on ``on_ready``.
        if (
            not was_created
            and existing_session is not None
            and existing_session.setup_channel_id == channel.id
            and existing_session.setup_message_id is not None
        ):
            return channel.id, existing_session.setup_message_id

        embed = _build_launcher_embed(None)
        view = SetupLauncherView()
        owner_mention = guild.owner.mention if guild.owner is not None else ""
        content = (
            f"{owner_mention} SuperBot just joined! I'll use this private "
            f"channel as the setup workspace. Click **Start Setup** below "
            f"(or run `!setup` / `/setup`) to begin."
            if was_created
            else None
        )
        try:
            message = await channel.send(
                content=content,
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions(users=True, everyone=False),
            )
        except discord.HTTPException as exc:
            logger.warning(
                "setup_cog._post_launcher_in_setup_channel: send failed "
                "in guild=%d: %s",
                guild.id,
                exc,
            )
            return None, None
        return channel.id, message.id

    async def _resume_launchers(self) -> None:
        """Refresh every guild's launcher message in place; isolate failures."""
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
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            logger.debug(
                "setup_cog.on_ready: channel %s not in guild %d cache.",
                session.setup_channel_id,
                guild.id,
            )
            return False

        try:
            message = await channel.fetch_message(session.setup_message_id)
        except discord.NotFound:
            logger.info(
                "setup_cog.on_ready: launcher message %s in guild %d is gone.",
                session.setup_message_id,
                guild.id,
            )
            return False
        except discord.Forbidden:
            logger.warning(
                "setup_cog.on_ready: cannot fetch launcher in #%s (guild=%d).",
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
