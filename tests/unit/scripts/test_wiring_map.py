"""Tests for ``scripts/wiring_map.py`` — the EventBus emit↔subscribe map.

The pure analysis core (``analyze_sources``) is exercised on synthetic
sources so it runs without the repo; a small smoke test then confirms the
real ``audit.action_recorded`` emitter→subscriber join — the canonical
edge invisible to both CodeGraph and Grimp — resolves on the live tree.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "wiring_map.py"


@pytest.fixture(scope="module")
def wm():
    spec = importlib.util.spec_from_file_location("wiring_map_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Synthetic source fixtures
# ---------------------------------------------------------------------------

_EMITTER = """
from core.events import bus

EVT_THING = "domain.thing"


async def fire():
    await bus.emit(EVT_THING, x=1)
    await bus.emit("domain.literal", y=2)
    await bus.emit("domain.uncatalogued", z=3)
    await bus.emit(some_dynamic_name, q=4)
"""

_SUBSCRIBER = """
from core.events import bus as _event_bus

EVT_THING = "domain.thing"


def register():
    _event_bus.on(EVT_THING, _on_thing)
    _event_bus.on("domain.literal", handlers.on_literal)
    _event_bus.on("domain.orphan", _on_orphan)
"""

_CATALOGUE = """
EVT_THING = "domain.thing"
KNOWN_EVENTS = frozenset(
    {
        EVT_THING,
        "domain.literal",
        "domain.uncatalogued_is_missing_on_purpose",
        "domain.orphan",
    }
)
"""


def _sources() -> dict[str, str]:
    return {
        "disbot/services/emitter.py": _EMITTER,
        "disbot/services/subscriber.py": _SUBSCRIBER,
        "disbot/core/events_catalogue.py": _CATALOGUE,
    }


# ---------------------------------------------------------------------------
# Constant + callsite extraction
# ---------------------------------------------------------------------------


def test_extract_event_constants(wm):
    consts = wm.extract_event_constants(
        'EVT_A = "x.a"\nEVT_B: str = "x.b"\nOTHER = "nope"\nevt_low = "x.c"',
    )
    assert consts == {"EVT_A": "x.a", "EVT_B": "x.b"}


def test_callsites_resolve_constant_literal_and_alias(wm):
    consts = {"EVT_THING": "domain.thing"}
    sites = wm.extract_callsites(_EMITTER, "emitter.py", consts)
    events = {(s.kind, s.event) for s in sites}
    assert ("emit", "domain.thing") in events  # via EVT_ constant
    assert ("emit", "domain.literal") in events  # via string literal
    # The dynamic name is unresolved (None), never guessed.
    assert any(s.event is None and s.raw_event == "some_dynamic_name" for s in sites)


def test_subscribe_handler_names(wm):
    consts = {"EVT_THING": "domain.thing"}
    sites = wm.extract_callsites(_SUBSCRIBER, "sub.py", consts)
    on = {s.event: s.handler for s in sites if s.kind == "on"}
    assert on["domain.thing"] == "_on_thing"  # Name
    assert on["domain.literal"] == "on_literal"  # Attribute → attr
    assert on["domain.orphan"] == "_on_orphan"


# ---------------------------------------------------------------------------
# analyze_sources — the join + queries
# ---------------------------------------------------------------------------


def test_join_emitter_and_subscriber_by_event(wm):
    m = wm.analyze_sources(_sources())
    thing = m.events["domain.thing"]
    assert [c.path for c in thing.emitters] == ["disbot/services/emitter.py"]
    assert [c.path for c in thing.subscribers] == ["disbot/services/subscriber.py"]
    assert thing.subscribers[0].handler == "_on_thing"


def test_dead_subscriber_detected(wm):
    m = wm.analyze_sources(_sources())
    dead = {c.event for c in m.dead_subscribers()}
    # "domain.orphan" is subscribed but never emitted.
    assert "domain.orphan" in dead
    # "domain.thing" / "domain.literal" have emitters → not dead.
    assert "domain.thing" not in dead


def test_catalogue_drift_detected(wm):
    m = wm.analyze_sources(_sources())
    drift = m.uncatalogued()
    # Emitted but absent from KNOWN_EVENTS.
    assert "domain.uncatalogued" in drift
    # Catalogued ones are not drift.
    assert "domain.thing" not in drift
    assert "domain.literal" not in drift


def test_unresolved_emit_tracked_not_dropped(wm):
    m = wm.analyze_sources(_sources())
    assert any(
        c.kind == "emit" and c.raw_event == "some_dynamic_name" for c in m.unresolved
    )


def test_catalogued_flag(wm):
    m = wm.analyze_sources(_sources())
    assert m.events["domain.thing"].catalogued is True
    assert m.events["domain.uncatalogued"].catalogued is False


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def test_render_shows_join_and_findings(wm):
    m = wm.analyze_sources(_sources())
    out = wm.render_map(m)
    assert "domain.thing" in out
    assert "emit →" in out and "on   →" in out
    assert "catalogue drift" in out  # the uncatalogued emit
    assert "possible dead subscriber" in out  # advisory framing


# ---------------------------------------------------------------------------
# Real-repo smoke — the both-tools-blind edge
# ---------------------------------------------------------------------------


def test_real_audit_action_recorded_join(wm):
    m = wm.analyze_repo()
    assert "audit.action_recorded" in m.events
    w = m.events["audit.action_recorded"]
    assert any(c.path.endswith("services/audit_events.py") for c in w.emitters)
    assert any(
        c.path.endswith("services/server_logging.py") for c in w.subscribers
    ), "server_logging must resolve as the subscriber even though it never imports the emitter"


def test_real_repo_has_no_catalogue_drift(wm):
    """Every emitted/subscribed event resolves into KNOWN_EVENTS.

    Mirrors the catalogue's own purpose; a new emit of an uncatalogued
    event name (a typo or a forgotten catalogue entry) fails here.
    """
    m = wm.analyze_repo()
    assert m.uncatalogued() == [], (
        "uncatalogued events — add them to core/events_catalogue.KNOWN_EVENTS: "
        f"{m.uncatalogued()}"
    )
