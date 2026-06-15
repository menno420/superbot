"""Runner-level guards for the migrations runner (RC-6 closeout).

`test_migrations_structure.py` already pins the *directory* invariants
(contiguous / unique / non-empty / terminator).  This file pins the *runner's*
behaviour: `_ordered_migration_versions` must REJECT a structurally invalid set
(bad filename, duplicate leading version) instead of silently skipping it — the
silent skip was the RC-6 latent bug (a duplicate version meant the second file
never applied once the first was recorded).

All tests here are DB-free (pure filename validation), so they run in CI without
Postgres.  A live fresh-DB bootstrap test is intentionally deferred: it needs a
Postgres test fixture, which `tests/conftest.py` does not provide and which the
plan keeps out of scope (adding the fixture is its own infra change).
"""

from __future__ import annotations

import os

import pytest

from utils.db import migrations as runner
from utils.db.migrations import MigrationError, _ordered_migration_versions


def test_orders_valid_filenames_by_version():
    out = _ordered_migration_versions(
        ["002_second.sql", "001_first.sql", "010_tenth.sql", "notes.txt"],
    )
    assert out == [
        (1, "001_first.sql"),
        (2, "002_second.sql"),
        (10, "010_tenth.sql"),
    ]


def test_ignores_non_sql_files():
    out = _ordered_migration_versions(["001_a.sql", "README.md", "001_a.sql.bak"])
    assert out == [(1, "001_a.sql")]


def test_raises_on_bad_filename():
    # Missing zero-pad: the old runner silently skipped this.
    with pytest.raises(MigrationError, match="NNN_"):
        _ordered_migration_versions(["1_missing_zero_pad.sql"])
    # Dash instead of underscore.
    with pytest.raises(MigrationError, match="NNN_"):
        _ordered_migration_versions(["001-dash-not-underscore.sql"])
    # Upper-case in the name part.
    with pytest.raises(MigrationError, match="NNN_"):
        _ordered_migration_versions(["001_BadName.sql"])


def test_raises_on_duplicate_version():
    with pytest.raises(MigrationError, match="Duplicate migration version 001"):
        _ordered_migration_versions(["001_first.sql", "001_clash.sql"])


def test_real_migrations_dir_is_valid():
    """The new raise must NOT fire on the real, shipped migration set — otherwise
    the guard would crash boot on existing data.  Also re-asserts contiguity at
    the runner level (a guard independent of the structure test)."""
    ordered = _ordered_migration_versions(os.listdir(runner._MIGRATIONS_DIR))
    versions = [v for v, _ in ordered]
    assert versions == sorted(versions)
    assert len(versions) == len(set(versions))
    assert versions == list(range(1, len(versions) + 1)), (
        f"real migrations are not contiguous from 1: {versions}"
    )
