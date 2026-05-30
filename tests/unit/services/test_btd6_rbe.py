"""RBE (Red Bloon Equivalent) consistency for the BTD6 bloon dataset.

The point of these tests is that nobody has to trust a hand-typed RBE
number. We recompute every bloon's RBE *from scratch* using only its
``health`` and its ``children`` spawn text — bottoming out at Red — and
assert it equals the ``rbe`` stored in ``bloons.json``. A typo in either
the children text or the rbe value makes the two disagree and fails CI.

This also pins the spawn chain that the user-facing bug was about: the
basic tiers (Red→Blue→Green→Yellow→Pink) must exist and chain correctly,
so the bot can never again claim "Pink is the bottom of the chain".
"""

from __future__ import annotations

import re

from services.btd6_data_service import get_dataset

# Modifier words that prefix a child name (e.g. "4 Camo Ceramic Bloons")
# and must be stripped before matching the underlying bloon.
_MODIFIER_WORDS = frozenset({"camo", "fortified", "regrow", "regrowth"})


def _name_lookup() -> dict[str, str]:
    """Map every canonical name + alias (lowercased) to a bloon id."""
    lookup: dict[str, str] = {}
    for bloon in get_dataset().bloons:
        lookup[bloon.canonical.lower()] = bloon.id
        for alias in bloon.aliases:
            lookup[alias.lower()] = bloon.id
    return lookup


def _resolve_child(name: str, lookup: dict[str, str]) -> tuple[str, bool]:
    """Resolve a child phrase to (bloon id, is_fortified).

    e.g. 'Camo Ceramic Bloons' -> ('ceramic', False);
    'Fortified Ceramic Bloon' -> ('ceramic', True).
    """
    tokens = [t for t in re.split(r"\s+", name.strip().lower()) if t]
    # Drop trailing 'bloon' / 'bloons'; capture then drop modifier words.
    tokens = [t for t in tokens if t not in {"bloon", "bloons"}]
    fortified = "fortified" in tokens
    tokens = [t for t in tokens if t not in _MODIFIER_WORDS]
    candidate = " ".join(tokens)
    if candidate in lookup:
        return lookup[candidate], fortified
    # Fall back to the last token (handles 'massive ... blimp' style names
    # never appearing in children, but keeps the resolver robust).
    if tokens and tokens[-1] in lookup:
        return lookup[tokens[-1]], fortified
    raise AssertionError(f"could not resolve child bloon from {name!r}")


def _parse_children(
    text: str,
    lookup: dict[str, str],
) -> list[tuple[int, str, bool]]:
    """Parse 'N <Bloon>, M <Bloon> and K <Bloon>' into (count, id, fortified)."""
    text = (text or "").strip()
    if not text:
        return []
    parts = re.split(r"\s+and\s+|,", text)
    out: list[tuple[int, str, bool]] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.match(r"(\d+)\s+(.*)", part)
        assert m, f"unparseable child phrase {part!r}"
        cid, fortified = _resolve_child(m.group(2), lookup)
        out.append((int(m.group(1)), cid, fortified))
    return out


def _compute_rbe() -> dict[str, int]:
    """Compute RBE for every non-modifier bloon from health + children."""
    dataset = get_dataset()
    lookup = _name_lookup()
    bloons = {b.id: b for b in dataset.bloons if b.category != "modifier"}
    children = {bid: _parse_children(b.children, lookup) for bid, b in bloons.items()}
    computed: dict[str, int] = {}
    # Iterate to a fixpoint; the spawn graph is a DAG bottoming at Red.
    for _ in range(len(bloons) + 1):
        progressed = False
        for bid, b in bloons.items():
            if bid in computed:
                continue
            kids = children[bid]
            if any(cid not in computed for _, cid, _ in kids):
                continue
            layer_hits = b.health if isinstance(b.health, int) else 1
            total = layer_hits
            for count, cid, fortified in kids:
                # A fortified child contributes its fortified RBE (e.g. a
                # Diamond pops one fortified Ceramic: 114, not 104).
                child_rbe = computed[cid]
                if fortified and isinstance(bloons[cid].rbe_fortified, int):
                    child_rbe = bloons[cid].rbe_fortified
                total += count * child_rbe
            computed[bid] = total
            progressed = True
        if not progressed:
            break
    missing = set(bloons) - set(computed)
    assert not missing, f"RBE could not be computed (spawn cycle?) for {missing}"
    return computed


def test_stored_rbe_matches_recomputed_chain():
    computed = _compute_rbe()
    for bloon in get_dataset().bloons:
        if bloon.category == "modifier":
            continue
        assert bloon.rbe is not None, f"{bloon.id} is missing an rbe value"
        assert bloon.rbe == computed[bloon.id], (
            f"{bloon.id}: stored rbe={bloon.rbe} but children/health imply "
            f"{computed[bloon.id]}"
        )


def test_basic_tier_chain_is_present_and_ordered():
    by_id = {b.id: b for b in get_dataset().bloons}
    for tier in ("red", "blue", "green", "yellow", "pink"):
        assert tier in by_id, f"basic tier {tier!r} missing from bloons.json"
    # Canonical RBE anchors for the basic tiers.
    assert by_id["red"].rbe == 1
    assert by_id["pink"].rbe == 5
    # Red is the only bottom-of-chain bloon; Pink is NOT.
    assert by_id["red"].children == ""
    assert "Yellow" in by_id["pink"].children


def test_known_rbe_values():
    """Spot-check the canonical RBE figures the bot is asked about."""
    by_id = {b.id: b for b in get_dataset().bloons}
    expected = {
        "ceramic": 104,
        "moab": 616,
        "bfb": 3164,
        "zomg": 16656,
        "ddt": 816,
        # BAD spawns 2 ZOMGs + 3 DDTs per bloonswiki's extracted data
        # (rbe column + parent_of agree): 20000 + 2*16656 + 3*816 = 55760.
        "bad": 55760,
    }
    for bid, rbe in expected.items():
        assert by_id[bid].rbe == rbe
