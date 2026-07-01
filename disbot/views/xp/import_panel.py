"""XP migration confirm panel.

``XpImportView`` previews a resolved level-up channel scan (:class:`ScanPlan`)
and, on confirm, applies it through :func:`services.xp_migration.import_levels`.
Ephemeral, author-locked, admin-gated at both the opening command *and* the
confirm callback (opening a panel does not authorize a later bulk write).

The import is **raise-only** — it never lowers a member who already earned more
here — so re-running is safe; the panel says so up front.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from core.runtime.interaction_helpers import safe_edit
from services import xp_migration
from utils.ui_constants import UTILITY_COLOR
from utils.xp_migration import ScanPlan
from views.base import BaseView, interaction_is_admin

_SAMPLE_LIMIT = 10


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
