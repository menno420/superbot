"""Decode Contested Territory tile codes into hex-grid positions.

Ninja Kiwi labels every CT tile with a 3-letter code (e.g. ``DEC``,
``MRX``, ``FAH``). The CT map is one large hexagon of edge length 8 →
``3·8² − 3·8 + 1 = 169`` tiles. The code structure (reverse-engineered
from a full live tile set and consistent with the documented
Blooncyclopedia rules) is:

* **1st letter** ``A``–``F`` selects one of 6 sixty-degree *sectors*
  (28 tiles each); ``M`` marks the single centre tile ``MRX``.
* **2nd letter** ``A``–``G`` is the *ring* (distance from centre): ``A``
  is the outer ring (7 tiles per sector), ``G`` the innermost ring next
  to the centre (1 tile per sector). Per-sector ring sizes 7…1 sum to
  the 28 tiles in a sector, and ``6 × ring`` reproduces the global ring
  sizes 42/36/30/24/18/12/6.
* **3rd letter** is the position ``0…ring-1`` along that ring inside the
  sector. The lone exception is ``FAH``: sector ``F``'s outer-ring final
  tile uses ``H`` in place of ``G`` (a Ninja Kiwi quirk), so ``H`` maps
  to the same slot ``G`` would occupy.

The human descriptor (sector letter + ring + position) is exact. The
axial ``(q, r)`` coordinates form a self-consistent hexagon (centre at
the origin, correct ring distances, bijective over all 169 codes); their
*rotation* relative to the in-game art is a fixed convention and should
be treated as provisional until spot-checked against a labelled CT map.

Pure module — stdlib only, no I/O — so it sits cleanly in ``utils/``.
"""

from __future__ import annotations

from dataclasses import dataclass

_CENTER_CODE = "MRX"
_EDGE_LENGTH = 8
_MAX_RING = _EDGE_LENGTH - 1  # 7 — outermost ring index (centre is ring 0)
_NUM_SECTORS = 6

# Cube-coordinate step directions (redblobgames convention). Index 4 is the
# ring start corner used by the ring-walk below.
_CUBE_DIRECTIONS: tuple[tuple[int, int, int], ...] = (
    (1, -1, 0),
    (1, 0, -1),
    (0, 1, -1),
    (-1, 1, 0),
    (-1, 0, 1),
    (0, -1, 1),
)


@dataclass(frozen=True)
class CTTilePosition:
    """A decoded CT tile position.

    ``ring`` is the distance from the centre (0 = ``MRX`` centre, 7 =
    outer edge). ``sector`` is ``0``–``5`` (``None`` for the centre) and
    ``sector_label`` is the originating first letter. ``position_in_ring``
    is ``0…ring-1``. ``axial`` is ``(q, r)`` with the centre at the
    origin. ``is_corner`` flags the six corner tiles of each ring.
    """

    tile_id: str
    is_center: bool
    ring: int
    sector: int | None
    sector_label: str
    position_in_ring: int
    axial: tuple[int, int]
    is_corner: bool

    def describe(self) -> str:
        """Short human-readable position, e.g. for grounding / embeds."""
        if self.is_center:
            return "centre tile (MRX)"
        if self.ring == _MAX_RING:
            band = "outer ring (map edge)"
        elif self.ring == 1:
            band = "inner ring (next to centre)"
        else:
            band = f"ring {self.ring} of {_MAX_RING}"
        corner = ", a corner tile" if self.is_corner else ""
        return (
            f"sector {self.sector_label}, {band}, "
            f"position {self.position_in_ring + 1} of {self.ring}{corner}"
        )


def _cube_to_axial(cube: tuple[int, int, int]) -> tuple[int, int]:
    x, _y, z = cube
    return (x, z)


def _ring_cube(ring: int, sector: int, position: int) -> tuple[int, int, int]:
    """Cube coord of the ``position``-th tile on ``sector``'s slice of ``ring``.

    Walks the standard hex ring starting at the corner ``direction[4] *
    ring`` and stepping through full sectors; ``sector * ring + position``
    is the index around the ring.
    """
    sx, sy, sz = _CUBE_DIRECTIONS[4]
    cube = (sx * ring, sy * ring, sz * ring)
    target = sector * ring + position
    count = 0
    for i in range(_NUM_SECTORS):
        dx, dy, dz = _CUBE_DIRECTIONS[i]
        for _ in range(ring):
            if count == target:
                return cube
            cube = (cube[0] + dx, cube[1] + dy, cube[2] + dz)
            count += 1
    return cube


def decode_tile(code: str) -> CTTilePosition | None:
    """Decode a 3-letter CT tile code into a :class:`CTTilePosition`.

    Returns ``None`` for anything that is not a valid CT tile code
    (wrong length, out-of-range letters, or a position that overflows
    its ring).
    """
    if not isinstance(code, str):
        return None
    norm = code.strip().upper()
    if len(norm) != 3:
        return None

    if norm == _CENTER_CODE:
        return CTTilePosition(
            tile_id=norm,
            is_center=True,
            ring=0,
            sector=None,
            sector_label="M",
            position_in_ring=0,
            axial=(0, 0),
            is_corner=False,
        )

    first, second, third = norm[0], norm[1], norm[2]

    # 1st letter → sector 0..5.
    sector = ord(first) - ord("A")
    if not 0 <= sector < _NUM_SECTORS:
        return None

    # 2nd letter A..G → ring 7..1.
    row = ord(second) - ord("A")
    if not 0 <= row <= _MAX_RING - 1:
        return None
    ring = _MAX_RING - row

    # 3rd letter → position 0..ring-1. 'H' is the FAH exception (= G slot).
    position = 6 if third == "H" else ord(third) - ord("A")
    if not 0 <= position < ring:
        return None

    cube = _ring_cube(ring, sector, position)
    return CTTilePosition(
        tile_id=norm,
        is_center=False,
        ring=ring,
        sector=sector,
        sector_label=first,
        position_in_ring=position,
        axial=_cube_to_axial(cube),
        is_corner=position == 0,
    )


__all__ = ["CTTilePosition", "decode_tile"]
