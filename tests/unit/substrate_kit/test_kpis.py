"""Tests for the loop's workflow KPIs (Lane B1).

Covers the router metrics math (completeness counts filled only, the
assumption-confirmation-rate edge cases), the workflow KPI extras, and the
one-line 📊 footer.
"""

from pathlib import Path

from engine.loop.kpis import kpi_footer, router_metrics, workflow_kpis


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _state(**over) -> dict:
    base = {
        "mode": "guided",
        "stage": "integration",
        "session_count": 7,
        "quiet_sessions": 2,
        "slots": {},
        "slot_values": {},
        "open_questions": [],
        "reflection_buffer": {"active_count": 0, "last_mined": None},
    }
    base.update(over)
    return base


# ---------------------------------------------------------------------------
# router_metrics
# ---------------------------------------------------------------------------


def test_router_metrics_counts_and_completeness():
    state = _state(
        slots={"a": "filled", "b": "provisional", "c": "partial", "d": "filled"},
        open_questions=["Q-001"],
    )
    m = router_metrics(state)
    assert m["slots_total"] == 4
    assert m["slots_filled"] == 2
    assert m["slots_provisional"] == 1
    assert m["completeness_pct"] == 50.0  # filled only — provisional/partial excluded
    assert m["open_questions"] == 1
    assert m["quiet_sessions"] == 2
    assert m["session_count"] == 7


def test_router_metrics_empty_state():
    m = router_metrics({})
    assert m["slots_total"] == 0
    assert m["slots_filled"] == 0
    assert m["slots_provisional"] == 0
    assert m["completeness_pct"] == 0.0
    assert m["open_questions"] == 0
    assert m["assumption_confirmation_rate"] == 1.0
    assert m["quiet_sessions"] == 0
    assert m["session_count"] == 0


def test_confirmation_rate_confirmed_over_self_answered():
    state = _state(
        slots={"a": "filled", "b": "provisional", "c": "provisional"},
        slot_values={
            "a": {"value": "x", "source": "confirmed:user"},
            "b": {"value": "y", "source": "assumption"},
            "c": {"value": "z", "source": "assumption"},
        },
    )
    m = router_metrics(state)
    assert m["assumption_confirmation_rate"] == 1 / 3


def test_confirmation_rate_one_when_no_self_answers():
    state = _state(
        slots={"a": "filled"},
        slot_values={"a": {"value": "x", "source": "user"}},
    )
    assert router_metrics(state)["assumption_confirmation_rate"] == 1.0


def test_confirmation_rate_all_confirmed():
    state = _state(
        slot_values={
            "a": {"source": "confirmed:user"},
            "b": {"source": "confirmed:reviewer:gpt"},
        },
    )
    assert router_metrics(state)["assumption_confirmation_rate"] == 1.0


def test_confirmation_rate_zero_when_all_unconfirmed():
    state = _state(slot_values={"a": {"source": "assumption"}})
    assert router_metrics(state)["assumption_confirmation_rate"] == 0.0


# ---------------------------------------------------------------------------
# workflow_kpis
# ---------------------------------------------------------------------------


def test_workflow_kpis_adds_session_and_reflection_counters(tmp_path):
    sessions = tmp_path / ".sessions"
    _write(sessions / "README.md", "convention doc\n")
    _write(sessions / "2026-07-01-a.md", "# A\n")
    _write(sessions / "2026-07-02-b.md", "# B\n")
    state = _state(reflection_buffer={"active_count": 3, "last_mined": None})
    k = workflow_kpis(state, sessions)
    assert k["sessions_logged"] == 2  # README excluded
    assert k["reflections_active"] == 3
    assert k["stage"] == "integration"
    assert k["mode"] == "guided"
    assert k["slots_total"] == 0  # router metrics included


def test_workflow_kpis_absent_sessions_dir(tmp_path):
    k = workflow_kpis(_state(), tmp_path / "nope")
    assert k["sessions_logged"] == 0
    assert k["reflections_active"] == 0


# ---------------------------------------------------------------------------
# kpi_footer
# ---------------------------------------------------------------------------


def test_kpi_footer_starts_with_bar_chart_marker():
    line = kpi_footer(router_metrics(_state()))
    assert line.startswith("📊 substrate:")
    assert "\n" not in line


def test_kpi_footer_router_metrics_content():
    state = _state(slots={"a": "filled", "b": "provisional"}, open_questions=["Q"])
    line = kpi_footer(router_metrics(state))
    assert "completeness 50%" in line
    assert "open-Q 1" in line
    assert "sessions 7" in line
    assert "quiet 2" in line
    assert "mode" not in line  # workflow extras absent from router metrics


def test_kpi_footer_includes_workflow_extras(tmp_path):
    sessions = tmp_path / ".sessions"
    _write(sessions / "2026-07-01-a.md", "# A\n")
    state = _state(reflection_buffer={"active_count": 4, "last_mined": None})
    line = kpi_footer(workflow_kpis(state, sessions))
    assert "logged 1" in line
    assert "lessons 4" in line
    assert "mode guided" in line
    assert "stage integration" in line
