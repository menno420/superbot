from helpers import inventory_helper
import math
import discord
from discord.ext import commands
from discord import app_commands
import traceback
from config import Config
from utils.data_manager import DatabaseManager
from helpers.embed_helper import create_embed, error_embed, success_embed
from helpers.fuzzy_matching_helper import matcher
from helpers.item_stats_manager import ItemStatsManager  # Ensure async functions are awaited

ITEMS_PER_SUBPAGE = 20
VALID_SORTS = {"name", "amount", "rarity", "value", "category", "weight"}

# Asynchronous grouping functions:
async def group_or_sort_inventory(inventory_dict, sort_by):
    items = list(inventory_dict.items())

    # ✅ Filter out items with missing stats
    valid_items = []
    for item_id, qty in items:
        stats = await ItemStatsManager.get(item_id, "rarity", default=None)
        if stats is not None:
            valid_items.append((item_id, qty))
        else:
            print(f"[WARNING] Skipping item not found in stats: '{item_id}'")

    if sort_by in {"category", "rarity", "value", "weight"}:
        return await ItemStatsManager.get_grouped(valid_items, sort_by)
    elif sort_by == "amount":
        sorted_items = sorted(valid_items, key=lambda x: x[1], reverse=True)
        return [("All Items", sorted_items)]
    else:
        sorted_items = sorted(valid_items, key=lambda x: matcher.get_display_name(x[0]).lower())
        return [("All Items", sorted_items)]

async def group_or_sort_item_list(item_list, sort_by):
    if sort_by in {"category", "rarity", "value", "weight"}:
        return await ItemStatsManager.get_grouped(item_list, sort_by)
    else:
        sorted_list = sorted(item_list, key=lambda x: x[1].lower())
        return [("All Items", sorted_list)]

def build_pages_for_grouped_data(grouped_data, is_inventory=True):
    all_pages = []
    for (group_label, items) in grouped_data:
        total_items = len(items)
        subpage_count = math.ceil(total_items / ITEMS_PER_SUBPAGE)
        for subpage_index in range(subpage_count):
            start = subpage_index * ITEMS_PER_SUBPAGE
            end = start + ITEMS_PER_SUBPAGE
            chunk = items[start:end]
            page_info = {
                "group_label": group_label,
                "subpage_index": subpage_index + 1,
                "subpage_count": subpage_count,
                "items": chunk
            }
            all_pages.append(page_info)
    return all_pages

class InventoryView(discord.ui.View):
    def __init__(self, ctx, all_pages, sort_by):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.all_pages = all_pages
        self.sort_by = sort_by
        self.page_index = 0
        self.max_page = len(all_pages)
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.ctx.author

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)

    def current_page_data(self):
        if not self.all_pages:
            return None
        self.page_index = max(0, min(self.page_index, self.max_page - 1))
        return self.all_pages[self.page_index]

    def build_inventory_embed(self):
        page = self.current_page_data()
        if not page:
            return error_embed("No items found.")
        group_label = page["group_label"]
        subpage_index = page["subpage_index"]
        subpage_count = page["subpage_count"]
        items = page["items"]
        lines = [f"**{matcher.get_display_name(canon)}** × {count}" for canon, count in items]
        overall_page = self.page_index + 1
        if self.sort_by == "category":
            title = f"📦 {group_label} (Page {subpage_index} of {subpage_count}) — Overall {overall_page}/{self.max_page}"
            embed_color = discord.Color.gold()
        else:
            title = f"🎒 {self.ctx.author.display_name}'s Inventory (Sorted by {self.sort_by.title()}) (Page {subpage_index} of {subpage_count})"
            if group_label and group_label != "All Items":
                title += f" — {group_label}"
            title += f" — Overall {overall_page}/{self.max_page}"
            embed_color = discord.Color.green()
        description = "\n".join(lines) if lines else "No items in this sub-page."
        return create_embed(title=title, description=description, color=embed_color)

    async def update_embed(self, interaction: discord.Interaction):
        try:
            embed = self.build_inventory_embed()
            self.prev_page.disabled = (self.page_index <= 0)
            self.next_page.disabled = (self.page_index >= self.max_page - 1)
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            traceback.print_exc()
            await interaction.response.send_message(embed=error_embed(f"⚠️ Could not update inventory page: {e}"), ephemeral=True)

    @discord.ui.button(label="⬅️ Prev", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, _):
        if self.page_index > 0:
            self.page_index -= 1
        await self.update_embed(interaction)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, _):
        if self.page_index < self.max_page - 1:
            self.page_index += 1
        await self.update_embed(interaction)

    @discord.ui.button(label="📦 View All Items", style=discord.ButtonStyle.primary)
    async def view_all_items(self, interaction: discord.Interaction, _):
        view = AllItemsView(self.ctx, sort_by="name")
        await view.send(interaction)

class AllItemsView(discord.ui.View):
    def __init__(self, ctx, sort_by="name"):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.sort_by = sort_by
        self.all_pages = []
        self.page_index = 0
        self.max_page = 0
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.ctx.author

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def load_items(self):
        all_items = await inventory_helper.get_all_items()
        grouped = await group_or_sort_item_list(all_items, self.sort_by)
        self.all_pages = build_pages_for_grouped_data(grouped, is_inventory=False)
        self.page_index = 0
        self.max_page = len(self.all_pages)

    def current_page_data(self):
        if not self.all_pages:
            return None
        self.page_index = max(0, min(self.page_index, self.max_page - 1))
        return self.all_pages[self.page_index]

    async def build_all_items_embed(self):
        page = self.current_page_data()
        if not page:
            return error_embed("No items found.")
        group_label = page["group_label"]
        subpage_index = page["subpage_index"]
        subpage_count = page["subpage_count"]
        items = page["items"]
        lines = []
        for canon, _ in items:
            rarity = await ItemStatsManager.get(canon, "rarity", 1)
            value = await ItemStatsManager.get(canon, "value", 1)
            display_name = matcher.get_display_name(canon)
            lines.append(f"📦 **{display_name}** — rarity: {rarity}, value: {value}")
        overall_page = self.page_index + 1
        if self.sort_by == "category":
            title = f"📦 {group_label} (Page {subpage_index} of {subpage_count}) — Overall {overall_page}/{self.max_page}"
            embed_color = discord.Color.gold()
        else:
            title = f"📚 All Known Items (Sorted by {self.sort_by.title()}) (Page {subpage_index} of {subpage_count})"
            if group_label and group_label != "All Items":
                title += f" — {group_label}"
            title += f" — Overall {overall_page}/{self.max_page}"
            embed_color = discord.Color.blurple()
        description = "\n".join(lines) if lines else "No items in this sub-page."
        return create_embed(title=title, description=description, color=embed_color)

    async def update_embed(self, interaction: discord.Interaction):
        try:
            embed = await self.build_all_items_embed()
            self.prev_page.disabled = (self.page_index <= 0)
            self.next_page.disabled = (self.page_index >= self.max_page - 1)
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            traceback.print_exc()
            await interaction.response.send_message(embed=error_embed(f"⚠️ Could not update item list: {e}"), ephemeral=True)

    async def send(self, ctx_or_interaction):
        await self.load_items()
        embed = await self.build_all_items_embed()
        if hasattr(ctx_or_interaction, "response"):
            self.message = await ctx_or_interaction.response.send_message(embed=embed, view=self)
        else:
            self.message = await ctx_or_interaction.send(embed=embed, view=self)

    @discord.ui.button(label="⬅️ Prev", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, _):
        if self.page_index > 0:
            self.page_index -= 1
        await self.update_embed(interaction)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, _):
        if self.page_index < self.max_page - 1:
            self.page_index += 1
        await self.update_embed(interaction)

    @discord.ui.button(label="Sort: Rarity", style=discord.ButtonStyle.success)
    async def sort_rarity(self, interaction: discord.Interaction, _):
        self.sort_by = "rarity"
        await self.load_items()
        await self.update_embed(interaction)

    @discord.ui.button(label="Sort: Value", style=discord.ButtonStyle.success)
    async def sort_value(self, interaction: discord.Interaction, _):
        self.sort_by = "value"
        await self.load_items()
        await self.update_embed(interaction)

    @discord.ui.button(label="Sort: Category", style=discord.ButtonStyle.success)
    async def sort_category(self, interaction: discord.Interaction, _):
        self.sort_by = "category"
        await self.load_items()
        await self.update_embed(interaction)

class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="inventory", description="Shows your current inventory.")
    @app_commands.describe(sort_by="Sort by name, amount, rarity, value, or category.")
    async def inventory(self, ctx, sort_by: str = "name"):
        try:
            await ctx.defer()
            user_id = str(ctx.author.id)
            inventory = await inventory_helper.get_inventory(user_id)
            if not inventory:
                return await ctx.send(embed=error_embed("Your inventory is empty."))
            if sort_by not in VALID_SORTS:
                sort_by = "name"
            grouped_inventory = await group_or_sort_inventory(inventory, sort_by)
            if not grouped_inventory:
                return await ctx.send(embed=error_embed("No items in inventory."))
            all_pages = build_pages_for_grouped_data(grouped_inventory, is_inventory=True)
            if not all_pages:
                return await ctx.send(embed=error_embed("No items in inventory."))
            view = InventoryView(ctx, all_pages, sort_by)
            embed = view.build_inventory_embed()
            view.message = await ctx.send(embed=embed, view=view)
        except Exception as e:
            traceback.print_exc()
            await ctx.send(embed=error_embed(f"⚠️ Unexpected error: {e}"))

    @commands.hybrid_command(name="items", description="View all known items.")
    @app_commands.describe(sort_by="Sort by name, rarity, value, or category.")
    async def items(self, ctx, sort_by: str = "name"):
        try:
            await ctx.defer()
            if sort_by not in VALID_SORTS:
                sort_by = "name"
            view = AllItemsView(ctx, sort_by)
            await view.send(ctx)
        except Exception as e:
            traceback.print_exc()
            await ctx.send(embed=error_embed(f"⚠️ Could not load item list: {e}"))

    @commands.hybrid_command(name="additem", description="Adds items to your inventory (Owner Only).")
    @commands.is_owner()
    async def additem(self, ctx, item: str, amount: int = 1):
        try:
            if amount <= 0:
                return await ctx.send(embed=error_embed("Amount must be greater than zero."))
            success = await inventory_helper.update_inventory(str(ctx.author.id), item, amount)
            display_name = matcher.get_display_name(item)
            if success:
                await ctx.send(embed=success_embed(f"✅ Added **{amount}× {display_name}** to your inventory."))
            else:
                await ctx.send(embed=error_embed(f"❌ Could not add **{display_name}**."))
        except Exception as e:
            traceback.print_exc()
            await ctx.send(embed=error_embed(f"Error adding item: {e}"))

    @commands.hybrid_command(name="removeitem", description="Removes items from your inventory (Owner Only).")
    @commands.is_owner()
    async def removeitem(self, ctx, item: str, amount: int = 1):
        try:
            if amount <= 0:
                return await ctx.send(embed=error_embed("Amount must be greater than zero."))
            success = await inventory_helper.update_inventory(str(ctx.author.id), item, -amount)
            display_name = matcher.get_display_name(item)
            if success:
                await ctx.send(embed=success_embed(f"🗑️ Removed **{amount}× {display_name}** from your inventory."))
            else:
                await ctx.send(embed=error_embed(f"❌ Could not remove **{display_name}**."))
        except Exception as e:
            traceback.print_exc()
            await ctx.send(embed=error_embed(f"Error removing item: {e}"))

async def setup(bot):
    await bot.add_cog(InventoryCog(bot))
