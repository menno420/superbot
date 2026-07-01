#!/usr/bin/env python3
"""Per-command help-reachability guard for SuperBot.

A command-level companion to the *subsystem*-level discoverability invariant
(``tests/unit/invariants/test_discoverability.py``) and to
``scripts/check_consistency.py`` (UX-pattern linter).  Where those guard that
every *subsystem* is homed, this one guards the next level down — the gap the
owner actually reported ("the general cog is completely unfindable from the help
menu"): **every user-facing command must live in a cog that is reachable by
clicking through ``!help``.**

The check is static (no live bot, no Postgres).  For every prefix command it:

  1. resolves the **owning subsystem(s)** of its cog the way the live help layer
     does (``cogs.help_cog._cog_for_subsystem``) — by the cog class name
     (``core.runtime.command_surface_ledger.cog_name_to_subsystem``) **or** by an
     ``entry_points`` match in ``utils.subsystem_registry.SUBSYSTEMS``;
  2. classifies the command as **reachable** (some owning subsystem is *homed*
     under a top-level hub **and** has a help-discovery path), **exempt**
     (operator/owner-tier, Discord-hidden, an internal subsystem, the ``help``
     root, or allowlisted), or a **gap** (a member-tier command whose cog maps to
     no homed + discoverable subsystem → it will not appear in any help
     command-list and is unreachable except via a hand-wired panel button).

A *gap* is the actionable finding: home the cog's subsystem, mark it operator/
internal, surface the command via a panel button, or allowlist it with a reason.

It is **warn-first and disposable** (Q-0105): every finding is a warning, nothing
fails CI yet.  The invariant test ratchets against a recorded baseline so *new*
gaps fail while the pre-existing ones are tolerated until a per-cog audit session
clears them.  The guard graduates to ``--mode strict`` failing on any finding only
once the baseline is empty and it has run clean across a few sessions.

Provenance / reliability (Q-0105):
  - Added 2026-06-23 for the consolidation/discoverability audit (Session 1):
    `docs/planning/consolidation-discoverability-audit-brief-2026-06-23.md` §3.2/§4.2.
  - **Unverified:** the static cog→subsystem resolution mirrors the live
    ``_cog_for_subsystem`` but cannot see hand-wired hub-panel buttons; confirm a
    flagged command really is unreachable in a live guild before homing it, and
    keep the rule warn-only until proven quiet.
  - **Disposable:** if it proves noisy across multiple sessions, delete it (or widen
    the allowlist) rather than working around it.

Usage::

    python scripts/check_command_reachability.py            # report (exit 0)
    python scripts/check_command_reachability.py --mode strict   # exit 1 on a gap
    python scripts/check_command_reachability.py --json     # machine-readable
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DISBOT_ROOT = REPO_ROOT / "disbot"
COGS_DIR = DISBOT_ROOT / "cogs"
RULES_DIR = REPO_ROOT / "architecture_rules"
_EXCEPTIONS_FILE = "command_reachability_exceptions.yml"

if str(DISBOT_ROOT) not in sys.path:
    sys.path.insert(0, str(DISBOT_ROOT))

from core.runtime.command_surface_ledger import (  # noqa: E402
    cog_name_to_subsystem,
)
from services.customization_catalogue import KNOWN_PANEL_COMMANDS  # noqa: E402
from utils.hub_registry import HUBS  # noqa: E402
from utils.subsystem_registry import SUBSYSTEMS  # noqa: E402

_MENU_RE = re.compile(r".+menu$")
_HUB_KEYS = {h.key for h in HUBS}

# Command-body calls that gate a command to operator/owner at runtime — these are
# checks the decorator scan misses (the command verifies permission *inside* its
# body, e.g. ``if not is_administrator_member(ctx.author): ...``).  A command whose
# body calls one of these is treated as operator-tier (exempt — found via the
# admin hub, not a member-facing discoverability gap).
_ADMIN_GATE_CALLS = frozenset(
    {
        "is_administrator_member",
        "is_staff_member",
        "is_admin_or_owner",
        "is_owner",
        "require_admin",
        "require_staff",
    },
)
# Permission keywords on a @commands.has_permissions(...) decorator → operator.
_OPERATOR_PERM_KEYWORDS = frozenset(
    {
        "administrator",
        "manage_guild",
        "manage_channels",
        "manage_roles",
        "manage_messages",
        "manage_members",
        "moderate_members",
        "kick_members",
        "ban_members",
    },
)


# ---------------------------------------------------------------------------
# Finding model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    cog_file: str  # repo-relative, e.g. "disbot/cogs/paragon_cog.py"
    line: int
    command: str
    cog_class: str
    owning_subsystems: tuple[str, ...]
    message: str
    severity: str = "warning"

    def key(self) -> tuple[str, str]:
        """Stable identity used by the baseline ratchet: (cog_file, command)."""
        return (self.cog_file, self.command)

    def display(self) -> str:
        tag = "ERROR" if self.severity == "error" else " WARN"
        return f"  [{tag}] {self.cog_file}:{self.line}  !{self.command}  ({self.cog_class})  {self.message}"


# ---------------------------------------------------------------------------
# Allowlist
# ---------------------------------------------------------------------------


def _load_exceptions() -> dict:
    p = RULES_DIR / _EXCEPTIONS_FILE
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _is_allowlisted(cog_file: str, command: str, exceptions: dict) -> bool:
    """True if (cog_file, command) — or the whole cog_file — is allowlisted.

    An entry with only ``cog_file`` exempts every command in that file; adding a
    ``command`` narrows it to one command.  Paths are matched with the ``disbot/``
    prefix optional so the YAML can read either way.
    """
    for exc in exceptions.get("exceptions", []):
        pat_file = str(exc.get("cog_file", "")).strip()
        if not pat_file:
            continue
        norm = cog_file.replace("disbot/", "")
        if pat_file.replace("disbot/", "") != norm:
            continue
        cmd = exc.get("command")
        if cmd is None or str(cmd) == command:
            return True
    return False


# ---------------------------------------------------------------------------
# AST command extraction (cog class → its prefix commands, with tier hints)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Command:
    name: str
    aliases: tuple[str, ...]
    tier: str  # "member" | "operator" | "owner"
    hidden: bool
    line: int


def _decorator_name(dec: ast.expr) -> tuple[str, ast.expr | None]:
    """(attr, parent-of-attr) for a decorator (``commands.command`` → ("command", Name commands))."""
    target = dec.func if isinstance(dec, ast.Call) else dec
    if isinstance(target, ast.Attribute):
        return target.attr, target.value
    if isinstance(target, ast.Name):
        return target.id, None
    return "", None


def _tier_from_decorators(fn: ast.AsyncFunctionDef | ast.FunctionDef) -> str:
    """Tier ("owner" / "operator" / "member") from a command method's decorators."""
    for dec in fn.decorator_list:
        attr, _ = _decorator_name(dec)
        if attr in {"is_owner"}:
            return "owner"
        if attr in {
            "is_admin_or_owner",
            "admin_or_owner",
            "app_admin_or_owner",
            "perms_or_owner",
            "app_perms_or_owner",
        }:
            return "operator"
        if isinstance(dec, ast.Call):
            for kw in dec.keywords:
                if kw.arg in _OPERATOR_PERM_KEYWORDS:
                    return "operator"
    return "member"


def _body_gates_to_operator(fn: ast.AST) -> bool:
    """True if the command body calls a runtime admin/staff gate helper."""
    for sub in ast.walk(fn):
        if isinstance(sub, ast.Call):
            f = sub.func
            name = (
                f.id
                if isinstance(f, ast.Name)
                else (f.attr if isinstance(f, ast.Attribute) else "")
            )
            if name in _ADMIN_GATE_CALLS:
                return True
    return False


def _extract_cog_commands(path: Path) -> list[tuple[str, list[_Command]]]:
    """Return ``[(cog_class_name, [_Command, ...]), ...]`` for one cog file.

    Only ``@commands.command`` / ``@commands.group`` (prefix) methods are
    collected — slash and app-group commands are surfaced by Discord's own
    command picker, not the ``!help`` text tree this guard models.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    out: list[tuple[str, list[_Command]]] = []
    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        cmds: list[_Command] = []
        for fn in ast.walk(cls):
            if not isinstance(fn, ast.AsyncFunctionDef):
                continue
            deco = None
            for dec in fn.decorator_list:
                attr, parent = _decorator_name(dec)
                if (
                    attr in {"command", "group"}
                    and isinstance(parent, ast.Name)
                    and parent.id == "commands"
                ):
                    deco = dec
                    break
            if deco is None:
                continue

            name = fn.name
            aliases: tuple[str, ...] = ()
            hidden = False
            if isinstance(deco, ast.Call):
                for kw in deco.keywords:
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                        name = str(kw.value.value)
                    elif kw.arg == "hidden" and isinstance(kw.value, ast.Constant):
                        hidden = bool(kw.value.value)
                    elif kw.arg == "aliases" and isinstance(
                        kw.value,
                        (ast.List, ast.Tuple),
                    ):
                        aliases = tuple(
                            str(e.value)
                            for e in kw.value.elts
                            if isinstance(e, ast.Constant)
                        )

            tier = _tier_from_decorators(fn)
            if tier == "member" and _body_gates_to_operator(fn):
                tier = "operator"

            cmds.append(
                _Command(
                    name=name,
                    aliases=aliases,
                    tier=tier,
                    hidden=hidden,
                    line=fn.lineno,
                ),
            )
        if cmds:
            out.append((cls.name, cmds))
    return out


# ---------------------------------------------------------------------------
# Reachability model
# ---------------------------------------------------------------------------

# entry_point command name → owning subsystem(s) (inverse of the registry).
_EP_TO_SUBS: dict[str, set[str]] = {}
for _sub, _meta in SUBSYSTEMS.items():
    for _ep in _meta.get("entry_points") or ():
        _EP_TO_SUBS.setdefault(_ep, set()).add(_sub)


def _subsystem_homed(subsystem: str) -> bool:
    """True if the subsystem is a top-level hub or a child of one."""
    if subsystem in _HUB_KEYS:
        return True
    return SUBSYSTEMS.get(subsystem, {}).get("parent_hub") in _HUB_KEYS


def _subsystem_discoverable(subsystem: str) -> bool:
    """Mirror of ``test_discoverability._discoverability`` (subsystem-level path).

    A subsystem is help-discoverable when it is internal, the help root, exposes a
    panel command / a ``*menu`` entry-point, or its ``{subsystem}_cog.py`` declares
    a ``build_help_menu_view`` hook.
    """
    meta = SUBSYSTEMS.get(subsystem)
    if not meta:
        return False
    if meta.get("visibility_mode") == "internal":
        return True
    eps = set(meta.get("entry_points") or ())
    if subsystem == "help" and "help" in eps:
        return True
    panel_cmds = {cmd for sub, cmd in KNOWN_PANEL_COMMANDS if sub == subsystem}
    if panel_cmds & eps:
        return True
    if any(_MENU_RE.match(ep) for ep in eps):
        return True
    cog_path = COGS_DIR / f"{subsystem}_cog.py"
    return cog_path.exists() and "build_help_menu_view" in cog_path.read_text(
        encoding="utf-8",
    )


def _owning_subsystems(cog_class: str, cmds: list[_Command]) -> set[str]:
    """Subsystems whose help panel would surface this cog — the live resolution.

    Matches ``cogs.help_cog._cog_for_subsystem``: a subsystem owns this cog when
    the cog *class name* normalises to it, **or** one of the cog's command
    names/aliases is one of the subsystem's ``entry_points``.
    """
    subs: set[str] = set()
    mapped = cog_name_to_subsystem(cog_class)
    if mapped:
        subs.add(mapped)
    names: set[str] = set()
    for c in cmds:
        names.add(c.name)
        names.update(c.aliases)
    for n in names:
        subs |= _EP_TO_SUBS.get(n, set())
    return subs


def _classify(
    command: _Command,
    cog_class: str,
    owning: set[str],
) -> str:
    """Return "reachable" | "exempt" | "gap" for one command."""
    if command.hidden:
        return "exempt"
    if command.tier in {"operator", "owner"}:
        return "exempt"
    if command.name == "help":
        return "exempt"  # the help root cannot be reached *through* itself
    if any(SUBSYSTEMS.get(s, {}).get("visibility_mode") == "internal" for s in owning):
        return "exempt"
    if any(_subsystem_homed(s) and _subsystem_discoverable(s) for s in owning):
        return "reachable"
    return "gap"


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


@dataclass
class Report:
    reachable: int = 0
    exempt: int = 0
    gaps: list[Finding] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.gaps is None:
            self.gaps = []


def run_check(exceptions: dict | None = None) -> Report:
    """Classify every prefix command and return the report (gaps = findings)."""
    if exceptions is None:
        exceptions = _load_exceptions()
    report = Report()
    for path in sorted(COGS_DIR.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        cog_file = str(path.relative_to(REPO_ROOT))
        for cog_class, cmds in _extract_cog_commands(path):
            owning = _owning_subsystems(cog_class, cmds)
            for command in cmds:
                state = _classify(command, cog_class, owning)
                if state == "reachable":
                    report.reachable += 1
                elif state == "exempt":
                    report.exempt += 1
                else:  # gap
                    if _is_allowlisted(cog_file, command.name, exceptions):
                        report.exempt += 1
                        continue
                    report.gaps.append(
                        Finding(
                            cog_file=cog_file,
                            line=command.line,
                            command=command.name,
                            cog_class=cog_class,
                            owning_subsystems=tuple(sorted(owning)),
                            message=(
                                "member-tier command whose cog maps to no homed + "
                                "help-discoverable subsystem — it will not appear in any "
                                "!help command-list. Home the cog's subsystem, surface the "
                                "command via a panel button, mark it operator/internal, or "
                                f"allowlist it in {_EXCEPTIONS_FILE}"
                            ),
                        ),
                    )
    report.gaps.sort(key=lambda f: (f.cog_file, f.command))
    return report


def gap_keys(report: Report) -> set[tuple[str, str]]:
    """The ``(cog_file, command)`` identity set of all gaps — used by the ratchet."""
    return {f.key() for f in report.gaps}


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _print_report(report: Report) -> None:
    total = report.reachable + report.exempt + len(report.gaps)
    print(
        f"\ncheck_command_reachability — {total} prefix commands  "
        f"({report.reachable} reachable, {report.exempt} exempt, "
        f"{len(report.gaps)} GAP)\n",
    )
    if not report.gaps:
        print("  all member-tier commands are reachable ✓")
        return
    print("  GAPS — member-tier commands not reachable from the help tree:")
    by_cog: dict[str, list[Finding]] = {}
    for f in report.gaps:
        by_cog.setdefault(f.cog_file, []).append(f)
    for cog_file in sorted(by_cog):
        print(f"\n  {cog_file}")
        for f in by_cog[cog_file]:
            subs = ", ".join(f.owning_subsystems) or "(none)"
            print(
                f"      !{f.command:<22} class={f.cog_class:<26} owning_subsystems=[{subs}]",
            )
    print(
        "\n  Each is an audit follow-on: home the cog's subsystem, surface the command "
        f"via a panel button, mark it operator/internal, or allowlist it in {_EXCEPTIONS_FILE}.",
    )


def _print_json(report: Report) -> None:
    print(
        json.dumps(
            {
                "reachable": report.reachable,
                "exempt": report.exempt,
                "gaps": [
                    {
                        "cog_file": f.cog_file,
                        "line": f.line,
                        "command": f.command,
                        "cog_class": f.cog_class,
                        "owning_subsystems": list(f.owning_subsystems),
                    }
                    for f in report.gaps
                ],
            },
            indent=2,
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Per-command help-reachability guard (warn-first)",
    )
    parser.add_argument(
        "--mode",
        choices=["report", "strict"],
        default="report",
        help="report: always exit 0; strict: exit 1 if any gap is found",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    report = run_check()

    if args.json:
        _print_json(report)
    else:
        _print_report(report)

    if args.mode == "strict" and report.gaps:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
