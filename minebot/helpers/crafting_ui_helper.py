import discord
from discord.ext import commands
from helpers.embed_helper import create_embed, error_embed
from config import Config
import json

# Load recipes from file (or this could come from a shared cache)
with open(Config.RECIPES_FILE, 'r', encoding='utf-8') as f:
    RECIPES = json.load(f)

class CraftOptionsView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id

        # Add some common tool buttons
        self.add_item(discord.ui.Button(label="Craft Pickaxe", style=discord.ButtonStyle.green, custom_id="craft_pickaxe"))
        self.add_item(discord.ui.Button(label="Craft Axe", style=discord.ButtonStyle.green, custom_id="craft_axe"))
        self.add_item(discord.ui.Button(label="Craft Sword", style=discord.ButtonStyle.green, custom_id="craft_sword"))
        self.add_item(discord.ui.Button(label="🔍 View Recipes", style=discord.ButtonStyle.secondary, custom_id="view_recipes"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == int(self.user_id)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(embed=error_embed("Crafting canceled."), view=None)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        # Optionally, disable buttons on timeout
        try:
            await self.message.edit(view=self)
        except:
            pass

    async def on_interaction(self, interaction: discord.Interaction):
        custom_id = interaction.data.get("custom_id")
        if custom_id.startswith("craft_"):
            item = custom_id.replace("craft_", "")
            await self.cog.attempt_craft(interaction, self.user_id, item)
        elif custom_id == "view_recipes":
            embed = create_embed(
                title="📜 Available Recipes",
                description="\n".join([f"**{key}**: {', '.join(val['requires'])}" for key, val in RECIPES.items()]),
                color=discord.Color.blurple()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
