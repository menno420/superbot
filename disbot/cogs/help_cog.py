from __future__ import annotations

import logging

import discord
from discord.ext import commands
from services import governance_service
from services.governance_service import GovernanceContext
from utils.subsystem_registry import SUBSYSTEMS, all_subsystems_sorted
from utils.ui_constants import ADMIN_COLOR, GENERAL_COLOR, MOD_COLOR, UTILITY_COLOR
from utils.visibility_rules import VISIBILITY_TIERS, is_tier_sufficient

logger = logging.getLogger("bot")

# Tier group display configuration
_TIER_GROUPS = [
    {
        "label": "🟢 User Commands",
        "tiers": {"user", "trusted"},
        "color": GENERAL_COLOR,
    },
    {
        "label": "🟠 Moderation",
        "tiers": {"staff", "moderator"},
        "color": MOD_COLOR,
    },
    {
        "label": "🔴 Administration",
        "tiers": {"administrator", "owner"},
        "color": ADMIN_COLOR,
    },
]


def _cog_for_subsystem(bot: commands.Bot, subsystem_name: str) -> commands.Cog | None:
    """Find the cog that corresponds to a subsystem by checking entry_points."""
    meta = SUBSYSTEMS.get(subsystem_name)
    if not meta:
        return None
    for cog in bot.cogs.values():
        cog_cmds = {cmd.name for cmd in cog.get_commands()}
        entry_points = set(meta.get("entry_points", []))
        if cog_cmds & entry_points:
            return cog
    return None


def _get_visible_commands(cog: commands.Cog) -> list[commands.Command]:
    return [cmd for cmd in cog.get_commands() if not cmd.hidden and cmd.enabled]


async def build_overview_embed(
    bot: commands.Bot, ctx: commands.Context, visible: set[str], member_tier: str
) -> discord.Embed:
    """Build a governance-aware overview embed grouped by visibility tier."""
    embed = discord.Embed(
        title="📚 Help Menu",
        description="Select a category from the dropdown below.",
        color=UTILITY_COLOR,
    )

    subsystems_by_name = dict(all_subsystems_sorted())

    for group in _TIER_GROUPS:
        group_tiers: set[str] = group["tiers"]
        entries: list[str] = []

        for name, meta in subsystems_by_name.items():
            if name not in visible:
                continue
            if meta.get("visibility_tier") not in group_tiers:
                continue
            emoji = meta.get("emoji", "•")
            display = meta.get("display_name", name)
            desc = meta.get("description", "")
            entries.append(f"{emoji} **{display}** — {desc}")

        if entries:
            embed.add_field(
                name=group["label"],
                value="\n".join(entries),
                inline=False,
            )

    if not embed.fields:
        embed.description = "No commands are available in this channel."
    return embed


def build_cog_embed(
    cog: commands.Cog,
    prefix: str,
    subsystem_name: str | None = None,
) -> discord.Embed:
    """Build a detail embed for one cog/subsystem."""
    meta = SUBSYSTEMS.get(subsystem_name) if subsystem_name else None
    color = discord.Color(meta["color"]) if meta else UTILITY_COLOR
    display = (
        meta.get("display_name", cog.qualified_name.replace("Cog", ""))
        if meta
        else cog.qualified_name.replace("Cog", "")
    )
    emoji = meta.get("emoji", "📖") if meta else "📖"

    embed = discord.Embed(title=f"{emoji} {display}", color=color)
    cmds = _get_visible_commands(cog)
    for cmd in cmds:
        aliases = f"  *(aliases: {', '.join(cmd.aliases)})*" if cmd.aliases else ""
        sig = f" {cmd.signature}".rstrip() if cmd.signature else ""
        embed.add_field(
            name=f"`{prefix}{cmd.name}`{aliases}",
            value=f"{cmd.help or 'No description.'}\nUsage: `{prefix}{cmd.name}{sig}`",
            inline=False,
        )
    if not embed.fields:
        embed.description = "No commands available in this category."
    return embed


class _SubsystemSelect(discord.ui.Select):
    def __init__(self, bot: commands.Bot, visible: set[str]):
        subsystems_sorted = [
            (name, meta) for name, meta in all_subsystems_sorted() if name in visible
        ]
        options = [
            discord.SelectOption(
                label=meta.get("display_name", name),
                value=name,
                description=meta.get("description", "")[:100],
                emoji=meta.get("emoji"),
            )
            for name, meta in subsystems_sorted
        ][:25]
        super().__init__(
            placeholder="Choose a category…",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        subsystem_name = self.values[0]
        cog = _cog_for_subsystem(interaction.client, subsystem_name)
        if not cog:
            await interaction.response.send_message(
                "That category is no longer loaded.", ephemeral=True
            )
            return
        prefix = self.view.prefix
        embed = build_cog_embed(cog, prefix, subsystem_name)
        self.view.back_btn.disabled = False
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        ctx: commands.Context,
        visible: set[str],
        member_tier: str,
    ):
        super().__init__(timeout=300)
        self.bot = bot
        self.ctx = ctx
        self.visible = visible
        self.member_tier = member_tier
        self.prefix = ctx.prefix or "!"
        self._select = _SubsystemSelect(bot, visible)
        self.add_item(self._select)
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "This help menu is not for you.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="◀ Back", style=discord.ButtonStyle.grey, row=1, disabled=True
    )
    async def back_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        button.disabled = True
        self.remove_item(self._select)
        self._select = _SubsystemSelect(self.bot, self.visible)
        self.add_item(self._select)
        embed = await build_overview_embed(
            self.bot, self.ctx, self.visible, self.member_tier
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True  # type: ignore[union-attr]
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help", aliases=["hilfe"])
    async def help_command(self, ctx: commands.Context, *, category: str = None):
        """Shows available commands. Pass a category name for details."""
        gctx = GovernanceContext.from_ctx(ctx)
        vis_result = await governance_service.resolve_visibility(gctx)
        visible = vis_result.visible_subsystems
        member_tier = vis_result.member_tier

        if category:
            # Try subsystem name lookup
            for name, meta in SUBSYSTEMS.items():
                if name not in visible:
                    continue
                if category.lower() in (
                    name.lower(),
                    meta.get("display_name", "").lower(),
                ):
                    cog = _cog_for_subsystem(self.bot, name)
                    if cog:
                        await ctx.send(
                            embed=build_cog_embed(cog, ctx.prefix or "!", name),
                            delete_after=60,
                        )
                        return

            # Try cog name or command name
            cog = self.bot.get_cog(category) or self.bot.get_cog(category + "Cog")
            cmd = self.bot.get_command(category)
            if cog:
                await ctx.send(
                    embed=build_cog_embed(cog, ctx.prefix or "!"),
                    delete_after=60,
                )
                return
            if cmd:
                prefix = ctx.prefix or "!"
                embed = discord.Embed(
                    title=f"`{prefix}{cmd.name}`",
                    description=cmd.help or "No description.",
                    color=UTILITY_COLOR,
                )
                if cmd.aliases:
                    embed.add_field(
                        name="Aliases",
                        value=", ".join(f"`{a}`" for a in cmd.aliases),
                    )
                embed.add_field(
                    name="Usage",
                    value=f"`{prefix}{cmd.name}{(' ' + cmd.signature) if cmd.signature else ''}`",
                    inline=False,
                )
                await ctx.send(embed=embed, delete_after=60)
                return
            await ctx.send(
                f"No command or category named `{category}` found.", delete_after=10
            )
            return

        embed = await build_overview_embed(self.bot, ctx, visible, member_tier)
        view = HelpView(self.bot, ctx, visible, member_tier)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
    logger.info("HelpCog loaded.")
