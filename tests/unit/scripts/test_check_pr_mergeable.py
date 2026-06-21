"""Temp-repo tests for ``scripts/check_pr_mergeable.py``.

The git-based mergeability check is the agent-side companion to the conflict-guard: it must agree
with ``git`` ground truth and never trust GitHub. These build real repos with known topologies and
assert the verdict + exit code, so a regression fails CI. Runs with ``--no-fetch`` and a local
``--base`` ref (no remote in a temp repo).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "check_pr_mergeable.py"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _commit(repo: Path, name: str, content: str, msg: str) -> str:
    (repo / name).write_text(content)
    _git(repo, "add", name)
    _git(repo, "commit", "-qm", msg)
    return _git(repo, "rev-parse", "HEAD")


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--no-fetch", *args],
        cwd=repo,
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "r"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@example.com")
    _git(r, "config", "user.name", "t")
    _commit(r, "f.txt", "base\n", "base")
    return r


def test_clean_reports_and_exits_zero(repo: Path) -> None:
    """Disjoint edits merge cleanly: CLEAN verdict, exit 0 even with --strict."""
    c0 = _git(repo, "rev-parse", "HEAD")
    _git(repo, "branch", "feat", c0)
    _commit(repo, "m.txt", "main\n", "main work")  # main advances
    _git(repo, "checkout", "-q", "feat")
    feat = _commit(repo, "f2.txt", "feat\n", "feat work")  # feat advances elsewhere

    r = _run(repo, "--base", "main", "--head", feat, "--strict")
    assert r.returncode == 0, r.stderr
    assert "conflict: CLEAN" in r.stdout
    assert "no conflict" in r.stdout


def test_dirty_fails_only_under_strict(repo: Path) -> None:
    """Same-line divergence is DIRTY: --strict exits 1, report mode still exits 0."""
    c0 = _git(repo, "rev-parse", "HEAD")
    _git(repo, "branch", "feat", c0)
    _commit(repo, "f.txt", "main-change\n", "main edits f")
    _git(repo, "checkout", "-q", "feat")
    feat = _commit(repo, "f.txt", "feat-change\n", "feat edits f")

    report = _run(repo, "--base", "main", "--head", feat)
    assert report.returncode == 0, report.stderr  # report mode never fails
    assert "conflict: DIRTY" in report.stdout
    assert "real merge conflict" in report.stdout

    strict = _run(repo, "--base", "main", "--head", feat, "--strict")
    assert strict.returncode == 1
    assert "conflict: DIRTY" in strict.stdout


def test_behind_is_informational_not_a_failure(repo: Path) -> None:
    """A clean-but-behind branch reports BEHIND but never fails (out-of-date != conflict)."""
    c0 = _git(repo, "rev-parse", "HEAD")
    _git(repo, "branch", "feat", c0)
    _commit(repo, "m.txt", "main\n", "main work")
    _git(repo, "checkout", "-q", "feat")
    feat = _commit(repo, "f2.txt", "feat\n", "feat work")

    r = _run(repo, "--base", "main", "--head", feat, "--strict")
    assert r.returncode == 0
    assert "behind:   BEHIND" in r.stdout
