"""Tests for the pure ``classify`` core of ``scripts/check_loop_health.py``.

The ``gh``-shelling fetch is not exercised in CI (no auth there); only the pure
verdict logic is tested, fed synthetic issue lists shaped like ``gh issue list --json``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_loop_health.py"


@pytest.fixture(scope="module")
def lh():
    spec = importlib.util.spec_from_file_location("check_loop_health_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _issue(number, title, author, state="CLOSED"):
    return {
        "number": number,
        "title": title,
        "author_login": author,
        "state": state,
        "created_at": "2026-06-14T06:00:00Z",
    }


def _status(verdicts, check):
    return next(s for c, s, _ in verdicts if c == check)


def test_routine_pat_pass_when_trigger_is_user_authored(lh):
    # The real 2026-06-14 signal: an auto-opened scheduled run authored by the PAT owner.
    issues = [_issue(819, "Scheduled executor run (2026-06-14 06:04 UTC)", "menno420")]
    assert _status(lh.classify(issues), "ROUTINE_PAT") == "PASS"


def test_routine_pat_fail_when_trigger_is_bot_authored(lh):
    issues = [
        _issue(
            768,
            "Scheduled executor run (2026-06-13 01:20 UTC)",
            "github-actions[bot]",
        ),
    ]
    assert _status(lh.classify(issues), "ROUTINE_PAT") == "FAIL"


def test_routine_pat_bare_bot_login_also_fails(lh):
    issues = [_issue(781, "Docs reconciliation due (Q-0107)", "github-actions")]
    assert _status(lh.classify(issues), "ROUTINE_PAT") == "FAIL"


def test_routine_pat_skip_when_no_trigger_issue(lh):
    issues = [_issue(1, "Some unrelated issue", "menno420")]
    assert _status(lh.classify(issues), "ROUTINE_PAT") == "SKIP"


def test_routine_pat_reads_newest_trigger_first(lh):
    # Newest-first: a recent user-authored trigger wins over an older bot one.
    issues = [
        _issue(841, "Docs reconciliation due (Q-0107)", "menno420"),
        _issue(781, "Docs reconciliation due (Q-0107)", "github-actions"),
    ]
    assert _status(lh.classify(issues), "ROUTINE_PAT") == "PASS"


def test_backup_fail_when_open_backup_issue_present(lh):
    issues = [
        _issue(
            823,
            "Postgres backup failed (2026-06-14)",
            "github-actions",
            state="OPEN",
        ),
    ]
    assert _status(lh.classify(issues), "DATABASE_PUBLIC_URL") == "FAIL"


def test_backup_pass_when_backup_issue_closed(lh):
    issues = [
        _issue(
            773,
            "Postgres backup failed (2026-06-13)",
            "github-actions",
            state="CLOSED",
        ),
    ]
    assert _status(lh.classify(issues), "DATABASE_PUBLIC_URL") == "PASS"


def test_loop_self_fired_pass_on_scheduled_issue(lh):
    issues = [_issue(819, "Scheduled executor run (2026-06-14 06:04 UTC)", "menno420")]
    assert _status(lh.classify(issues), "loop-self-fired") == "PASS"


def test_all_three_checks_always_present(lh):
    verdicts = lh.classify([])
    checks = {c for c, _, _ in verdicts}
    assert checks == {"ROUTINE_PAT", "DATABASE_PUBLIC_URL", "loop-self-fired"}


# --- fetch_issues source-selection seam (gh → REST → SKIP) --------------------------------
# The two fetchers are stubbed so no live network/subprocess runs in CI; we only assert the
# selection order and the labelled source the script reports.


def test_fetch_prefers_gh_when_available(lh, monkeypatch):
    sentinel = [_issue(1, "x", "menno420")]
    monkeypatch.setattr(lh, "_fetch_via_gh", lambda limit=40: sentinel)
    monkeypatch.setattr(
        lh, "_fetch_via_rest", lambda limit=40: pytest.fail("should not call REST")
    )
    issues, source = lh.fetch_issues()
    assert source == "gh"
    assert issues is sentinel


def test_fetch_falls_back_to_rest_when_gh_absent(lh, monkeypatch):
    sentinel = [_issue(2, "y", "menno420")]
    monkeypatch.setattr(lh, "_fetch_via_gh", lambda limit=40: None)
    monkeypatch.setattr(lh, "_fetch_via_rest", lambda limit=40: sentinel)
    issues, source = lh.fetch_issues()
    assert source == "REST"
    assert issues is sentinel


def test_fetch_skips_when_neither_available(lh, monkeypatch):
    monkeypatch.setattr(lh, "_fetch_via_gh", lambda limit=40: None)
    monkeypatch.setattr(lh, "_fetch_via_rest", lambda limit=40: None)
    issues, source = lh.fetch_issues()
    assert source == "SKIP"
    assert issues is None


def test_rest_fetch_returns_none_without_token(lh, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert lh._fetch_via_rest() is None


def test_rest_fetch_maps_user_login_field(lh, monkeypatch):
    # The REST `issues` payload nests the author under `user.login` (gh uses `author.login`).
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    payload = json.dumps(
        [
            {
                "number": 1171,
                "title": "Docs reconciliation due (Q-0107)",
                "user": {"login": "menno420"},
                "state": "open",
                "created_at": "2026-06-20T06:00:00Z",
            },
        ],
    ).encode("utf-8")

    class _Resp:
        def read(self):
            return payload

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(lh.urllib.request, "urlopen", lambda req, timeout=30: _Resp())
    issues = lh._fetch_via_rest()
    assert issues == [
        {
            "number": 1171,
            "title": "Docs reconciliation due (Q-0107)",
            "author_login": "menno420",
            "state": "open",
            "created_at": "2026-06-20T06:00:00Z",
        },
    ]
    # And it classifies as a ROUTINE_PAT PASS end-to-end.
    assert _status(lh.classify(issues), "ROUTINE_PAT") == "PASS"
