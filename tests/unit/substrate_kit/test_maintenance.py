"""Tests for the loop's maintenance actuators (Lane B3).

Covers the compaction cadence math, the State Delta render (determinism,
truncation, empty-section skipping, active-lesson filtering), the
compaction write + counter update, escalate/resolve idempotency, the
promotion downgrade log entry, and the maintenance-report composition.
"""

import datetime
from pathlib import Path

from engine.checks.check_docs import Finding
from engine.lib.config import Config
from engine.lib.state import JsonStateBackend, default_state
from engine.loop.kpis import kpi_footer
from engine.loop.maintenance import (
    compaction_due,
    downgrade_promotion,
    escalate_blocking,
    maintenance_report,
    resolve_open_question,
    run_compaction,
    state_delta,
)
from engine.loop.triggers import Trigger


def _backend(tmp_path: Path, **over) -> JsonStateBackend:
    backend = JsonStateBackend(tmp_path / ".substrate" / "state.json")
    state = default_state("pid")
    state.update(over)
    for key, value in state.items():
        backend.set(key, value)
    return backend


def _state(**over) -> dict:
    state = default_state("pid")
    state.update(over)
    return state


# ---------------------------------------------------------------------------
# compaction_due
# ---------------------------------------------------------------------------


def test_compaction_not_due_inside_window():
    state = _state(session_count=19, last_compaction_session=0)
    assert not compaction_due(state, {"compaction_sessions": 20})


def test_compaction_due_at_cadence_boundary():
    state = _state(session_count=20, last_compaction_session=0)
    assert compaction_due(state, {"compaction_sessions": 20})


def test_compaction_counts_from_last_compaction():
    state = _state(session_count=25, last_compaction_session=20)
    assert not compaction_due(state, {"compaction_sessions": 20})


def test_compaction_defaults_on_empty_inputs():
    assert not compaction_due({}, {})
    assert compaction_due({"session_count": 20}, {})


# ---------------------------------------------------------------------------
# state_delta
# ---------------------------------------------------------------------------


def test_state_delta_counters_and_slot_table():
    state = _state(
        session_count=8,
        quiet_sessions=3,
        slots={"project_name": "filled", "verify_command": "provisional"},
        slot_values={
            "project_name": {"value": "superbot", "source": "user"},
            "verify_command": {"value": "pytest -q", "source": "assumption"},
        },
        open_questions=["Q-001"],
    )
    delta = state_delta(state, [])
    assert "# State Delta — session 8" in delta
    assert "mode: guided" in delta
    assert "stage: integration" in delta
    assert "quiet: 3" in delta
    assert "| project_name | filled | superbot |" in delta
    assert "| verify_command | provisional | pytest -q |" in delta
    assert "- Q-001" in delta


def test_state_delta_truncates_values_to_80_chars():
    state = _state(
        slots={"a": "filled"},
        slot_values={"a": {"value": "x" * 200, "source": "user"}},
    )
    delta = state_delta(state, [])
    row = next(line for line in delta.splitlines() if line.startswith("| a |"))
    assert "x" * 80 in row
    assert "x" * 81 not in row


def test_state_delta_is_deterministic():
    state = _state(
        session_count=5,
        slots={"b": "provisional", "a": "filled"},
        slot_values={"a": {"value": "1"}, "b": {"value": "2"}},
        open_questions=["Q-004"],
    )
    reflections = [{"id": "R-0001", "lesson": "batch pushes", "status": "confirmed"}]
    assert state_delta(state, reflections) == state_delta(state, reflections)


def test_state_delta_skips_empty_sections():
    delta = state_delta(_state(), [])
    assert "## Slots" not in delta
    assert "## Open questions" not in delta
    assert "## Active lessons" not in delta


def test_state_delta_renders_active_lessons_only():
    reflections = [
        {"id": "R-0001", "lesson": "old", "superseded_by": "R-0002"},
        {"id": "R-0002", "lesson": "new", "status": "confirmed"},
    ]
    delta = state_delta(_state(), reflections)
    assert "[R-0002] new" in delta
    assert "[R-0001]" not in delta


def test_state_delta_renders_unsuperseded_entry():
    reflections = [{"id": "R-0001", "lesson": "still active"}]
    delta = state_delta(_state(), reflections)
    assert "[R-0001] still active" in delta


# ---------------------------------------------------------------------------
# run_compaction
# ---------------------------------------------------------------------------


def test_run_compaction_writes_delta_and_stamps_counter(tmp_path):
    backend = _backend(
        tmp_path,
        session_count=20,
        slots={"project_name": "filled"},
        slot_values={"project_name": {"value": "superbot", "source": "user"}},
    )
    config = Config(state_dir=".substrate")
    path = run_compaction(tmp_path, config, backend)
    assert path == tmp_path / ".substrate" / "state-delta-20.md"
    text = path.read_text(encoding="utf-8")
    assert "# State Delta — session 20" in text
    assert "| project_name | filled | superbot |" in text
    assert backend.get("last_compaction_session") == 20
    assert not compaction_due(backend.data, config.cadence)


def test_run_compaction_includes_reflection_buffer(tmp_path):
    backend = _backend(tmp_path, session_count=3)
    (tmp_path / ".substrate").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".substrate" / "reflections.json").write_text(
        '[{"id": "R-0001", "lesson": "push in batches", "status": "confirmed"}]',
        encoding="utf-8",
    )
    path = run_compaction(tmp_path, Config(state_dir=".substrate"), backend)
    assert "[R-0001] push in batches" in path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# escalate / resolve open questions
# ---------------------------------------------------------------------------


def test_escalate_blocking_is_idempotent(tmp_path):
    backend = _backend(tmp_path)
    assert escalate_blocking(backend, "Q-001") is True
    assert escalate_blocking(backend, "Q-001") is False
    assert backend.get("open_questions") == ["Q-001"]


def test_resolve_open_question_removes_once(tmp_path):
    backend = _backend(tmp_path, open_questions=["Q-001", "Q-004"])
    assert resolve_open_question(backend, "Q-001") is True
    assert backend.get("open_questions") == ["Q-004"]
    assert resolve_open_question(backend, "Q-001") is False


# ---------------------------------------------------------------------------
# downgrade_promotion
# ---------------------------------------------------------------------------


def test_downgrade_promotion_sets_rights_and_logs(tmp_path):
    backend = _backend(tmp_path, promotion_rights="promote")
    downgrade_promotion(backend, reason="review fail on slot 'x'")
    assert backend.get("promotion_rights") == "propose"
    entry = backend.get("review_log")[-1]
    assert entry["event"] == "promotion_downgrade"
    assert entry["reason"] == "review fail on slot 'x'"
    assert entry["date"] == datetime.date.today().isoformat()


# ---------------------------------------------------------------------------
# maintenance_report
# ---------------------------------------------------------------------------


def test_report_skips_sections_with_empty_inputs(tmp_path):
    backend = _backend(tmp_path, session_count=2)
    report = maintenance_report(
        tmp_path,
        Config(),
        backend,
        triggers=[],
        economy_findings=[],
        ledger_findings=[],
        kpis={},
    )
    assert "# Maintenance report — session 2" in report
    assert "## Triggers" not in report
    assert "## Economy findings" not in report
    assert "## Ledger findings" not in report
    assert "📊" not in report


def test_report_composes_all_sections(tmp_path):
    backend = _backend(tmp_path, session_count=20)
    (tmp_path / ".substrate" / "review").mkdir(parents=True)
    (tmp_path / ".substrate" / "review" / "payload-a.json").write_text(
        "{}",
        encoding="utf-8",
    )
    triggers = [Trigger("drift", "high", "doc hygiene reports 2 finding(s)", ())]
    ledger = [Finding("decisions.md", "ledger", "duplicate id D-0002")]
    report = maintenance_report(
        tmp_path,
        Config(state_dir=".substrate"),
        backend,
        triggers=triggers,
        economy_findings=["plans/old.md: over_cap"],
        ledger_findings=ledger,
        kpis={"completeness_pct": 50.0, "open_questions": 1},
    )
    assert "## Triggers" in report
    assert "- [high] drift: doc hygiene reports 2 finding(s)" in report
    assert "## Economy findings" in report
    assert "- plans/old.md: over_cap" in report
    assert "## Ledger findings" in report
    assert "- decisions.md: [ledger] duplicate id D-0002" in report
    assert "## Maintenance" in report
    assert "compaction due" in report  # 20 sessions since compaction
    assert "1 review payload(s) awaiting a reviewer" in report
    last_line = report.rstrip().splitlines()[-1]
    assert last_line.startswith("📊 substrate:")  # kpi footer closes the report
    assert "open-Q 1" in last_line


def test_report_footer_uses_kpi_footer_format(tmp_path):
    backend = _backend(tmp_path)
    report = maintenance_report(
        tmp_path,
        Config(),
        backend,
        triggers=[],
        economy_findings=[],
        ledger_findings=[],
        kpis={"completeness_pct": 75.0, "open_questions": 0},
    )
    assert "📊 substrate: completeness 75%" in report


def test_report_footer_uses_kpi_footer(tmp_path):
    """The report footer is the canonical kpi_footer line (top-level import)."""
    backend = _backend(tmp_path)
    report = maintenance_report(
        tmp_path,
        Config(),
        backend,
        triggers=[],
        economy_findings=[],
        ledger_findings=[],
        kpis={"open_questions": 1},
    )
    assert kpi_footer({"open_questions": 1}) in report
