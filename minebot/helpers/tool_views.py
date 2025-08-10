import discord
from discord import ui, Interaction, ButtonStyle, SelectOption

class EquipSlotView(ui.View):
    def __init__(self, user_id: str, cog):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.cog = cog
        for slot in ["helmet", "chestplate", "sword", "shield", "leggings", "boots"]:
            self.add_item(EquipSlotButton(slot, user_id, cog))

class EquipSlotButton(ui.Button):
    def __init__(self, slot: str, user_id: str, cog):
        super().__init__(label=slot.capitalize(), style=ButtonStyle.primary)
        self.slot = slot
        self.user_id = user_id
        self.cog = cog

    async def callback(self, interaction: Interaction):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("Not for you.", ephemeral=True)
            return
        inventory = await self.cog.get_inventory(self.user_id)
        available = [item for item, count in inventory.items() if count > 0 and self.slot in item.lower()]
        if not available:
            await interaction.response.send_message(f"No {self.slot} available.", ephemeral=True)
        else:
            view = MultiEquipView(self.user_id, self.cog, inventory=inventory, specific_slot=self.slot)
            await interaction.response.send_message(f"Select a {self.slot}:", view=view, ephemeral=True)

class EquipItemButton(ui.Button):
    def __init__(self, item: str, user_id: str, slot: str, cog):
        super().__init__(label=item, style=ButtonStyle.secondary)
        self.item = item
        self.user_id = user_id
        self.slot = slot
        self.cog = cog

    async def callback(self, interaction: Interaction):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("Not for you.", ephemeral=True)
            return
        if self.user_id not in self.cog.equipped_items:
            self.cog.equipped_items[self.user_id] = {}
        self.cog.equipped_items[self.user_id][self.slot] = self.item
        await self.cog.update_inventory(self.user_id, self.item, -1)
        await interaction.response.send_message(f"Equipped {self.item} as {self.slot}.", ephemeral=True)
        self.view.stop()

class EquipItemSelect(ui.Select):
    def __init__(self, options: list, user_id: str, slot: str, cog):
        super().__init__(placeholder="Choose an item...", min_values=1, max_values=1, options=options)
        self.user_id = user_id
        self.slot = slot
        self.cog = cog

    async def callback(self, interaction: Interaction):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("Not for you.", ephemeral=True)
            return
        selected_item = self.values[0]
        if self.user_id not in self.cog.equipped_items:
            self.cog.equipped_items[self.user_id] = {}
        self.cog.equipped_items[self.user_id][self.slot] = selected_item
        await self.cog.update_inventory(self.user_id, selected_item, -1)
        await interaction.response.send_message(f"Equipped {selected_item} as {self.slot}.", ephemeral=True)
        self.view.stop()

class UnequipView(ui.View):
    def __init__(self, user_id: str, equipped: dict, cog):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.cog = cog
        for slot, item in equipped.items():
            self.add_item(UnequipButton(slot, item, user_id, cog))

class UnequipButton(ui.Button):
    def __init__(self, slot: str, item: str, user_id: str, cog):
        super().__init__(label=f"{slot.capitalize()}: {item}", style=ButtonStyle.danger)
        self.slot = slot
        self.item = item
        self.user_id = user_id
        self.cog = cog

    async def callback(self, interaction: Interaction):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("Not for you.", ephemeral=True)
            return
        if self.user_id in self.cog.equipped_items and self.slot in self.cog.equipped_items[self.user_id]:
            del self.cog.equipped_items[self.user_id][self.slot]
            await self.cog.update_inventory(self.user_id, self.item, 1)
            await interaction.response.send_message(f"Unequipped {self.item} from {self.slot}.", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing to unequip.", ephemeral=True)
        self.view.stop()

class MultiEquipView(ui.View):
    """
    Allows a user to set equipment for multiple slots at once.
    If specific_slot is provided, the view will only handle that slot.
    Otherwise, it shows selects for all slots.
    """
    def __init__(self, user_id: str, cog, inventory: dict, specific_slot: str = None):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.cog = cog
        self.inventory = inventory
        self.slots = [specific_slot] if specific_slot else ["helmet", "chestplate", "sword", "shield", "leggings", "boots"]
        for slot in self.slots:
            options = [discord.SelectOption(label="None", value="none")]
            for item, count in self.inventory.items():
                if count > 0 and slot in item.lower():
                    options.append(discord.SelectOption(label=item, value=item))
            select = ui.Select(placeholder=f"{slot.capitalize()}...", min_values=0, max_values=1, options=options)
            select.callback = self.make_select_callback(slot)
            self.add_item(select)
        self.add_item(ConfirmButton())

    def make_select_callback(self, slot: str):
        async def callback(interaction: Interaction):
            await interaction.response.defer(ephemeral=True)
        return callback

class ConfirmButton(ui.Button):
    def __init__(self):
        super().__init__(label="Confirm", style=ButtonStyle.success)
    async def callback(self, interaction: Interaction):
        view: MultiEquipView = self.view  # type: ignore
        updates = {}
        for child in view.children:
            if isinstance(child, ui.Select):
                value = child.values[0] if child.values else "none"
                slot = child.placeholder.lower().replace("...", "")
                updates[slot] = None if value == "none" else value
        for slot in view.slots:
            current = view.cog.equipped_items.get(view.user_id, {}).get(slot)
            new = updates.get(slot, current)
            if new != current:
                if current:
                    await view.cog.update_inventory(view.user_id, current, 1)
                if new:
                    await view.cog.update_inventory(view.user_id, new, -1)
                if view.user_id not in view.cog.equipped_items:
                    view.cog.equipped_items[view.user_id] = {}
                if new:
                    view.cog.equipped_items[view.user_id][slot] = new
                else:
                    view.cog.equipped_items[view.user_id].pop(slot, None)
        await interaction.response.send_message("✅ Updated!", ephemeral=True)
        view.stop()