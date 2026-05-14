from __future__ import annotations
import sqlite3
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger("DataManager")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
JSON_DIR = os.path.join(DATA_DIR, "json")
_default_db = (
    "/data/bot_data.db"
    if os.path.isdir("/data")
    else os.path.join(DATA_DIR, "bot_data.db")
)
DB_PATH = os.environ.get("BOT_DB_PATH", _default_db)


class DataManager:
    logger = logger
    DATA_DIR = DATA_DIR
    JSON_DIR = JSON_DIR
    DB_PATH = DB_PATH
    _registered_tables: dict = {}

    @classmethod
    def init(cls):
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(JSON_DIR, exist_ok=True)
        cls._register_table("logs", (
            "CREATE TABLE IF NOT EXISTS logs ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "timestamp TEXT NOT NULL, "
            "level TEXT NOT NULL, "
            "message TEXT NOT NULL)"
        ))
        cls._create_tables()

    @classmethod
    def _register_table(cls, name: str, create_stmt: str):
        cls._registered_tables[name] = create_stmt

    @classmethod
    def _create_tables(cls):
        with sqlite3.connect(cls.DB_PATH) as conn:
            for stmt in cls._registered_tables.values():
                conn.execute(stmt)
            conn.commit()

    @classmethod
    def fetch_all(cls, query: str, params: tuple = ()) -> list[dict]:
        with sqlite3.connect(cls.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    @classmethod
    def execute(cls, query: str, params: tuple = ()):
        with sqlite3.connect(cls.DB_PATH) as conn:
            conn.execute(query, params)
            conn.commit()

    @classmethod
    def read_json(cls, filename: str, read_only: bool = True):
        path = os.path.join(cls.JSON_DIR, filename)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to read {filename}: {e}")
            return None

    @classmethod
    def write_json(cls, filename: str, data):
        path = os.path.join(cls.JSON_DIR, filename)
        os.makedirs(cls.JSON_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def query_logs(cls, event_type: str = None, limit: int = 10) -> list[dict]:
        if event_type:
            return cls.fetch_all(
                "SELECT * FROM logs WHERE level = ? ORDER BY timestamp DESC LIMIT ?",
                (event_type, limit)
            )
        return cls.fetch_all(
            "SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )

    @classmethod
    def log_event(cls, level: str, message: str):
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        cls.execute(
            "INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)",
            (timestamp, level, message)
        )

    @classmethod
    def notify_error(cls, message: str):
        cls.log_event("ERROR", message)
        logger.error(f"[Notification] {message}")


DataManager.init()
