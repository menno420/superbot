"""Mining structure recipes — JSON-loaded with safe defaults (S4.1).

Extracted from the pre-decomposition ``cogs/mining_cog.py``.  The loader
normalises every key to lowercase, skips malformed entries, and falls
back to a hard-coded default if the JSON file is missing or invalid.
"""

from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger("bot.cogs.mining.recipes")

# Path to the JSON recipes file shipped under disbot/data/json/.  Kept
# identical to the pre-S4.1 location so deployed data files Just Work.
RECIPES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "json",
    "recipes.json",
)

DEFAULT_RECIPES: dict[str, dict[str, int]] = {
    "stone hut": {"stone": 5},
    "iron pickaxe": {"iron": 3, "wood": 1},
    "gold statue": {"gold": 4},
    "diamond throne": {"diamond": 6},
    "wooden house": {"wood": 8},
}


def load_recipes() -> dict[str, dict[str, int]]:
    """Load + normalise the recipes JSON; fall back to defaults on error.

    Normalisations:
      * recipe names lower-cased
      * material names lower-cased
      * non-dict entries skipped
      * non-int quantities skipped
    """
    if not os.path.exists(RECIPES_FILE):
        return dict(DEFAULT_RECIPES)

    try:
        with open(RECIPES_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return dict(DEFAULT_RECIPES)

        normalised: dict[str, dict[str, int]] = {}
        for recipe_name, requirements in data.items():
            if not isinstance(requirements, dict):
                continue
            recipe_lower = recipe_name.lower()
            normalised_req: dict[str, int] = {}
            for mat, qty in requirements.items():
                if isinstance(mat, str) and isinstance(qty, int):
                    normalised_req[mat.lower()] = qty
            if normalised_req:
                normalised[recipe_lower] = normalised_req
        return normalised if normalised else dict(DEFAULT_RECIPES)
    except (json.JSONDecodeError, ValueError):
        return dict(DEFAULT_RECIPES)
