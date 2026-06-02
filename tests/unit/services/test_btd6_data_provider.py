"""Tests for the BTD6 raw-fixture provider seam.

Pins that:

* ``FileRawProvider`` reproduces the historical disk-read behaviour.
* The default provider is a ``FileRawProvider`` (production unchanged).
* ``set_provider`` lets ``get_dataset`` load from *any* backend that
  satisfies the ``BTD6RawProvider`` Protocol — the guarantee the
  cloud-storage migration relies on (a network provider plugs in with no
  change to the ~14 dataset consumers).
"""

from __future__ import annotations

import json

import pytest

from services.btd6_data_provider import (
    DATA_ROOT,
    BTD6RawProvider,
    FileRawProvider,
)
from services.btd6_data_service import (
    get_dataset,
    get_provider,
    reset_cache,
    set_provider,
)

_REQUIRED = ("towers", "heroes", "maps", "modes", "rounds")


@pytest.fixture(autouse=True)
def _restore_provider():
    """Each test restores the original provider + cache (hermetic seam)."""
    original = get_provider()
    reset_cache()
    yield
    set_provider(original)
    reset_cache()


def test_default_provider_is_file_provider():
    assert isinstance(get_provider(), FileRawProvider)


def test_file_provider_satisfies_protocol():
    assert isinstance(FileRawProvider(), BTD6RawProvider)


def test_file_provider_reads_committed_fixtures():
    raw = FileRawProvider().load("towers.json")
    assert raw is not None
    assert "towers" in raw


def test_file_provider_matches_direct_disk_read():
    direct = json.loads((DATA_ROOT / "towers.json").read_text(encoding="utf-8"))
    assert FileRawProvider().load("towers.json") == direct


def test_file_provider_missing_file_returns_none(tmp_path):
    assert FileRawProvider(tmp_path).load("nope.json") is None


def test_set_provider_with_file_root_drives_get_dataset(tmp_path):
    for name in _REQUIRED:
        (tmp_path / f"{name}.json").write_text(
            (DATA_ROOT / f"{name}.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    set_provider(FileRawProvider(tmp_path))
    reset_cache()
    dataset = get_dataset()
    assert len(dataset.towers) >= 4


class _DictProvider:
    """In-memory provider — proves ``get_dataset`` is backend-agnostic."""

    def __init__(self, data: dict[str, dict]) -> None:
        self._data = data

    def load(self, name: str) -> dict | None:
        return self._data.get(name)


def test_injected_in_memory_provider_drives_get_dataset():
    """A non-file provider (the cloud-migration shape) loads end-to-end."""
    payload = {
        f"{name}.json": json.loads(
            (DATA_ROOT / f"{name}.json").read_text(encoding="utf-8"),
        )
        for name in _REQUIRED
    }
    set_provider(_DictProvider(payload))
    reset_cache()
    dataset = get_dataset()
    assert dataset.towers
    assert dataset.data_version
    # Optional fixtures absent from the dict degrade to empty categories.
    assert dataset.bloons == ()
