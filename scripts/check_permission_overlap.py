#!/usr/bin/env python3.10
"""Permission-overlap guard — flag `allow` rules shadowed by a broader `ask`/`deny`.

Why this exists (2026-06-21): the maintainer kept hitting a confirmation prompt on the
standard *verify + force-push* bundle. Root cause was a shadow in `.claude/settings.json`:
`permissions.ask` held `Bash(git push --force*)`, whose prefix `git push --force` is a
prefix of the command the owner actually runs, `git push --force-with-lease …`. The first
fix (#1211) added `Bash(git push --force-with-lease*)` to `allow`, but whether a narrower
`allow` overrides a broader `ask` depends on the harness's precedence semantics
(most-specific-wins vs. ask-always-wins) — so the allow could still be dead. The
semantics-independent fix is to make the `ask` rule precise so it never matches the allowed
form. This guard catches that whole class at config-edit time instead of at the prompt:

    an `allow` rule whose matched command set is fully contained in some `ask`/`deny`
    rule's set is *potentially shadowed* — depending on precedence it may never take
    effect. Narrow the broader rule (or confirm the override is intended).

It does NOT flag the normal carve-out direction (a broad `allow` like `Bash(git push*)`
with a narrower `ask` like `Bash(git push --force*)` that restricts a slice of it) — that
works under either precedence and is how exceptions are meant to be expressed.

Scope: only `Bash(...)` prefix/exact rules, where shadowing is well-defined. Tool-name
rules (`Read`, `mcp__...`) are skipped.

Reliability (Q-0105): **unverified — added 2026-06-21.** Confirm its verdicts against the
real settings a few times before trusting it; it is a convenience config-lint, NOT
load-bearing and NOT wired into hard CI. **Delete it** if it proves noisy or unreliable
over multiple sessions rather than working around it.

Usage:
    python3.10 scripts/check_permission_overlap.py            # advisory, human-readable
    python3.10 scripts/check_permission_overlap.py --strict   # exit 1 if any shadow found
    python3.10 scripts/check_permission_overlap.py --json      # machine-readable
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.json"


@dataclass(frozen=True)
class Rule:
    """A single permission rule, e.g. ``Bash(git push --force*)``."""

    raw: str
    tool: str
    prefix: str  # the literal portion before the first '*'
    is_glob: bool  # True if the rule ended in '*' (prefix match), else exact match

    def covers(self, other: Rule) -> bool:
        """True if every command matched by ``other`` is also matched by ``self``.

        A glob rule ``P*`` matches all commands starting with ``P``. An exact rule ``P``
        matches only the string ``P``. So ``self`` covers ``other`` iff ``self`` is a glob
        and ``other``'s literal prefix starts with ``self``'s prefix (an exact ``self`` can
        only cover an identical exact ``other``).
        """
        if self.tool != other.tool:
            return False
        if self.is_glob:
            return other.prefix.startswith(self.prefix)
        return (not other.is_glob) and other.prefix == self.prefix


def parse_rule(raw: str) -> Rule | None:
    """Parse ``Bash(<pattern>)`` into a Rule; return None for non-Bash / tool-only rules."""
    if not raw.startswith("Bash(") or not raw.endswith(")"):
        return None
    inner = raw[len("Bash(") : -1]
    if not inner:
        return None
    is_glob = inner.endswith("*")
    prefix = inner[:-1] if is_glob else inner
    return Rule(raw=raw, tool="Bash", prefix=prefix, is_glob=is_glob)


def parse_rules(entries: list[str]) -> list[Rule]:
    out = []
    for e in entries:
        r = parse_rule(e)
        if r is not None:
            out.append(r)
    return out


@dataclass(frozen=True)
class Shadow:
    allow_rule: str
    blocker_rule: str
    blocker_list: str  # "ask" or "deny"


def find_shadows(perms: dict) -> list[Shadow]:
    """Find allow rules whose command set is contained in a broader ask/deny rule."""
    allow = parse_rules(perms.get("allow", []))
    ask = parse_rules(perms.get("ask", []))
    deny = parse_rules(perms.get("deny", []))

    shadows: list[Shadow] = []
    for a in allow:
        for blockers, name in ((deny, "deny"), (ask, "ask")):
            for b in blockers:
                # A broader-or-equal higher-precedence rule shadows the allow. Skip the
                # exact-same string (that's a contradictory dup, reported separately by
                # callers if desired) only when prefixes differ in glob-ness handled by
                # covers(); equal glob prefixes => covers() True => genuine shadow.
                if b.covers(a):
                    shadows.append(
                        Shadow(allow_rule=a.raw, blocker_rule=b.raw, blocker_list=name),
                    )
    return shadows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any shadow is found",
    )
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument(
        "--settings",
        default=str(SETTINGS_PATH),
        help="path to settings.json (default: .claude/settings.json)",
    )
    args = ap.parse_args()

    path = Path(args.settings)
    if not path.exists():
        print(f"SKIP: {path} not found", file=sys.stderr)
        return 0

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"ERROR: {path} is not valid JSON: {exc}", file=sys.stderr)
        return 1

    perms = data.get("permissions", {})
    shadows = find_shadows(perms)

    if args.json:
        print(
            json.dumps(
                [
                    {
                        "allow": s.allow_rule,
                        "shadowed_by": s.blocker_rule,
                        "list": s.blocker_list,
                    }
                    for s in shadows
                ],
                indent=2,
            ),
        )
    else:
        if not shadows:
            print("permission-overlap: clean ✓ (no allow rule shadowed by ask/deny)")
        else:
            print(
                f"permission-overlap: {len(shadows)} shadowed allow rule(s) found\n",
            )
            for s in shadows:
                print(f"  ⚠ allow  {s.allow_rule}")
                print(f"    shadowed by {s.blocker_list}: {s.blocker_rule}")
                print(
                    "    → the allow's command set is fully inside the broader "
                    f"{s.blocker_list} rule; depending on the harness's precedence it "
                    "may never take effect. Narrow the broader rule (e.g. add a trailing "
                    "space / more of the literal) so it no longer matches the allowed "
                    "form, or confirm the override is intended.\n",
                )

    if shadows and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
