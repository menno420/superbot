"""BTD6 live-events browser: empty-state control behaviour.

Regression for "the current race button does nothing": when a kind has no
stored events, the event-select must be a *disabled*, clearly-empty control
rather than an enabled dropdown whose only option silently defers on click.
"""

from __future__ import annotations

from types import SimpleNamespace

from views.btd6.live_events_view import _EventSelect


def _vm(items):
    return SimpleNamespace(kind="race", entity_kind="btd6_race", items=tuple(items))


def _item(name="Reversed Loop", key="r1"):
    return SimpleNamespace(
        name=name,
        entity_key=key,
        window=SimpleNamespace(state="active", human="ends in 2h"),
    )


def test_event_select_disabled_when_no_events():
    sel = _EventSelect(_vm([]))
    assert sel.disabled is True
    assert [o.value for o in sel.options] == ["__none__"]
    assert "check back" in (sel.placeholder or "").lower()


def test_event_select_enabled_when_events_present():
    sel = _EventSelect(_vm([_item(), _item("Other Race", "r2")]))
    assert sel.disabled is False
    assert {o.value for o in sel.options} == {"r1", "r2"}
    assert "pick an event" in (sel.placeholder or "").lower()
