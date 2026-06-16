"""Round ``common_threats`` must not claim a modifier no group actually has.

The ``summary`` / ``danger`` / ``common_threats`` fields of ``rounds.json`` (and
its ABR sidecar) are *curated* prose — ``fetch_bloonswiki.py`` preserves them
across regeneration while re-deriving ``groups``/``rbe`` from the dump. That
split is convenient but means a curator can type a threat the composition does
not support, and nothing catches it: round 63 shipped ``common_threats =
["Ceramic", "Camo Lead"]`` even though its groups are 75 plain Lead + 122 plain
Ceramic with no camo modifier anywhere (the live-tested bug this guards).

A bloon's *modifiers* (camo / fortified / regrow) are ground truth in the group
data. So a structured threat token that names one of those modifier words must
be backed by at least one group on that round actually carrying it. We check the
structured ``common_threats`` only — the free-form ``summary`` may legitimately
*negate* ("no camo this round"), so a bare word-match there would false-positive.

Provenance: added 2026-06-15 alongside the round-63 data fix. Verifiable (it
recomputes from the same JSON the bot loads). Delete it if it ever proves
unreliable across multiple sessions — but a green here means no round's
common_threats over-claims a bloon modifier.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DATA = _REPO_ROOT / "disbot" / "data" / "btd6"

# The three bloon modifiers the group data records. A threat token naming one of
# these (e.g. "Camo Lead", "Fortified MOAB") asserts the round contains a bloon
# carrying that modifier — so a matching group must exist.
_MODIFIERS = ("camo", "fortified", "regrow")


def _round_files() -> list[Path]:
    return [p for p in (_DATA / "rounds.json", _DATA / "abr_rounds.json") if p.exists()]


def _present_modifiers(groups: list[dict]) -> set[str]:
    present: set[str] = set()
    for group in groups:
        for mod in group.get("modifiers", ()) or ():
            present.add(str(mod).lower())
    return present


@pytest.mark.parametrize("path", _round_files(), ids=lambda p: p.name)
def test_common_threats_do_not_overclaim_modifiers(path: Path) -> None:
    doc = json.loads(path.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for entry in doc.get("rounds", []):
        round_no = entry.get("round")
        present = _present_modifiers(entry.get("groups", []) or [])
        for threat in entry.get("common_threats", []) or []:
            tokens = str(threat).lower().split()
            for mod in _MODIFIERS:
                if mod in tokens and mod not in present:
                    offenders.append(
                        f"{path.name} round {round_no}: threat {threat!r} claims "
                        f"'{mod}' but no group carries it (present: "
                        f"{sorted(present) or 'none'})",
                    )
    assert not offenders, "Round threats over-claim bloon modifiers:\n" + "\n".join(
        offenders,
    )
