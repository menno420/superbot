"""Offline structural checks for the migrations directory (P1 PR-8).

We cannot run migrations against a real Postgres in unit-test CI, but
we CAN catch the classes of bug that cause migration runner failures
before they reach a deployment:

  - Filename pattern matches the runner's expectations
    (``NNN_<snake_name>.sql``)
  - Version numbers are sequential and unique (no gaps, no duplicates)
  - Each file is non-empty
  - Each file contains a recognisable SQL statement terminator
  - The migrations runner can list the directory and resolves to the
    expected set of versions

These are cheap to run, catch real "I added 015 but it's 014b" or
"I deleted 007 by mistake" mistakes, and run in milliseconds.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MIGRATIONS_DIR = _REPO_ROOT / "disbot" / "migrations"

_FILENAME_PATTERN = re.compile(r"^(\d{3})_[a-z][a-z0-9_]*\.sql$")


def _sql_files() -> list[Path]:
    return sorted(_MIGRATIONS_DIR.glob("*.sql"))


def test_migrations_dir_exists():
    assert _MIGRATIONS_DIR.is_dir(), f"{_MIGRATIONS_DIR} missing"


def test_at_least_one_migration_present():
    files = _sql_files()
    assert files, "no .sql migrations found"


@pytest.mark.parametrize("path", _sql_files(), ids=lambda p: p.name)
def test_filename_matches_pattern(path: Path):
    """Filename must be NNN_<snake_name>.sql so the runner's sort is stable."""
    assert _FILENAME_PATTERN.match(path.name), (
        f"{path.name} doesn't match NNN_<snake_name>.sql"
    )


def test_version_numbers_are_sequential_and_unique():
    versions = [
        int(_FILENAME_PATTERN.match(p.name).group(1))
        for p in _sql_files()
    ]
    assert versions == sorted(versions), "filenames don't sort by version"
    assert len(versions) == len(set(versions)), (
        f"duplicate version numbers in migrations: {versions}"
    )
    expected = list(range(1, len(versions) + 1))
    assert versions == expected, (
        f"non-contiguous version numbers: {versions} vs expected {expected}"
    )


@pytest.mark.parametrize("path", _sql_files(), ids=lambda p: p.name)
def test_migration_file_non_empty(path: Path):
    """An empty migration is almost certainly a mistake."""
    assert path.read_text().strip(), f"{path.name} is empty"


@pytest.mark.parametrize("path", _sql_files(), ids=lambda p: p.name)
def test_migration_contains_statement_terminator(path: Path):
    """Sanity check: contains at least one ';' so it parses as SQL."""
    src = path.read_text()
    # Strip block comments so we don't accept a "; inside /* … */" only.
    stripped = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    stripped = re.sub(r"--[^\n]*", "", stripped)
    assert ";" in stripped, f"{path.name} has no SQL statement terminator"


def test_runner_resolves_to_expected_directory():
    """The migrations runner must point at disbot/migrations/."""
    from utils.db import migrations as runner

    assert Path(runner._MIGRATIONS_DIR).resolve() == _MIGRATIONS_DIR.resolve()
