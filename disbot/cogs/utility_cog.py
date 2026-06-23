from __future__ import annotations

import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

from core.runtime import tasks
from core.runtime.interaction_helpers import help_ctx_shim
from services import governance_service
from services.governance_service import GovernanceContext
from utils import embeds as em
from utils.subsystem_registry import SUBSYSTEMS
from utils.ui_constants import INFO_COLOR, SUCCESS_COLOR, UTILITY_COLOR
from views.base import HubView, send_panel
from views.navigation import (
    BackTarget,
    attach_back_button,
    attach_back_target,
    chain_back,
)

logger = logging.getLogger("bot.cogs.utility")


def discover_utility_children() -> list[tuple[str, dict]]:
    """``SUBSYSTEMS`` entries whose ``parent_hub`` is the Utility hub.

    Mirrors :func:`views.games.hub.discover_game_children` /
    :func:`views.community.hub.discover_community_children`.  The Utility hub is a
    *hybrid* surface — it has its own action buttons (server info, poll, …) **and**
    hosts child subsystems (General, 420).  Before the discoverability-audit fix the
    panel rendered only its own actions, so the child subsystems — and every command
    they own (``!joke`` / ``!fact`` / …) — were unreachable by clicking through
    ``!help`` (the "general cog is unfindable from the help menu" report).  Surfacing
    them as buttons here is the same way every other parent hub surfaces its children.

    Sorted by ``ui_priority`` then key so the button order is deterministic.
    """
    children = [
        (name, dict(meta))
        for name, meta in SUBSYSTEMS.items()
        if meta.get("parent_hub") == "utility"
    ]
    children.sort(key=lambda item: (item[1].get("ui_priority", 99), item[0]))
    return children


def _format_child_label(subsystem: str, meta: dict) -> str:
    """``{emoji} {display_name}`` button label, capped at Discord's 80-char limit.

    Mirrors the identical helper in the Games / Community hub views.
    """
    emoji = meta.get("emoji") or ""
    display = meta.get("display_name") or subsystem
    return f"{emoji} {display}".strip()[:80]


async def _remind_later(
    user: discord.User,
    channel: discord.abc.Messageable,
    delay: float,
    message: str,
) -> None:
    await asyncio.sleep(delay)
    try:
        await channel.send(f"⏰ {user.mention} — Reminder: {message}")
    except Exception:
        pass


class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        """Cancel pending reminders so a reload doesn't leak them.

        Reminders are in-memory only; a reload would lose state regardless,
        so cancellation matches the user expectation.
        """
        tasks.cancel_by_prefix("utility:")

    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    @commands.command(name="utilitymenu")
    async def utility_menu(self, ctx):
        """Open the interactive utility panel."""
        view = _UtilityPanelView(ctx)
        await send_panel(ctx, embed=view.build_embed(), view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (returns the utility panel)."""
        view = _UtilityPanelView(help_ctx_shim(interaction))
        return view.build_embed(), view

    @app_commands.command(
        name="utility",
        description="Open the Utility hub (server info, polls, reminders).",
    )
    async def utility_slash(self, interaction: discord.Interaction) -> None:
        """Slash front door for the Utility hub — ephemeral.

        PR E1 — user-tier slash. Reuses
        :meth:`build_help_menu_view` so the slash entry mirrors the
        help-routed and prefix entries.
        """
        embed, view = await self.build_help_menu_view(interaction)
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )

    @commands.cooldown(rate=3, per=15, type=commands.BucketType.user)
    @commands.command(name="myprofile")
    @commands.guild_only()
    async def myprofile(self, ctx):
        """View your per-server profile card.

        Self-scoped (the viewer is the subject) — shows your participation,
        subscriptions, preferences, and visibility across every subsystem
        that registered a per-user surface. Read-only (PR A); the panel is
        owner-locked so only you can interact with it.
        """
        from views.profile import ProfileHomeView, build_profile_card

        view = ProfileHomeView(ctx.author, ctx.guild.id)
        embed, file = await build_profile_card(ctx.author, ctx.guild.id)
        await send_panel(ctx, embed=embed, view=view, file=file)

    @app_commands.command(
        name="myprofile",
        description="View your profile: participation, subscriptions, preferences, visibility.",
    )
    @app_commands.guild_only()
    async def myprofile_slash(self, interaction: discord.Interaction) -> None:
        """Ephemeral, self-scoped profile card (Q-0080 stranger-grade).

        Ephemeral by construction and scoped to the invoking user (no
        member parameter) — being yourself is the whole access model.
        """
        from views.profile import ProfileHomeView, build_profile_card

        guild_id = interaction.guild_id
        if guild_id is None:
            await interaction.response.send_message(
                "Use `/myprofile` from inside a server.",
                ephemeral=True,
            )
            return

        view = ProfileHomeView(interaction.user, guild_id)
        embed, file = await build_profile_card(interaction.user, guild_id)
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
            **({"file": file} if file is not None else {}),
        )

    @commands.command(name="clear", aliases=["purge"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 5):
        """Purge messages. Max 100."""
        if amount <= 0:
            await ctx.send(
                embed=em.error("Please specify a number greater than 0."),
                delete_after=5,
            )
            return
        if amount > 100:
            await ctx.send(
                embed=em.error("You can only clear up to 100 messages at a time."),
                delete_after=5,
            )
            return
        deleted = await ctx.channel.purge(limit=amount)
        msg = await ctx.send(f"Cleared {len(deleted)} messages.")
        await msg.delete(delay=5)

    @commands.command(name="info")
    async def info(self, ctx, target: str = "server", member: discord.Member = None):
        """Show server or user info.  !info [server|user] [@mention]"""
        if target.lower() in ("user", "u") or member:
            member = member or ctx.author
            embed = discord.Embed(
                title=f"User Info — {member}",
                color=SUCCESS_COLOR,
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Username", value=member.name, inline=True)
            embed.add_field(name="User ID", value=str(member.id), inline=True)
            embed.add_field(
                name="Joined Server",
                value=member.joined_at.strftime("%Y-%m-%d"),
                inline=True,
            )
            embed.add_field(
                name="Joined Discord",
                value=member.created_at.strftime("%Y-%m-%d"),
                inline=True,
            )
            embed.add_field(
                name="Status",
                value=str(member.status).capitalize(),
                inline=True,
            )
            embed.add_field(
                name="Activity",
                value=member.activity.name if member.activity else "None",
                inline=True,
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
        else:
            guild = ctx.guild
            embed = discord.Embed(
                title=f"{guild.name}",
                description="Server Information",
                color=INFO_COLOR,
            )
            embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
            embed.add_field(name="Members", value=str(guild.member_count), inline=True)
            embed.add_field(
                name="Boost Level",
                value=str(guild.premium_tier),
                inline=True,
            )
            embed.add_field(
                name="Created",
                value=guild.created_at.strftime("%Y-%m-%d"),
                inline=True,
            )
            embed.add_field(
                name="Text Channels",
                value=str(len(guild.text_channels)),
                inline=True,
            )
            embed.add_field(
                name="Voice Channels",
                value=str(len(guild.voice_channels)),
                inline=True,
            )
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
        await ctx.send(embed=embed)

    @commands.command(
        name="serverinfo",
        hidden=True,
        extras={"classification": "legacy_duplicate"},
    )
    async def serverinfo(self, ctx):
        """Alias for !info server."""
        await ctx.invoke(self.info, target="server")

    @commands.command(
        name="userinfo",
        hidden=True,
        extras={"classification": "legacy_duplicate"},
    )
    async def userinfo(self, ctx, member: discord.Member = None):
        """Alias for !info user [@member]."""
        await ctx.invoke(self.info, target="user", member=member)

    @commands.command(
        name="avatar",
        hidden=True,
        extras={"classification": "hidden"},
    )
    async def avatar(self, ctx, member: discord.Member = None):
        """Display a user's avatar."""
        member = member or ctx.author
        embed = discord.Embed(title=f"{member}'s Avatar", color=INFO_COLOR)
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="remind")
    async def remind(self, ctx, time: int, *, message: str):
        """Set a reminder.  !remind <minutes> <message>"""
        if time <= 0:
            await ctx.send(
                embed=em.error("Please specify a time greater than 0 minutes."),
            )
            return
        await ctx.send(f"⏳ Reminder set for **{time}** minute(s): {message}")
        tasks.spawn(
            f"utility:remind:{ctx.author.id}",
            _remind_later(ctx.author, ctx.channel, time * 60, message),
        )

    @commands.command(name="invite")
    @commands.has_permissions(create_instant_invite=True)
    async def invite(self, ctx):
        """Generate a one-use server invite."""
        invite = await ctx.channel.create_invite(max_uses=1, unique=True)
        await ctx.send(f"Here is your invite link (valid for 1 use): {invite.url}")

    @commands.command(name="poll")
    async def poll(self, ctx, question: str, *options):
        """Create a simple reaction poll."""
        if len(options) < 2:
            await ctx.send(embed=em.error("You need at least two options for a poll."))
            return
        if len(options) > 10:
            await ctx.send(embed=em.error("You can only provide up to 10 options."))
            return
        embed = discord.Embed(
            title=f"Poll: {question}",
            description="\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options)),
            color=INFO_COLOR,
        )
        poll_msg = await ctx.send(embed=embed)
        for i in range(len(options)):
            await poll_msg.add_reaction(f"{i+1}\N{COMBINING ENCLOSING KEYCAP}")


# ---------------------------------------------------------------------------
# Utility Panel View
# ---------------------------------------------------------------------------


def attach_back_to_utility_button(
    view: discord.ui.View,
    author: discord.Member | discord.User,
    *,
    grandparent: BackTarget | None = None,
) -> bool:
    """Append a "↩ Back to Utility" control to a child view opened from the hub.

    Mirrors :func:`views.community.hub.attach_back_to_community_button`.  The
    parent-builder closure captures ``author`` so the rebuilt Utility panel stays
    invoker-restricted; when ``grandparent`` is supplied (e.g. a Back-to-Help
    target set by :func:`cogs.help_cog._attach_back_to_help_button`),
    :func:`views.navigation.chain_back` wraps the builder so the rebuilt Utility
    panel re-attaches that grandparent too.
    """

    async def _build_utility_parent(
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        parent = _UtilityPanelView(help_ctx_shim(interaction))
        return parent.build_embed(), parent

    builder = chain_back(_build_utility_parent, grandparent)
    return attach_back_button(
        view,
        label="↩ Back to Utility",
        custom_id="utility:back",
        parent_builder=builder,
        row=4,
        style=discord.ButtonStyle.secondary,
        error_message="Could not reload the Utility hub. Please try again.",
    )


class _UtilityChildButton(discord.ui.Button):
    """A Utility-hub button that opens a child subsystem's panel in place.

    Mirrors :class:`views.community.hub._CommunityChildButton`: it forwards to the
    target cog's ``build_help_menu_view`` hook (no business logic here), with a
    click-time governance recheck so a child that became invisible since render
    fails closed instead of opening.
    """

    def __init__(self, *, subsystem: str, label: str, row: int) -> None:
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            custom_id=f"utility:open:{subsystem}",
            row=row,
        )
        self._subsystem = subsystem

    async def callback(self, interaction: discord.Interaction) -> None:
        # Click-time governance recheck — fail closed if the child has become
        # invisible since this button was rendered (cached resolve, ~free).
        gctx = GovernanceContext.from_interaction(interaction)
        vis_result = await governance_service.resolve_visibility(gctx)
        if self._subsystem not in vis_result.visible_subsystems:
            await interaction.response.send_message(
                "That feature is no longer available in this channel.",
                ephemeral=True,
            )
            return

        # Local import keeps the help cog out of module-import time (and the
        # import graph acyclic).
        from cogs.help_cog import _cog_for_subsystem

        cog = _cog_for_subsystem(interaction.client, self._subsystem)  # type: ignore[arg-type]
        builder = getattr(cog, "build_help_menu_view", None) if cog else None
        if not callable(builder):
            await interaction.response.send_message(
                f"The {self._subsystem!r} panel is not available right now.",
                ephemeral=True,
            )
            return

        try:
            embed, sub_view = await builder(interaction)
        except Exception as exc:  # noqa: BLE001 — navigation must not crash
            logger.warning(
                "Utility hub: build_help_menu_view failed for %r: %s",
                self._subsystem,
                exc,
                exc_info=True,
            )
            await interaction.response.send_message(
                f"Could not open the {self._subsystem!r} panel — see bot logs.",
                ephemeral=True,
            )
            return

        # Attach Back-to-Utility to the child view, threading any Back-to-Help
        # grandparent the help layer set on this hub (mirrors the Community hub).
        parent_view = self.view
        back_target: BackTarget | None = getattr(parent_view, "_back_target", None)
        attach_back_to_utility_button(
            sub_view,
            interaction.user,  # type: ignore[arg-type]
            grandparent=back_target,
        )
        if back_target is not None:
            attach_back_target(sub_view, back_target)
            sub_view._back_target = back_target  # type: ignore[attr-defined]

        await interaction.response.edit_message(embed=embed, view=sub_view)


class _UtilityPanelView(HubView):
    """Interactive utility panel — quick access to common utility actions.

    Hybrid surface: the decorated buttons below are the Utility cog's own actions;
    the child-subsystem buttons added in ``__init__`` (General, 420) surface the
    hub's ``parent_hub="utility"`` children so they are reachable by clicking
    through ``!help`` (the discoverability-audit fix — see
    :func:`discover_utility_children`).
    """

    def __init__(self, ctx: commands.Context):
        super().__init__(ctx.author, public=True)
        self.ctx = ctx
        # Surface child subsystems as forwarding buttons (row 3 — rows 0-2 hold the
        # cog's own actions, row 4 is reserved for the help layer's Back button).
        # Rendered unfiltered; visibility is enforced at click time in
        # _UtilityChildButton.callback (matches the Community hub's unfiltered path).
        for subsystem, meta in discover_utility_children():
            self.add_item(
                _UtilityChildButton(
                    subsystem=subsystem,
                    label=_format_child_label(subsystem, meta),
                    row=3,
                ),
            )

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🔧 Utility Panel",
            description=(
                "**🖥️ Server Info** — server statistics\n"
                "**👤 User Info** — your profile details\n"
                "**🖼️ Avatar** — display your avatar\n"
                "**📊 Poll** — create a reaction poll\n"
                "**🔔 Remind Me** — set a timed reminder\n"
                "**🔗 Invite** — generate a one-use server invite"
            ),
            color=UTILITY_COLOR,
        )
        children = discover_utility_children()
        if children:
            embed.add_field(
                name="More in Utility",
                value="\n".join(
                    f"{meta.get('emoji', '')} **{meta.get('display_name', name)}** — "
                    f"{meta.get('description', '')}".strip()
                    for name, meta in children
                ),
                inline=False,
            )
        embed.set_footer(text="Click an action below.")
        return embed

    @discord.ui.button(label="🖥️ Server Info", style=discord.ButtonStyle.blurple, row=0)
    async def serverinfo_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        guild = interaction.guild
        embed = discord.Embed(
            title=f"{guild.name}",
            description="Server Information",
            color=INFO_COLOR,
        )
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Boost Level", value=str(guild.premium_tier), inline=True)
        embed.add_field(
            name="Created",
            value=guild.created_at.strftime("%Y-%m-%d"),
            inline=True,
        )
        embed.add_field(
            name="Text Channels",
            value=str(len(guild.text_channels)),
            inline=True,
        )
        embed.add_field(
            name="Voice Channels",
            value=str(len(guild.voice_channels)),
            inline=True,
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="👤 User Info", style=discord.ButtonStyle.blurple, row=0)
    async def userinfo_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        member = interaction.user
        embed = discord.Embed(
            title=f"User Info — {member}",
            color=SUCCESS_COLOR,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Username", value=member.name, inline=True)
        embed.add_field(name="User ID", value=str(member.id), inline=True)
        embed.add_field(
            name="Joined Server",
            value=member.joined_at.strftime("%Y-%m-%d"),  # type: ignore[union-attr]
            inline=True,
        )
        embed.add_field(
            name="Joined Discord",
            value=member.created_at.strftime("%Y-%m-%d"),
            inline=True,
        )
        embed.add_field(
            name="Status",
            value=str(member.status).capitalize(),  # type: ignore[union-attr]
            inline=True,
        )
        embed.add_field(
            name="Activity",
            value=member.activity.name if member.activity else "None",  # type: ignore[union-attr]
            inline=True,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🖼️ Avatar", style=discord.ButtonStyle.blurple, row=0)
    async def avatar_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        member = interaction.user
        embed = discord.Embed(title=f"{member}'s Avatar", color=INFO_COLOR)
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="📊 Poll", style=discord.ButtonStyle.grey, row=1)
    async def poll_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_PollModal(interaction.channel))  # type: ignore[arg-type]

    @discord.ui.button(label="🔔 Remind Me", style=discord.ButtonStyle.grey, row=1)
    async def remind_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(
            _RemindModal(interaction.user, interaction.channel),  # type: ignore[arg-type]
        )

    @discord.ui.button(label="🔗 Invite", style=discord.ButtonStyle.grey, row=1)
    async def invite_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not interaction.user.guild_permissions.create_instant_invite:  # type: ignore[union-attr]
            await interaction.response.send_message(
                "❌ You need **Create Invite** permission.",
                ephemeral=True,
            )
            return
        invite = await interaction.channel.create_invite(max_uses=1, unique=True)  # type: ignore[union-attr]
        await interaction.response.send_message(
            f"🔗 One-use invite: {invite.url}",
            ephemeral=True,
        )

    @discord.ui.button(label="↩ Overview", style=discord.ButtonStyle.secondary, row=2)
    async def overview_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


# ---------------------------------------------------------------------------
# Poll Modal
# ---------------------------------------------------------------------------


class _PollModal(discord.ui.Modal, title="Create Poll"):  # type: ignore[call-arg]
    question = discord.ui.TextInput(label="Poll question", max_length=200)  # type: ignore[var-annotated]
    options = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Options (one per line, 2–10)",
        style=discord.TextStyle.paragraph,
        placeholder="Option 1\nOption 2\nOption 3",
        max_length=500,
    )

    def __init__(self, channel: discord.abc.Messageable):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        opts = [o.strip() for o in self.options.value.split("\n") if o.strip()]
        if len(opts) < 2:
            await interaction.response.send_message(
                "❌ Need at least 2 options.",
                ephemeral=True,
            )
            return
        if len(opts) > 10:
            await interaction.response.send_message(
                "❌ Max 10 options.",
                ephemeral=True,
            )
            return
        embed = discord.Embed(
            title=f"Poll: {self.question.value}",
            description="\n".join(f"{i+1}. {opt}" for i, opt in enumerate(opts)),
            color=INFO_COLOR,
        )
        poll_msg = await self.channel.send(embed=embed)
        for i in range(len(opts)):
            await poll_msg.add_reaction(f"{i+1}\N{COMBINING ENCLOSING KEYCAP}")
        await interaction.response.send_message("✅ Poll created!", ephemeral=True)


# ---------------------------------------------------------------------------
# Remind Modal
# ---------------------------------------------------------------------------


class _RemindModal(discord.ui.Modal, title="Set Reminder"):  # type: ignore[call-arg]
    minutes = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Minutes from now",
        placeholder="30",
        max_length=5,
    )
    message = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Reminder message",
        style=discord.TextStyle.paragraph,
        max_length=500,
    )

    def __init__(self, user: discord.User, channel: discord.abc.Messageable):
        super().__init__()
        self.user = user
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            t = int(self.minutes.value)
            if t <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Minutes must be a positive integer.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"⏳ Reminder set for **{t}** minute(s): {self.message.value}",
            ephemeral=True,
        )
        tasks.spawn(
            f"utility:remind:{self.user.id}",
            _remind_later(self.user, self.channel, t * 60, self.message.value),
        )


async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
