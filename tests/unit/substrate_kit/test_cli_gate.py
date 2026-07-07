"""The CI locked-door gate: `check --require-session-log`.

The kit's `check --strict` treats a *missing* session log as advisory (so a
host can lint mid-session). `--require-session-log` flips a missing log to a
hard failure — the gate mode the live CI workflow runs, so a session that never
writes its journal cannot merge. Proves the door locks (red) and opens (green).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("engine.hooks.settings")

from engine.adopt import adopt
from engine.cli import cmd_check
from engine.lib.config import Config
from engine.lib.state import JsonStateBackend, default_state


def _adopt_scratch(root: Path, kit_root: Path) -> Config:
    config = Config()
    backend = JsonStateBackend(root / config.state_dir / "state.json")
    with backend.transaction():
        for key, value in default_state(config.project_id).items():
            backend.set(key, value)
    adopt(root, config, backend, kit_root=kit_root)
    return config


def _write_complete_log(root: Path, config: Config) -> None:
    """A session card that carries every required marker (would pass the gate)."""
    markers = "\n".join(
        f"{m.get('needle', '')} {m.get('label', '')}" for m in config.session_markers
    )
    card = root / config.sessions_dir / "2026-07-07-demo.md"
    card.write_text(
        f"# demo session\n\n> **Status:** `complete`\n\n{markers}\n",
        encoding="utf-8",
    )


def test_missing_log_is_advisory_by_default(tmp_path, capsys):
    root = tmp_path / "repo"
    _adopt_scratch(root, tmp_path / "kit")
    # No session card written; default check does NOT fail on that alone.
    rc = cmd_check(root, strict=True)
    assert rc == 0
    assert "advisory" in capsys.readouterr().out


def test_require_session_log_holds_the_merge_red_when_absent(tmp_path, capsys):
    root = tmp_path / "repo"
    _adopt_scratch(root, tmp_path / "kit")
    # The locked door: same repo, gate mode → a missing journal fails.
    rc = cmd_check(root, strict=True, require_session_log=True)
    assert rc == 1
    assert "MERGE HELD" in capsys.readouterr().out


def test_require_session_log_opens_the_door_once_the_journal_exists(tmp_path):
    root = tmp_path / "repo"
    config = _adopt_scratch(root, tmp_path / "kit")
    # Red before the journal…
    assert cmd_check(root, strict=True, require_session_log=True) == 1
    # …green after writing a complete session card. The door opens.
    _write_complete_log(root, config)
    assert cmd_check(root, strict=True, require_session_log=True) == 0


def test_incomplete_log_fails_the_gate_too(tmp_path):
    root = tmp_path / "repo"
    config = _adopt_scratch(root, tmp_path / "kit")
    # A card missing its required markers is not enough to open the door.
    stub = root / config.sessions_dir / "2026-07-07-stub.md"
    stub.write_text("# stub\n\n> **Status:** `complete`\n", encoding="utf-8")
    assert cmd_check(root, strict=True, require_session_log=True) == 1
