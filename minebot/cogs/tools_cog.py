from helpers.equipment_ui_helper import EquipSlotView
import os
import discord
from discord.ext import commands
from discord.ext.commands import Context
from config import Config
from settings import GameSettings
from helpers import pil_helper
from helpers.fuzzy_matching_helper import matcher
from helpers.embed_helper import create_embed, error_embed
from utils.data_manager import DatabaseManager
from helpers.item_stats_manager import ItemStatsManager

ASSETS_DIR = Config.ASSETS_DIR
BASE_CHARACTER_PATH = os.path.join(ASSETS_DIR, "base_character.png")
TEMP_DIR = os.path.join(ASSETS_DIR, "temp")
pil_helper.ensure_temp_dir(TEMP_DIR)

EQUIP_POSITIONS = {k: v["position"] for k, v in GameSettings.ITEM_POSITIONS.items()}
SCALE_FACTORS = {k: v["scale"] for k, v in GameSettings.ITEM_POSITIONS.items()}

class ToolCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.equipped_items: dict[str, dict[str, str]] = {}

    async def equip_to_slot(self, interaction, user_id, slot):
        inventory = await DatabaseManager.get_inventory(user_id)
        for item_id in inventory:
            category = await ItemStatsManager.get(item_id, "category")
            if category and category.lower() == slot.lower():
                await DatabaseManager.update_equipped_item(user_id, slot, item_id)
                await interaction.response.send_message(embed=create_embed(
                    title="Item Equipped",
                    description=f"Equipped **{item_id}** to **{slot}**.",
                    color=discord.Color.green()
                ), ephemeral=True)
                return
        await interaction.response.send_message(embed=error_embed(f"No '{slot}' item found in your inventory."), ephemeral=True)

    async def get_inventory(self, user_id: str) -> dict:
        try:
            inventory = await DatabaseManager.get_inventory(user_id)
            return inventory if inventory is not None else {}
        except Exception as e:
            print(f"[ToolCog.get_inventory] Error for user {user_id}: {e}")
            return {}

    async def update_inventory(self, user_id: str, item: str, amount: int) -> bool:
        try:
            result = await DatabaseManager.update_inventory(user_id, item, amount)
            if not result:
                print(f"[ToolCog.update_inventory] Failed for user {user_id}, item: {item}, amount: {amount}")
            return result
        except Exception as e:
            print(f"[ToolCog.update_inventory] Exception for user {user_id}: {e}")
            return False

    async def generate_character_image(self, user_id: str) -> str | None:
        if not os.path.exists(BASE_CHARACTER_PATH):
            print("[ToolCog.generate_character_image] Base character image not found.")
            return None
        try:
            base = pil_helper.open_image(BASE_CHARACTER_PATH)
            equipped = self.equipped_items.get(user_id, {})
            for slot, item in equipped.items():
                if slot not in EQUIP_POSITIONS:
                    continue
                item_path = os.path.join(ASSETS_DIR, f"{item}.png")
                if not os.path.exists(item_path):
                    continue
                item_img = pil_helper.open_image(item_path)
                scale = SCALE_FACTORS.get(slot, 1.0)
                if scale != 1.0:
                    item_img = pil_helper.resize_image(item_img, scale)
                pil_helper.paste_image(base, item_img, EQUIP_POSITIONS[slot])
            out_path = os.path.join(TEMP_DIR, f"{user_id}_gear.png")
            pil_helper.save_image(base, out_path)
            return out_path
        except Exception as e:
            print(f"[ToolCog.generate_character_image] Error for user {user_id}: {e}")
            return None

    def get_stats(self, user_id: str) -> dict:
        equipped = self.equipped_items.get(user_id, {})
        total_defense = sum(
            (awaitable := DatabaseManager.get_item_stats(item)) and awaitable.get("defense", 0)
            for item in equipped.values()
        )
        total_damage = sum(
            (awaitable := DatabaseManager.get_item_stats(item)) and awaitable.get("damage", 0)
            for item in equipped.values()
        )
        return {"defense": total_defense, "damage": total_damage}

    async def get_equippable_items(self, user_id: str, slot: str) -> list:
        inventory = await self.get_inventory(user_id)
        available = []
        for item, count in inventory.items():
            category = await ItemStatsManager.get(item, "category")
            if category and category.lower() == slot.lower():
                available.append(item)
        return available

    @commands.hybrid_command(name="equip", description="Equip one item (slot-by-slot).")
    async def equip(self, ctx: Context):
        user_id = str(ctx.author.id)
        view = EquipSlotView(user_id, self)
        await view.setup_buttons()
        msg = await ctx.send("Select a slot to equip an item:", view=view)
        view.message = msg

    @commands.hybrid_command(name="unequip", description="Unequip one item (slot-by-slot).")
    async def unequip(self, ctx: Context):
        user_id = str(ctx.author.id)
        equipped = await DatabaseManager.get_equipped_items(user_id)
        if not equipped:
            await ctx.send("Nothing equipped!")
            return
        view = UnequipView(user_id, equipped, self)
        await ctx.send("Select an item to unequip:", view=view)

    @commands.hybrid_command(name="multiequip", description="Equip items for multiple slots at once.")
    async def multiequip(self, ctx: Context):
        user_id = str(ctx.author.id)
        inventory = await self.get_inventory(user_id)
        if not inventory:
            await ctx.send("Your inventory is empty!")
            return
        view = MultiEquipView(user_id, self, inventory=inventory)
        await ctx.send("Select items for each slot (leave blank for no change):", view=view, ephemeral=True)

    @commands.hybrid_command(name="gear", description="Show your current gear and stats.")
    async def gear(self, ctx: Context):
        user_id = str(ctx.author.id)
        image_path = await self.generate_character_image(user_id)
        stats = {"defense": 0, "damage": 0}  # Replace with real stats if needed
        if image_path and os.path.exists(image_path):
            file = discord.File(image_path, filename="gear.png")
            embed = create_embed(
                title=f"{ctx.author.display_name}'s Gear",
                description="Your setup:",
                fields=[
                    ("Defense", str(stats["defense"]), True),
                    ("Damage", str(stats["damage"]), True)
                ]
            )
            embed.set_image(url="attachment://gear.png")
            await ctx.send(file=file, embed=embed)
        else:
            await ctx.send("❌ Could not generate gear image.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ToolCog(bot))
