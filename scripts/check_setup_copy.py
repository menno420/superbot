#!/usr/bin/env python3
"""Setup-copy jargon guard for SuperBot.

The *plain-language* guard for the setup wizard.  The setup-wizard restructure
plan (``docs/planning/setup-wizard-restructure-plan-2026-06-24.md``) sets four
design laws; **Law 2 is "zero jargon"** — a non-technical server owner walking
``!setup`` must never read a Discord/bot internal term (*draft, operation, bind,
cog, subsystem, scope, resolver, threshold, seam, pipeline, routing, tier,
guild, preset, …*).  That law was the recurring failure: the jargon crept back
in because nothing enforced plain language.  This guard makes "zero jargon" a
**ratchet** instead of a one-off cleanup.

What it does (static — no live bot, no Postgres): it walks every ``*.py`` under
``disbot/views/setup/``, AST-extracts string literals, keeps the ones that look
like **operator-facing prose** (they contain a space — slugs / ``custom_id`` /
op-kind literals like ``bind_channel`` do not), and flags any that contain a
banned jargon stem.  Each finding is ``file:line — term … in "<copy>"``.

It is **warn-first and disposable** (Q-0105): in the default ``--mode report`` it
prints findings and exits 0; ``--mode strict`` exits 1 on any finding.  The
invariant test (``tests/unit/invariants/test_setup_copy_jargon.py``) ratchets
against a recorded baseline — the current jargon-heavy copy is tolerated, but
*new* jargon (or jargon in a *new* setup file) fails.  As the spine rewrite
(plan PR 1) cleans each section's copy, the baseline shrinks; once it reaches
zero the guard graduates to ``--mode strict`` in CI.

Provenance / reliability (Q-0105):
  - Added 2026-06-24 for the setup-wizard restructure plan (Law 2 enforcement):
    ``docs/planning/setup-wizard-restructure-plan-2026-06-24.md`` §4, §7 (PR 1).
  - **Unverified:** the "prose vs. machine string" split is a heuristic (has a
    space → prose).  It can miss a one-word jargon label (rare — real UI copy is
    phrases) and could in principle flag a benign spaced string that happens to
    contain a stem.  Confirm a flagged string is really operator-facing before
    treating it as a true positive, and keep the guard warn-only until proven
    quiet across a few sessions.
  - **Delete this guard if it proves unreliable over multiple sessions** — it is
    a convenience ratchet, not load-bearing runtime code.

Usage:
    python3.10 scripts/check_setup_copy.py              # report (exit 0)
    python3.10 scripts/check_setup_copy.py --strict     # exit 1 on any finding
    python3.10 scripts/check_setup_copy.py --json       # machine-readable
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SETUP_ROOT = _REPO_ROOT / "disbot" / "views" / "setup"

# Jargon a non-technical owner does not understand (plan §4). Matched as a
# word-start stem against lowercased prose, so "stage" catches "stages",
# "operation" catches "operations", "bind" catches "binding"/"bind_channel".
JARGON_STEMS: tuple[str, ...] = (
    "draft",
    "operation",
    "stage",
    "bind",
    "subsystem",
    "resolver",
    "precedence",
    "threshold",
    "seam",
    "pipeline",
    "routing",
    # multi-word / underscore forms (substring-matched)
    "final review",
    "set_setting",
    "set_role_threshold",
    "set_cleanup_policy",
    "set_cog_routing",
    "cog routing",
)
# Standalone words that are jargon on their own but appear inside many benign
# words; matched with strict word boundaries to avoid false hits.
JARGON_WORDS: tuple[str, ...] = (
    "cog",
    "scope",
    "tier",
    "guild",
    "preset",
)


@dataclass(frozen=True)
class Finding:
    file: str  # repo-relative path
    line: int
    text: str  # the offending string literal
    terms: tuple[str, ...]  # jargon terms it contains


def _terms_in(text: str) -> tuple[str, ...]:
    low = text.lower()
    hits: list[str] = []
    for stem in JARGON_STEMS:
        if " " in stem or "_" in stem:
            if stem in low:
                hits.append(stem)
        elif re.search(rf"\b{re.escape(stem)}", low):
            hits.append(stem)
    for word in JARGON_WORDS:
        if re.search(rf"\b{re.escape(word)}s?\b", low):
            hits.append(word)
    return tuple(dict.fromkeys(hits))  # dedupe, keep order


def _is_prose(text: str) -> bool:
    """Operator-facing prose contains a space; slugs / custom_ids / op-kinds do not."""
    return " " in text.strip() and any(c.isalpha() for c in text)


# Keyword arguments whose string value is rendered to the operator.
_UI_KWARGS = frozenset(
    {
        "label",
        "description",
        "placeholder",
        "title",
        "content",
        "text",
        "value",
        "name",
    },
)
# Call targets that send/edit operator-facing text (positional string args count).
_SEND_ATTRS = frozenset(
    {"send", "send_message", "edit", "edit_message", "edit_original_response"},
)
# Logging calls — their string args are developer-facing, never flagged.
_LOG_ATTRS = frozenset(
    {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"},
)


def _string_value(node: ast.AST) -> str | None:
    """Return the literal text of a str Constant or the literal parts of an f-string."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):  # f-string: keep only the literal segments
        parts = [
            v.value
            for v in node.values
            if isinstance(v, ast.Constant) and isinstance(v.value, str)
        ]
        return " ".join(parts) if parts else None
    return None


class _UICopyVisitor(ast.NodeVisitor):
    """Collect only strings that reach the operator (UI kwargs + send args)."""

    def __init__(self, rel: str) -> None:
        self.rel = rel
        self.findings: list[Finding] = []

    def _consider(self, value_node: ast.AST, line: int) -> None:
        text = _string_value(value_node)
        if text is None or not _is_prose(text):
            return
        terms = _terms_in(text)
        if terms:
            self.findings.append(Finding(self.rel, line, text, terms))

    def visit_Call(self, node: ast.Call) -> None:
        attr = ""
        if isinstance(node.func, ast.Attribute):
            attr = node.func.attr
        elif isinstance(node.func, ast.Name):
            attr = node.func.id
        if attr not in _LOG_ATTRS:
            for kw in node.keywords:
                if kw.arg in _UI_KWARGS:
                    self._consider(kw.value, getattr(kw.value, "lineno", node.lineno))
            if attr in _SEND_ATTRS:
                for arg in node.args:
                    self._consider(arg, getattr(arg, "lineno", node.lineno))
        self.generic_visit(node)


def scan_file(path: Path) -> list[Finding]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return []
    visitor = _UICopyVisitor(str(path.relative_to(_REPO_ROOT)))
    visitor.visit(tree)
    return visitor.findings


def scan_setup_copy(root: Path = _SETUP_ROOT) -> list[Finding]:
    """Return all jargon findings under *root*, sorted by (file, line)."""
    findings: list[Finding] = []
    for path in sorted(root.rglob("*.py")):
        findings.extend(scan_file(path))
    return sorted(findings, key=lambda f: (f.file, f.line))


def _format(findings: list[Finding]) -> str:
    lines: list[str] = []
    for f in findings:
        snippet = f.text if len(f.text) <= 80 else f.text[:77] + "…"
        lines.append(f'  {f.file}:{f.line} — {", ".join(f.terms)}  in "{snippet}"')
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Setup-copy jargon guard.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any jargon is found",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    findings = scan_setup_copy()

    if args.json:
        print(
            json.dumps(
                {
                    "count": len(findings),
                    "term_totals": _term_totals(findings),
                    "findings": [
                        {
                            "file": f.file,
                            "line": f.line,
                            "terms": list(f.terms),
                            "text": f.text,
                        }
                        for f in findings
                    ],
                },
                indent=2,
            ),
        )
        return 1 if (args.strict and findings) else 0

    print("check_setup_copy: setup-wizard plain-language guard (plan §4, Law 2)")
    print(
        f"  scanned {_SETUP_ROOT.relative_to(_REPO_ROOT)} — {len(findings)} jargon string(s)",
    )
    if findings:
        print(_format(findings))
        print("  term totals: " + _term_totals_str(findings))
        print(
            "  (warn-first: this is the baseline the spine rewrite drives toward zero;"
            " new jargon fails the ratchet test.)",
        )
    else:
        print("  no jargon — Law 2 holds ✓")
    return 1 if (args.strict and findings) else 0


def _term_totals(findings: list[Finding]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for f in findings:
        for t in f.terms:
            totals[t] = totals.get(t, 0) + 1
    return dict(sorted(totals.items(), key=lambda kv: (-kv[1], kv[0])))


def _term_totals_str(findings: list[Finding]) -> str:
    return ", ".join(f"{t}×{n}" for t, n in _term_totals(findings).items())


if __name__ == "__main__":
    raise SystemExit(main())
