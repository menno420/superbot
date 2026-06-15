"""Mining vault panel — a per-player safe stash (brainstorm §7.5).

An ephemeral child of the mining hub.  The vault is a protected store separate
from the active mining pack: depositing moves items out of ``mining_inventory``
into ``mining_vault``, withdrawing moves them back.  Every move runs through
:mod:`services.mining_workflow` (one transaction per operation — Q-0071/RS02);
this view is only the buttons + modal that call it.

v2 (Slice A) gives the vault an **upgradeable capacity** (distinct item-types):
the ⬆️ Upgrade button / ``!vaultupgrade`` spend coins to add room — a gentle
coin sink.  Capacity is *soft*: deposits are never blocked (owner: no hard
cap), the panel only nudges when you are over capacity.  See
``docs/planning/mining-structures-skill-tree-plan-2026-06-14.md`` Slice A.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import mining_workflow
from utils import db, equipment
from utils.mining import capacity, items
from utils.mining.market import TradeResult
from utils.mining.names import resolve_item_name
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import HubView

# Kind → display label for the grouped vault listing (mirrors the hub's typed
# inventory panel so the two stores read the same way).
_KIND_LABELS: dict[str, str] = {
    "resource": "⛏️ Resources",
    "tool": "🛠️ Tools",
    "consumable": "🧨 Consumables",
    "structure": "🏛️ Structures",
    "treasure": "💎 Treasure",
}


def _move_candidates() -> tuple[str, ...]:
    """Known item names for fuzzy resolution of a typed deposit/withdraw."""
    return tuple(items.catalog_names()) + tuple(equipment.gear_names())


async def build_vault_embed(
    user_id: int,
    guild_id: int,
    *,
    note: str = "",
) -> discord.Embed:
    """The vault embed: what's stashed (grouped), its value, and how to move items."""
    suid = str(user_id)
    vault = await db.get_vault(suid, guild_id)
    level = await db.get_vault_level(suid, guild_id)
    status = capacity.vault_status(vault, level)
    embed = discord.Embed(title="🏦 Mining Vault", color=MINING_COLOR)
    if note:
        embed.description = note
    embed.add_field(
        name="📦 Capacity",
        value=f"{status.used}/{status.cap} item types (tier {level})",
        inline=False,
    )
    over_cap_nudge = capacity.vault_warning(status)
    if over_cap_nudge:
        embed.add_field(name="​", value=over_cap_nudge, inline=False)
    if not vault:
        # Empty-state UX rule (mother-hub-map.md): say what the feature does and
        # what the next step is.
        embed.add_field(
            name="Your vault is empty",
            value=(
                "A vault is a **safe stash** for your loot, kept separate from "
                "your mining pack.\nUse **📥 Deposit** (or `!stash <item> [n]`) "
                "to tuck something away."
            ),
            inline=False,
        )
    else:
        for kind, rows in items.summarize_inventory(vault):
            embed.add_field(
                name=_KIND_LABELS.get(kind.value, kind.value.title()),
                value="\n".join(f"**{name.title()}** ×{qty}" for name, qty in rows),
                inline=False,
            )
    embed.set_footer(
        text=(
            f"Stored value: {items.total_value(vault)}  •  "
            "📥 Deposit · 📤 Withdraw · 📦 Stash All Ore · ⬆️ Upgrade"
        ),
    )
    return embed


class _VaultMoveModal(discord.ui.Modal):  # type: ignore[call-arg]
    """Deposit-into / withdraw-from-vault modal — validates then moves via the
    audited workflow, then refreshes the panel in place.
    """

    item = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Item name",
        placeholder="e.g. diamond, iron, lucky charm",
        max_length=100,
    )
    amount = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Amount",
        placeholder="how many",
        default="1",
        max_length=9,
    )

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
        *,
        direction: str,
    ) -> None:
        self._author = author
        self._guild_id = guild_id
        self._direction = direction  # "deposit" | "withdraw"
        verb = "Deposit into" if direction == "deposit" else "Withdraw from"
        super().__init__(title=f"{verb} Vault")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw_amount = (self.amount.value or "").strip()
        try:
            qty = int(raw_amount)
        except ValueError:
            result = TradeResult(
                False,
                f"**{raw_amount or '(blank)'}** isn't a number — try `5`.",
            )
        else:
            name = resolve_item_name(self.item.value, _move_candidates())
            name = name or self.item.value.strip().lower()
            mover = (
                mining_workflow.vault_deposit
                if self._direction == "deposit"
                else mining_workflow.vault_withdraw
            )
            result = await mover(self._author.id, self._guild_id, name, qty)
        embed = await build_vault_embed(
            self._author.id,
            self._guild_id,
            note=("✅ " if result.ok else "❌ ") + result.message,
        )
        embed.color = SUCCESS_COLOR if result.ok else ERROR_COLOR
        view = MiningVaultView(self._author, self._guild_id)
        await interaction.response.edit_message(embed=embed, view=view)


class MiningVaultView(HubView):
    """Deposit / withdraw / stash-all panel; a child of the mining hub."""

    SUBSYSTEM = "mining"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @discord.ui.button(label="📥 Deposit", style=discord.ButtonStyle.primary, row=0)
    async def deposit_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # send_modal must be the initial response — never defer first.
        await interaction.response.send_modal(
            _VaultMoveModal(self._author, self.guild_id, direction="deposit"),
        )

    @discord.ui.button(label="📤 Withdraw", style=discord.ButtonStyle.secondary, row=0)
    async def withdraw_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        await interaction.response.send_modal(
            _VaultMoveModal(self._author, self.guild_id, direction="withdraw"),
        )

    @discord.ui.button(
        label="📦 Stash All Ore",
        style=discord.ButtonStyle.success,
        row=1,
    )
    async def stash_all_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        if not await safe_defer(interaction):
            return
        result = await mining_workflow.vault_deposit_all_resources(
            self._author.id,
            self.guild_id,
        )
        embed = await build_vault_embed(
            self._author.id,
            self.guild_id,
            note=("✅ " if result.ok else "❌ ") + result.message,
        )
        embed.color = SUCCESS_COLOR if result.ok else ERROR_COLOR
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(label="⬆️ Upgrade", style=discord.ButtonStyle.primary, row=1)
    async def upgrade_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        if not await safe_defer(interaction):
            return
        result = await mining_workflow.vault_upgrade(self._author.id, self.guild_id)
        embed = await build_vault_embed(
            self._author.id,
            self.guild_id,
            note=("✅ " if result.ok else "❌ ") + result.message,
        )
        embed.color = SUCCESS_COLOR if result.ok else ERROR_COLOR
        await safe_edit(interaction, embed=embed, view=self)

    @discord.ui.button(label="↩ Mining Hub", style=discord.ButtonStyle.secondary, row=2)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Late import keeps the module-load graph acyclic (the hub imports this).
        from views.mining.main_panel import MiningHubView, build_overview_embed

        embed = await build_overview_embed(
            self._author.id,
            self.guild_id,
            name=getattr(self._author, "display_name", None),
        )
        view = MiningHubView()
        await interaction.response.edit_message(embed=embed, view=view)
        self.stop()


__all__ = ["MiningVaultView", "build_vault_embed"]
