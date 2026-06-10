"""Contract tests for the guild Help-overlay read model (HLP-3).

Pins: row/overlay shapes, the per-guild cache + invalidation, the
degrade-to-defaults fault posture, and the Q-0055 display-only fence
(no execution/admission module may consult the overlay).
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from services import help_overlay
from services.help_overlay import (
    EMPTY_OVERLAY,
    GuildHelpOverlay,
    HelpOverlayRow,
    get_guild_help_overlay,
    invalidate_help_overlay_cache,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def setup_function() -> None:
    invalidate_help_overlay_cache()


def teardown_function() -> None:
    invalidate_help_overlay_cache()


# ---------------------------------------------------------------------------
# Shapes
# ---------------------------------------------------------------------------


def test_row_is_noop_when_every_field_inherits():
    assert HelpOverlayRow(entity_kind="hub", entity_key="games").is_noop
    assert not HelpOverlayRow(
        entity_kind="hub",
        entity_key="games",
        display_hidden=True,
    ).is_noop
    assert not HelpOverlayRow(
        entity_kind="subsystem",
        entity_key="xp",
        display_name="Levels",
    ).is_noop


def test_overlay_get_and_is_empty():
    row = HelpOverlayRow(entity_kind="hub", entity_key="games", display_hidden=True)
    overlay = GuildHelpOverlay(guild_id=1, rows=(row,))
    assert overlay.get("hub", "games") is row
    assert overlay.get("subsystem", "games") is None
    assert overlay.get("hub", "economy") is None
    assert not overlay.is_empty
    assert EMPTY_OVERLAY.is_empty


# ---------------------------------------------------------------------------
# Cached read
# ---------------------------------------------------------------------------


async def test_dm_context_returns_the_empty_overlay():
    assert await get_guild_help_overlay(None) is EMPTY_OVERLAY


async def test_read_caches_until_invalidated(monkeypatch):
    from utils.db import help_overlay as db

    rows = [
        {
            "entity_kind": "subsystem",
            "entity_key": "xp",
            "display_hidden": None,
            "display_name": "Levels",
            "description": None,
            "updated_by": 7,
            "updated_at": None,
        },
    ]
    reader = AsyncMock(return_value=rows)
    home_reader = AsyncMock(return_value=None)  # no Q-0059 home row
    monkeypatch.setattr(db, "get_guild_rows", reader)
    monkeypatch.setattr(db, "get_home_row", home_reader)

    first = await get_guild_help_overlay(42)
    assert first.get("subsystem", "xp").display_name == "Levels"
    assert first.home is None
    second = await get_guild_help_overlay(42)
    assert second is first  # cached
    reader.assert_awaited_once()
    home_reader.assert_awaited_once()

    invalidate_help_overlay_cache(42)
    third = await get_guild_help_overlay(42)
    assert third is not first
    assert reader.await_count == 2


async def test_db_fault_degrades_to_empty_and_is_not_cached(monkeypatch):
    from utils.db import help_overlay as db

    reader = AsyncMock(side_effect=RuntimeError("db down"))
    monkeypatch.setattr(db, "get_guild_rows", reader)
    monkeypatch.setattr(db, "get_home_row", AsyncMock(return_value=None))

    overlay = await get_guild_help_overlay(42)
    assert overlay.is_empty  # Help renders defaults, never crashes

    # A fault result must not poison the cache — the next read retries.
    reader.side_effect = None
    reader.return_value = []
    again = await get_guild_help_overlay(42)
    assert again.is_empty
    assert reader.await_count == 2


async def test_invalidate_all_clears_every_guild(monkeypatch):
    from utils.db import help_overlay as db

    reader = AsyncMock(return_value=[])
    monkeypatch.setattr(db, "get_guild_rows", reader)
    monkeypatch.setattr(db, "get_home_row", AsyncMock(return_value=None))
    await get_guild_help_overlay(1)
    await get_guild_help_overlay(2)
    invalidate_help_overlay_cache()
    await get_guild_help_overlay(1)
    assert reader.await_count == 3


# ---------------------------------------------------------------------------
# Q-0055 / HLP-4 — display-only fence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "admission_path",
    [
        "disbot/core/runtime/command_access.py",
        "disbot/services/command_routing.py",
        "disbot/governance/resolver.py",
        "disbot/governance/writes.py",
    ],
)
def test_admission_paths_never_consult_the_overlay(admission_path: str):
    """Hiding from Help is presentation only: no execution/admission owner
    may import the overlay read model or its DB primitives (Q-0055)."""
    src = (_REPO_ROOT / admission_path).read_text()
    tree = ast.parse(src)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    offenders = {m for m in imported if "help_overlay" in m}
    assert not offenders, (
        f"{admission_path} consults the Help overlay — display-only hiding "
        f"must never gate execution: {offenders}"
    )


def test_overlay_read_model_is_import_safe_and_stdlib_only_at_top_level():
    """The render hot path imports this module — its top-level imports must
    stay stdlib-only (the access_projection cycle discipline)."""
    src = (_REPO_ROOT / "disbot" / "services" / "help_overlay.py").read_text()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            assert node.module in {
                "__future__",
                "dataclasses",
                "logging",
            }, f"non-stdlib top-level import: {node.module}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name in {
                    "logging"
                }, f"non-stdlib top-level import: {alias.name}"
