import aiosqlite
from config import Config
from utils.logging import log_info, log_warning, log_error

async def get_inventory(user_id):
    try:
        async with aiosqlite.connect(Config.DB_FILE) as db:
            async with db.execute("SELECT item_id, quantity FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return {item_id: quantity for item_id, quantity in rows} if rows else {}
    except Exception as e:
        log_error(f"[get_inventory] Error: {e}")
        return {}

async def update_inventory(user_id, item_id, amount):
    try:
        async with aiosqlite.connect(Config.DB_FILE) as db:
            # Ensure user exists
            await db.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (user_id,))
            # Check current quantity
            async with db.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id)) as cursor:
                row = await cursor.fetchone()
            if row:
                new_quantity = row[0] + amount
                if new_quantity > 0:
                    await db.execute("UPDATE inventory SET quantity = ? WHERE user_id = ? AND item_id = ?", (new_quantity, user_id, item_id))
                else:
                    await db.execute("DELETE FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
            else:
                if amount > 0:
                    await db.execute("INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?)", (user_id, item_id, amount))
            await db.commit()
            return True
    except Exception as e:
        log_error(f"[update_inventory] Error: {e}")
        return False

async def get_all_items():
    try:
        async with aiosqlite.connect(Config.DB_FILE) as db:
            async with db.execute("SELECT item_id FROM items") as cursor:
                rows = await cursor.fetchall()
                return [(item_id, item_id) for item_id, in rows]
    except Exception as e:
        log_error(f"[get_all_items] Error: {e}")
        return []
