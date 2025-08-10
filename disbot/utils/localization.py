import json
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Set the path to the localization file
LOCALIZATION_PATH = "/home/menno/disbot/data/json/localization.json"

class LocalizationManager:
    """Handles language translations for the bot."""

    def __init__(self, file_path=LOCALIZATION_PATH):
        self.file_path = file_path
        self.translations = self.load_translations()

    def load_translations(self):
        """Load translations from a JSON file."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            logger.error(f"Localization file not found at {self.file_path}. Using default fallback.")
            return {"en": {}, "de": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON file: {e}")
            return {"en": {}, "de": {}}

    def get(self, key, lang="en", **kwargs):
        """Fetch the localized string based on the key and language."""
        text = self.translations.get(lang, {}).get(key, self.translations["en"].get(key, key))
        return text.format(**kwargs)

# Create a global instance for easy import
localization = LocalizationManager()