"""Invariant: every ``EffectiveStats`` field is *read* by some game consumer.

The Q-0089 idea raised in the #1504 (fishing-gear stats) session log: the
cross-game :class:`utils.equipment.EffectiveStats` block is the single
"how strong is this character?" read model, and each game folds the subset it
cares about into its own math (``mining_power``/``light_radius``/``depth_access``
→ mining, ``damage``/``defense``/``max_health`` → the duel, ``fishing_power``/
``bite_luck`` → the cast). Nothing asserted that a *new* field actually gets wired
into a consumer — so the "added the stat, summed it, labelled it, but forgot the
knob" half-ship could ship silently.

Building this guard surfaced a real latent bug: ``light_radius`` and ``luck`` *were*
**dead stats** — defined, summed, and labelled, but read by no game. The owner chose
to wire them (BUG-0026), so they are now consumed (``light_radius`` → the fog-of-war
window in ``grid.reveal_radius``; ``luck`` → rare-find weighting in
``exploration.resolve``) and the allowlist below is **empty**. The second test keeps
the allowlist honest, so the moment a *new* dead stat ships its allowlist entry must
go (or this test fails).

AST-scoped to ``disbot/`` so it runs in well under a second and needs no live
bot / DB.

UNVERIFIED convenience guard (Q-0105, 2026-06-27): "consumed" means an attribute
read ``<expr>.<field>`` somewhere in ``disbot/`` outside the definition module and
the generic label/glyph/``__add__`` plumbing. This is name-based, so it is
*inclusive* (a coincidental ``.<field>`` on another object would also count as
consumed) — acceptable for a coverage floor whose only job is to catch a field
read by *nothing*. If it proves noisy or unreliable across multiple sessions,
broaden the consumer scan or delete this guard rather than working around it.
"""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from utils.equipment import EffectiveStats

_DISBOT = Path(__file__).resolve().parents[3] / "disbot"
_DEFINITION = _DISBOT / "utils" / "equipment.py"

# Stats that are defined on EffectiveStats but not yet read by any game's
# consumption path. EMPTY now that light_radius + luck are wired (BUG-0026 FIXED,
# 2026-06-27): light_radius → grid.reveal_radius (the fog-of-war window widens with
# a brighter light), luck → exploration rare-find weighting. REMOVE a name here the
# moment a consumer reads it (the honesty test below fails closed otherwise);
# adding a NEW name requires a docs/health/bug-book.md entry.
_UNWIRED_STATS: frozenset[str] = frozenset()


def _stat_field_names() -> set[str]:
    return {f.name for f in fields(EffectiveStats)}


def _consumed_field_names() -> set[str]:
    """Every EffectiveStats field name read as ``<expr>.<field>`` in a `disbot/`
    consumer — excluding the definition module (where the fields are declared,
    summed in ``__add__``, and listed in the label/glyph maps via ``getattr``)."""
    field_names = _stat_field_names()
    consumed: set[str] = set()
    for path in _DISBOT.rglob("*.py"):
        if path == _DEFINITION:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in field_names:
                consumed.add(node.attr)
    return consumed


def test_every_wired_stat_is_consumed_by_a_game():
    """Each EffectiveStats field is read by a consumer, or is on the documented
    unwired allowlist (with a bug-book entry)."""
    consumed = _consumed_field_names()
    dead = _stat_field_names() - consumed - _UNWIRED_STATS
    assert not dead, (
        f"EffectiveStats field(s) {sorted(dead)} are defined but read by no "
        f"`disbot/` consumer — wire them into a game's stat math, or add them to "
        f"_UNWIRED_STATS with a docs/health/bug-book.md entry."
    )


def test_unwired_allowlist_stays_honest():
    """An allowlisted stat that has *gained* a consumer must leave the allowlist —
    so the moment light_radius/luck are wired, this fails until the list is pruned."""
    consumed = _consumed_field_names()
    wired_but_listed = _UNWIRED_STATS & consumed
    assert not wired_but_listed, (
        f"{sorted(wired_but_listed)} is in _UNWIRED_STATS but now has a consumer — "
        f"remove it from the allowlist (the dead-stat bug is fixed)."
    )


def test_unwired_allowlist_only_names_real_fields():
    """Guard the guard: the allowlist can't drift to a non-existent field name."""
    assert _UNWIRED_STATS <= _stat_field_names()
