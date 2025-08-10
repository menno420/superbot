"""
mining_constants.py

This file stores the core configuration and helper functions for the mining system.
It is designed to be future proof by centralizing key settings for loot tables,
milestone intervals, XP rewards, durability costs, and tool rarity bonuses.
"""

# Milestone configuration
MILESTONE_INTERVAL = 20  # Milestone markers are set every 20 levels

# Loot table: mapping depth ranges (inclusive) to lists of possible loot items.
# Feel free to add new ranges and items for deeper levels.
DEPTH_LOOT_TABLE = {
    (0, 4): ["stone", "coal"],
    (5, 9): ["iron", "stone"],
    (10, 14): ["gold", "iron"],
    (15, 19): ["diamond", "gold"],
    (20, 39): ["mythril", "diamond", "rare_gem"],
    (40, 59): ["ancient_artifact", "mythril", "rare_gem"],
    # Extend as needed for deeper levels.
}

# Base XP reward per mining action
BASE_XP_REWARD = 10

# Tool rarity bonus multipliers.
# These values can modify XP gain, loot bonus chances, etc.
TOOL_RARITY_BONUS = {
    "common": 0.00,
    "uncommon": 0.20,
    "rare": 0.40,
    "epic": 0.60,
    "legendary": 1.00,
    "mythic": 2.00,
    # For bare hands or no tool:
    "none": 0.0,
}

def calculate_durability_cost(depth: int) -> int:
    """
    Calculates the durability cost for a mining action.
    Cost starts at 1 and increases by 1 for every 10 levels (depth).
    """
    return 1 + (depth // 10)

def xp_for_next_level(mining_level: int) -> int:
    """
    Returns the XP required for the next mining level.
    This example uses a linear progression (100 XP per level),
    but can be modified for exponential scaling if desired.
    """
    return 100 * mining_level

def bonus_chance_for_rarity(rarity: str) -> float:
    """
    Returns the bonus chance multiplier for a given tool rarity.
    This value can be used to determine the chance to receive bonus loot.
    """
    return TOOL_RARITY_BONUS.get(rarity.lower(), 0.0)

def get_loot_items_for_depth(depth: int) -> list:
    """
    Given an effective (absolute) depth, returns the list of loot items available.
    If no range matches, returns a default loot item.
    """
    for (min_depth, max_depth), items in DEPTH_LOOT_TABLE.items():
        if min_depth <= depth <= max_depth:
            return items
    return ["stone"]

# Future improvements can be added here.
# For example, functions to modify loot probabilities based on events,
# dynamic adjustments to milestone intervals, or new bonus multipliers.