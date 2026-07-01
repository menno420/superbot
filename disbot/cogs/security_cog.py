"""Security cog — raid detection + account-age filter (tiers 1+2, Q-0111).

The automated join-screening layer of the safety/community platform. This cog
is glue only — the detection + orchestration live in
:mod:`services.security_service` and the config read model in
:mod:`services.security_config`. Like every safety/community slice it registers
its :class:`SubsystemSchema` in ``cog_load`` so the settings are
operator-editable through the existing ``!settings`` widget.

Member events: ``on_member_join`` coexists with the welcome (welcome_cog),
autorole (role_cog), and event-logging (logging_cog) listeners — discord.py
dispatches each event to every registered listener independently.

Config: ``!settings`` → Security. ``!security`` shows the current policy. The
two DECLINED tiers (alt-detection / VPN blocking) are deliberately absent.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.permission_checks import perms_or_owner
from services import security_config
from utils.ui_constants import GENERAL_COLOR

logger = logging.getLogger("bot.cogs.security")


class SecurityCog(commands.Cog):
    """Join-screening layer (raid detection · account-age filter)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        from cogs.security.schemas import register_schemas

        register_schemas()  # declares the Security settings group.

    # -- member events --------------------------------------------------------

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Screen a joining member through the enabled tiers (per guild policy)."""
        if member.bot:
            return
        from services import security_service

        await security_service.handle_member_join(member)

    # -- status surface -------------------------------------------------------

    @staticmethod
    def _policy_embed(
        guild: discord.Guild,
        policy: security_config.SecurityPolicy,
    ) -> discord.Embed:
        """Render the effective security policy as a summary embed."""

        def _flag(on: bool) -> str:
            return "🟢 on" if on else "⚫ off"

        alert_channel = (
            resources.resolve_channel(guild, channel_id=policy.alert_channel_id)
            if policy.alert_channel_id
            else None
        )
        alert_str = alert_channel.mention if alert_channel else "*(unset)*"

        lines = [
            f"**Master:** {_flag(policy.enabled)}",
            f"📢 **Alert channel:** {alert_str}",
        ]
        embed = discord.Embed(
            title="🛡️ Server security",
            description="\n".join(lines),
            color=GENERAL_COLOR,
        )
        embed.add_field(
            name=f"🚨 Raid detection — {_flag(policy.raid_enabled)}",
            value=(
                f"Trigger: **{policy.raid_join_count}** joins / "
                f"**{policy.raid_window_seconds}s**\n"
                + (
                    f"Lockdown: slowmode **{policy.raid_slowmode_seconds}s** for "
                    f"**{policy.raid_lockdown_seconds}s**"
                    if policy.applies_raid_slowmode
                    else "Lockdown: alert-only (no slowmode channel set)"
                )
            ),
            inline=False,
        )
        embed.add_field(
            name=f"⚠️ Account-age filter — {_flag(policy.age_enabled)}",
            value=(
                f"Threshold: **{policy.age_min_days}** days\n"
                f"Action: **{policy.age_action}**"
            ),
            inline=False,
        )
        embed.set_footer(text="Configure in !settings → Security.")
        return embed

    @commands.command(
        name="security",
        help="Show the current server-security policy (raid + account-age).",
        extras={"classification": "primary_entrypoint"},
    )
    @commands.guild_only()
    @perms_or_owner(manage_guild=True)
    async def security_status(self, ctx: commands.Context) -> None:
        """Render the effective security policy (admin/manage-guild only)."""
        policy = await security_config.load_policy(ctx.guild.id)
        await ctx.send(embed=self._policy_embed(ctx.guild, policy))

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook — the security policy summary.

        security has no bespoke panel in v1 (config is the !settings widget
        group), so the help dropdown lands on the read-only policy summary with
        the pointer to !settings → Security.
        """
        from views.base import HubView

        if interaction.guild is None:
            return (
                discord.Embed(description="Security is only available in a server."),
                discord.ui.View(),
            )
        policy = await security_config.load_policy(interaction.guild.id)
        return self._policy_embed(interaction.guild, policy), HubView(interaction.user)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SecurityCog(bot))
