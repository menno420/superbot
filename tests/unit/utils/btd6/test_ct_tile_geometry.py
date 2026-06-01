"""CT tile-code geometry decoder.

The strongest guarantee is the bijection: every one of the 169 real
tile codes from a captured CT map must decode to a distinct hex cell,
with axial distance from the origin equal to the decoded ring. That
validates the whole scheme without an external coordinate reference.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from utils.btd6.ct_tile_geometry import decode_tile  # noqa: E402

_FIXTURES = Path(__file__).parents[4] / "tests" / "fixtures" / "ninjakiwi"


def _real_tile_codes() -> list[str]:
    raw = json.loads((_FIXTURES / "btd6_ct_mpejg5d0_tiles.json").read_text("utf-8"))
    body = raw.get("body", raw)
    return sorted({t["id"] for t in body["tiles"]})


def _axial_distance(q: int, r: int) -> int:
    return (abs(q) + abs(r) + abs(q + r)) // 2


def test_center_tile():
    pos = decode_tile("MRX")
    assert pos is not None
    assert pos.is_center is True
    assert pos.ring == 0
    assert pos.axial == (0, 0)
    assert "centre" in pos.describe().lower()


def test_full_tile_set_is_a_bijection():
    codes = _real_tile_codes()
    assert len(codes) == 169
    positions = {}
    for code in codes:
        pos = decode_tile(code)
        assert pos is not None, f"failed to decode {code!r}"
        positions[code] = pos.axial
    # 169 distinct hex cells.
    assert len(set(positions.values())) == 169


def test_axial_distance_equals_ring_for_all_real_tiles():
    for code in _real_tile_codes():
        pos = decode_tile(code)
        assert pos is not None
        q, r = pos.axial
        assert _axial_distance(q, r) == pos.ring, code


def test_fah_exception_is_outer_ring():
    pos = decode_tile("FAH")
    assert pos is not None
    assert pos.sector_label == "F"
    assert pos.ring == 7
    assert pos.position_in_ring == 6


def test_ring_letter_maps_outer_to_inner():
    # 2nd letter A → outer ring 7, G → inner ring 1.
    assert decode_tile("AAA").ring == 7
    assert decode_tile("AGA").ring == 1


def test_invalid_codes_return_none():
    assert decode_tile("ZZZ") is None  # sector out of range
    assert decode_tile("AB") is None  # too short
    assert decode_tile("GAA") is None  # 'G' is not a valid sector (A-F)
    assert decode_tile("AGB") is None  # inner ring has only 1 position
    assert decode_tile("") is None
    assert decode_tile(None) is None  # type: ignore[arg-type]
