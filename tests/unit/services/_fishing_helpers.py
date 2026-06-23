"""Shared stubs for the fishing-workflow service tests.

`services.fishing_workflow.roll_catch` is patched in ~17 places across
`test_fishing_workflow.py` and `test_fishing_workflow_bait.py`. Each patch has to
mirror `roll_catch`'s exact signature, so every signature change (the `venue=`
kwarg added with the deepwater venue, the weather ambient added with the daily
forecast) used to mean editing every call site by hand. These stubs put that
signature in **one** place: a future change is a single edit here.

Import-style helpers (the dir is a package — `tests/unit/services/__init__.py`),
not fixtures, because the tests need a *callable* to hand to `patch.object`.
"""

from __future__ import annotations

import random

from utils.fishing.fish import Catch, FishSpecies

#: The canonical caught-fish sentinel both test files assert against.
CATCH = Catch(species=FishSpecies("trout", 8, "🐠"))


def fake_roll_catch(catch: Catch | None = CATCH):
    """A ``roll_catch`` stub that ignores its inputs and returns *catch*.

    Pass ``catch=None`` for the empty-catalog path. Mirrors the real signature
    so a signature change updates only this helper, not every call site.
    """

    def _roll(
        level: int,
        rng: random.Random | None = None,
        *,
        rarity_pull: float = 1.0,
        venue: str = "shore",
    ) -> Catch | None:
        return catch

    return _roll


def recording_roll_catch(record: dict, catch: Catch | None = CATCH):
    """Like :func:`fake_roll_catch`, but records the call's inputs into *record*.

    Captures ``level`` / ``rarity_pull`` / ``venue`` of the (last) call so a test
    can assert which level gated the roll or which rarity pull / venue reached it.
    """

    def _roll(
        level: int,
        rng: random.Random | None = None,
        *,
        rarity_pull: float = 1.0,
        venue: str = "shore",
    ) -> Catch | None:
        record["level"] = level
        record["rarity_pull"] = rarity_pull
        record["venue"] = venue
        return catch

    return _roll
