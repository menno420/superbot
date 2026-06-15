"""S4.6 — soft cog-size invariant.

After Phase A's decomposition work (PRs S4.2-followup, S4.3, S4.4
rules, S4.4.5 + stabilization, S4.5, S4.6 rps), every cog file under
``disbot/cogs/*_cog.py`` is under 800 LOC.  This test pins that floor
so a future regression — re-inlining a large surface back into a cog
— surfaces in CI rather than gradually re-creating the god-cog
problem the decomposition resolved.

Thresholds match the audit's §3.5 proposal:

  WARN_LOC = 500     — emits a ``UserWarning`` (visible in pytest -W)
  FAIL_LOC = 800     — hard ``pytest.fail``

The warning tier is intentional: several cogs in the codebase (role,
counting, help, chain) sit between 500 and 700 LOC and are accepted
in their current shape per the audit (§3.5).  Pushing them under 500
would force premature extraction; failing them would block CI without
architectural cause.  The warning surfaces the trend without blocking.

Per-cog exclusions
------------------

There are intentionally none.  Every cog at the time of S4.6 landing
fits under 800.  If a new cog legitimately needs to exceed the ceiling
(e.g. a future game subsystem with irreducible state), the right move
is to land its decomposition stage BEFORE growing past the ceiling,
not to add it to an allow-list here.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_COG_DIR = _REPO_ROOT / "disbot" / "cogs"

WARN_LOC = 500
FAIL_LOC = 800


def _cog_files() -> list[Path]:
    """All cog files at the top of ``disbot/cogs/`` — excludes subpackages.

    The convention from F-3 is that ``cogs/<sub>_cog.py`` is the Discord-
    facing surface and ``cogs/<sub>/`` holds the helpers.  Helper modules
    are not subject to the 800-LOC ceiling — they're called from the cog,
    not registered with discord.py — so this test only looks at the
    cog files themselves.
    """
    return sorted(_COG_DIR.glob("*_cog.py"))


def _line_count(path: Path) -> int:
    """Lines-of-code for *path*.  Matches what ``wc -l`` reports."""
    with path.open(encoding="utf-8") as f:
        return sum(1 for _ in f)


@pytest.mark.parametrize("cog_path", _cog_files(), ids=lambda p: p.name)
def test_cog_size_under_fail_threshold(cog_path: Path):
    """Hard ceiling: cog files must stay under 800 LOC.

    Re-inlining 100+ LOC of view/persistence/helper code back into a
    cog after Phase A's decomposition is an architectural regression.
    The fix is to follow the F-3 convention and extract the new
    surface into the cog's helpers subpackage (or its ``views/<sub>/``
    sibling) rather than growing the cog file.
    """
    loc = _line_count(cog_path)
    if loc >= FAIL_LOC:
        pytest.fail(
            f"{cog_path.name} is {loc} LOC — over the {FAIL_LOC}-LOC fail "
            f"threshold set by S4.6.  Decompose the cog before adding to "
            f"it: move view code to ``views/<sub>/``, persistence helpers "
            f"to ``cogs/<sub>/_persistence.py``, etc.  See docs/architecture.md "
            f'§"Subsystem decomposition" and the Phase A PRs for the '
            f"established pattern.",
        )


@pytest.mark.parametrize("cog_path", _cog_files(), ids=lambda p: p.name)
def test_cog_size_warn_threshold(cog_path: Path):
    """Soft tier: cogs ≥500 LOC emit a UserWarning (informational).

    Not a failure — several cogs in the audit's §3.5 inventory sit
    between 500 and 700 LOC by design (role, counting, help, chain).
    This warning surfaces drift over time so reviewers see when a
    formerly-clean cog crosses into warn-tier.
    """
    loc = _line_count(cog_path)
    if loc >= WARN_LOC:
        warnings.warn(
            f"{cog_path.name} is {loc} LOC — in the {WARN_LOC}..{FAIL_LOC} "
            f"warn-tier.  Not a failure, but watch for further growth.",
            UserWarning,
            stacklevel=2,
        )


def test_at_least_one_cog_exists():
    """Sanity: glob finds cog files (catches a broken CWD or path).

    If this fails, ``_cog_files()`` returned an empty list — likely
    because someone changed the cog directory layout.  The
    per-cog parametrized tests would silently produce zero cases
    without this guard.
    """
    cogs = _cog_files()
    assert cogs, (
        f"No cog files found under {_COG_DIR}.  Path resolution broken "
        f"or directory layout changed."
    )
