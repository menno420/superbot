"""The state-backend interface and its default JSON implementation.

The *interface* — not a raw JSON shape — is the contract the rest of the engine
codes against (Hermes-final, plan §2), so a future SQLite backend can replace the
JSON one without a rewrite. The default backend is one JSON file written
atomically; mutations inside a ``transaction`` roll back on error and flush once.
"""

from __future__ import annotations

import copy
import json
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path
from typing import Any

from engine.lib.atomicio import atomic_write_text

STATE_SCHEMA_VERSION = 1


def default_state(project_id: str) -> dict[str, Any]:
    """Return the initial state document for a fresh install."""
    return {
        "version": STATE_SCHEMA_VERSION,
        "project_id": project_id,
        "mode": "guided",
        "promotion_rights": "propose",
        "stage": "integration",
        "stance": "analysis",
        "session_count": 0,
        "slots": {},
        "slot_values": {},
        "open_questions": [],
        "quiet_sessions": 0,
        "graduation": {
            "soft_target_sessions": 50,
            "criteria": {
                "critical_slots_filled_pct": 0.8,
                "blocking_questions": 0,
            },
        },
        "mode_history": [],
        "reflection_buffer": {"active_count": 0, "last_mined": None},
        "graduation_proposed": False,
        "last_compaction_session": 0,
        "review_log": [],
    }


class StateBackend(ABC):
    """Read / write / query / transaction / migrate contract for engine state."""

    version: int = STATE_SCHEMA_VERSION

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Return the value stored at ``key`` or ``default``."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Store ``value`` at ``key`` (flushing unless inside a transaction)."""

    @abstractmethod
    def query(self, prefix: str = "") -> dict[str, Any]:
        """Return all key/value pairs whose key starts with ``prefix``."""

    @abstractmethod
    def transaction(self) -> AbstractContextManager[StateBackend]:
        """Return a context manager that commits on success, rolls back on error."""

    @abstractmethod
    def migrate(self, to_version: int) -> None:
        """Migrate the stored document to schema ``to_version``."""


class JsonStateBackend(StateBackend):
    """A StateBackend backed by one atomically-written JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._data: dict[str, Any] = self._read()
        self._in_txn = False

    def _read(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _flush(self) -> None:
        atomic_write_text(
            self._path,
            json.dumps(self._data, indent=2, sort_keys=True) + "\n",
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value stored at ``key`` or ``default``."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store ``value`` at ``key``; flush now unless inside a transaction."""
        self._data[key] = value
        if not self._in_txn:
            self._flush()

    def query(self, prefix: str = "") -> dict[str, Any]:
        """Return all key/value pairs whose key starts with ``prefix``."""
        return {k: v for k, v in self._data.items() if k.startswith(prefix)}

    @contextmanager
    def transaction(self) -> Iterator[JsonStateBackend]:
        """Buffer writes; roll back the whole document on error, else flush once."""
        snapshot = copy.deepcopy(self._data)
        self._in_txn = True
        try:
            yield self
        except Exception:
            self._data = snapshot
            raise
        finally:
            self._in_txn = False
        self._flush()

    def migrate(self, to_version: int) -> None:
        """Set the stored schema version (no transforms needed at v1)."""
        self._data["version"] = to_version
        self._flush()

    @property
    def data(self) -> dict[str, Any]:
        """Return a shallow copy of the current state document."""
        return dict(self._data)
