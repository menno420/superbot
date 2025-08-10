import json
import os
import discord
from discord.ext import commands

LOCALIZATION_PATH = "/home/menno/disbot/data/json/localization.json"

class TranslationUpdater(commands.Cog):
    """Cog to update localization.json with all command descriptions and aliases."""

    def __init__(self, bot):
        self.bot = bot

    def load_localization_file(self):
        """Safely loads localization.json as a dictionary, ensuring it’s correctly formatted."""
        if not os.path.exists(LOCALIZATION_PATH):
            return {"en": {"aliases": {}}, "de": {"aliases": {}}}

        try:
            with open(LOCALIZATION_PATH, "r", encoding="utf-8") as file:
                data = json.load(file)
                if not isinstance(data, dict):  # Ensure correct JSON structure
                    raise ValueError("Invalid JSON format: Expected a dictionary.")
                return data
        except json.JSONDecodeError:
            print("❌ Error: localization.json is corrupted or has invalid syntax.")
            return {"en": {"aliases": {}}, "de": {"aliases": {}}}
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return {"en": {"aliases": {}}, "de": {"aliases": {}}}

    def extract_commands(self):
        """Extracts all commands, descriptions, and aliases dynamically."""
        localization_data = self.load_localization_file()

        # Ensure the localization data structure is correct
        if not isinstance(localization_data, dict):
            localization_data = {"en": {"aliases": {}}, "de": {"aliases": {}}}

        # Ensure English and German sections exist
        localization_data.setdefault("en", {}).setdefault("aliases", {})
        localization_data.setdefault("de", {}).setdefault("aliases", {})

        for command in self.bot.commands:
            cmd_key = f"cmd_{command.name}"

            # Store command descriptions (preserve existing translations)
            if isinstance(localization_data["en"], dict):  # Ensure it's a dictionary
                localization_data["en"].setdefault(cmd_key, command.help or "No description provided.")
            if isinstance(localization_data["de"], dict):
                localization_data["de"].setdefault(cmd_key, localization_data["de"].get(cmd_key, ""))

            # Store command aliases (preserve existing aliases)
            if isinstance(localization_data["en"]["aliases"], dict):
                localization_data["en"]["aliases"].setdefault(command.name, command.aliases)
            if isinstance(localization_data["de"]["aliases"], dict):
                localization_data["de"]["aliases"].setdefault(command.name, localization_data["de"]["aliases"].get(command.name, []))

        return localization_data

    def update_localization_file(self, updated_data):
        """Merges updated command descriptions and aliases into localization.json."""
        with open(LOCALIZATION_PATH, "w", encoding="utf-8") as file:
            json.dump(updated_data, file, indent=4, ensure_ascii=False)

    @commands.command(name="update_translations", aliases=["update_lang", "update_locales"])
    async def update_translations(self, ctx):
        """Fetches all commands and updates localization.json with descriptions and aliases."""
        try:
            updated_data = self.extract_commands()
            self.update_localization_file(updated_data)
            await ctx.send("✅ Localization file updated! Please complete missing translations in localization.json.")
        except Exception as e:
            await ctx.send(f"❌ Error while updating translations: {e}")

async def setup(bot):
    await bot.add_cog(TranslationUpdater(bot))