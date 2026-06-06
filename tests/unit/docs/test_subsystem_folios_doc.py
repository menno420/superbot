"""Pin the subsystem-folio index to the standard folio shape."""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SUBSYSTEM_DIR = _REPO_ROOT / "docs" / "subsystems"
_INDEX = _SUBSYSTEM_DIR / "README.md"
_FOLIO_LINK = re.compile(r"\| [^|]+ \| ✅ \[`[^`]+`\]\(\./([^)]+\.md)\)")
_REQUIRED_HEADINGS = (
    "## What & where",
    "## Rules & approved structures",
    "## Current state",
    "## Plans / pending approval",
    "## Ideas",
    "## Next candidates",
    "## Related docs",
)


def test_indexed_subsystem_folios_exist_and_follow_standard_shape() -> None:
    """Every indexed folio exists and exposes the standard navigation headings."""
    indexed = _FOLIO_LINK.findall(_INDEX.read_text(encoding="utf-8"))
    assert indexed, "Subsystem index must list at least one canonical folio"

    for filename in indexed:
        folio = _SUBSYSTEM_DIR / filename
        assert folio.is_file(), f"Indexed subsystem folio does not exist: {filename}"
        text = folio.read_text(encoding="utf-8")
        for heading in _REQUIRED_HEADINGS:
            assert heading in text, f"{filename} is missing standard heading: {heading}"
