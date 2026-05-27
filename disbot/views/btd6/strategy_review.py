"""Staff strategy-review view for ``!btd6 strategies pending`` (PR5).

Per the plan: pending strategies need a staff review surface that
funnels every state transition through
:mod:`services.btd6_strategy_mutation`. The view does not write to
the DB directly; each button is a thin wrapper over a mutation call.

Button matrix per strategy embed:

* **Approve (guild)** — calls ``staff_approve_guild``. Keeps the
  strategy at ``visibility='guild'``; the global publish action
  stays a separate click so guild-local approval is explicitly
  decoupled from staff-confirmed global publishing.
* **Publish (global)** — calls ``staff_publish``. Flips
  ``visibility='published'``.
* **Reject** — calls ``reject``.
* **Unpublish** — calls ``unpublish``; visible only when the
  strategy is currently published.

All four actions require ``manage_guild`` or ``administrator``
permissions; the mutation service enforces this server-side, and the
view's ``interaction_check`` mirrors it client-side so non-staff get
a clear ephemeral denial.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup

logger = logging.getLogger("bot.views.btd6.strategy_review")

_VIEW_TIMEOUT_SECONDS = 300
_PANEL_COLOR = discord.Color.gold()


def _is_staff(member: Any) -> bool:
    perms = getattr(member, "guild_permissions", None)
    if perms is None:
        return False
    return bool(
        getattr(perms, "administrator", False) or getattr(perms, "manage_guild", False),
    )


def build_strategy_embed(strategy: dict[str, Any]) -> discord.Embed:
    """Render one strategy as a review-friendly embed.

    The body fields are surfaced inline for the reviewer's benefit but
    the strategy itself stays as untrusted text — no markdown beyond
    the field labels that the staff control.
    """
    title = strategy.get("title") or f"Strategy #{strategy.get('id')}"
    embed = discord.Embed(
        title=f"📜 {title}"[:256],
        description=(strategy.get("summary") or "")[:2048],
        color=_PANEL_COLOR,
    )
    inline_keys = (
        ("map", "Map"),
        ("mode", "Mode"),
        ("difficulty", "Difficulty"),
        ("hero", "Hero"),
    )
    for key, label in inline_keys:
        value = strategy.get(key)
        if value:
            embed.add_field(name=label, value=str(value)[:128], inline=True)
    state_bits = [
        f"approval=`{strategy.get('approval_status')}`",
        f"visibility=`{strategy.get('visibility')}`",
        f"v{strategy.get('version', 0)}",
    ]
    embed.add_field(name="State", value=" · ".join(state_bits), inline=False)
    snapshot = strategy.get("submitter_display_snapshot")
    submitted_by = strategy.get("submitted_by")
    if snapshot or submitted_by:
        actor = snapshot or f"<@{submitted_by}>"
        embed.set_footer(text=f"id={strategy.get('id')} · submitted by {actor}")
    else:
        embed.set_footer(text=f"id={strategy.get('id')}")
    return embed


async def _refresh_or_followup(
    interaction: discord.Interaction,
    *,
    strategy_id: int,
    confirm_message: str,
) -> None:
    """Re-fetch the strategy and refresh the parent embed, plus an
    ephemeral confirmation so the staff actor sees what happened.

    Assumes the caller has already deferred the interaction so the
    safe helpers route through ``followup.send`` /
    ``followup.edit_message``.
    """
    try:
        from utils.db import btd6_strategies as db

        refreshed = await db.get_strategy(strategy_id)
    except Exception:  # noqa: BLE001 — defensive
        logger.exception("strategy_review: refresh fetch failed for id=%s", strategy_id)
        await safe_followup(
            interaction,
            f"⚠️ {confirm_message} (refresh failed — the change went through "
            "but the panel could not reload).",
            ephemeral=True,
        )
        return

    if refreshed is None:
        await safe_followup(
            interaction,
            f"✅ {confirm_message} (the strategy is gone from the table now).",
            ephemeral=True,
        )
        return

    embed = build_strategy_embed(refreshed)
    view = StrategyReviewView(refreshed)
    edited = await safe_edit(interaction, embed=embed, view=view)
    if not edited:
        await safe_followup(
            interaction,
            f"⚠️ {confirm_message} but the review panel could not be refreshed.",
            ephemeral=True,
        )
        return
    await safe_followup(interaction, f"✅ {confirm_message}", ephemeral=True)


class StrategyReviewView(discord.ui.View):
    """Per-strategy review controls. Staff-only."""

    def __init__(self, strategy: dict[str, Any]) -> None:
        super().__init__(timeout=_VIEW_TIMEOUT_SECONDS)
        self.strategy_id = int(strategy["id"])
        self.visibility = str(strategy.get("visibility") or "guild")
        # The Unpublish button only makes sense for currently-published
        # rows; remove it when visibility is guild-local so the staff
        # doesn't try to "unpublish" a guild draft.
        if self.visibility != "published":
            self.remove_item(self.unpublish_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not _is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Strategy review requires `manage_guild` or administrator.",
                ephemeral=True,
            )
            return False
        return True

    async def _mutate(
        self,
        interaction: discord.Interaction,
        *,
        action_callable: Any,
        kwargs: dict[str, Any],
        confirm: str,
    ) -> None:
        from services.btd6_strategy_mutation import BTD6StrategyMutationError

        # Defer first (component defer_update — silent ack on the
        # parent message) so we have the full 15-minute followup
        # window for the mutation + refresh round-trip.
        if not await safe_defer(interaction):
            return

        try:
            await action_callable(self.strategy_id, **kwargs)
        except BTD6StrategyMutationError as exc:
            # Typed mutation errors expose the service message but
            # not the class name — service messages are already
            # user-facing.
            await safe_followup(
                interaction,
                f"❌ Could not update strategy #{self.strategy_id}: {exc}",
                ephemeral=True,
            )
            return
        except Exception:  # noqa: BLE001 — surface unexpected errors
            logger.exception(
                "StrategyReviewView: mutation %s raised for strategy=%s",
                action_callable.__name__,
                self.strategy_id,
            )
            await safe_followup(
                interaction,
                "❌ Unexpected error while updating this strategy. "
                "Check logs for details.",
                ephemeral=True,
            )
            return
        await _refresh_or_followup(
            interaction,
            strategy_id=self.strategy_id,
            confirm_message=confirm,
        )

    @discord.ui.button(
        label="Approve (guild)",
        style=discord.ButtonStyle.success,
        row=0,
    )
    async def approve_guild_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from services import btd6_strategy_mutation

        await self._mutate(
            interaction,
            action_callable=btd6_strategy_mutation.staff_approve_guild,
            kwargs={"staff_actor": interaction.user},
            confirm=f"Approved strategy #{self.strategy_id} at guild visibility.",
        )

    @discord.ui.button(
        label="Publish (global)",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def publish_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from services import btd6_strategy_mutation

        await self._mutate(
            interaction,
            action_callable=btd6_strategy_mutation.staff_publish,
            kwargs={"staff_actor": interaction.user},
            confirm=f"Published strategy #{self.strategy_id} globally.",
        )

    @discord.ui.button(
        label="Reject",
        style=discord.ButtonStyle.danger,
        row=0,
    )
    async def reject_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from services import btd6_strategy_mutation

        await self._mutate(
            interaction,
            action_callable=btd6_strategy_mutation.staff_reject,
            kwargs={"staff_actor": interaction.user},
            confirm=f"Rejected strategy #{self.strategy_id}.",
        )

    @discord.ui.button(
        label="Unpublish",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def unpublish_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        from services import btd6_strategy_mutation

        await self._mutate(
            interaction,
            action_callable=btd6_strategy_mutation.unpublish,
            kwargs={"staff_actor": interaction.user},
            confirm=f"Unpublished strategy #{self.strategy_id} (back to guild).",
        )


__all__ = [
    "StrategyReviewView",
    "build_strategy_embed",
]
