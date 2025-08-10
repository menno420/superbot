import aiosqlite
from config import Config

class ItemStatsManager:
    @staticmethod
    async def get(item_id, stat_name, default=None):
        query = f"SELECT {stat_name} FROM items WHERE item_id = ?"
        try:
            async with aiosqlite.connect(Config.DB_FILE) as db:
                async with db.execute(query, (item_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return row[0]
        except Exception as e:
            print(f"[ItemStatsManager] Error getting '{stat_name}' for '{item_id}': {e}")
        return default

    @staticmethod
    async def get_grouped(items, stat_name):
        grouped = {}
        for item_id, count in items:
            group = await ItemStatsManager.get(item_id, stat_name, "Unknown")
            if group not in grouped:
                grouped[group] = []
            grouped[group].append((item_id, count))
        return sorted(grouped.items(), key=lambda x: x[0].lower())
