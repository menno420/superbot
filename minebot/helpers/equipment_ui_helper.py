import discord
from discord.ext import commands
from helpers.embed_helper import error_embed, create_embed
from helpers import inventory_helper
from helpers.item_stats_manager import ItemStatsManager

class EquipSlotView(discord.ui.View):
    def __init__(self, user_id, cog):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.cog = cog
        self.message = None

    async def setup_buttons(self):
        inventory = await inventory_helper.get_inventory(str(self.user_id))
        slots_to_items = {}

        for item in inventory:
            slot = await ItemStatsManager.get(item, "slot") or await ItemStatsManager.get(item, "category")
            if slot:
                slot = slot.lower()
                if slot not in slots_to_items:
                    slots_to_items[slot] = []
                slots_to_items[slot].append(item)

        if not slots_to_items:
            self.add_item(discord.ui.Button(
                label="No equipable items found",
                disabled=True,
                style=discord.ButtonStyle.secondary
            ))
        else:
            for slot in slots_to_items:
                self.add_item(discord.ui.Button(
                    label=f"Equip {slot.title()}",
                    style=discord.ButtonStyle.primary,
                    custom_id=f"equip_{slot}"
                ))

        self.add_item(discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.danger,
            custom_id="cancel"
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == int(self.user_id)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass

    async def on_interaction(self, interaction: discord.Interaction):
        try:
            custom_id = interaction.data.get("custom_id", "")
            if custom_id == "cancel":
                await interaction.response.edit_message(embed=error_embed("Equip canceled."), view=None)
            elif custom_id.startswith("equip_"):
                slot = custom_id.replace("equip_", "")
                await self.cog.equip_to_slot(interaction, self.user_id, slot)
        except Exception as e:
            print(f"[EquipSlotView] Interaction error: {e}")
            await interaction.response.send_message(embed=error_embed("❌ Failed to equip item."), ephemeral=True)
