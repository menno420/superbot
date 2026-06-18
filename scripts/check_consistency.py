#!/usr/bin/env python3
"""UX / interaction-pattern consistency linter for SuperBot.

A companion to ``check_architecture.py``.  Where the architecture checker sees
*import layers*, this one sees *interaction patterns* — the mechanical UX house
rules that no import graph can catch (owner directive Q-0170, 2026-06-17):

  1. **edit-in-place** — a panel button/select callback that delivers its result
     as a standalone ephemeral message instead of updating the panel in place.

It is **warn-first and disposable** (Q-0105): every finding is a warning, nothing
fails CI yet.  A rule graduates to an error + a ``code-quality`` wire-in only once
it runs clean on a fresh tree across a few sessions (the Q-0120 / ``dead-unresolved``
discipline — a noisy checker trains people to ignore it).  The only valid bypass is
an allowlist entry in ``architecture_rules/consistency_exceptions.yml`` — never
suppress the check.

Provenance / reliability (Q-0105):
  - Added 2026-06-18 for the owner's "CI but for inconsistencies" ask (Q-0170).
  - **Unverified:** confirm each rule's output against ground truth across a few
    sessions before trusting its green; rules stay warn-only until proven quiet.
  - **Disposable:** if a rule proves unreliable over multiple sessions, delete it
    (or keep it allowlisted) rather than working around it.

Usage::

    python scripts/check_consistency.py                  # report mode (exit 0)
    python scripts/check_consistency.py --mode strict    # exit 1 on errors (none yet)
    python scripts/check_consistency.py --file disbot/views/x.py
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DISBOT_ROOT = REPO_ROOT / "disbot"
RULES_DIR = REPO_ROOT / "architecture_rules"
_EXCEPTIONS_FILE = "consistency_exceptions.yml"


# ---------------------------------------------------------------------------
# Finding model
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    file: Path
    line: int
    rule: str
    message: str
    qualname: str = ""
    severity: str = "warning"  # every rule is warn-only until it graduates

    def display(self, root: Path) -> str:
        try:
            rel = self.file.relative_to(root)
        except ValueError:
            rel = self.file
        tag = "ERROR" if self.severity == "error" else " WARN"
        return f"  [{tag}] {rel}:{self.line}  ({self.rule})  {self.message}"


# ---------------------------------------------------------------------------
# Allowlist
# ---------------------------------------------------------------------------


def _load_exceptions() -> dict:
    p = RULES_DIR / _EXCEPTIONS_FILE
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _is_allowlisted(rel_file: str, qualname: str, rule_cfg: dict) -> bool:
    """True if *rel_file*[::qualname] matches an allowlist ``pattern`` for the rule.

    A ``pattern`` is a ``views/...py`` path (matched as a prefix) optionally
    suffixed with ``::Class.method`` to scope the exception to one callback.
    """
    for exc in rule_cfg.get("exceptions", []):
        pattern = str(exc.get("pattern", "")).replace("disbot/", "").strip()
        if not pattern:
            continue
        if "::" in pattern:
            path_part, _, name_part = pattern.partition("::")
            if rel_file.startswith(path_part.strip()) and name_part.strip() in qualname:
                return True
        elif rel_file.startswith(pattern):
            return True
    return False


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _class_bases(node: ast.ClassDef) -> list[str]:
    """Dotted base names for a class (``["BaseView", "discord.ui.View"]``)."""
    names = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
        elif isinstance(base, ast.Attribute):
            parts = []
            cur: ast.expr = base
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            names.append(".".join(reversed(parts)))
    return names


def _is_view_class(node: ast.ClassDef) -> bool:
    """True if the class is a Discord UI view / panel (by its base names)."""
    for base in _class_bases(node):
        leaf = base.rsplit(".", 1)[-1]
        if leaf.endswith("View") or leaf == "View":
            return True
    return False


def _decorator_attr(dec: ast.expr) -> str:
    """The trailing attribute name of a decorator (``ui.button`` -> ``button``)."""
    target = dec.func if isinstance(dec, ast.Call) else dec
    if isinstance(target, ast.Attribute):
        return target.attr
    if isinstance(target, ast.Name):
        return target.id
    return ""


def _is_ui_callback(node: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    """True if the method is a ``@discord.ui.button`` / ``@ui.select`` callback."""
    return any(_decorator_attr(d) in {"button", "select"} for d in node.decorator_list)


def _call_attr(call: ast.Call) -> str:
    """The method name of a call (``x.response.send_message(...)`` -> ``send_message``)."""
    return call.func.attr if isinstance(call.func, ast.Attribute) else ""


def _is_followup_send(call: ast.Call) -> bool:
    """``<x>.followup.send(...)`` — a new (often ephemeral) message."""
    func = call.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "send"
        and isinstance(func.value, ast.Attribute)
        and func.value.attr == "followup"
    )


def _is_response_send_message(call: ast.Call) -> bool:
    """``<x>.response.send_message(...)`` — a fresh reply (not an edit)."""
    func = call.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "send_message"
        and isinstance(func.value, ast.Attribute)
        and func.value.attr == "response"
    )


def _is_ephemeral(call: ast.Call) -> bool:
    """``ephemeral=True`` among the call's keywords."""
    for kw in call.keywords:
        if kw.arg == "ephemeral" and isinstance(kw.value, ast.Constant):
            return bool(kw.value.value)
    return False


_EDIT_METHODS = frozenset({"edit_message", "edit_original_response", "edit"})


def _edits_in_place(fn: ast.AST) -> bool:
    """True if the callback updates a message in place anywhere in its body."""
    for sub in ast.walk(fn):
        if isinstance(sub, ast.Call) and _call_attr(sub) in _EDIT_METHODS:
            return True
    return False


def _unwrap(stmt: ast.stmt) -> ast.Call | None:
    """The bare ``Call`` of an expression-statement (``await x.send(...)`` -> Call)."""
    if not isinstance(stmt, ast.Expr):
        return None
    value = stmt.value
    if isinstance(value, ast.Await):
        value = value.value
    return value if isinstance(value, ast.Call) else None


def _guarded_send_lines(fn: ast.AST) -> set[int]:
    """Line numbers of ephemeral sends that are early-return guards (``send; return``).

    A validation toast (``await ...send(..., ephemeral=True)`` immediately followed
    by ``return``) is the *correct* pattern, not the edit-in-place bug — so it is
    excluded.  We scan every statement block (function body, ``if``/``for``/``with``
    branches) for an ephemeral send directly followed by a ``return``.
    """
    guarded: set[int] = set()
    for sub in ast.walk(fn):
        for attr in ("body", "orelse", "finalbody"):
            block = getattr(sub, attr, None)
            if not isinstance(block, list):
                continue
            for i, stmt in enumerate(block):
                call = _unwrap(stmt)
                if call is None or not (
                    _is_followup_send(call) or _is_response_send_message(call)
                ):
                    continue
                nxt = block[i + 1] if i + 1 < len(block) else None
                if isinstance(nxt, ast.Return):
                    guarded.add(call.lineno)
    return guarded


# ---------------------------------------------------------------------------
# Rule 1 — edit-in-place
# ---------------------------------------------------------------------------


def rule_edit_in_place(files: list[Path], exceptions: dict) -> list[Finding]:
    """Flag panel callbacks whose result is a standalone ephemeral, not an edit.

    A button/select callback that sends a *new* ephemeral message and never edits
    the panel in place delivers its outcome out-of-band — the owner's headline
    inconsistency.  Early-return validation toasts (``send; return``) are excluded;
    so are callbacks that also edit in place (a mixed/guarded path).
    """
    cfg = exceptions.get("edit_in_place", {})
    findings: list[Finding] = []

    for filepath in files:
        try:
            rel = str(filepath.relative_to(DISBOT_ROOT))
        except ValueError:
            continue
        if not rel.startswith("views/") or "test" in rel.lower():
            continue
        try:
            tree = ast.parse(filepath.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, OSError):
            continue

        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef) or not _is_view_class(cls):
                continue
            for fn in cls.body:
                if not isinstance(fn, (ast.AsyncFunctionDef, ast.FunctionDef)):
                    continue
                if not _is_ui_callback(fn) or _edits_in_place(fn):
                    continue
                qualname = f"{cls.name}.{fn.name}"
                if _is_allowlisted(rel, qualname, cfg):
                    continue
                guarded = _guarded_send_lines(fn)
                for sub in ast.walk(fn):
                    if not isinstance(sub, ast.Call):
                        continue
                    if not (_is_followup_send(sub) or _is_response_send_message(sub)):
                        continue
                    if not _is_ephemeral(sub) or sub.lineno in guarded:
                        continue
                    findings.append(
                        Finding(
                            file=filepath,
                            line=sub.lineno,
                            rule="edit_in_place",
                            qualname=qualname,
                            message=(
                                f"`{qualname}` delivers its result via a new "
                                "ephemeral message but never edits the panel in "
                                "place — prefer `interaction.response.edit_message(...)` "
                                "(allowlist in consistency_exceptions.yml if this is "
                                "a genuine new message)"
                            ),
                        ),
                    )

    return findings


# ---------------------------------------------------------------------------
# Rule registry — add a (name, fn) entry per future rule (back button, base class)
# ---------------------------------------------------------------------------


@dataclass
class Rule:
    name: str
    fn: object
    description: str = field(default="")


RULES: list[Rule] = [
    Rule(
        "edit_in_place",
        rule_edit_in_place,
        "panel callbacks that reply with a standalone ephemeral instead of editing in place",
    ),
]


# ---------------------------------------------------------------------------
# File collection + entry point
# ---------------------------------------------------------------------------


def _all_files() -> list[Path]:
    return sorted((DISBOT_ROOT / "views").rglob("*.py"))


def _counts_by_rule(findings: list[Finding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.rule] = counts.get(f.rule, 0) + 1
    return counts


def run_checks(files: list[Path], exceptions: dict) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        findings += rule.fn(files, exceptions)  # type: ignore[operator]
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="SuperBot UX consistency linter")
    parser.add_argument(
        "--mode",
        choices=["report", "strict"],
        default="report",
        help="report: always exit 0; strict: exit 1 if any errors (none yet — warn-only)",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Check a single file (relative or absolute)",
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Positional file list (used by pre-commit pass_filenames)",
    )
    args = parser.parse_args()

    if args.files:
        files = [
            (REPO_ROOT / f).resolve()
            for f in args.files
            if (REPO_ROOT / f).resolve().suffix == ".py"
        ]
    elif args.file:
        files = [(REPO_ROOT / args.file).resolve()]
    else:
        files = _all_files()

    if not files:
        print("check_consistency: no files to check")
        return 0

    exceptions = _load_exceptions()
    findings = run_checks(files, exceptions)

    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]

    if not findings:
        print("check_consistency: all rules passed ✓")
        return 0

    print(f"\ncheck_consistency — {len(errors)} error(s)  {len(warnings)} warning(s)\n")
    counts = _counts_by_rule(findings)
    print("  by rule: " + ", ".join(f"{k}={counts[k]}" for k in sorted(counts)))
    print()

    if errors:
        print("ERRORS — must fix before merge:")
        for f in sorted(errors, key=lambda x: (str(x.file), x.line)):
            print(f.display(REPO_ROOT))

    if warnings:
        print("WARNINGS — tracked; triage into real fixes or allowlist entries:")
        for f in sorted(warnings, key=lambda x: (str(x.file), x.line)):
            print(f.display(REPO_ROOT))

    print()
    if args.mode == "strict" and errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
