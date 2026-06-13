"""Host-project configuration for one substrate-kit install.

Reads and writes ``substrate.config.json`` — the single file that absorbs every
host-specific knob so the engine code never hardcodes a project value. Two
interpreters are kept explicitly separate (Hermes-final): ``interpreter`` is the
kit's own runtime, ``interpreter_for_checks`` is the host project's verification
runtime (e.g. ``python3.10`` for a repo whose CI pins 3.10).
"""

from __future__ import annotations

import json
import sys
import uuid
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from engine.lib.atomicio import atomic_write_text

CONFIG_FILENAME = "substrate.config.json"
DEFAULT_STATE_DIR = ".substrate"


def _new_project_id() -> str:
    """Return a short, stable identifier for one install."""
    return uuid.uuid4().hex[:12]


def _default_cadence() -> dict[str, int]:
    """Return the default cadence knobs."""
    return {"reconciliation_prs": 20}


@dataclass
class Config:
    """Host-project configuration for one substrate-kit install."""

    project_id: str = field(default_factory=_new_project_id)
    interpreter: str = field(default_factory=lambda: sys.executable)
    interpreter_for_checks: str | None = None
    state_dir: str = DEFAULT_STATE_DIR
    paths: dict[str, str] = field(default_factory=dict)
    cadence: dict[str, int] = field(default_factory=_default_cadence)
    scopes: dict[str, str] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialise the config to indented, key-sorted JSON."""
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> Config:
        """Build a Config from a parsed dict, ignoring unknown keys."""
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


def config_path(root: Path) -> Path:
    """Return the config-file path for a project ``root``."""
    return root / CONFIG_FILENAME


def load_config(root: Path) -> Config:
    """Load the config from ``root``; return defaults if none exists."""
    path = config_path(root)
    if not path.exists():
        return Config()
    data = json.loads(path.read_text(encoding="utf-8"))
    return Config.from_dict(data)


def save_config(root: Path, config: Config) -> None:
    """Write ``config`` to ``root`` atomically."""
    atomic_write_text(config_path(root), config.to_json() + "\n")
