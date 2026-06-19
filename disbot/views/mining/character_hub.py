"""Character sub-hub — the "everything about you" group of the mining hub.

Part of the Option A hub declutter (owner-directed, 2026-06-15;
``docs/planning/mining-hub-redesign-2026-06-15.md``): the main mining hub shrinks
to 6 buttons, and this sub-hub absorbs the player-centric actions —
**Overview** (the read-only character stat card), **Inventory**, **Stats**,
**Skills**, **Vault**, and **Home**.

Home placement (deviation flagged for owner review, 2026-06-19): the plan's
Character list predates the Home feature (#910). Home personalizes the Character
card, so it lives here in the Character sub-hub rather than on the main hub.

Each button renders **in place** (the ``main_panel`` child-opener pattern); this
view owns no game logic, it only groups. Writes still flow through
``services.mining_workflow`` from inside the panels it opens. Authority is
re-checked at callback time via ``HubView``'s invoker lock + the per-callback
guild guard (mirrors the main hub).
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from utils import db
from utils.mining import items
from utils.ui_constants import MINING_COLOR
from views.base import HubView

# Display labels for the typed Inventory panel, keyed by ItemKind.value
# (string keys keep this rendering table independent of the enum). Mirrors the
# table the Inventory button used on the main hub before the declutter.
_KIND_LABELS: dict[str, str] = {
    "resource": "⛏️ Resources",
    "tool": "🛠️ Tools",
    "consumable": "🧨 Consumables",
    "structure": "🏛️ Structures",
    "treasure": "💎 Treasure",
}

_GUIDE = (
    "**🧍 Overview** — your full character profile (location, gear, level, worth)\n"
    "**📦 Inventory** — view your mining resources\n"
    "**📊 Stats** — view your mining statistics\n"
    "**🌳 Skills** — spend skill points to specialize your character\n"
    "**🏦 Vault** — stash loot safely, separate from your pack\n"
    "**🏠 Home** — build it to personalize your Character card"
)

_INVENTORY_FILENAME = "inventory.png"


def build_character_hub_embed() -> discord.Embed:
    """The Character sub-hub overview (static — the panels own live state)."""
    embed = discord.Embed(
        title="🧍 Character — everything about you",
        description=_GUIDE,
        color=MINING_COLOR,
    )
    embed.set_footer(text="Only you can interact with this panel.")
    return embed


def _render_inventory_file(
    display_name: str,
    inventory: dict[str, int],
    embed: discord.Embed,
) -> discord.File | None:
    """Render the PIL inventory card and wire it into *embed* as the in-place
    image. Returns the File to attach (or ``None`` without Pillow — additive,
    the text embed already carries the full inventory). Mirrors the helper the
    Inventory button used on the main hub before the declutter.
    """
    import io

    from utils.mining_render import build_card_spec, render_inventory_card

    spec = build_card_spec(
        f"{display_name}'s Mining Inventory",
        items.sort_inventory(inventory),
        classify_kind=lambda n: items.classify(n).value,
        footer=f"Net worth: {items.total_value(inventory)}",
    )
    png = render_inventory_card(spec)
    if png is None:
        return None
    embed.set_image(url=f"attachment://{_INVENTORY_FILENAME}")
    return discord.File(io.BytesIO(png), filename=_INVENTORY_FILENAME)


class MiningCharacterHubView(HubView):
    """Sub-hub grouping Overview / Inventory / Stats / Skills / Vault / Home.

    A child of the mining hub.
    """

    SUBSYSTEM = "mining"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    async def _edit_in_place(
        self,
        interaction: discord.Interaction,
        *,
        embed: discord.Embed,
        view: discord.ui.View,
        image: discord.File | None = None,
    ) -> None:
        """Edit the sub-hub's anchor message in place, owning its optional image.

        The inventory card renders *into* this one message instead of a separate
        ephemeral follow-up; every other action passes no image, which clears a
        prior card so it never lingers on the next screen.
        """
        await safe_edit(
            interaction,
            embed=embed,
            view=view,
            attachments=[image] if image is not None else [],
        )

    @discord.ui.button(label="🧍 Overview", style=discord.ButtonStyle.primary, row=0)
    async def overview_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        if not await safe_defer(interaction):
            return
        if interaction.guild_id is None:
            await safe_followup(
                interaction,
                "Mining is only available inside a guild.",
                ephemeral=True,
            )
            return
        # Read-only character overview, shown in place on the sub-hub.
        from views.mining.character_panel import build_character_embed

        embed = await build_character_embed(
            interaction.user.id,
            interaction.guild_id,
            name=interaction.user.display_name,
        )
        embed.set_footer(text="Pick another action above to continue.")
        await self._edit_in_place(interaction, embed=embed, view=self)

    @discord.ui.button(label="📦 Inventory", style=discord.ButtonStyle.grey, row=0)
    async def inventory_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        if not await safe_defer(interaction):
            return
        if interaction.guild_id is None:
            await safe_followup(
                interaction,
                "Mining is only available inside a guild.",
                ephemeral=True,
            )
            return
        user_id = str(interaction.user.id)
        inventory = await db.get_mining_inventory(user_id, interaction.guild_id)
        embed = discord.Embed(
            title=f"📦 {interaction.user.name}'s Mining Inventory",
            color=MINING_COLOR,
        )
        if not inventory:
            # Empty-state UX rule (mother-hub-map.md): explain what the
            # feature does and what the next step is.
            embed.description = (
                "Your mining inventory is empty. Use `!mine` in the mining "
                "channel to start collecting items."
            )
            embed.set_footer(text="Pick another action above to continue.")
        else:
            for kind, rows in items.summarize_inventory(inventory):
                embed.add_field(
                    name=_KIND_LABELS.get(kind.value, kind.value.title()),
                    value="\n".join(f"**{name.title()}** ×{qty}" for name, qty in rows),
                    inline=False,
                )
            embed.set_footer(
                text=(
                    f"Net worth: {items.total_value(inventory)}  •  "
                    "Pick another action above to continue."
                ),
            )
        image = (
            _render_inventory_file(interaction.user.display_name, inventory, embed)
            if inventory
            else None
        )
        await self._edit_in_place(interaction, embed=embed, view=self, image=image)

    @discord.ui.button(label="📊 Stats", style=discord.ButtonStyle.grey, row=0)
    async def stats_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        if interaction.guild_id is None:
            await safe_followup(
                interaction,
                "Mining is only available inside a guild.",
                ephemeral=True,
            )
            return
        user_id = str(interaction.user.id)
        inventory = await db.get_mining_inventory(user_id, interaction.guild_id)
        total_items = sum(inventory.values())
        unique_items = len(inventory)
        embed = discord.Embed(
            title=f"📊 {interaction.user.name}'s Mining Stats",
            color=MINING_COLOR,
        )
        embed.add_field(name="Total Items Collected", value=str(total_items))
        embed.add_field(name="Unique Items", value=str(unique_items))
        embed.add_field(name="Net Worth", value=str(items.total_value(inventory)))
        embed.set_footer(text="Pick another action above to continue.")
        await self._edit_in_place(interaction, embed=embed, view=self)

    @discord.ui.button(label="🌳 Skills", style=discord.ButtonStyle.primary, row=1)
    async def skills_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        if interaction.guild_id is None:
            await safe_followup(
                interaction,
                "Mining is only available inside a guild.",
                ephemeral=True,
            )
            return
        from views.mining.skills_panel import MiningSkillsView, build_skills_embed

        embed = await build_skills_embed(interaction.user.id, interaction.guild_id)
        view = MiningSkillsView(interaction.user, interaction.guild_id)
        await self._edit_in_place(interaction, embed=embed, view=view)

    @discord.ui.button(label="🏦 Vault", style=discord.ButtonStyle.primary, row=1)
    async def vault_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        if interaction.guild_id is None:
            await safe_followup(
                interaction,
                "Mining is only available inside a guild.",
                ephemeral=True,
            )
            return
        from views.mining.vault_panel import MiningVaultView, build_vault_embed

        embed = await build_vault_embed(interaction.user.id, interaction.guild_id)
        view = MiningVaultView(interaction.user, interaction.guild_id)
        await self._edit_in_place(interaction, embed=embed, view=view)

    @discord.ui.button(label="🏠 Home", style=discord.ButtonStyle.primary, row=1)
    async def home_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not await safe_defer(interaction):
            return
        if interaction.guild_id is None:
            await safe_followup(
                interaction,
                "Mining is only available inside a guild.",
                ephemeral=True,
            )
            return
        from views.mining.home_panel import MiningHomeView, build_home_embed

        embed = await build_home_embed(interaction.user.id, interaction.guild_id)
        view = MiningHomeView(interaction.user, interaction.guild_id)
        await self._edit_in_place(interaction, embed=embed, view=view)

    @discord.ui.button(label="↩ Mining Hub", style=discord.ButtonStyle.secondary, row=2)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        from views.mining.main_panel import MiningHubView, build_overview_embed

        embed = await build_overview_embed(
            self._author.id,
            self.guild_id,
            name=getattr(self._author, "display_name", None),
        )
        await interaction.response.edit_message(
            embed=embed,
            view=MiningHubView(),
            attachments=[],
        )
        self.stop()


__all__ = ["MiningCharacterHubView", "build_character_hub_embed"]
