"""Sanity check for ``docs/help-command-surface-map.md``.

Verifies the inventory doc exists, has the expected section headings,
and lists every committed subsystem and every committed hub.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from utils.hub_registry import HUBS
from utils.subsystem_registry import SUBSYSTEMS

DOC_PATH = Path(__file__).resolve().parents[3] / "docs" / "help-command-surface-map.md"


@pytest.fixture(scope="module")
def doc_text() -> str:
    assert DOC_PATH.exists(), f"missing inventory doc at {DOC_PATH}"
    return DOC_PATH.read_text(encoding="utf-8")


def test_doc_has_required_section_headings(doc_text):
    """Section headings keep the doc navigable. Hub table, subsystem
    inventory, and the inconsistencies callout are the load-bearing
    sections — pin these three explicitly.
    """
    for heading in (
        "## 1. Mother hubs",
        "## 2. Subsystem inventory",
        "## 3. Known inconsistencies",
    ):
        assert heading in doc_text, f"missing required heading: {heading}"


def test_doc_lists_every_committed_hub(doc_text):
    """Every hub registered in :data:`HUBS` must appear in the doc so
    the inventory tracks reality. We match by hub key wrapped in
    backticks (the doc's table convention).
    """
    for hub in HUBS:
        assert f"`{hub.key}`" in doc_text, (
            f"hub {hub.key!r} missing from inventory doc"
        )


def test_doc_lists_every_subsystem_key(doc_text):
    """Every subsystem key in :data:`SUBSYSTEMS` must appear in the
    inventory table. Match by key wrapped in backticks.
    """
    for key in SUBSYSTEMS:
        assert f"`{key}`" in doc_text, (
            f"subsystem {key!r} missing from inventory doc"
        )
