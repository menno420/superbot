"""check_session_close_gate asserts every [session-close-gate] checker is wired in."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).parents[3]


def _load():
    spec = importlib.util.spec_from_file_location(
        "check_session_close_gate",
        _REPO / "scripts" / "check_session_close_gate.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


csg = _load()


# --------------------------------------------------------------------------- live
def test_live_repo_passes():
    """Ground truth (Q-0105): the real repo is correctly wired after this PR."""
    assert csg.run() == []


def test_main_exits_zero_and_reports_ok(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["check_session_close_gate.py"])
    assert csg.main() == 0
    assert "OK" in capsys.readouterr().out


def test_at_least_the_known_gates_are_sentinel_marked():
    """The 6 retrofitted checkers + the meta-check itself all carry the sentinel."""
    marked = set(csg.sentinel_checkers())
    for name in (
        "check_docs.py",
        "check_session_log.py",
        "check_current_state_ledger.py",
        "check_plan_code_drift.py",
        "check_sector_next_freshness.py",
        "check_reconciliation_due.py",
        "check_session_close_gate.py",
    ):
        assert name in marked, f"{name} lost its {csg.SENTINEL} sentinel"


# ------------------------------------------------------------------- block parsing
_SKILL = """\
# /session-close

### Step 3b — previous-session review
do a thing with scripts/not_a_gate.py mentioned here (must be ignored).

### Step 4 — quality gate

```bash
python3.10 scripts/check_alpha.py --strict
python3.10 scripts/check_quality.py --check-only
```

### Step 5 — commit
also mentions scripts/check_beta.py (outside Step 4 — must be ignored).
"""


def test_step4_block_isolated_from_neighbours():
    block = csg.step4_block(_SKILL)
    assert "check_alpha.py" in block
    # Step 3b and Step 5 references must not leak into the Step-4 block.
    assert "not_a_gate.py" not in block
    assert "check_beta.py" not in block


def test_step4_script_refs():
    refs = csg.step4_script_refs(csg.step4_block(_SKILL))
    assert refs == {"check_alpha.py", "check_quality.py"}


# ----------------------------------------------------------------- finding logic
def _setup(tmp_path, monkeypatch, *, scripts: dict[str, str], skill_step4: str):
    scripts_dir = tmp_path / "scripts"
    skill_dir = tmp_path / ".claude" / "skills" / "session-close"
    scripts_dir.mkdir()
    skill_dir.mkdir(parents=True)
    for name, body in scripts.items():
        (scripts_dir / name).write_text(body, encoding="utf-8")
    (skill_dir / "SKILL.md").write_text(
        "# skill\n\n### Step 4 — quality gate\n\n"
        f"```bash\n{skill_step4}\n```\n\n### Step 5\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(csg, "SCRIPTS_DIR", scripts_dir)
    monkeypatch.setattr(csg, "SKILL_FILE", skill_dir / "SKILL.md")


def test_forward_flags_sentinel_checker_not_in_step4(tmp_path, monkeypatch):
    """A checker that declares the sentinel but is not wired in is flagged."""
    _setup(
        tmp_path,
        monkeypatch,
        scripts={
            "check_wired.py": f"'''{csg.SENTINEL} doc'''\n",
            "check_orphan.py": f"'''{csg.SENTINEL} doc'''\n",
            "check_plain.py": "'''no marker'''\n",
        },
        skill_step4="python3.10 scripts/check_wired.py",
    )
    findings = csg.run()
    assert len(findings) == 1
    assert "check_orphan.py" in findings[0]
    # The wired one and the unmarked one are not flagged.
    assert all("check_wired.py" not in f for f in findings)
    assert all("check_plain.py" not in f for f in findings)


def test_reverse_flags_dangling_step4_reference(tmp_path, monkeypatch):
    """A Step-4 reference to a check_*.py that does not exist is flagged."""
    _setup(
        tmp_path,
        monkeypatch,
        scripts={"check_wired.py": f"'''{csg.SENTINEL}'''\n"},
        skill_step4=(
            "python3.10 scripts/check_wired.py\n"
            "python3.10 scripts/check_gone.py"
        ),
    )
    findings = csg.run()
    assert len(findings) == 1
    assert "check_gone.py" in findings[0]


def test_non_check_step4_reference_is_not_required_to_exist(tmp_path, monkeypatch):
    """The reverse direction only governs check_*.py gates (not e.g. check_quality is fine,
    but a non-check helper script reference is ignored entirely)."""
    _setup(
        tmp_path,
        monkeypatch,
        scripts={"check_wired.py": f"'''{csg.SENTINEL}'''\n"},
        skill_step4=(
            "python3.10 scripts/check_wired.py\n"
            "python3.10 scripts/some_helper.py"  # not a check_ file, never required to exist
        ),
    )
    assert csg.run() == []


def test_missing_skill_file_reports_error(tmp_path, monkeypatch):
    monkeypatch.setattr(csg, "SKILL_FILE", tmp_path / "nope.md")
    findings = csg.run()
    assert findings and "cannot read" in findings[0]
