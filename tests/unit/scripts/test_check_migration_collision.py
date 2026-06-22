"""Tests for scripts/check_migration_collision.py — the pure collision analyzer.

Guards the duplicate-migration-number class that renumbered #1279's migration four
times in one afternoon (concurrent fleet PRs picking the same next number off the
shared append point). Only the pure `analyze()` core is tested; the git I/O is a
thin read-only wrapper exercised against the real repo by the script itself.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO / "scripts" / "check_migration_collision.py"


def _load():
    spec = importlib.util.spec_from_file_location(
        "check_migration_collision_ut", _SCRIPT,
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # Register before exec: @dataclass introspects the owning module via sys.modules.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _load()


def test_parse_number(mod):
    assert mod.parse_number("089_role_menu_card.sql") == 89
    assert mod.parse_number("008_panel_anchors.sql") == 8
    assert mod.parse_number("README.md") is None
    assert mod.parse_number("schema.sql") is None


def test_no_collision_when_branch_adds_a_fresh_number(mod):
    base = {"087_a.sql", "088_b.sql", "089_c.sql"}
    head = base | {"090_new.sql"}
    report = mod.analyze("disbot/migrations", base, head)
    assert report.ok
    assert report.collisions == []


def test_no_collision_when_branch_adds_nothing(mod):
    base = {"087_a.sql", "088_b.sql"}
    report = mod.analyze("disbot/migrations", base, set(base))
    assert report.ok


def test_collision_when_branch_reuses_a_base_number(mod):
    # The #1279 case: branch picked 089 but 089 already merged to main as a different file.
    base = {"087_a.sql", "088_b.sql", "089_already_on_main.sql"}
    head = base | {"089_my_new_migration.sql"}
    report = mod.analyze("disbot/migrations", base, head)
    assert not report.ok
    (c,) = report.collisions
    assert c.filename == "089_my_new_migration.sql"
    assert c.number == 89
    assert c.suggested == 90  # next free above max(89)


def test_multiple_collisions_get_distinct_suggestions(mod):
    base = {"088_a.sql", "089_b.sql"}
    head = base | {"088_mine.sql", "089_also_mine.sql"}
    report = mod.analyze("disbot/migrations", base, head)
    suggestions = sorted(c.suggested for c in report.collisions)
    # Two collisions → two distinct free numbers above the max, never reused.
    assert suggestions == [90, 91]


def test_added_non_colliding_files_are_ignored(mod):
    # A brand-new high number is fine; only reuse of a base number is a collision.
    base = {"088_a.sql", "089_b.sql"}
    head = base | {"090_fine.sql", "089_collides.sql", "notes.md"}
    report = mod.analyze("disbot/migrations", base, head)
    assert [c.filename for c in report.collisions] == ["089_collides.sql"]
    assert report.collisions[0].suggested == 91  # 90 is taken by the fresh file


def test_suggested_renumber_command_uses_zero_padded_swap(mod):
    c = mod.Collision("089_my_new_migration.sql", 89, 90)
    line = mod._suggest(c, "disbot/migrations")
    assert (
        line.strip() == "git mv disbot/migrations/089_my_new_migration.sql "
        "disbot/migrations/090_my_new_migration.sql"
    )
