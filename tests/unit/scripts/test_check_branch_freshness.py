"""Tests for ``scripts/check_branch_freshness.py`` — the Q-0138 staleness advisory hook."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_MOD = REPO_ROOT / "scripts" / "check_branch_freshness.py"

_spec = importlib.util.spec_from_file_location("check_branch_freshness", _MOD)
assert _spec and _spec.loader
cbf = importlib.util.module_from_spec(_spec)
sys.modules["check_branch_freshness"] = cbf
_spec.loader.exec_module(cbf)


# --- _is_git_push -----------------------------------------------------------------------


def test_is_git_push_recognizes_plain_and_chained() -> None:
    mk = lambda cmd: f'{{"tool_name":"Bash","tool_input":{{"command":"{cmd}"}}}}'
    assert cbf._is_git_push(mk("git push origin my-branch")) is True
    assert cbf._is_git_push(mk("git add -A && git commit -m x && git push")) is True
    assert cbf._is_git_push(mk("git push -u origin x")) is True


def test_is_git_push_rejects_non_push_and_other_tools() -> None:
    mk = lambda cmd: f'{{"tool_name":"Bash","tool_input":{{"command":"{cmd}"}}}}'
    assert cbf._is_git_push(mk("git status")) is False
    assert cbf._is_git_push(mk("ls -la")) is False
    # A commit message merely *mentioning* push must not trip it.
    assert cbf._is_git_push(mk("git commit -m 'ready to push'")) is False
    assert cbf._is_git_push('{"tool_name":"Edit","tool_input":{}}') is False
    assert cbf._is_git_push("not json") is False


# --- _freshness_warning -----------------------------------------------------------------


def _fake_git(responses: dict[tuple[str, ...], str]):
    def _git(*args: str, timeout: int = 15) -> str:
        return responses.get(args, "")

    return _git


def test_no_warning_when_up_to_date(monkeypatch) -> None:
    monkeypatch.setattr(
        cbf,
        "_git",
        _fake_git(
            {
                ("rev-parse", "--abbrev-ref", "HEAD"): "claude/my-branch",
                ("rev-list", "--count", "HEAD..origin/main"): "0",
            }
        ),
    )
    assert cbf._freshness_warning() is None


def test_no_warning_on_main_or_detached(monkeypatch) -> None:
    monkeypatch.setattr(
        cbf, "_git", _fake_git({("rev-parse", "--abbrev-ref", "HEAD"): "main"})
    )
    assert cbf._freshness_warning() is None
    monkeypatch.setattr(
        cbf, "_git", _fake_git({("rev-parse", "--abbrev-ref", "HEAD"): "HEAD"})
    )
    assert cbf._freshness_warning() is None


def test_warning_lists_prs_and_hot_files_when_behind(monkeypatch) -> None:
    monkeypatch.setattr(
        cbf,
        "_git",
        _fake_git(
            {
                ("rev-parse", "--abbrev-ref", "HEAD"): "claude/my-branch",
                ("rev-list", "--count", "HEAD..origin/main"): "3",
                ("log", "--merges", "--pretty=format:%s", "HEAD..origin/main"): (
                    "Merge PR #855: BTD6 path resolution\nMerge PR #854: media diagnostics"
                ),
                ("diff", "--name-only", "HEAD...origin/main"): (
                    "docs/owner/active-work.md\ndisbot/services/metrics.py"
                ),
            }
        ),
    )
    warning = cbf._freshness_warning()
    assert warning is not None
    assert "3 commit(s) behind" in warning
    assert "#855" in warning and "#854" in warning
    # The cross-cutting ledger file must be called out; the runtime file should not be.
    assert "docs/owner/active-work.md" in warning
    assert "metrics.py" not in warning


# --- main (always non-blocking) ---------------------------------------------------------


def test_main_always_exits_zero(monkeypatch) -> None:
    monkeypatch.setattr(cbf, "_freshness_warning", lambda: "behind!")
    assert cbf.main(["--event", "stop"]) == 0


def test_main_pretooluse_skips_non_push(monkeypatch, capsys) -> None:
    # Non-push command → returns 0 without ever computing freshness.
    called = {"n": 0}
    monkeypatch.setattr(cbf, "_freshness_warning", lambda: called.__setitem__("n", 1))
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(sys.stdin, "read", lambda: '{"tool_name":"Bash","tool_input":{"command":"ls"}}')
    assert cbf.main(["--event", "pretooluse"]) == 0
    assert called["n"] == 0
