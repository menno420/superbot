from helpers import inventory_helper
import discord
from discord.ext import commands
import random

from helpers import mining_helper, mining_ui_helper, embed_helper, button_helper
from utils.data_manager import DatabaseManager
from helpers.item_stats_manager import ItemStatsManager
from helpers import mining_constants

class MiningCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def update_mining_records(self, user_id: int, new_level: int, data: dict):
        max_depth = data.get("max_mining_depth", new_level)
        min_depth = data.get("min_mining_depth", new_level)
        if new_level > max_depth:
            max_depth = new_level
        if new_level < min_depth:
            min_depth = new_level
        await DatabaseManager.update_user_data(user_id, {
            "mining_depth": new_level,
            "max_mining_depth": max_depth,
            "min_mining_depth": min_depth
        })

    def get_mining_view(self, user_id: int) -> discord.ui.View:
        def make_callback(direction: str):
            async def callback(interaction: discord.Interaction):
                await self.process_mining_action(interaction, user_id, direction)
            return callback

        buttons_info = [
            ("Mine Up", discord.ButtonStyle.primary, make_callback("up")),
            ("Mine Forward", discord.ButtonStyle.primary, make_callback("forward")),
            ("Mine Down", discord.ButtonStyle.primary, make_callback("down")),
        ]
        return button_helper.create_button_view(buttons_info)

    async def process_mining_action(self, interaction: discord.Interaction, user_id: int, direction: str):
        data = await DatabaseManager.get_user_data(user_id)
        current_level = data.get("mining_depth", 0)
        tool = data.get("equipped_tool")

        if direction == "down" and not tool:
            await interaction.response.send_message(embed=embed_helper.error_embed("You need a tool to mine down!"), ephemeral=True)
            return

        if not tool:
            if current_level != 0:
                await interaction.response.send_message(embed=embed_helper.error_embed("You need a tool to mine away from level 0!"), ephemeral=True)
                return
            else:
                tool = {"name": "Bare Hands", "rarity": "none", "durability": 9999}

        level_change = 0 if direction == "forward" else (1 if direction == "up" else -1)
        new_level = current_level + level_change
        effective_level = abs(new_level)

        result = mining_helper.mine(tool, effective_level)

        # Update inventory
        await inventory_helper.update_inventory(str(user_id), result["loot"], result["quantity"])

        await self.update_mining_records(user_id, new_level, data)

        current_xp = data.get("mining_xp", 0)
        current_mining_level = data.get("mining_level", 1)
        xp_for_next = mining_constants.xp_for_next_level(current_mining_level)
        new_xp = current_xp + result["xp"]
        leveled_up = False
        if new_xp >= xp_for_next:
            new_xp -= xp_for_next
            current_mining_level += 1
            leveled_up = True

        await DatabaseManager.update_user_data(user_id, {
            "mining_xp": new_xp,
            "mining_level": current_mining_level
        })

        if tool.get("name") != "Bare Hands":
            tool["durability"] = max(0, tool.get("durability", 1) - result["durability_used"])
            await DatabaseManager.update_user_data(user_id, {"equipped_tool": tool})

        user = self.bot.get_user(user_id)
        updated_embed = mining_ui_helper.create_mining_embed(
            user=user,
            tool=None if tool.get("name") == "Bare Hands" else tool,
            depth=new_level,
            loot=result["loot"],
            quantity=result["quantity"],
            xp=result["xp"]
        )

        if tool.get("name") != "Bare Hands" and tool.get("durability", 0) <= 0:
            updated_embed.add_field(name="Tool Broken", value=f"Your {tool.get('name', 'tool')} is at 0 durability!", inline=False)
            await interaction.response.edit_message(embed=updated_embed, view=None)
        else:
            view = self.get_mining_view(user_id)
            await interaction.response.edit_message(embed=updated_embed, view=view)

        if leveled_up:
            await interaction.followup.send(embed=embed_helper.success_embed(f"Level Up! You’re now Mining Level {current_mining_level}."), ephemeral=True)

    @commands.hybrid_command(name="mine", description="Begin an interactive mining session!")
    async def mine(self, ctx: commands.Context):
        user_id = ctx.author.id
        data = await DatabaseManager.get_user_data(user_id)
        current_level = data.get("mining_depth", 0)
        tool = data.get("equipped_tool")
        if not tool and current_level != 0:
            await ctx.send(embed=embed_helper.error_embed("You need a tool to mine away from level 0!"))
            return
        embed = mining_ui_helper.create_mining_embed(
            user=ctx.author,
            tool=tool,
            depth=current_level,
            loot=None,
            quantity=0,
            xp=0
        )
        view = self.get_mining_view(user_id)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="fastmine", description="Perform a quick mining action (no interactive UI).")
    async def fastmine(self, ctx: commands.Context):
        user_id = ctx.author.id
        data = await DatabaseManager.get_user_data(user_id)
        current_level = data.get("mining_depth", 0)
        tool = data.get("equipped_tool")
        if not tool and current_level != 0:
            await ctx.send(embed=embed_helper.error_embed("You need a tool to mine away from level 0!"))
            return
        elif not tool:
            tool = {"name": "Bare Hands", "rarity": "none", "durability": 9999}

        effective_level = abs(current_level)
        result = mining_helper.mine(tool, effective_level)

        await inventory_helper.update_inventory(str(user_id), result["loot"], result["quantity"])
        await self.update_mining_records(user_id, current_level, data)

        current_xp = data.get("mining_xp", 0)
        current_mining_level = data.get("mining_level", 1)
        xp_for_next = mining_constants.xp_for_next_level(current_mining_level)
        new_xp = current_xp + result["xp"]
        leveled_up = False
        if new_xp >= xp_for_next:
            new_xp -= xp_for_next
            current_mining_level += 1
            leveled_up = True

        await DatabaseManager.update_user_data(user_id, {
            "mining_xp": new_xp,
            "mining_level": current_mining_level
        })

        if tool.get("name") != "Bare Hands":
            tool["durability"] = max(0, tool.get("durability", 1) - result["durability_used"])
            await DatabaseManager.update_user_data(user_id, {"equipped_tool": tool})

        embed = mining_ui_helper.create_mining_embed(
            user=ctx.author,
            tool=None if tool.get("name") == "Bare Hands" else tool,
            depth=current_level,
            loot=result["loot"],
            quantity=result["quantity"],
            xp=result["xp"]
        )
        await ctx.send(embed=embed)
        if tool.get("durability", 0) <= 0:
            await ctx.send(embed=embed_helper.error_embed("Your tool just broke!"))
        if leveled_up:
            await ctx.send(embed=embed_helper.success_embed(f"You leveled up! Now Mining Level {current_mining_level}."))

    @commands.hybrid_command(name="chop", description="Chop wood for a quick reward.")
    async def chop(self, ctx: commands.Context):
        wood_reward = random.randint(1, 3)
        await ctx.send(embed=embed_helper.success_embed(f"You chopped some trees and got {wood_reward} wood!"))

    @commands.hybrid_command(name="resetdepth", description="Reset your mining level to 0. Admins can reset others' levels.")
    async def resetdepth(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        if target != ctx.author and not ctx.author.guild_permissions.administrator:
            await ctx.send(embed=embed_helper.error_embed("You don't have permission to reset someone else's mining level."))
            return
        await DatabaseManager.update_user_data(target.id, {"mining_depth": 0})
        await ctx.send(embed=embed_helper.success_embed(f"{target.display_name}'s mining level has been reset to 0."))

    @commands.hybrid_command(name="restdepth", description="Reset your mining level to a milestone marker (e.g. +20, -20).")
    async def restdepth(self, ctx: commands.Context, milestone: str):
        user_id = ctx.author.id
        data = await DatabaseManager.get_user_data(user_id)
        try:
            if milestone[0] not in "+-":
                raise ValueError
            target_milestone = int(milestone)
        except Exception:
            await ctx.send(embed=embed_helper.error_embed("Invalid milestone format. Use a value like +20 or -20."))
            return

        if target_milestone % mining_constants.MILESTONE_INTERVAL != 0:
            await ctx.send(embed=embed_helper.error_embed(f"The milestone must be a multiple of {mining_constants.MILESTONE_INTERVAL}."))
            return

        max_depth = data.get("max_mining_depth", 0)
        min_depth = data.get("min_mining_depth", 0)
        if target_milestone > 0 and max_depth < target_milestone:
            await ctx.send(embed=embed_helper.error_embed(f"You haven't reached {target_milestone} (max reached: {max_depth})."))
            return
        if target_milestone < 0 and min_depth > target_milestone:
            await ctx.send(embed=embed_helper.error_embed(f"You haven't reached {target_milestone} (lowest reached: {min_depth})."))
            return

        await DatabaseManager.update_user_data(user_id, {"mining_depth": target_milestone})
        await ctx.send(embed=embed_helper.success_embed(f"Your mining level has been reset to {target_milestone}."))

async def setup(bot: commands.Bot):
    await bot.add_cog(MiningCog(bot))
