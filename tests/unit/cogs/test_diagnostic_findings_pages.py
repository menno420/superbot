"""Tests for build_findings_pages — paginated health findings (cert punch #2).

`!platform findings` previously rendered only the first
`_HEALTH_FINDINGS_SHOWN` rows in one embed; `build_findings_pages` chunks all
fetched rows across pages so dense output stays reachable via the paginator.
"""

from __future__ import annotations

from cogs.diagnostic._platform_embeds import (
    build_findings_embed,
    build_findings_pages,
)
from services.diagnostic_embeds import _FINDINGS_PER_PAGE


def _rows(n: int) -> list[dict]:
    return [
        {
            "severity": "warn",
            "status": "open",
            "category": f"cat.{i}",
            "message": f"finding number {i}",
            "occurrence_count": i + 1,
            "file_hint": f"disbot/file_{i}.py",
        }
        for i in range(n)
    ]


_COUNTS = {"open": 100, "resolved": 2, "ignored": 1}


def test_single_page_when_rows_fit_one_page():
    rows = _rows(_FINDINGS_PER_PAGE)
    pages = build_findings_pages(rows, status="open", counts=_COUNTS, is_owner=False)
    assert len(pages) == 1
    # The one-page path delegates to the legacy embed (no "Page i/N" prefix).
    assert not (pages[0].footer.text or "").startswith("Page ")


def test_empty_rows_returns_one_none_page():
    pages = build_findings_pages([], status="open", counts={}, is_owner=False)
    assert len(pages) == 1
    assert pages[0].fields[0].value == "*(none)*"


def test_many_rows_split_into_pages_nothing_dropped():
    rows = _rows(_FINDINGS_PER_PAGE * 2 + 1)  # forces 3 pages
    pages = build_findings_pages(rows, status="all", counts=_COUNTS, is_owner=True)
    assert len(pages) == 3
    n = len(pages)
    for i, page in enumerate(pages, start=1):
        assert (page.footer.text or "").startswith(f"Page {i}/{n}")
        # Each page block stays under Discord's per-field 1024-char limit.
        assert len(page.fields[0].value or "") <= 1024
        assert f"{len(rows)} total" in page.fields[0].name


def test_owner_view_shows_file_hint_admin_view_does_not():
    rows = _rows(_FINDINGS_PER_PAGE * 2)  # multi-page so the paginated path runs
    owner_pages = build_findings_pages(
        rows, status="open", counts=_COUNTS, is_owner=True,
    )
    admin_pages = build_findings_pages(
        rows, status="open", counts=_COUNTS, is_owner=False,
    )
    owner_text = "\n".join(p.fields[0].value or "" for p in owner_pages)
    admin_text = "\n".join(p.fields[0].value or "" for p in admin_pages)
    assert "disbot/file_0.py" in owner_text
    assert "disbot/file_0.py" not in admin_text
    assert "owner view" in (owner_pages[0].footer.text or "")
    assert "admin view (redacted)" in (admin_pages[0].footer.text or "")


def test_single_page_matches_legacy_embed_shape():
    rows = _rows(3)
    page = build_findings_pages(rows, status="open", counts=_COUNTS, is_owner=True)[0]
    legacy = build_findings_embed(rows, status="open", counts=_COUNTS, is_owner=True)
    assert page.title == legacy.title
    assert page.fields[0].value == legacy.fields[0].value
