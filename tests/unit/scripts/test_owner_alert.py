"""Tests for scripts/lib/owner_alert.py — the shared idempotent owner-alert issue opener (Q-0089).

Cover the pure orchestration (search → dedupe → create) with injected fakes: absent issue → create;
present issue → no create (dedupe); gh unavailable (search None) → no create (conservative); create
failure → False.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "owner_alert",
    Path(__file__).resolve().parents[3] / "scripts" / "lib" / "owner_alert.py",
)
assert _SPEC and _SPEC.loader
oa = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(oa)


def test_alert_marker_namespaces_by_kind():
    assert oa.alert_marker("ci-coverage", 42) == "<!-- ci-coverage-alert:42 -->"
    # Different watchdogs never collide on the same subject.
    assert oa.alert_marker("codeql-coverage", 42) != oa.alert_marker("ci-coverage", 42)


def test_ensure_issue_creates_when_absent():
    created: list[tuple[str, str]] = []
    ok = oa.ensure_issue(
        "r",
        "<!-- m -->",
        "T",
        "body <!-- m -->",
        search=lambda repo, marker: False,
        create=lambda repo, title, body: bool(created.append((title, body))) or True,
    )
    assert ok is True
    assert created == [("T", "body <!-- m -->")]


def test_ensure_issue_dedupes_when_present():
    created: list[int] = []
    ok = oa.ensure_issue(
        "r",
        "<!-- m -->",
        "T",
        "B",
        search=lambda repo, marker: True,  # an alert already exists
        create=lambda repo, title, body: bool(created.append(1)) or True,
    )
    assert ok is True
    assert created == []  # did NOT open a duplicate


def test_ensure_issue_skips_create_when_gh_unavailable():
    created: list[int] = []
    ok = oa.ensure_issue(
        "r",
        "<!-- m -->",
        "T",
        "B",
        search=lambda repo, marker: None,  # gh unavailable — dedupe state unknown
        create=lambda repo, title, body: bool(created.append(1)) or True,
    )
    assert ok is False
    assert (
        created == []
    )  # conservative: never create when a duplicate can't be ruled out


def test_ensure_issue_returns_false_on_create_failure():
    ok = oa.ensure_issue(
        "r",
        "<!-- m -->",
        "T",
        "B",
        search=lambda repo, marker: False,
        create=lambda repo, title, body: False,
    )
    assert ok is False
