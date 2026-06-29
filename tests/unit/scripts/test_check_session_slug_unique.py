"""Tests for scripts/check_session_slug_unique.py — the slug-collision guard (BUG-0027 residual).

Closes the residual *silent-clobber* harm: a new session reusing an existing ``.sessions/`` slug
overwrites the prior session's log. The guard fires when a touched card path already exists in
``origin/main`` and the card is an active (non-re-badge) session card.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location(
    "check_session_slug_unique",
    _REPO_ROOT / "scripts" / "check_session_slug_unique.py",
)
assert _SPEC and _SPEC.loader
guard = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(guard)


def _write_card(tmp_path: Path, name: str, status: str) -> Path:
    card = tmp_path / name
    card.write_text(f"# {name}\n\n> **Status:** `{status}`\n", encoding="utf-8")
    return card


# --- collisions: the core distinction --------------------------------------


def test_net_new_slug_is_not_a_collision(monkeypatch, tmp_path):
    """A card that does NOT exist in origin/main is the normal case — never a collision."""
    card = _write_card(tmp_path, "2026-06-29-fresh.md", "in-progress")
    monkeypatch.setattr(guard, "gate_session_cards", lambda b, h: [card])
    monkeypatch.setattr(guard, "_exists_in_main", lambda rel: False)
    assert guard.collisions(None, None) == []


def test_reused_slug_active_card_is_a_collision(monkeypatch, tmp_path):
    """A card that exists in main AND is an active (in-progress) session card collides."""
    card = _write_card(tmp_path, "2026-06-29-dup.md", "in-progress")
    monkeypatch.setattr(guard, "gate_session_cards", lambda b, h: [card])
    monkeypatch.setattr(guard, "_exists_in_main", lambda rel: True)
    assert guard.collisions(None, None) == [(card, "in-progress")]


def test_reused_slug_complete_card_is_still_a_collision(monkeypatch, tmp_path):
    """Even a `complete` card collides — a finished new session reusing a slug still clobbers.

    Only a terminal *re-badge* status (historical/archived/…) is exempt; `complete` is an active
    session's done-state, not a reconciliation re-badge.
    """
    card = _write_card(tmp_path, "2026-06-29-dup.md", "complete")
    monkeypatch.setattr(guard, "gate_session_cards", lambda b, h: [card])
    monkeypatch.setattr(guard, "_exists_in_main", lambda rel: True)
    assert guard.collisions(None, None) == [(card, "complete")]


def test_reconciliation_rebadge_is_exempt(monkeypatch, tmp_path):
    """A reconciliation pass re-badging an OLD log to `historical` is a legitimate modify-in-place."""
    for status in sorted(guard._REBADGE_OK_STATUSES):
        card = _write_card(tmp_path, f"2026-06-29-old-{status}.md", status)
        monkeypatch.setattr(guard, "gate_session_cards", lambda b, h, c=card: [c])
        monkeypatch.setattr(guard, "_exists_in_main", lambda rel: True)
        assert guard.collisions(None, None) == [], f"{status} should be exempt"


# --- _exists_in_main: git probe --------------------------------------------


def test_exists_in_main_true_on_zero_returncode(monkeypatch):
    class _R:
        returncode = 0

    monkeypatch.setattr(guard.subprocess, "run", lambda *a, **k: _R())
    assert guard._exists_in_main(".sessions/x.md") is True


def test_exists_in_main_false_on_missing(monkeypatch):
    class _R:
        returncode = 1

    monkeypatch.setattr(guard.subprocess, "run", lambda *a, **k: _R())
    assert guard._exists_in_main(".sessions/x.md") is False


def test_exists_in_main_false_on_oserror(monkeypatch):
    def _boom(*a, **k):
        raise OSError("no git")

    monkeypatch.setattr(guard.subprocess, "run", _boom)
    assert guard._exists_in_main(".sessions/x.md") is False


# --- main / exit codes ------------------------------------------------------


def test_main_clean_passes(monkeypatch, capsys):
    monkeypatch.setattr(guard, "collisions", lambda b, h: [])
    assert guard.main(["--base", "a", "--head", "b"]) == 0
    assert "OK" in capsys.readouterr().out


def test_main_collision_fails_with_rename_hint(monkeypatch, capsys, tmp_path):
    card = _write_card(tmp_path, "2026-06-29-dup.md", "in-progress")
    monkeypatch.setattr(guard, "collisions", lambda b, h: [(card, "in-progress")])
    assert guard.main([]) == 1
    out = capsys.readouterr().out
    assert "COLLISION" in out
    assert "unique slug" in out


def test_main_quiet_suppresses_output(monkeypatch, capsys):
    monkeypatch.setattr(guard, "collisions", lambda b, h: [])
    assert guard.main(["--quiet"]) == 0
    assert capsys.readouterr().out == ""


# --- the sentinel is declared (kept wired by check_session_close_gate) ------


def test_declares_session_close_gate_sentinel():
    src = (_REPO_ROOT / "scripts" / "check_session_slug_unique.py").read_text(
        encoding="utf-8"
    )
    assert "[session-close-gate]" in src
