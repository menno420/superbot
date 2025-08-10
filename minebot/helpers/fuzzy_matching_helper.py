import json
import difflib
import asyncio
from config import Config
from utils.data_manager import DatabaseManager
from utils.logging import log_info, log_warning, log_error

class FuzzyMatcher:
    def __init__(self):
        # Initially load aliases from JSON as fallback.
        self.aliases = self.load_aliases_from_json()
        self.reverse_map = {}
        self.canonical_to_display = {}
        self.build_lookup_maps()

    def load_aliases_from_json(self):
        try:
            with open(Config.ITEM_ALIASES_FILE, "r") as f:
                aliases = json.load(f)
                log_info("Loaded item aliases from JSON successfully.")
                return aliases
        except Exception as e:
            log_error(f"Failed to load item aliases from JSON: {e}")
            return {}

    async def load_aliases_from_db(self):
        """Load aliases from the database asynchronously."""
        aliases_list = await DatabaseManager.load_all_aliases()
        # We expect a flat mapping { alias: canonical } from DatabaseManager.
        # To reconstruct a similar structure to the JSON, we simply store the flat map.
        self.aliases = {"db": aliases_list}
        log_info("Loaded item aliases from DB successfully.")
        self.build_lookup_maps()

    def build_lookup_maps(self):
        """Build reverse lookup maps from self.aliases.
           If self.aliases is in JSON format, iterate through categories;
           if loaded from DB (flat mapping), use it directly.
        """
        self.reverse_map.clear()
        self.canonical_to_display.clear()
        if "db" in self.aliases:
            # Aliases loaded from DB as a flat dict.
            for alias, canonical in self.aliases["db"].items():
                norm = alias.strip().lower().replace("_", " ").replace("-", " ")
                self.reverse_map[norm] = canonical
                # For display, simply title-case the canonical name.
                self.canonical_to_display[canonical] = canonical.replace("_", " ").title()
        else:
            # JSON structure: { category: { canonical: [variant, ...], ... }, ... }
            for category in self.aliases.values():
                for canonical, variants in category.items():
                    for alias in [canonical] + variants:
                        normalized = alias.strip().lower().replace("_", " ").replace("-", " ")
                        self.reverse_map[normalized] = canonical
                    self.canonical_to_display[canonical] = canonical.replace("_", " ").title()

    def get_canonical_name(self, user_input):
        user_input_clean = user_input.strip().lower().replace("_", " ").replace("-", " ")
        if user_input_clean in self.reverse_map:
            canonical = self.reverse_map[user_input_clean]
            log_info(f"Exact matched '{user_input}' to '{canonical}'")
            return canonical
        best_match = None
        best_ratio = 0.0
        for alias, canonical in self.reverse_map.items():
            ratio = difflib.SequenceMatcher(None, user_input_clean, alias).ratio()
            if ratio > best_ratio:
                best_match = canonical
                best_ratio = ratio
        if best_ratio >= 0.7:
            log_info(f"Fuzzy matched '{user_input}' to '{best_match}' ({best_ratio:.2f})")
            return best_match
        log_warning(f"No good match found for '{user_input}'")
        return None

    def get_display_name(self, canonical_name):
        return self.canonical_to_display.get(canonical_name, canonical_name.replace("_", " ").title())

# Global matcher instance.
matcher = FuzzyMatcher()

# To load from the database during startup, somewhere in your bot initialization code call:
# await matcher.load_aliases_from_db()