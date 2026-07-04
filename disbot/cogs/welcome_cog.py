"""Welcome cog — member greetings, farewells, and the optional entry role.

welcome v1 (owner decision Q-0110): the member-greeting layer of the
safety/community platform.  This cog is glue only — the greeting/farewell
embeds and the join/leave orchestration live in
:mod:`services.welcome_service`, and the config read model in
:mod:`services.welcome_config`.  Like every safety/community slice it registers
its :class:`SubsystemSchema` in ``cog_load`` so the settings are
operator-editable through the existing ``!settings`` widget.

Member events: ``on_member_join`` / ``on_member_remove`` coexist with the
autorole (role_cog) and event-logging (logging_cog) listeners — discord.py
dispatches each event to every registered listener independently.

Config: ``!settings`` → Welcome.  ``!welcome`` shows the current policy.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.permission_checks import perms_or_owner
from services import welcome_config
from utils.ui_constants import GENERAL_COLOR

logger = logging.getLogger("bot.cogs.welcome")


class WelcomeCog(commands.Cog):
    """Member-greeting layer (join greeting · leave farewell · entry role)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        from cogs.welcome.schemas import register_schemas

        register_schemas()  # declares the Welcome settings group.

    # -- member events --------------------------------------------------------

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Greet a joining member + grant the entry role (per guild policy)."""
        if member.bot:
            return
        from services import welcome_service

        await welcome_service.handle_member_join(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Post a farewell for a departing member (per guild policy)."""
        if member.bot:
            return
        from services import welcome_service

        await welcome_service.handle_member_leave(member)

    # -- status surface -------------------------------------------------------

    @staticmethod
    def _policy_embed(
        guild: discord.Guild,
        policy: welcome_config.WelcomePolicy,
    ) -> discord.Embed:
        """Render the effective welcome policy as a summary embed."""

        def _flag(on: bool) -> str:
            return "🟢 on" if on else "⚫ off"

        channel = (
            resources.resolve_channel(guild, channel_id=policy.channel_id)
            if policy.channel_id
            else None
        )
        channel_str = channel.mention if channel else "*(unset)*"
        role = (
            resources.resolve_role(guild, role_id=policy.entry_role_id)
            if policy.entry_role_id
            else None
        )
        role_str = role.mention if role else "*(none)*"

        lines = [
            f"**Master:** {_flag(policy.enabled)}",
            "",
            f"👋 **Greet on join** — {_flag(policy.join_enabled)}",
            f"🚪 **Farewell on leave** — {_flag(policy.leave_enabled)}",
            f"✉️ **DM on join** — {_flag(policy.dm_enabled)}",
            f"📢 **Channel:** {channel_str}",
            f"🎟️ **Entry role:** {role_str}",
        ]
        if policy.age_gate_enabled:
            lines.append(
                "🛡️ **Min account age:** "
                f"{policy.min_account_age_days}d "
                "(younger accounts skipped — anti-raid)",
            )
        if policy.greeting_delete_after is not None:
            lines.append(
                f"🧹 **Auto-delete greeting after:** {policy.delete_after_seconds}s",
            )
        embed = discord.Embed(
            title="👋 Welcome",
            description="\n".join(lines),
            color=GENERAL_COLOR,
        )
        # Show the rendered templates with a sample member/count so the
        # operator sees exactly what posts, placeholders expanded.  When the
        # message holds multiple "---"-separated variants, preview the first
        # and note that one is chosen at random per greeting.
        sample_count = max(guild.member_count or 1, 1)

        def _preview(template: str, sample_name: str) -> tuple[str, str]:
            variants = welcome_config.split_message_variants(template) or [template]
            rendered = welcome_config.render_template(
                variants[0],
                member_name=sample_name,
                guild_name=guild.name,
                member_count=sample_count,
            )
            suffix = (
                f" (1 of {len(variants)} random variants)" if len(variants) > 1 else ""
            )
            return rendered, suffix

        join_preview, join_suffix = _preview(policy.join_message, "@NewMember")
        embed.add_field(
            name=f"Join message preview{join_suffix}",
            value=join_preview,
            inline=False,
        )
        if policy.leave_enabled:
            leave_preview, leave_suffix = _preview(policy.leave_message, "NewMember")
            embed.add_field(
                name=f"Leave message preview{leave_suffix}",
                value=leave_preview,
                inline=False,
            )
        if policy.dm_enabled:
            dm_preview, dm_suffix = _preview(policy.dm_message, "@NewMember")
            embed.add_field(
                name=f"DM message preview{dm_suffix}",
                value=dm_preview,
                inline=False,
            )
        embed.set_footer(text="Configure in !settings → Welcome.")
        return embed

    @commands.command(
        name="welcome",
        help="Show the current welcome (greeting) policy for this server.",
        extras={"classification": "primary_entrypoint"},
    )
    @commands.guild_only()
    @perms_or_owner(manage_guild=True)
    async def welcome_status(self, ctx: commands.Context) -> None:
        """Render the effective welcome policy (admin/manage-guild only)."""
        policy = await welcome_config.load_policy(ctx.guild.id)
        await ctx.send(embed=self._policy_embed(ctx.guild, policy))

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — the welcome policy summary.

        welcome has no bespoke panel in v1 (config is the !settings widget
        group), so the help dropdown lands on the read-only policy summary
        with the pointer to !settings → Welcome.
        """
        from views.base import HubView

        if interaction.guild is None:
            return (
                discord.Embed(description="Welcome is only available in a server."),
                discord.ui.View(),
            )
        policy = await welcome_config.load_policy(interaction.guild.id)
        return self._policy_embed(interaction.guild, policy), HubView(interaction.user)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
