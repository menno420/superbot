import json
import aiosqlite
import asyncio
from config import Config

# Global caches for static data
_item_cache = None
_alias_cache = None

class DatabaseManager:
    DB_FILE = Config.DB_FILE

    @staticmethod
    async def initialize():
        """Initialize the database and create all necessary tables."""
        async with aiosqlite.connect(DatabaseManager.DB_FILE) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            # Users table: global user data.
            await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                global_xp INTEGER DEFAULT 0,
                global_level INTEGER DEFAULT 1,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            # User progress: XP and levels per activity.
            await db.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                user_id TEXT PRIMARY KEY,
                mining_xp INTEGER DEFAULT 0,
                mining_level INTEGER DEFAULT 1,
                exploration_xp INTEGER DEFAULT 0,
                exploration_level INTEGER DEFAULT 1,
                crafting_xp INTEGER DEFAULT 0,
                crafting_level INTEGER DEFAULT 1,
                equipped_tool TEXT DEFAULT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            """)
            # Inventory: one row per user-item pair.
            await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                user_id TEXT,
                item_id TEXT,
                quantity INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, item_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            """)
            # Equipped items: tracks which item is in which slot.
            await db.execute("""
            CREATE TABLE IF NOT EXISTS equipped_items (
                user_id TEXT,
                slot TEXT,
                item_id TEXT,
                equipped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, slot),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            """)
            # Items: static data and stats.
            await db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                item_id TEXT PRIMARY KEY,
                display_name TEXT,
                category TEXT,
                rarity TEXT,
                value INTEGER,
                weight INTEGER,
                description TEXT,
                other_stats TEXT
            );
            """)
            # Exploration data: log events.
            await db.execute("""
            CREATE TABLE IF NOT EXISTS exploration_data (
                exploration_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                location TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                xp_gained INTEGER,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            """)
            # Item aliases: map alternative names to canonical item_id.
            await db.execute("""
            CREATE TABLE IF NOT EXISTS item_aliases (
                alias TEXT PRIMARY KEY,
                item_id TEXT,
                FOREIGN KEY (item_id) REFERENCES items(item_id)
            );
            """)
            # Bot info: stores version and changelog.
            await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_info (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version TEXT,
                changelog TEXT
            );
            """)
            await db.commit()
            print("✅ Database initialized successfully.")

    @staticmethod
    async def execute_query(query, params=(), fetch_one=False, fetch_all=False):
        """General-purpose query executor."""
        try:
            async with aiosqlite.connect(DatabaseManager.DB_FILE) as db:
                await db.execute("PRAGMA foreign_keys = ON;")
                cursor = await db.execute(query, params)
                await db.commit()
                if fetch_one:
                    return await cursor.fetchone()
                if fetch_all:
                    return await cursor.fetchall()
        except Exception as e:
            print(f"Database error: {e}")
            return None

    # ---------- User Data Functions ----------
    @staticmethod
    async def add_user_if_not_exists(user_id: str, username: str):
        query = "SELECT user_id FROM users WHERE user_id = ?"
        result = await DatabaseManager.execute_query(query, (user_id,), fetch_one=True)
        if not result:
            await DatabaseManager.execute_query(
                "INSERT INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            await DatabaseManager.execute_query(
                "INSERT INTO user_progress (user_id) VALUES (?)",
                (user_id,)
            )

    @staticmethod
    async def get_user_data(user_id: str) -> dict:
        user_row = await DatabaseManager.execute_query(
            "SELECT user_id, username, global_xp, global_level, join_date FROM users WHERE user_id = ?",
            (user_id,), fetch_one=True
        )
        progress_row = await DatabaseManager.execute_query(
            "SELECT mining_xp, mining_level, exploration_xp, exploration_level, crafting_xp, crafting_level FROM user_progress WHERE user_id = ?",
            (user_id,), fetch_one=True
        )
        data = {}
        if user_row:
            keys = ["user_id", "username", "global_xp", "global_level", "join_date"]
            data.update(dict(zip(keys, user_row)))
        if progress_row:
            keys = ["mining_xp", "mining_level", "exploration_xp", "exploration_level", "crafting_xp", "crafting_level"]
            data.update(dict(zip(keys, progress_row)))
        return data

    @staticmethod
    async def update_user_data(user_id: str, updates: dict) -> dict:
        set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
        params = list(updates.values()) + [user_id]
        query = f"UPDATE user_progress SET {set_clause} WHERE user_id = ?"
        await DatabaseManager.execute_query(query, params)
        return await DatabaseManager.get_user_data(user_id)

    # ---------- Inventory Functions ----------
    @staticmethod
    async def get_inventory(user_id: str) -> dict:
        rows = await DatabaseManager.execute_query(
            "SELECT item_id, quantity FROM inventory WHERE user_id = ?",
            (user_id,), fetch_all=True
        )
        inventory = {}
        if rows:
            for item_id, quantity in rows:
                inventory[item_id] = quantity
        return inventory

    @staticmethod
    async def update_inventory(user_id: str, item_id: str, amount: int) -> bool:
        row = await DatabaseManager.execute_query(
            "SELECT quantity FROM inventory WHERE user_id = ? AND item_id = ?",
            (user_id, item_id), fetch_one=True
        )
        current = row[0] if row else 0
        new_quantity = current + amount
        if new_quantity < 0:
            print(f"Insufficient quantity for user {user_id} - item {item_id}")
            return False
        elif new_quantity == 0:
            await DatabaseManager.execute_query(
                "DELETE FROM inventory WHERE user_id = ? AND item_id = ?",
                (user_id, item_id)
            )
        else:
            if row:
                await DatabaseManager.execute_query(
                    "UPDATE inventory SET quantity = ?, last_updated = CURRENT_TIMESTAMP WHERE user_id = ? AND item_id = ?",
                    (new_quantity, user_id, item_id)
                )
            else:
                await DatabaseManager.execute_query(
                    "INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?)",
                    (user_id, item_id, new_quantity)
                )
        return True

    # ---------- Equipped Items Functions ----------
    @staticmethod
    async def get_equipped_items(user_id: str) -> dict:
        rows = await DatabaseManager.execute_query(
            "SELECT slot, item_id FROM equipped_items WHERE user_id = ?",
            (user_id,), fetch_all=True
        )
        equipped = {}
        if rows:
            for slot, item_id in rows:
                equipped[slot] = item_id
        return equipped

    @staticmethod
    async def update_equipped_item(user_id: str, slot: str, item_id: str) -> bool:
        row = await DatabaseManager.execute_query(
            "SELECT item_id FROM equipped_items WHERE user_id = ? AND slot = ?",
            (user_id, slot), fetch_one=True
        )
        if row:
            await DatabaseManager.execute_query(
                "UPDATE equipped_items SET item_id = ?, equipped_at = CURRENT_TIMESTAMP WHERE user_id = ? AND slot = ?",
                (item_id, user_id, slot)
            )
        else:
            await DatabaseManager.execute_query(
                "INSERT INTO equipped_items (user_id, slot, item_id) VALUES (?, ?, ?)",
                (user_id, slot, item_id)
            )
        return True

    # ---------- Static Items Functions (with Caching) ----------
    @staticmethod
    async def load_all_items():
        global _item_cache
        rows = await DatabaseManager.execute_query(
            "SELECT item_id, display_name, category, rarity, value, weight, description, other_stats FROM items",
            fetch_all=True
        )
        cache = {}
        if rows:
            for row in rows:
                keys = ["item_id", "display_name", "category", "rarity", "value", "weight", "description", "other_stats"]
                item = dict(zip(keys, row))
                if item.get("other_stats"):
                    try:
                        item["other_stats"] = json.loads(item["other_stats"])
                    except Exception:
                        item["other_stats"] = {}
                cache[item["item_id"]] = item
        _item_cache = cache
        return _item_cache

    @staticmethod
    async def get_item_stats(item_id: str) -> dict:
        global _item_cache
        if _item_cache is None:
            await DatabaseManager.load_all_items()
        return _item_cache.get(item_id, {})

    @staticmethod
    async def get_all_items() -> list:
        global _item_cache
        if _item_cache is None:
            await DatabaseManager.load_all_items()
        return [(item["item_id"], item["display_name"]) for item in _item_cache.values()]

    # ---------- Item Aliases Functions ----------
    @staticmethod
    async def load_all_aliases():
        global _alias_cache
        rows = await DatabaseManager.execute_query(
            "SELECT alias, item_id FROM item_aliases",
            fetch_all=True
        )
        cache = {}
        if rows:
            for alias, item_id in rows:
                cache[alias.lower()] = item_id
        _alias_cache = cache
        return _alias_cache

    @staticmethod
    async def get_item_by_alias(alias: str) -> str:
        global _alias_cache
        if _alias_cache is None:
            await DatabaseManager.load_all_aliases()
        return _alias_cache.get(alias.lower())

    @staticmethod
    async def add_item_alias(alias: str, item_id: str) -> bool:
        try:
            await DatabaseManager.execute_query(
                "INSERT OR REPLACE INTO item_aliases (alias, item_id) VALUES (?, ?)",
                (alias, item_id)
            )
            await DatabaseManager.load_all_aliases()
            return True
        except Exception as e:
            print(f"Error adding alias: {e}")
            return False

    # ---------- Exploration Data Logging ----------
    @staticmethod
    async def log_exploration(user_id: str, location: str, xp_gained: int, notes: str = "") -> bool:
        try:
            await DatabaseManager.execute_query(
                "INSERT INTO exploration_data (user_id, location, xp_gained, notes) VALUES (?, ?, ?, ?)",
                (user_id, location, xp_gained, notes)
            )
            return True
        except Exception as e:
            print(f"Error logging exploration data: {e}")
            return False

    # ---------- Bot Info ----------
    @staticmethod
    async def get_bot_info() -> dict:
        row = await DatabaseManager.execute_query(
            "SELECT version, changelog FROM bot_info WHERE id = 1",
            fetch_one=True
        )
        if row:
            return {"version": row[0], "changelog": row[1]}
        return {"version": "", "changelog": ""}

    @staticmethod
    async def update_bot_info(version: str, changelog: str) -> bool:
        await DatabaseManager.execute_query(
            """
            INSERT INTO bot_info (id, version, changelog)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET version = excluded.version, changelog = excluded.changelog;
            """,
            (version, changelog)
        )
        return True

    # ---------- Schema Helper ----------
    @staticmethod
    async def get_table_columns(table: str) -> list:
        rows = await DatabaseManager.execute_query(f"PRAGMA table_info({table})", fetch_all=True)
        return [row[1] for row in rows] if rows else []

if __name__ == "__main__":
    asyncio.run(DatabaseManager.initialize())
