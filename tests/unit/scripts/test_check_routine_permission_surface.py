"""Tests for ``scripts/check_routine_permission_surface.py``.

The routine permission-surface lint flags routine-common commands that would hit a
``permissions.ask`` brake and silently stall an unattended run (the Q-0161 lesson).
These tests pin the prefix-match semantics, the compound-command split, the
deny>ask>allow precedence, the warn-only-vs-strict exit behavior, and a guard that
the live repo's settings.json keeps every routine command on ``allow``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_MOD = REPO_ROOT / "scripts" / "check_routine_permission_surface.py"

_spec = importlib.util.spec_from_file_location("check_routine_permission_surface", _MOD)
assert _spec and _spec.loader
crps = importlib.util.module_from_spec(_spec)
sys.modules["check_routine_permission_surface"] = crps
_spec.loader.exec_module(crps)


# --- matches() — prefix-match semantics --------------------------------------


def test_matches_trailing_star_is_prefix() -> None:
    assert crps.matches("rm -r foo", "rm -r*") is True
    assert crps.matches("rm -rf /tmp/x", "rm -r*") is True


def test_matches_trailing_star_requires_prefix() -> None:
    # `git push` should NOT match the `rm -r*` rule.
    assert crps.matches("git push origin main", "rm -r*") is False


def test_matches_exact_when_no_star() -> None:
    assert crps.matches("true", "true") is True
    assert crps.matches("true; rm", "true") is False


def test_matches_space_star_rule() -> None:
    # `Bash(tr *)` — the deliberate trailing space then star.
    assert crps.matches("tr a b", "tr *") is True
    # bare `tr` with no args still matches the word-prefix form.
    assert crps.matches("tr", "tr *") is True
    # `transmute` must NOT match `tr *` (the space prevents the false prefix).
    assert crps.matches("transmute x", "tr *") is False


def test_matches_is_whitespace_insensitive() -> None:
    assert crps.matches("rm   -r   foo", "rm -r*") is True


# --- split_command() — compound commands -------------------------------------


def test_split_on_and() -> None:
    assert crps.split_command("a && b && c") == ["a", "b", "c"]


def test_split_on_mixed_separators() -> None:
    assert crps.split_command("a && b ; c || d | e") == ["a", "b", "c", "d", "e"]


def test_split_single_command() -> None:
    assert crps.split_command("git push origin main") == ["git push origin main"]


def test_split_drops_empties() -> None:
    assert crps.split_command("a &&  && b") == ["a", "b"]


# --- resolve() — deny > ask > allow precedence -------------------------------


def _rules() -> tuple[list[str], list[str], list[str]]:
    allow = ["git push*", "rm -f*", "python3.10 scripts/check_*"]
    ask = ["rm -r*", "railway*", "psql*"]
    deny = ["sudo rm -rf /*"]
    return allow, ask, deny


def test_resolve_allow() -> None:
    allow, ask, deny = _rules()
    assert crps.resolve("git push origin main", allow, ask, deny) == "allow"
    assert crps.resolve("rm -f scratch.txt", allow, ask, deny) == "allow"


def test_resolve_ask_brake() -> None:
    allow, ask, deny = _rules()
    assert crps.resolve("rm -r build/", allow, ask, deny) == "ask"
    assert crps.resolve("railway up", allow, ask, deny) == "ask"


def test_resolve_ask_outranks_allow() -> None:
    # If a command matches BOTH an allow and an ask rule, ask wins (it stalls).
    allow = ["rm*"]
    ask = ["rm -r*"]
    assert crps.resolve("rm -r x", allow, ask, []) == "ask"


def test_resolve_deny_outranks_ask() -> None:
    allow, ask, deny = _rules()
    assert crps.resolve("sudo rm -rf /etc", allow, ask, deny) == "deny"


def test_resolve_unmatched_is_prompt() -> None:
    allow, ask, deny = _rules()
    assert crps.resolve("frobnicate --hard", allow, ask, deny) == "prompt"


# --- load_rules() — only Bash() rules, by bucket -----------------------------


def test_load_rules_extracts_bash_patterns(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(
        json.dumps(
            {
                "permissions": {
                    "allow": ["Bash(git push*)", "Read", "mcp__github__merge_pull_request"],
                    "ask": ["Bash(rm -r*)", "Bash(railway*)"],
                    "deny": ["Bash(sudo rm -rf /*)"],
                }
            }
        ),
        encoding="utf-8",
    )
    allow, ask, deny = crps.load_rules(settings)
    assert allow == ["git push*"]  # Read / mcp rules dropped
    assert ask == ["rm -r*", "railway*"]
    assert deny == ["sudo rm -rf /*"]


def test_load_rules_missing_buckets(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"permissions": {}}), encoding="utf-8")
    assert crps.load_rules(settings) == ([], [], [])


# --- scan() — findings -------------------------------------------------------


def test_scan_flags_ask_in_compound() -> None:
    # The Q-0161 case: a compound where one part hits `ask`.
    allow = ["python3.10 scripts/check_*"]
    ask = ["rm -r*"]
    findings = crps.scan(
        ("python3.10 scripts/check_quality.py && rm -r build",), allow, ask, []
    )
    assert len(findings) == 1
    assert findings[0].verdict == "ask"
    assert findings[0].part == "rm -r build"
    assert findings[0].rule == "rm -r*"


def test_scan_clean_when_all_allow() -> None:
    allow = ["git push*", "rm -f*"]
    findings = crps.scan(("git push origin x && rm -f scratch",), allow, [], [])
    assert findings == []


def test_scan_unmatched_reported_only_when_requested() -> None:
    findings_default = crps.scan(("mystery-cmd --go",), [], [], [])
    assert findings_default == []  # unmatched suppressed by default
    findings_incl = crps.scan(("mystery-cmd --go",), [], [], [], include_unmatched=True)
    assert len(findings_incl) == 1
    assert findings_incl[0].verdict == "prompt"


# --- main() — exit codes -----------------------------------------------------


def test_main_clean_exits_zero(monkeypatch, capsys) -> None:
    monkeypatch.setattr(crps, "scan", lambda *a, **k: [])
    assert crps.main([]) == 0
    assert "resolve to `allow`" in capsys.readouterr().out


def test_main_ask_hit_warn_only_default(monkeypatch, capsys) -> None:
    finding = crps.Finding("a && rm -r b", "rm -r b", "ask", "rm -r*")
    monkeypatch.setattr(crps, "scan", lambda *a, **k: [finding])
    # Warn-only default: exit 0 even with an ask hit.
    assert crps.main([]) == 0
    out = capsys.readouterr().out
    assert "ASK-BRAKE" in out and "rm -r b" in out


def test_main_ask_hit_strict_fails(monkeypatch) -> None:
    finding = crps.Finding("a && rm -r b", "rm -r b", "ask", "rm -r*")
    monkeypatch.setattr(crps, "scan", lambda *a, **k: [finding])
    assert crps.main(["--strict"]) == 1


def test_main_unreadable_settings_exits_zero(tmp_path, capsys) -> None:
    missing = tmp_path / "nope.json"
    assert crps.main(["--settings", str(missing), "--strict"]) == 0
    assert "cannot read" in capsys.readouterr().out


# --- live-repo guard ---------------------------------------------------------


def test_live_settings_keep_all_routine_commands_allowed() -> None:
    """The shipped .claude/settings.json must not stall any routine command.

    This is the lint's reason for existing: if a settings change ever pushes a
    routine-common command onto the `ask` list, this test (and the strict CLI)
    goes red so it is caught before a scheduled run is wasted.
    """
    settings = REPO_ROOT / ".claude" / "settings.json"
    allow, ask, deny = crps.load_rules(settings)
    findings = crps.scan(crps.ROUTINE_COMMANDS, allow, ask, deny)
    ask_hits = [f for f in findings if f.verdict == "ask"]
    assert not ask_hits, "\n".join(f.describe() for f in ask_hits)
