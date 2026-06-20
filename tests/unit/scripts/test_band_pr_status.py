"""Tests for ``scripts/band_pr_status.py`` — the band PR merge-status classifier.

The ``gh``/REST fetchers are not exercised against the network in CI; only the pure
``classify_band`` core, the marker parse, and the fetch source-selection seam are tested,
fed synthetic inputs shaped like ``git log`` subjects and ``gh pr list --json`` rows.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "band_pr_status.py"


@pytest.fixture(scope="module")
def bs():
    spec = importlib.util.spec_from_file_location("band_pr_status_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _pr(number, state, merged, title=""):
    return {"number": number, "state": state, "merged": merged, "title": title}


def _status_of(rows, number):
    return next(s for n, s, _ in rows if n == number)


# --- marker parse -------------------------------------------------------------------------


def test_marker_pr_reads_the_reconciliation_marker(bs):
    text = "blah\n> **Last reconciliation pass:** PR #1170 (2026-06-20 …)\nmore"
    assert bs.marker_pr(text) == 1170


def test_marker_pr_none_when_absent(bs):
    assert bs.marker_pr("no marker here") is None


# --- classify_band core -------------------------------------------------------------------


def test_merged_on_main_classifies_as_merged(bs):
    merged = {1175: "Merge PR #1175: a thing", 1174: "Merge pull request #1174"}
    rows = bs.classify_band(1170, merged, prs=None)
    assert _status_of(rows, 1175) == bs.MERGED
    assert _status_of(rows, 1174) == bs.MERGED


def test_only_numbers_above_marker_are_reported(bs):
    merged = {1170: "Merge PR #1170 (the marker itself)", 1175: "Merge PR #1175"}
    rows = bs.classify_band(1170, merged, prs=None)
    numbers = {n for n, _, _ in rows}
    assert numbers == {1175}  # the marker and anything below it are excluded


def test_rows_are_newest_first(bs):
    merged = {1175: "a", 1177: "b", 1176: "c"}
    rows = bs.classify_band(1170, merged, prs=None)
    assert [n for n, _, _ in rows] == [1177, 1176, 1175]


def test_closed_unmerged_split_from_open_with_pr_list(bs):
    # #1133-style: closed but never merged → closed-unmerged, distinct from a still-open PR.
    merged = {1175: "Merge PR #1175"}
    prs = [
        _pr(1175, "closed", merged=True, title="merged one"),
        _pr(1176, "closed", merged=False, title="superseded + closed"),
        _pr(1177, "open", merged=False, title="still cooking"),
    ]
    rows = bs.classify_band(1170, merged, prs)
    assert _status_of(rows, 1175) == bs.MERGED
    assert _status_of(rows, 1176) == bs.CLOSED_UNMERGED
    assert _status_of(rows, 1177) == bs.OPEN


def test_git_merged_wins_over_a_disagreeing_pr_list(bs):
    # Git ground truth: a merge commit on main means merged even if a truncated/stale PR
    # list reports the PR as open.
    merged = {1180: "Merge PR #1180: shipped"}
    prs = [_pr(1180, "open", merged=False, title="stale list says open")]
    rows = bs.classify_band(1170, merged, prs)
    assert _status_of(rows, 1180) == bs.MERGED


def test_pr_list_surfaces_a_closed_pr_git_never_saw(bs):
    # A closed-unmerged PR never reaches main, so git can't enumerate it; the PR list does.
    rows = bs.classify_band(1170, merged_on_main={}, prs=[_pr(1181, "closed", False)])
    assert _status_of(rows, 1181) == bs.CLOSED_UNMERGED


def test_token_absent_reports_only_merged_rows(bs):
    # Without a PR list, only git's merged-on-main set is knowable (the degraded mode).
    merged = {1175: "Merge PR #1175", 1176: "Merge PR #1176"}
    rows = bs.classify_band(1170, merged, prs=None)
    assert {n for n, _, _ in rows} == {1175, 1176}
    assert all(s == bs.MERGED for _, s, _ in rows)


def test_pr_list_below_marker_is_ignored(bs):
    rows = bs.classify_band(1170, {}, prs=[_pr(1169, "open", False)])
    assert rows == []


# --- fetch source-selection seam (gh → REST → none) ---------------------------------------


def test_fetch_prefers_gh_when_available(bs, monkeypatch):
    sentinel = [_pr(1, "open", False)]
    monkeypatch.setattr(bs, "_fetch_prs_via_gh", lambda limit: sentinel)
    monkeypatch.setattr(
        bs, "_fetch_prs_via_rest", lambda limit: pytest.fail("should not call REST")
    )
    prs, source = bs.fetch_prs()
    assert source == "gh"
    assert prs is sentinel


def test_fetch_falls_back_to_rest_when_gh_absent(bs, monkeypatch):
    sentinel = [_pr(2, "open", False)]
    monkeypatch.setattr(bs, "_fetch_prs_via_gh", lambda limit: None)
    monkeypatch.setattr(bs, "_fetch_prs_via_rest", lambda limit: sentinel)
    prs, source = bs.fetch_prs()
    assert source == "REST"
    assert prs is sentinel


def test_fetch_reports_none_when_neither_available(bs, monkeypatch):
    monkeypatch.setattr(bs, "_fetch_prs_via_gh", lambda limit: None)
    monkeypatch.setattr(bs, "_fetch_prs_via_rest", lambda limit: None)
    prs, source = bs.fetch_prs()
    assert source == "none"
    assert prs is None


def test_rest_fetch_returns_none_without_token(bs, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert bs._fetch_prs_via_rest(100) is None


def test_rest_fetch_maps_merged_at_to_merged_flag(bs, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    payload = json.dumps(
        [
            {
                "number": 1175,
                "state": "closed",
                "merged_at": "2026-06-20T...",
                "title": "m",
            },
            {"number": 1176, "state": "closed", "merged_at": None, "title": "c"},
        ],
    ).encode("utf-8")

    class _Resp:
        def read(self):
            return payload

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(bs.urllib.request, "urlopen", lambda req, timeout=30: _Resp())
    prs = bs._fetch_prs_via_rest(100)
    assert prs == [
        {"number": 1175, "state": "closed", "merged": True, "title": "m"},
        {"number": 1176, "state": "closed", "merged": False, "title": "c"},
    ]


# --- end-to-end render --------------------------------------------------------------------


def test_render_table_escapes_pipes_and_shapes_markdown(bs):
    rows = [(1176, bs.CLOSED_UNMERGED, "a | b"), (1175, bs.MERGED, "ok")]
    out = bs._render_table(rows)
    assert "| PR | status | title |" in out
    assert "| #1176 | closed-unmerged | a \\| b |" in out
    assert "| #1175 | merged | ok |" in out
