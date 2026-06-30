"""Guided CT-team configuration flow (Settings Phase 2, Q-0064).

The decided shape for the BTD6 CT group pointer: **accept URL/ID → parse →
preview → confirm**, never a generic scalar text field. The flow is
presentation only — :mod:`services.btd6_ct_team_service` stays the typed
mutation owner (``set_team_group_id``), and the Confirm callback re-checks
Manage Server at execution time (opening the flow never authorizes the
later commit).

Entry points:

* ``!btd6 ctteam <url-or-id>`` — the parsed id goes straight to the
  preview+confirm step (no immediate write anymore).
* ``!btd6 ctteam`` (no arg, Manage Server) — the team embed carries a
  "Set CT team…" button that opens :class:`CTGroupFlowModal`.
"""

from __future__ import annotations

import logging

import discord

from views.base import BaseView

logger = logging.getLogger("bot.views.btd6.ct_group_flow")


def _manage_guild(user: object) -> bool:
    from config import is_platform_owner

    if is_platform_owner(getattr(user, "id", None)):
        return True
    perms = getattr(user, "guild_permissions", None)
    return bool(perms is not None and getattr(perms, "manage_guild", False))


async def build_ct_preview_embed(guild_id: int, group_id: str) -> discord.Embed:
    """Preview embed for ``group_id`` before it is committed.

    Shows the current → new pointer change and, best-effort, the
    bracket's live standing so the operator can confirm it is really
    their team. A live-fetch failure degrades to a note — committing a
    pointer must not require the Ninja Kiwi API to be reachable.
    """
    from services import btd6_ct_team_service
    from utils.btd6.context_footer import append_context_footer

    embed = discord.Embed(
        title="🛡️ BTD6 — Confirm CT team",
        color=discord.Color.gold(),
    )
    current = await btd6_ct_team_service.get_team_group_id(guild_id)
    if current and current != group_id:
        embed.add_field(
            name="Change",
            value=f"`{current}` → `{group_id}`",
            inline=False,
        )
    else:
        embed.add_field(name="Bracket id", value=f"`{group_id}`", inline=False)

    try:
        result = await btd6_ct_team_service.get_ct_bracket(group_id)
    except Exception:  # noqa: BLE001 — preview survives a live-fetch failure
        logger.warning(
            "ct_group_flow: live preview fetch failed for %s",
            group_id,
            exc_info=True,
        )
        result = None
    if result is None:
        embed.add_field(
            name="Preview",
            value="Couldn't fetch the live standing right now — you can still confirm.",
            inline=False,
        )
    elif result.ct_id is None:
        embed.add_field(
            name="Preview",
            value="No Contested Territory event is active right now.",
            inline=False,
        )
    elif result.stale or not result.rows:
        embed.add_field(
            name="⚠️ Check this id",
            value=(
                "This id returned no teams for the current CT event. Ninja "
                "Kiwi rotates bracket ids each event — confirm only if you "
                "are sure this is this week's id."
            ),
            inline=False,
        )
    else:
        lines = [
            f"`#{row.rank}` **{discord.utils.escape_markdown(row.display_name)}**"
            f" — {row.score:,}"
            for row in result.rows[:5]
        ]
        embed.add_field(
            name=f"Bracket standings (CT {result.ct_id})",
            value="\n".join(lines),
            inline=False,
        )
    embed.set_footer(text="Confirm to save, Cancel to discard.")
    return append_context_footer(embed, "btd6_ct:confirm")


class CTGroupConfirmView(BaseView):
    """Confirm/Cancel step of the guided flow (author-locked, 180s)."""

    def __init__(self, author: discord.abc.User, group_id: str) -> None:
        super().__init__(author)
        self._group_id = group_id

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        # Authority is re-checked at execution time (views rule) — the
        # preview may have been sitting for minutes.
        if not _manage_guild(interaction.user):
            await interaction.response.send_message(
                "You need the Manage Server permission to change the CT team.",
                ephemeral=True,
            )
            return
        from services import btd6_ct_team_service

        stored = await btd6_ct_team_service.set_team_group_id(
            interaction.guild.id,
            self._group_id,
        )
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        if stored is None:  # pragma: no cover - parsed earlier; defensive
            await interaction.response.edit_message(
                content="That bracket id no longer parses — nothing saved.",
                embed=None,
                view=self,
            )
            return
        await interaction.response.edit_message(
            content=f"✅ CT team set to `{stored}`.",
            embed=None,
            view=self,
        )
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(
            content="Cancelled — CT team unchanged.",
            embed=None,
            view=self,
        )
        self.stop()


class CTGroupFlowModal(discord.ui.Modal, title="Set CT team"):
    """Step 1 — accept the bracket URL or bare id."""

    raw: discord.ui.TextInput = discord.ui.TextInput(
        label="CT bracket URL or id",
        placeholder="https://…/leaderboard/group/<id> or the bare id",
        required=True,
        max_length=200,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        from services import btd6_ct_team_service

        group_id = btd6_ct_team_service.parse_group_id(str(self.raw.value))
        if group_id is None:
            await interaction.response.send_message(
                "That doesn't look like a CT bracket id or group URL. Paste "
                "your team's `…/leaderboard/group/<id>` link or the bare id.",
                ephemeral=True,
            )
            return
        embed = await build_ct_preview_embed(interaction.guild.id, group_id)
        view = CTGroupConfirmView(interaction.user, group_id)
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )


class CTGroupSetButton(discord.ui.Button):
    """The "Set CT team…" entry on the team embed (Manage Server only)."""

    def __init__(self) -> None:
        super().__init__(
            label="Set CT team…",
            style=discord.ButtonStyle.primary,
            emoji="🛡️",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not _manage_guild(interaction.user):
            await interaction.response.send_message(
                "You need the Manage Server permission to change the CT team.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(CTGroupFlowModal())


class CTGroupEntryView(BaseView):
    """Wraps the team embed with the guided-flow entry button."""

    def __init__(self, author: discord.abc.User) -> None:
        super().__init__(author)
        self.add_item(CTGroupSetButton())


__all__ = [
    "CTGroupConfirmView",
    "CTGroupEntryView",
    "CTGroupFlowModal",
    "CTGroupSetButton",
    "build_ct_preview_embed",
]
