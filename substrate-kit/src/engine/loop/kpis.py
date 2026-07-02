"""Workflow KPIs for the self-improving loop (plan section 5, Lane B1).

Deterministic read-only metrics over the state document + sessions directory:
``router_metrics`` measures the question-router's health (slot completeness,
open questions, the assumption-confirmation rate that keeps autonomous runs
honest), ``workflow_kpis`` adds the session/reflection counters, and
``kpi_footer`` renders the one-line 📊 summary the orientation and reports
embed. Pure stdlib; returns data / text, never prints.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _kpi_confirmation_rate(slot_values: dict[str, Any]) -> float:
    """Return confirmed-over-self-answered for the recorded slot values.

    Self-answered slots are those whose ``source`` is ``"assumption"`` or
    starts with ``"confirmed:"`` (a confirmed former assumption). With no
    self-answered slots there is nothing to confirm — the rate is 1.0.
    """
    confirmed = 0
    self_answered = 0
    if not isinstance(slot_values, dict):
        return 1.0
    for entry in slot_values.values():
        if not isinstance(entry, dict):
            # A hand-corrupted state.json can carry a non-dict slot value; skip
            # it rather than raising (the kit's read-side fail-open contract —
            # a KPI read must never brick session-close / maintain). Matches the
            # non-dict guards in reflections / episodes / maintenance.
            continue
        source = str(entry.get("source", ""))
        if source.startswith("confirmed:"):
            confirmed += 1
            self_answered += 1
        elif source == "assumption":
            self_answered += 1
    if self_answered == 0:
        return 1.0
    return confirmed / self_answered


def router_metrics(state: dict[str, Any]) -> dict[str, Any]:
    """Return the question-router health metrics for one state document.

    ``completeness_pct`` counts ``filled`` slots only — ``provisional`` and
    ``partial`` answers never inflate completeness (the anti-gaming floor's
    KPI mirror). With no recorded slots completeness is 0.0.
    """
    slots = state.get("slots", {})
    statuses = list(slots.values())
    total = len(statuses)
    filled = statuses.count("filled")
    provisional = statuses.count("provisional")
    completeness = round(100.0 * filled / total, 1) if total else 0.0
    return {
        "slots_total": total,
        "slots_filled": filled,
        "slots_provisional": provisional,
        "completeness_pct": completeness,
        "open_questions": len(state.get("open_questions", [])),
        "assumption_confirmation_rate": _kpi_confirmation_rate(
            state.get("slot_values", {}),
        ),
        "quiet_sessions": int(state.get("quiet_sessions", 0)),
        "session_count": int(state.get("session_count", 0)),
    }


def workflow_kpis(state: dict[str, Any], sessions_dir: Path) -> dict[str, Any]:
    """Return the full workflow KPI record: router metrics + session counters.

    ``sessions_logged`` counts ``*.md`` logs under ``sessions_dir`` (README
    excluded, 0 when the directory is absent); ``reflections_active`` reads
    the state's reflection-buffer counter.
    """
    kpis = router_metrics(state)
    logged = 0
    if sessions_dir.is_dir():
        logged = sum(1 for p in sessions_dir.glob("*.md") if p.name != "README.md")
    buffer = state.get("reflection_buffer", {})
    kpis["sessions_logged"] = logged
    kpis["reflections_active"] = int(buffer.get("active_count", 0))
    kpis["stage"] = state.get("stage")
    kpis["mode"] = state.get("mode")
    return kpis


def kpi_footer(kpis: dict[str, Any]) -> str:
    """Render the one-line 📊 KPI summary for orientation blocks and reports.

    Router metrics always appear; the workflow extras (logged sessions,
    active lessons, mode, stage) appear when present in ``kpis``.
    """
    completeness = float(kpis.get("completeness_pct", 0.0))
    parts = [
        f"completeness {completeness:.0f}%",
        f"open-Q {kpis.get('open_questions', 0)}",
        f"sessions {kpis.get('session_count', 0)}",
        f"quiet {kpis.get('quiet_sessions', 0)}",
    ]
    if "sessions_logged" in kpis:
        parts.append(f"logged {kpis['sessions_logged']}")
    if "reflections_active" in kpis:
        parts.append(f"lessons {kpis['reflections_active']}")
    if kpis.get("mode") is not None:
        parts.append(f"mode {kpis['mode']}")
    if kpis.get("stage") is not None:
        parts.append(f"stage {kpis['stage']}")
    return "📊 substrate: " + " · ".join(parts)
