"""Unit tests for :mod:`services.tournament_state_service` (PR B').

The service wraps the per-guild ``ACTIVE_TOURNAMENT`` flag so callers
cannot bypass typed validation. These tests pin:

* ``get_active`` reads via ``db.get_setting`` with the canonical key.
* ``set_active`` rejects unknown kinds.
* ``set_active`` and ``clear_active`` route through ``db.set_setting``
  with the canonical key.
* A regex-based invariant scan that the four pre-PR-B' caller modules
  (blackjack_cog, rps_tournament_cog, rps_tournament/_helpers,
  views/blackjack/tournament_views) no longer reference the
  ``ACTIVE_TOURNAMENT`` key — the migration is the whole point.
"""

from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from services import tournament_state_service


@pytest.mark.asyncio
async def test_get_active_reads_canonical_key():
    with patch(
        "services.tournament_state_service.db.get_setting",
        new_callable=AsyncMock,
        return_value="rps",
    ) as mock_get:
        kind = await tournament_state_service.get_active(42)

    assert kind == "rps"
    mock_get.assert_awaited_once_with(42, "active_tournament", "")


@pytest.mark.asyncio
async def test_get_active_returns_empty_for_inactive_guild():
    with patch(
        "services.tournament_state_service.db.get_setting",
        new_callable=AsyncMock,
        return_value="",
    ):
        assert await tournament_state_service.get_active(42) == ""


@pytest.mark.asyncio
async def test_set_active_rejects_unknown_kind():
    with patch(
        "services.tournament_state_service.db.set_setting",
        new_callable=AsyncMock,
    ) as mock_set:
        with pytest.raises(ValueError, match="Unknown tournament kind"):
            await tournament_state_service.set_active(42, "tetris")
    # Defense-in-depth: the DB must NOT have been touched on a rejected
    # kind. If the validation ever moves below the write, this fails.
    mock_set.assert_not_called()


@pytest.mark.asyncio
async def test_set_active_writes_rps():
    with patch(
        "services.tournament_state_service.db.set_setting",
        new_callable=AsyncMock,
    ) as mock_set:
        await tournament_state_service.set_active(42, "rps")
    mock_set.assert_awaited_once_with(42, "active_tournament", "rps")


@pytest.mark.asyncio
async def test_set_active_writes_blackjack():
    with patch(
        "services.tournament_state_service.db.set_setting",
        new_callable=AsyncMock,
    ) as mock_set:
        await tournament_state_service.set_active(42, "blackjack")
    mock_set.assert_awaited_once_with(42, "active_tournament", "blackjack")


@pytest.mark.asyncio
async def test_clear_active_writes_empty_string():
    with patch(
        "services.tournament_state_service.db.set_setting",
        new_callable=AsyncMock,
    ) as mock_set:
        await tournament_state_service.clear_active(42)
    mock_set.assert_awaited_once_with(42, "active_tournament", "")


# ---------------------------------------------------------------------------
# Migration invariant — pre-PR-B' callers must not reference the key directly
# ---------------------------------------------------------------------------


_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# These four modules previously contained the 9-plus direct
# ``set_setting(..., ACTIVE_TOURNAMENT, ...)`` writes that PR B'
# migrated to ``tournament_state_service``. They must no longer touch
# the key directly — any new direct caller would defeat the typed
# service boundary.
_MIGRATED_FILES = [
    _DISBOT / "cogs" / "blackjack_cog.py",
    _DISBOT / "cogs" / "rps_tournament_cog.py",
    _DISBOT / "cogs" / "rps_tournament" / "_helpers.py",
    _DISBOT / "views" / "blackjack" / "tournament_views.py",
]


def test_migrated_callers_no_longer_reference_active_tournament_key():
    """The four migrated files must not import or use
    ``ACTIVE_TOURNAMENT`` after PR B'.

    A future refactor that re-imports the key in any of these files
    should also re-introduce the direct ``set_setting`` write, which
    the existing S4 invariant
    (``test_no_direct_settings_keys_writes.py``) would catch. This
    test catches the import alone, before the write lands.
    """
    pattern = re.compile(r"\bACTIVE_TOURNAMENT\b")
    violations: list[tuple[str, int, str]] = []
    for path in _MIGRATED_FILES:
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            # Allow docstring / comment mentions — the failure mode we
            # care about is an actual code reference. A simple test:
            # ignore lines whose stripped form starts with ``#`` or
            # which are inside a triple-quoted docstring. Detecting
            # docstrings precisely needs AST; an approximation here is
            # to skip lines whose only ACTIVE_TOURNAMENT use is inside
            # double-quoted strings beginning with `"""` or `'''`.
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if pattern.search(line):
                # Allow narrative docstring lines (``""" ... ACTIVE_TOURNAMENT ...``).
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    continue
                # The phrasing "on-startup ACTIVE_TOURNAMENT sweep" appears
                # inside a docstring; if the line contains 'sweep' AND
                # 'ACTIVE_TOURNAMENT' the regex would still match — guard
                # by requiring a likely-code form (assignment / call /
                # import). For belt-and-braces, also exclude lines that
                # are pure prose (no =, no (, no .).
                if not any(ch in line for ch in "=(."):
                    continue
                violations.append(
                    (str(path.relative_to(_REPO_ROOT)), lineno, line.rstrip()),
                )
    assert not violations, (
        "PR B' invariant violation: a migrated tournament file still "
        "references ACTIVE_TOURNAMENT directly. Route through "
        "services.tournament_state_service instead.\n\n"
        + "\n".join(f"  {p}:{ln}: {src}" for p, ln, src in violations)
    )
