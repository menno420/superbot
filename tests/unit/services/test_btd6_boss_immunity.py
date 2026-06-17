"""The deterministic boss damage-immunity floor (BUG-0009 wrong-assembly class).

``deterministic_boss_immunity_reply`` owns three shapes off ``bosses[].immune_to``
so the model can never mis-state a boss's immunities (claim one it lacks, omit one
it has): a single boss's immunity list, a yes/no for one boss + damage, and the
cross-boss roster. Pinned to the committed ``bosses.json`` (Blastapopoulos is the
fire/energy/frigid/plasma-immune boss; most bosses have no immunities).
"""

from __future__ import annotations

import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_context_service  # noqa: E402

reply = btd6_context_service.deterministic_boss_immunity_reply


def test_single_boss_immunity_list():
    out = reply("what is Blastapopoulos immune to")
    assert out is not None and "Blastapopoulos is immune to" in out
    for dmg in ("Energy", "Fire", "Frigid", "Plasma"):
        assert dmg in out


def test_single_boss_with_no_immunities_is_answered_honestly():
    out = reply("what is Lych immune to")
    assert out is not None and "no damage-type immunities" in out


def test_single_boss_yes_no_for_a_named_damage():
    yes = reply("is Blastapopoulos immune to fire")
    assert yes is not None and "is immune to" in yes and "Fire" in yes
    no = reply("is Lych immune to fire")
    assert no is not None and "not" in no and "Fire" in no


def test_cross_boss_roster():
    out = reply("which bosses are immune to fire")
    assert out is not None and "bosses immune to Fire" in out
    assert "Blastapopoulos" in out
    # Dreadbloon resists Cold/Energy/Sharp/Shatter, not Fire — excluded.
    assert "Dreadbloon" not in out


def test_cross_boss_roster_empty_is_honest():
    out = reply("which bosses are immune to acid")
    assert out is not None and "No BTD6 boss is immune to Acid" in out


def test_defers_without_an_immunity_cue():
    # A boss HP question is not an immunity question — reaches the model.
    assert reply("how much health does Lych have per tier") is None
    assert reply("list all bosses") is None


def test_defers_for_a_bloon_immunity_question():
    # The bloon immunity roster (bloon subject) owns this — the boss floor must
    # not fire on a bloon, even though "immune" is present.
    assert reply("which bloons are immune to sharp") is None
    assert reply("is the lead bloon immune to sharp") is None
