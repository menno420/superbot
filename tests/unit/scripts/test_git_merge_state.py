"""Temp-repo tests pinning the deterministic merge-state logic the PR CI guards rely on.

This is the regression guard for ``scripts/git_merge_state.py``: the conflict-guard /
auto-update workflows kept getting re-broken by reaching back for GitHub's async
``mergeStateStatus``. These tests build real git repos with known conflict / clean / behind /
up-to-date topologies and assert the helper's verdict, so a regression fails CI.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "git_merge_state.py"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _state(repo: Path, mode: str, base: str, head: str) -> str:
    r = subprocess.run(
        [sys.executable, str(SCRIPT), mode, base, head],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def _commit(repo: Path, name: str, content: str, msg: str) -> str:
    (repo / name).write_text(content)
    _git(repo, "add", name)
    _git(repo, "commit", "-qm", msg)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "r"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@example.com")
    _git(r, "config", "user.name", "t")
    _commit(r, "f.txt", "base\n", "base")
    return r


def test_clean_and_behind_for_disjoint_divergence(repo: Path) -> None:
    """Branch and main edit different files: merge is CLEAN, and the branch is BEHIND main."""
    c0 = _git(repo, "rev-parse", "HEAD")
    _git(repo, "branch", "feat", c0)
    # main advances on one file
    main_sha = _commit(repo, "m.txt", "main\n", "main work")
    # feat advances on a different file
    _git(repo, "checkout", "-q", "feat")
    feat_sha = _commit(repo, "f2.txt", "feat\n", "feat work")

    assert _state(repo, "conflict", main_sha, feat_sha) == "CLEAN"
    assert _state(repo, "behind", main_sha, feat_sha) == "BEHIND"


def test_dirty_when_same_line_diverges(repo: Path) -> None:
    """Branch and main edit the SAME file divergently: merge is DIRTY."""
    c0 = _git(repo, "rev-parse", "HEAD")
    _git(repo, "branch", "feat", c0)
    main_sha = _commit(repo, "f.txt", "main-change\n", "main edits f")
    _git(repo, "checkout", "-q", "feat")
    feat_sha = _commit(repo, "f.txt", "feat-change\n", "feat edits f")

    assert _state(repo, "conflict", main_sha, feat_sha) == "DIRTY"


def test_current_when_head_contains_base(repo: Path) -> None:
    """A head that descends from base is CURRENT (not behind)."""
    base = _git(repo, "rev-parse", "HEAD")
    head = _commit(repo, "f2.txt", "more\n", "descendant")
    assert _state(repo, "behind", base, head) == "CURRENT"


def test_unknown_on_missing_object(repo: Path) -> None:
    """A non-existent sha never false-flags — both modes return UNKNOWN."""
    head = _git(repo, "rev-parse", "HEAD")
    bogus = "0" * 40
    assert _state(repo, "conflict", head, bogus) == "UNKNOWN"
    assert _state(repo, "behind", head, bogus) == "UNKNOWN"


def test_usage_error_exits_nonzero(repo: Path) -> None:
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "bogus-mode", "a", "b"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
