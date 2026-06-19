"""Tests for ``scripts/router_status.py`` — the question-router digest."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_module():
    """Load ``scripts/router_status.py`` by path (scripts/ is not a package)."""
    script = REPO_ROOT / "scripts" / "router_status.py"
    spec = importlib.util.spec_from_file_location("_router_status", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec so the @dataclass decorator can resolve the module
    # (dataclasses looks the module up in sys.modules by name).
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_MOD = _load_module()

_SAMPLE = """# Maintainer question router

### Q-0001 — A decided thing (2026-06-01)

> **DECISION 2026-06-01 (owner-directed).** Body.

**Home:** somewhere.

---

### Q-0002 — An answered thing (2026-06-02)

> **ANSWERED 2026-06-02.** Body.

### Q-0010 — Still open (2026-06-19)

> **OPEN — DISCUSS lane, owner decides.** Body.

### Q-0011 — Partial (2026-06-19)

> **PARTLY DECIDED 2026-06-19.** Body.

### Q-0012 — An observation

> **OBSERVED 2026-06-14.** Body, no decision.
"""


def test_parse_blocks_counts_and_numbers() -> None:
    blocks = _MOD.parse_blocks(_SAMPLE)
    assert [b.number for b in blocks] == [1, 2, 10, 11, 12]
    assert [b.qid for b in blocks] == ["Q-0001", "Q-0002", "Q-0010", "Q-0011", "Q-0012"]


def test_title_and_date_extracted() -> None:
    blocks = _MOD.parse_blocks(_SAMPLE)
    first = blocks[0]
    assert first.title == "A decided thing"
    assert first.date == "2026-06-01"
    # A block without a trailing date still parses (no date, full title).
    obs = blocks[-1]
    assert obs.title == "An observation"
    assert obs.date == ""


def test_classification() -> None:
    by_id = {b.qid: b.status for b in _MOD.parse_blocks(_SAMPLE)}
    assert by_id["Q-0001"] == "decided"  # DECISION
    assert by_id["Q-0002"] == "decided"  # ANSWERED
    assert by_id["Q-0010"] == "open"  # OPEN
    assert by_id["Q-0011"] == "open"  # PARTLY DECIDED -> open (checked before DECIDED)
    assert by_id["Q-0012"] == "unclassified"  # OBSERVED is neither


def test_next_number() -> None:
    blocks = _MOD.parse_blocks(_SAMPLE)
    assert _MOD.next_number(blocks) == "Q-0013"  # highest (12) + 1
    assert _MOD.next_number([]) == "Q-0001"


def test_classify_tokens() -> None:
    assert _MOD.classify("DECIDED + APPLIED 2026-06-16") == "decided"
    assert _MOD.classify("NOW LIVE") == "decided"
    assert _MOD.classify("PROPOSED") == "open"
    assert _MOD.classify("Status:") == "unclassified"


def test_real_router_parses() -> None:
    """Smoke test against the committed router: it parses and the next number is sane."""
    router = REPO_ROOT / "docs" / "owner" / "maintainer-question-router.md"
    if not router.exists():  # pragma: no cover - the file is committed
        return
    blocks = _MOD.parse_blocks(router.read_text(encoding="utf-8"))
    assert len(blocks) > 100  # the router is large and append-only
    numbers = [b.number for b in blocks]
    assert max(numbers) >= 179  # Q-0179 was appended this initiative
    # Every block classified into exactly one of the three buckets.
    assert all(b.status in {"open", "decided", "unclassified"} for b in blocks)
