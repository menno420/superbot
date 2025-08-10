# settings.py

class GameSettings:
    # Player initial balances and stats
    INITIAL_BALANCE = 100
    STARTING_ITEMS = {
        "wood": 5,
        "stone": 5
    }

    # Crafting and mining bonuses
    MINING_BONUS_MULTIPLIER = {
        "default": 1,
        "iron_pickaxe": 2,
        "golden_pickaxe": 3,
    }

    CHOPPING_BONUS_MULTIPLIER = {
        "default": 1,
        "axe": 2
    }

    # Exploration outcomes
    EXPLORATION_EVENTS = [
        {"event": "Found gold", "item": "gold", "amount": 1, "chance": 0.2},
        {"event": "Lost stone", "item": "stone", "amount": -2, "chance": 0.1},
        {"event": "Nothing happened", "item": None, "amount": 0, "chance": 0.7}
    ]

    # PIL item positioning/scaling (example)
    ITEM_POSITIONS = {
        "helmet": {"position": (4, 1), "scale": 0.4},
        "chestplate": {"position": (4, -60), "scale": 0.5},
        "sword": {"position": (60, -20), "scale": 0.6},
        "shield": {"position": (2, 2), "scale": 0.5},
        "leggings": {"position": (4, -10), "scale": 0.5},
        "boots": {"position": (7, 100), "scale": 0.5}
    }
