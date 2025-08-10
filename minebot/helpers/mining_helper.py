# helpers/mining_helper.py
import random

# Depth-based loot tiers
DEPTH_LOOT_TABLE = {
    (0, 4): ["stone", "coal"],
    (5, 9): ["iron", "stone"],
    (10, 14): ["gold", "iron"],
    (15, 19): ["diamond", "gold"],
    (20, 999): ["mythril", "diamond", "rare_gem"]
}

def get_loot_for_depth(depth: int):
    """Returns a random item from the depth-based loot tiers."""
    for (min_d, max_d), items in DEPTH_LOOT_TABLE.items():
        if min_d <= depth <= max_d:
            return random.choice(items)
    return "stone"

def calculate_durability_cost(depth: int) -> int:
    """Every 10 depth requires +1 durability per mine."""
    return 1 + (depth // 10)

def get_tool_bonus_probability(rarity: str) -> float:
    """Returns the chance of a +1 quantity bonus based on tool rarity."""
    bonus_table = {
        "common": 0.00,
        "uncommon": 0.20,
        "rare": 0.40,
        "epic": 0.60,
        "legendary": 1.00,
        "mythic": 2.00  # can interpret >1.0 as guaranteed + 1 plus a second chance
    }
    return bonus_table.get(rarity.lower(), 0.0)

def mine(tool: dict, depth: int) -> dict:
    """
    Performs the mining logic:
     - Chooses loot for given depth
     - Applies rarity-based quantity bonus
     - Determines durability usage and XP
     - Returns a dictionary with the results (loot, quantity, xp, durability_used, depth_gained).
    """

    loot = get_loot_for_depth(depth)
    quantity = 1
    rarity = tool.get("rarity", "common")

    # Bonus: if random() < bonus, you get +1 item
    # If bonus > 1.0 (e.g. "mythic" = 2.0), you can handle guaranteed +1, or do multiple rolls
    bonus_chance = get_tool_bonus_probability(rarity)
    if bonus_chance > 1.0:
        # e.g. for "mythic", add +1 guaranteed, and do an additional roll
        quantity += 1
        if random.random() < (bonus_chance - 1.0):
            quantity += 1
    else:
        # single roll for +1
        if random.random() < bonus_chance:
            quantity += 1

    durability_used = calculate_durability_cost(depth)

    # XP: for demonstration, base of 10 XP plus small fraction from rarity
    # e.g. if bonus_chance=0.4, XP = 10 + int(0.4 * 5) = 12
    xp_earned = 10 + int(bonus_chance * 5)

    return {
        "loot": loot,
        "quantity": quantity,
        "xp": xp_earned,
        "durability_used": durability_used,
        "depth_gained": 1  # default to +1 depth each mine
    }