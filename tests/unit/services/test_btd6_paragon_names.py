"""BTD6 paragon names are grounded (fetched from bloonswiki's btd6_paragons).

The per-tower stats files carried ``paragon_cost`` but not the paragon's
name, because ``fetch_bloonswiki.py`` only queried the ``cost`` column.
The bot therefore answered "list the paragons" from memory and
hallucinated names (and paragons for towers that have none). These tests
pin that the 13 real paragons now carry their verified name end-to-end:
data file -> btd6_stats_service -> superlative ranking -> grounding line.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import (  # noqa: E402
    btd6_context_service,
    btd6_stats_service,
    btd6_superlative_service,
)

_STATS = _DISBOT / "data" / "btd6" / "stats"


def test_stats_service_loads_paragon_name():
    stats = btd6_stats_service.get_tower_stats("dart_monkey")
    assert stats is not None
    assert stats.paragon_name == "Apex Plasma Master"
    assert stats.paragon_cost == 150000


def test_every_paragon_cost_tower_has_a_name():
    """Data integrity: each of the towers with a paragon_cost carries the
    verified paragon_name (and towers without a paragon claim neither).
    """
    named = 0
    for f in _STATS.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("paragon_cost"):
            assert d.get("paragon_name"), f"{f.name} has paragon_cost but no name"
            named += 1
        else:
            assert not d.get("paragon_name"), f"{f.name} names a non-existent paragon"
    # BTD6 has exactly 13 monkey paragons.
    assert named == 13


def test_super_monkey_has_no_paragon():
    """Refutes the model's hallucinated 'Super Monkey Paragon' — there is
    no Super Monkey paragon in the data.
    """
    stats = btd6_stats_service.get_tower_stats("super_monkey")
    assert stats is not None
    assert stats.paragon_cost is None
    assert stats.paragon_name is None


def test_superlative_paragon_rows_carry_real_names():
    rows = btd6_superlative_service.rank("paragon_cost", limit=25)
    assert len(rows) == 13
    whats = " | ".join(h.what for h in rows)
    assert "Apex Plasma Master" in whats
    assert "Goliath Doomship" in whats  # priciest (Monkey Ace, 900k)
    # The tower name is still present so "X Paragon" phrasing keeps working.
    assert all("Paragon" in h.what for h in rows)


def test_render_paragon_grounding_line_names_the_paragon():
    lines = btd6_context_service._render_paragon("dart_monkey", "Dart Monkey")
    # First line still names the paragon + Medium cost (unchanged contract);
    # combat-stat lines now follow it (see test_btd6_paragon_stats.py).
    assert "btd6_paragon" in lines[0]
    assert "Apex Plasma Master" in lines[0]
    assert "150000" in lines[0]
    assert len(lines) >= 1


def test_render_paragon_returns_nothing_for_non_paragon_tower():
    assert btd6_context_service._render_paragon("super_monkey", "Super Monkey") == []
