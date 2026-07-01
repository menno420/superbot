"""XP migration panels.

Two views, both ephemeral / author-locked / admin-gated:

* ``XpImportSetupView`` — the button entry point (from ``!xpconfig``): pick the
  other bot's level-up channel + which bot posted the announcements, then scan.
* ``XpImportView`` — previews a resolved scan (:class:`ScanPlan`) and, on
  confirm, applies it through :func:`services.xp_migration.import_levels`.
  Admin-gated again at the confirm callback (opening a panel does not authorize
  a later bulk write).

The import is **raise-only** — it never lowers a member who already earned more
here — so re-running is safe; the panels say so up front.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime import resources
from core.runtime.interaction_helpers import safe_edit
from services import xp_migration
from utils import xp_migration as xpm
from utils.ui_constants import UTILITY_COLOR
from utils.xp_migration import ScanPlan
from views.base import BaseView, interaction_is_admin


class XpImportView(BaseView):
    def __init__(self, ctx: commands.Context, plan: ScanPlan) -> None:
        super().__init__(ctx.author, timeout=300)
        self.ctx = ctx
        self.plan = plan
        self.apply_roles = True
        self._done = False
        self._sync_role_button()

    # ------------------------------------------------------------------ render
    def build_embed(self) -> discord.Embed:
        plan = self.plan
        embed = discord.Embed(
            title="📥 Import XP / levels",
            description=(
                f"Scanned **{plan.scanned_messages}** messages in "
                f"<#{plan.channel_id}> for **{plan.source_label}** level-up "
                f"announcements.\n"
                f"Found **{plan.user_count}** member(s) to import "
                f"(highest level seen per member)."
            ),
            color=UTILITY_COLOR,
        )
        if plan.sample:
            lines = "\n".join(
                f"• **{name}** → level {level}" for name, level in plan.sample
            )
            more = plan.user_count - len(plan.sample)
            if more > 0:
                lines += f"\n• …and **{more}** more"
            embed.add_field(name="Preview", value=lines, inline=False)
        if plan.unresolved_names:
            shown = ", ".join(plan.unresolved_names[:10])
            extra = len(plan.unresolved_names) - 10
            if extra > 0:
                shown += f", +{extra} more"
            embed.add_field(
                name=f"⚠️ Unmatched ({len(plan.unresolved_names)})",
                value=(
                    "These announcements named a member by text (no mention) "
                    f"that isn't in the server now, so they're skipped:\n{shown}"
                ),
                inline=False,
            )
        embed.add_field(
            name="Merge policy",
            value=(
                "**Raise-only** — a member is never lowered below what they've "
                "already earned here, so this is safe to re-run."
            ),
            inline=False,
        )
        embed.set_footer(
            text=(
                "Level roles will also be assigned."
                if self.apply_roles
                else "Level roles will NOT be assigned."
            ),
        )
        return embed

    def _sync_role_button(self) -> None:
        self.btn_roles.label = (
            "Assign level roles: ON" if self.apply_roles else "Assign level roles: OFF"
        )
        self.btn_roles.style = (
            discord.ButtonStyle.green if self.apply_roles else discord.ButtonStyle.grey
        )

    # ----------------------------------------------------------------- actions
    @discord.ui.button(
        label="✅ Apply import",
        style=discord.ButtonStyle.blurple,
        row=0,
    )
    async def btn_apply(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "You need the Administrator permission to run an import.",
                ephemeral=True,
            )
            return
        if self._done:
            return
        self._done = True
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        await safe_edit(
            interaction,
            embed=discord.Embed(
                title="📥 Importing…",
                description=f"Importing **{self.plan.user_count}** member(s)…",
                color=UTILITY_COLOR,
            ),
            view=self,
        )

        summary = await xp_migration.import_levels(
            self.ctx.guild,
            self.plan.records,
            source=f"import:{self.plan.source_key}",
            actor_id=self.ctx.author.id,
            apply_roles=self.apply_roles,
        )

        result = discord.Embed(
            title="✅ Import complete",
            description=(
                f"Imported **{summary.total}** member(s) from "
                f"**{self.plan.source_label}**."
            ),
            color=UTILITY_COLOR,
        )
        result.add_field(name="Raised", value=str(summary.raised), inline=True)
        result.add_field(
            name="Unchanged",
            value=str(summary.unchanged),
            inline=True,
        )
        if self.apply_roles:
            role_line = f"{summary.roles_succeeded} applied"
            if summary.roles_failed:
                role_line += f", {summary.roles_failed} failed"
            result.add_field(name="Level roles", value=role_line, inline=True)
        result.set_footer(text="Raise-only — safe to re-run any time.")
        self.stop()
        await safe_edit(interaction, embed=result, view=None)

    @discord.ui.button(label="Assign level roles: ON", row=0)
    async def btn_roles(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if self._done:
            return
        self.apply_roles = not self.apply_roles
        self._sync_role_button()
        await safe_edit(interaction, embed=self.build_embed(), view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey, row=0)
    async def btn_cancel(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        self._done = True
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        self.stop()
        await safe_edit(
            interaction,
            embed=discord.Embed(
                title="Import cancelled",
                description="No XP was changed.",
                color=UTILITY_COLOR,
            ),
            view=self,
        )


def _source_options(selected_key: str) -> list[discord.SelectOption]:
    """Build the "which bot" select options from the announcer registry."""
    options: list[discord.SelectOption] = []
    for key in xpm.format_keys():
        fmt = xpm.get_format(key)
        if fmt is None:
            continue
        options.append(
            discord.SelectOption(
                label=fmt.label,
                value=key,
                default=key == selected_key,
                description="default" if key == xpm.DEFAULT_FORMAT else None,
            ),
        )
    return options


class XpImportSetupView(BaseView):
    """Button entry point for importing levels from another bot.

    Pick the other bot's **level-up channel** and **which bot** posted the
    announcements, then scan → :class:`XpImportView` preview. Reached from the
    "📥 Import from another bot" button on the XP config panel. Framed generically
    (Arcane is just the default source, one of several) — the only requirement it
    states up front is that the other bot has a dedicated level-up channel.
    """

    def __init__(self, ctx: commands.Context) -> None:
        super().__init__(ctx.author, timeout=300)
        self.ctx = ctx
        self.channel_id: int | None = None
        self.source_key = xpm.DEFAULT_FORMAT
        self.pick_source.options = _source_options(self.source_key)  # type: ignore[assignment]

    def build_embed(self) -> discord.Embed:
        fmt = xpm.get_format(self.source_key)
        label = fmt.label if fmt is not None else self.source_key
        channel = f"<#{self.channel_id}>" if self.channel_id else "*not selected*"
        embed = discord.Embed(
            title="📥 Import XP from another bot",
            description=(
                "Copy the levels members earned under a **different leveling "
                "bot** into SuperBot. It works by reading that bot's **dedicated "
                "level-up channel** — the one where it posts *“so-and-so reached "
                "level N”* — and keeping each member's highest level.\n\n"
                "1. Pick that **level-up channel** below.\n"
                "2. Pick **which bot** posted the messages.\n"
                "3. Press **🔍 Scan** to preview before anything is written."
            ),
            color=UTILITY_COLOR,
        )
        embed.add_field(name="Level-up channel", value=channel, inline=True)
        embed.add_field(name="From bot", value=label, inline=True)
        embed.set_footer(text="Raise-only — a member is never lowered. Safe to re-run.")
        return embed

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Pick the other bot's level-up channel",
        row=0,
    )
    async def pick_channel(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect,
    ) -> None:
        self.channel_id = select.values[0].id
        await safe_edit(interaction, embed=self.build_embed(), view=self)

    @discord.ui.select(placeholder="Which bot posted them? (default: Arcane)", row=1)
    async def pick_source(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select,
    ) -> None:
        self.source_key = select.values[0]
        self.pick_source.options = _source_options(self.source_key)  # type: ignore[assignment]
        await safe_edit(interaction, embed=self.build_embed(), view=self)

    @discord.ui.button(label="🔍 Scan", style=discord.ButtonStyle.blurple, row=2)
    async def btn_scan(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "You need the Administrator permission to import.",
                ephemeral=True,
            )
            return
        if self.channel_id is None:
            await interaction.response.send_message(
                "Pick the other bot's level-up channel first.",
                ephemeral=True,
            )
            return
        fmt = xpm.get_format(self.source_key)
        assert fmt is not None  # noqa: S101 — source_key always comes from the registry
        channel = resources.resolve_channel(self.ctx.guild, channel_id=self.channel_id)
        if channel is None:
            await interaction.response.send_message(
                "That channel is no longer available — pick another.",
                ephemeral=True,
            )
            return

        await safe_edit(
            interaction,
            embed=discord.Embed(
                title="📥 Scanning…",
                description=f"Reading <#{self.channel_id}> for **{fmt.label}** level-ups…",
                color=UTILITY_COLOR,
            ),
            view=self,
        )
        plan = await xp_migration.scan_channel(self.ctx.guild, channel, fmt, None)
        if plan is None:
            await safe_edit(
                interaction,
                embed=discord.Embed(
                    title="Can't read that channel",
                    description=(
                        f"I can't read message history in <#{self.channel_id}>. "
                        "Grant me **Read Message History** there and scan again."
                    ),
                    color=UTILITY_COLOR,
                ),
                view=self,
            )
            return
        if not plan.records:
            await safe_edit(
                interaction,
                embed=discord.Embed(
                    title="Nothing to import",
                    description=(
                        f"Scanned **{plan.scanned_messages}** message(s) in "
                        f"<#{self.channel_id}> but found no **{fmt.label}** "
                        "level-up announcements. Try a different bot or channel."
                    ),
                    color=UTILITY_COLOR,
                ),
                view=self,
            )
            return

        preview = XpImportView(self.ctx, plan)
        self.stop()
        await safe_edit(interaction, embed=preview.build_embed(), view=preview)
        preview.message = self.message

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey, row=2)
    async def btn_cancel(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        self.stop()
        await safe_edit(
            interaction,
            embed=discord.Embed(
                title="Import cancelled",
                description="No XP was changed.",
                color=UTILITY_COLOR,
            ),
            view=self,
        )
