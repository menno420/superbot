"""Tests for the self-improving loop's trigger scan (Lane B1).

Covers every trigger kind firing AND not firing, the mandatory-question
selection (trigger-field pull, critical-slot pull, dedupe, priority order),
and the mandate-vs-advisory orientation block.
"""

import os
import time
from pathlib import Path

from engine.interview.interview import critical_slots
from engine.interview.question_bank import QUESTIONS
from engine.lib.config import Config
from engine.loop.triggers import (
    Trigger,
    check_triggers,
    mandatory_questions,
    trigger_block,
)

_CONFIG = Config()


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _state(**over) -> dict:
    base = {
        "mode": "guided",
        "session_count": 0,
        "slots": {},
        "slot_values": {},
        "open_questions": [],
        "quiet_sessions": 0,
        "last_compaction_session": 0,
        "stage": "integration",
        "reflection_buffer": {"active_count": 0, "last_mined": None},
    }
    base.update(over)
    return base


def _clean_root(tmp_path: Path) -> Path:
    """A project tree that fires nothing: clean docs + a fresh session log."""
    docs = tmp_path / "docs"
    _write(
        docs / "AGENT_ORIENTATION.md",
        "# O\n\n> **Status:** `reference`\n\n[cs](current-state.md)\n",
    )
    _write(docs / "current-state.md", "# CS\n\n> **Status:** `living-ledger`\n")
    _write(tmp_path / ".sessions" / "2026-07-02-fresh.md", "# Log\n")
    return tmp_path


def _filled_slots() -> dict:
    return {slot: "filled" for slot in critical_slots()}


def _kinds(triggers: list) -> set:
    return {t.kind for t in triggers}


_BANK = [
    {
        "id": "T-1",
        "slot": "alpha",
        "audience": "user",
        "prompt": "Alpha?",
        "routing": "state:alpha",
        "priority": "blocking",
        "critical": True,
    },
    {
        "id": "T-2",
        "slot": "beta",
        "audience": "user",
        "prompt": "Beta?",
        "routing": "state:beta",
        "priority": "normal",
        "critical": False,
    },
    {
        "id": "T-3",
        "slot": "drift_fix",
        "audience": "self",
        "prompt": "What drifted?",
        "routing": "state:open_questions",
        "priority": "high",
        "critical": False,
        "trigger": "drift",
    },
    {
        "id": "T-4",
        "slot": "stale_review",
        "audience": "user",
        "prompt": "What changed?",
        "routing": "state:refresh",
        "priority": "normal",
        "critical": False,
        "trigger": "staleness",
    },
]


# ---------------------------------------------------------------------------
# check_triggers — clean tree
# ---------------------------------------------------------------------------


def test_clean_tree_fires_nothing(tmp_path):
    root = _clean_root(tmp_path)
    state = _state(session_count=5, slots=_filled_slots())
    assert check_triggers(root, _CONFIG, state) == []


# ---------------------------------------------------------------------------
# critical_unfilled
# ---------------------------------------------------------------------------


def test_critical_unfilled_fires_per_slot_after_grace(tmp_path):
    root = _clean_root(tmp_path)
    state = _state(session_count=4)  # grace default is 3; 4 > 3
    triggers = check_triggers(root, _CONFIG, state, bank=_BANK)
    fired = [t for t in triggers if t.kind == "critical_unfilled"]
    assert len(fired) == 1  # only "alpha" is critical in _BANK
    assert fired[0].severity == "blocking"
    assert "alpha" in fired[0].message
    assert fired[0].question_ids == ("T-1",)


def test_critical_unfilled_silent_within_grace(tmp_path):
    root = _clean_root(tmp_path)
    state = _state(session_count=3)  # not strictly greater than grace 3
    triggers = check_triggers(root, _CONFIG, state, bank=_BANK)
    assert "critical_unfilled" not in _kinds(triggers)


def test_critical_unfilled_silent_when_filled(tmp_path):
    root = _clean_root(tmp_path)
    state = _state(session_count=10, slots={"alpha": "filled"})
    triggers = check_triggers(root, _CONFIG, state, bank=_BANK)
    assert "critical_unfilled" not in _kinds(triggers)


def test_critical_unfilled_provisional_does_not_count_as_filled(tmp_path):
    root = _clean_root(tmp_path)
    state = _state(session_count=10, slots={"alpha": "provisional"})
    triggers = check_triggers(root, _CONFIG, state, bank=_BANK)
    assert "critical_unfilled" in _kinds(triggers)


# ---------------------------------------------------------------------------
# blocking_open
# ---------------------------------------------------------------------------


def test_blocking_open_fires_with_question_ids(tmp_path):
    root = _clean_root(tmp_path)
    state = _state(slots=_filled_slots(), open_questions=["Q-001", "Q-004"])
    triggers = check_triggers(root, _CONFIG, state)
    fired = [t for t in triggers if t.kind == "blocking_open"]
    assert len(fired) == 1
    assert fired[0].severity == "blocking"
    assert fired[0].question_ids == ("Q-001", "Q-004")
    assert "2 blocking question(s)" in fired[0].message


def test_blocking_open_silent_when_empty(tmp_path):
    root = _clean_root(tmp_path)
    state = _state(slots=_filled_slots())
    assert "blocking_open" not in _kinds(check_triggers(root, _CONFIG, state))


# ---------------------------------------------------------------------------
# drift
# ---------------------------------------------------------------------------


def test_drift_fires_on_doc_findings(tmp_path):
    root = _clean_root(tmp_path)
    _write(root / "docs" / "bare.md", "# No badge, orphan too\n")
    state = _state(slots=_filled_slots())
    fired = [t for t in check_triggers(root, _CONFIG, state) if t.kind == "drift"]
    assert len(fired) == 1
    assert fired[0].severity == "high"
    assert "finding(s)" in fired[0].message


def test_drift_silent_on_clean_docs(tmp_path):
    root = _clean_root(tmp_path)
    state = _state(slots=_filled_slots())
    assert "drift" not in _kinds(check_triggers(root, _CONFIG, state))


# ---------------------------------------------------------------------------
# staleness
# ---------------------------------------------------------------------------


def test_staleness_fires_on_old_session_log(tmp_path):
    root = _clean_root(tmp_path)
    log = root / ".sessions" / "2026-07-02-fresh.md"
    old = time.time() - 30 * 86400  # 30 days > default 14
    os.utime(log, (old, old))
    state = _state(slots=_filled_slots())
    fired = [
        t for t in check_triggers(root, _CONFIG, state) if t.kind == "staleness"
    ]
    assert len(fired) == 1
    assert "days old" in fired[0].message


def test_staleness_fires_when_reconciliation_overdue(tmp_path):
    root = _clean_root(tmp_path)  # fresh log — only the session-count branch
    state = _state(
        slots=_filled_slots(),
        session_count=25,
        last_compaction_session=0,  # 25 - 0 >= default 20
    )
    fired = [
        t for t in check_triggers(root, _CONFIG, state) if t.kind == "staleness"
    ]
    assert len(fired) == 1
    assert "compaction" in fired[0].message


def test_staleness_silent_when_fresh_and_recently_compacted(tmp_path):
    root = _clean_root(tmp_path)
    state = _state(
        slots=_filled_slots(),
        session_count=25,
        last_compaction_session=10,  # 15 < 20
    )
    assert "staleness" not in _kinds(check_triggers(root, _CONFIG, state))


def test_staleness_mtime_branch_silent_without_logs(tmp_path):
    root = _clean_root(tmp_path)
    (root / ".sessions" / "2026-07-02-fresh.md").unlink()
    state = _state(slots=_filled_slots())
    assert "staleness" not in _kinds(check_triggers(root, _CONFIG, state))


# ---------------------------------------------------------------------------
# new_area
# ---------------------------------------------------------------------------


def test_new_area_fires_on_unowned_subdir(tmp_path):
    root = _clean_root(tmp_path)
    _write(root / "docs" / "newarea" / "thing.md", "# Unbadged, unlinked\n")
    state = _state(slots=_filled_slots())
    fired = [
        t for t in check_triggers(root, _CONFIG, state) if t.kind == "new_area"
    ]
    assert len(fired) == 1
    assert "newarea" in fired[0].message


def test_new_area_silent_when_a_file_is_badged(tmp_path):
    root = _clean_root(tmp_path)
    _write(root / "docs" / "area" / "a.md", "# A\n\n> **Status:** `reference`\n")
    _write(root / "docs" / "area" / "b.md", "# B, unbadged\n")
    state = _state(slots=_filled_slots())
    assert "new_area" not in _kinds(check_triggers(root, _CONFIG, state))


def test_new_area_silent_when_reachable_via_readme(tmp_path):
    root = _clean_root(tmp_path)
    _write(
        root / "docs" / "area" / "README.md",
        "# R\n\n> **Status:** `reference`\n\n[c](child.md)\n",
    )
    _write(root / "docs" / "area" / "child.md", "# C\n\n> **Status:** `reference`\n")
    state = _state(slots=_filled_slots())
    assert "new_area" not in _kinds(check_triggers(root, _CONFIG, state))


def test_new_area_skips_absent_docs_root(tmp_path):
    _write(tmp_path / ".sessions" / "2026-07-02-x.md", "# Log\n")
    state = _state(slots=_filled_slots())
    triggers = check_triggers(tmp_path, _CONFIG, state)
    assert "new_area" not in _kinds(triggers)


# ---------------------------------------------------------------------------
# mandatory_questions
# ---------------------------------------------------------------------------


def test_mandatory_questions_empty_without_triggers():
    assert mandatory_questions([], bank=_BANK) == []


def test_mandatory_questions_pulls_by_trigger_field():
    fired = [Trigger("drift", "high", "m", ())]
    ids = [q["id"] for q in mandatory_questions(fired, bank=_BANK)]
    assert ids == ["T-3"]


def test_mandatory_questions_pulls_critical_slot_ids():
    fired = [Trigger("critical_unfilled", "blocking", "alpha unfilled", ("T-1",))]
    ids = [q["id"] for q in mandatory_questions(fired, bank=_BANK)]
    assert ids == ["T-1"]


def test_mandatory_questions_priority_order_and_dedupe():
    fired = [
        Trigger("staleness", "normal", "m", ()),
        Trigger("drift", "high", "m", ()),
        Trigger("critical_unfilled", "blocking", "alpha unfilled", ("T-1",)),
        Trigger("critical_unfilled", "blocking", "alpha again", ("T-1",)),
    ]
    ids = [q["id"] for q in mandatory_questions(fired, bank=_BANK)]
    assert ids == ["T-1", "T-3", "T-4"]  # blocking, high, normal; T-1 once


def test_mandatory_questions_dedupes_trigger_and_slot_pull():
    # Real-bank Q-004 both carries trigger "critical_unfilled" AND is the
    # question a critical_unfilled trigger names — it must appear once.
    fired = [
        Trigger(
            "critical_unfilled",
            "blocking",
            "architecture_layers unfilled",
            ("Q-004",),
        ),
    ]
    questions = mandatory_questions(fired, bank=QUESTIONS)
    assert [q["id"] for q in questions] == ["Q-004"]


# ---------------------------------------------------------------------------
# trigger_block
# ---------------------------------------------------------------------------


def test_trigger_block_empty_without_triggers():
    assert trigger_block([], [], mandate=True) == ""
    assert trigger_block([], [], mandate=False) == ""


def test_trigger_block_mandate_header_and_content():
    fired = [Trigger("drift", "high", "doc hygiene reports 2 finding(s)", ())]
    questions = mandatory_questions(fired, bank=_BANK)
    block = trigger_block(fired, questions, mandate=True)
    assert "MANDATORY" in block
    assert "doc hygiene reports 2 finding(s)" in block
    assert "T-3" in block and "What drifted?" in block


def test_trigger_block_advisory_header():
    fired = [Trigger("staleness", "normal", "memory looks stale", ())]
    block = trigger_block(fired, [], mandate=False)
    assert "MANDATORY" not in block
    assert "advisory" in block.lower()
    assert "memory looks stale" in block


def test_trigger_is_a_named_tuple():
    t = Trigger("drift", "high", "msg", ("Q-011",))
    assert (t.kind, t.severity, t.message, t.question_ids) == (
        "drift",
        "high",
        "msg",
        ("Q-011",),
    )
