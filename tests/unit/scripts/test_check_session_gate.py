"""Tests for scripts/check_session_gate.py — the born-red session merge-gate (Q-0133)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location(
    "check_session_gate",
    _REPO_ROOT / "scripts" / "check_session_gate.py",
)
assert _SPEC and _SPEC.loader
gate = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gate)


# --- parse_status -----------------------------------------------------------


def test_parse_status_backticked():
    assert (
        gate.parse_status("> **Status:** `in-progress` — doing the thing")
        == "in-progress"
    )


def test_parse_status_plain():
    assert gate.parse_status("> **Status:** complete") == "complete"


def test_parse_status_complete_with_trailing():
    assert gate.parse_status("> **Status:** `complete` — PR #843 merged.") == "complete"


def test_parse_status_missing():
    assert gate.parse_status("# A log with no badge\n\nsome text") is None


# --- held_cards -------------------------------------------------------------


def test_held_card_in_progress(tmp_path):
    card = tmp_path / "2026-06-14-x.md"
    card.write_text("# x\n\n> **Status:** `in-progress`\n", encoding="utf-8")
    held = gate.held_cards([card])
    assert held == [(card, "in-progress")]


def test_ready_card_complete_not_held(tmp_path):
    card = tmp_path / "2026-06-14-x.md"
    card.write_text("# x\n\n> **Status:** `complete`\n", encoding="utf-8")
    assert gate.held_cards([card]) == []


def test_unknown_status_is_held_fail_safe(tmp_path):
    """An added card with an unrecognized status fails safe (held), not merged."""
    card = tmp_path / "2026-06-14-x.md"
    card.write_text("# x\n\n> **Status:** `frobnicating`\n", encoding="utf-8")
    held = gate.held_cards([card])
    assert held == [(card, "frobnicating")]


def test_missing_badge_is_held(tmp_path):
    card = tmp_path / "2026-06-14-x.md"
    card.write_text("# x\n\njust prose, no badge\n", encoding="utf-8")
    held = gate.held_cards([card])
    assert held and held[0][1] == "(no Status badge)"


# --- main / exit codes ------------------------------------------------------


def test_main_no_cards_passes(monkeypatch, capsys):
    monkeypatch.setattr(gate, "gate_session_cards", lambda base, head: [])
    assert gate.main(["--base", "a", "--head", "b"]) == 0
    assert "not gated" in capsys.readouterr().out


def test_main_held_card_fails(monkeypatch, capsys, tmp_path):
    card = tmp_path / "2026-06-14-x.md"
    card.write_text("# x\n\n> **Status:** `in-progress`\n", encoding="utf-8")
    monkeypatch.setattr(gate, "gate_session_cards", lambda base, head: [card])
    monkeypatch.setattr(gate, "added_session_cards", lambda base, head: [card])
    assert gate.main([]) == 1
    out = capsys.readouterr().out
    assert "MERGE HELD" in out and "in-progress" in out


def test_main_ready_card_passes(monkeypatch, capsys, tmp_path):
    card = tmp_path / "2026-06-14-x.md"
    card.write_text("# x\n\n> **Status:** `complete`\n", encoding="utf-8")
    monkeypatch.setattr(gate, "gate_session_cards", lambda base, head: [card])
    assert gate.main([]) == 0
    assert "merge unblocked" in capsys.readouterr().out


# --- BUG-0027: collision (modified-not-added) + terminal-OK re-badge --------


def test_merge_blocking_terminal_ok_not_held(tmp_path):
    """A re-badged old log (historical) must NOT hold the merge — reconciliation PRs."""
    card = tmp_path / "2026-06-14-x.md"
    card.write_text("# x\n\n> **Status:** `historical` — old\n", encoding="utf-8")
    assert gate.merge_blocking_cards([card]) == []


def test_merge_blocking_in_progress_held(tmp_path):
    card = tmp_path / "2026-06-14-x.md"
    card.write_text("# x\n\n> **Status:** `in-progress`\n", encoding="utf-8")
    assert gate.merge_blocking_cards([card]) == [(card, "in-progress")]


def test_main_modified_card_collision_held_with_hint(monkeypatch, capsys, tmp_path):
    """The #1523 regression: a born-red card that collided with an existing slug lands
    as a MODIFICATION (gate_session_cards sees it, added_session_cards does not). The
    merge gate must hold it AND print the rename hint."""
    card = tmp_path / "2026-06-28-collision.md"
    card.write_text("# x\n\n> **Status:** `in-progress`\n", encoding="utf-8")
    monkeypatch.setattr(gate, "gate_session_cards", lambda base, head: [card])
    monkeypatch.setattr(gate, "added_session_cards", lambda base, head: [])
    assert gate.main([]) == 1
    out = capsys.readouterr().out
    assert "MERGE HELD" in out
    assert "MODIFIED, not added" in out and "rename your card" in out


def test_main_reconciliation_rebadge_not_held(monkeypatch, capsys, tmp_path):
    """A reconciliation PR that MODIFIES an old log to `historical` must merge freely."""
    card = tmp_path / "2026-06-01-old.md"
    card.write_text("# old\n\n> **Status:** `historical`\n", encoding="utf-8")
    monkeypatch.setattr(gate, "gate_session_cards", lambda base, head: [card])
    monkeypatch.setattr(gate, "added_session_cards", lambda base, head: [])
    assert gate.main([]) == 0
    assert "merge unblocked" in capsys.readouterr().out


# --- --require-ready-card (Codex final-review trigger) ----------------------


def test_require_ready_card_no_card_does_not_trigger(monkeypatch, capsys):
    """No session card → no Codex trigger (exit 1), unlike the default not-gated pass."""
    monkeypatch.setattr(gate, "added_session_cards", lambda base, head: [])
    assert gate.main(["--require-ready-card"]) == 1
    assert "no Codex final-review trigger" in capsys.readouterr().out


def test_require_ready_card_held_does_not_trigger(monkeypatch, capsys, tmp_path):
    """A still-in-progress (born-red) card must NOT fire `@codex review`."""
    card = tmp_path / "2026-06-14-x.md"
    card.write_text("# x\n\n> **Status:** `in-progress`\n", encoding="utf-8")
    monkeypatch.setattr(gate, "added_session_cards", lambda base, head: [card])
    assert gate.main(["--require-ready-card"]) == 1
    assert "not ready" in capsys.readouterr().out


def test_require_ready_card_complete_triggers(monkeypatch, capsys, tmp_path):
    """A card flipped to complete is the final-head signal → exit 0 (trigger)."""
    card = tmp_path / "2026-06-14-x.md"
    card.write_text("# x\n\n> **Status:** `complete`\n", encoding="utf-8")
    monkeypatch.setattr(gate, "added_session_cards", lambda base, head: [card])
    assert gate.main(["--require-ready-card"]) == 0
    assert "Codex final-review trigger" in capsys.readouterr().out
