#!/usr/bin/env python3.10
"""Deferred-action restart-recovery guard for SuperBot — catch one-shot timers that a restart drops.

A repo-wide, read-only AST checker (same `architecture_rules/` allowlist family as
``scripts/check_audit_seam.py``) for a bug shape the rebuild Stage-2 subsystem walk found **twice, in
unrelated subsystems, days apart** (PR #1725): a **fire-and-forget delayed Discord-state mutation** with
no way to recover across a restart.

THE SHAPE (calibration, ``docs/ideas/deferred-action-restart-recovery-checker-2026-07-05.md``): a
callable **scheduled as a background task** (``tasks.spawn`` / ``asyncio.create_task`` /
``asyncio.ensure_future``) — fire-and-forget, outliving the interaction — whose body does
``asyncio.sleep(...)`` **then** a **Discord state mutation** (slowmode / permission overwrite / role
grant-or-removal / channel edit). If the process restarts during the sleep, the mutation never
completes: the raid-lockdown slowmode is never restored (``security_service``), the prize channel stays
locked to the winner forever (``proof_channel`` — since fixed in #1728). The recovery a durable one-shot
needs is a **persisted deadline + a boot-time reconcile sweep**.

THE FINDING: a spawn-target with ``asyncio.sleep`` + a Discord state mutation, in a module that has
**neither** (a) a persisted-deadline write **nor** (b) a boot reconcile (an ``on_ready`` / ``cog_load``
sweep). ``proof_channel_cog`` (the #1728 fix) has both → clean; a new deferred lock without them → flagged.

WHY SPAWN-TARGET, NOT RAW ``asyncio.sleep`` (calibration): raw ``asyncio.sleep`` is in 23 ``disbot/``
files, mostly NOT this bug — retry/backoff, ``@tasks.loop`` infra loops, and inline UX animations
(``poker_table`` / ``cast_view`` sleep + *await a message edit inline* within an interaction). The
discriminating signal is the **spawn** (fire-and-forget) plus a **persistent Discord state mutation**
(a message re-render / in-memory game state is not the bug — a restart just ends that game).

PROVENANCE / RELIABILITY (Q-0105):
  - Added 2026-07-06 (CI-setup arc, handoff item #5, second guard) from the calibrated spec.
  - **Unverified:** spawn-target resolution is by name within the module (an inline/lambda coroutine or a
    cross-module spawn target is not resolved → a false negative, the safe direction); the
    persist/reconcile detection is a module-level heuristic (keyword/regex) that can miss an unusually
    named recovery path (→ a false positive). Confirm a flagged timer really lacks restart recovery
    against source before "fixing" it, and keep it **warn-first** (wired ``continue-on-error`` in
    ``code-quality.yml``).
  - **Disposable:** if noisy across sessions, widen ``architecture_rules/deferred_recovery_exceptions.yml``
    or **delete this script** — the subsystem walk is the backstop.

Usage::

    python3.10 scripts/check_deferred_recovery.py                # report (exit 0)
    python3.10 scripts/check_deferred_recovery.py --mode strict   # exit 1 on any finding
    python3.10 scripts/check_deferred_recovery.py --json          # machine-readable
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DISBOT_ROOT = REPO_ROOT / "disbot"
RULES_DIR = REPO_ROOT / "architecture_rules"
_EXCEPTIONS_FILE = "deferred_recovery_exceptions.yml"

# Background-task schedulers — the "fire-and-forget" tell. The coroutine argument's callee is the
# spawn-target we resolve and analyse.
_SPAWN_CALLS = frozenset({"spawn", "create_task", "ensure_future"})

# Discord state-mutation methods that persist beyond the process (need recovery if deferred). Mirrors
# check_audit_seam's set; ``edit``/``delete`` on a message receiver are re-renders, excluded.
_DISCORD_MUT_ATTRS = frozenset(
    {
        "set_permissions",
        "edit_permissions",
        "ban",
        "kick",
        "add_roles",
        "remove_roles",
        "move_to",
        "timeout",
        "edit_role",
    },
)
_OVERLOADED_MUT_ATTRS = frozenset({"edit", "delete"})
_MESSAGE_RECEIVERS = frozenset({"message", "msg"})
_MESSAGE_EDIT_KWARGS = frozenset(
    {
        "embed",
        "embeds",
        "view",
        "content",
        "attachments",
        "attachment",
        "suppress",
        "delete_after",
    },
)
# Name-based state-effect verbs — catch a mutation routed through a lifecycle/service call rather than a
# raw Discord attribute (e.g. security's slowmode restore goes through ChannelLifecycleService, not a
# raw ``channel.edit``). A call whose name contains one of these is treated as a deferred state effect.
_STATE_EFFECT_VERB = re.compile(
    r"slowmode|lockdown|unlock|set_permission|overwrite|lift_lock|restore.*lock|grant_role|revoke_role",
    re.IGNORECASE,
)

# Module-level recovery signals (heuristic — a module property, not a per-function one).
_PERSIST_SIGNAL = re.compile(
    r"upsert_lock|_persist_\w*lock|persist\w*deadline|proof_channel_locks|"
    r"\b\w*_locks\.\w|persisted[- ]?deadline|save_\w*deadline|record_\w*(lock|deadline|timer)",
    re.IGNORECASE,
)
_RECONCILE_SIGNAL = re.compile(
    r"reconcile|boot[- ]?sweep|recover_\w*lock|_resume_\w*lock", re.IGNORECASE
)
_BOOT_HOOK = re.compile(r"on_ready|cog_load", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Finding model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    spawn_target: str
    detail: str

    def key(self) -> tuple[str, str]:
        return (self.file, self.spawn_target)

    def display(self) -> str:
        return f"  [FINDING] {self.file}:{self.line}  spawn→{self.spawn_target}()  —  {self.detail}"


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _callee_name(call: ast.Call) -> str | None:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _receiver_tail(value: ast.expr) -> str:
    try:
        return ast.unparse(value).rsplit(".", 1)[-1]
    except Exception:  # pragma: no cover - defensive
        return ""


def _is_discord_state_mutation(call: ast.Call) -> bool:
    """True if the call is a persistent Discord state mutation (not a message re-render)."""
    func = call.func
    if isinstance(func, ast.Attribute):
        attr = func.attr
        if attr in _DISCORD_MUT_ATTRS:
            return True
        if attr in _OVERLOADED_MUT_ATTRS:
            tail = _receiver_tail(func.value)
            if tail in _MESSAGE_RECEIVERS or tail.endswith(("_message", "_msg")):
                return False  # a message receiver → a re-render, not state
            # An ``.edit(...)`` writing only message fields is a re-render, not a state mutation.
            edits_only_message = (
                attr == "edit"
                and bool(call.keywords)
                and all(
                    kw.arg in _MESSAGE_EDIT_KWARGS
                    for kw in call.keywords
                    if kw.arg is not None
                )
            )
            return not edits_only_message
    # Name-based state-effect verb (a lifecycle/service-routed mutation).
    name = _callee_name(call)
    return bool(name and _STATE_EFFECT_VERB.search(name))


def _direct_calls(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.Call]:
    """Every call in ``fn``'s body, not descending into nested def/class bodies."""
    calls: list[ast.Call] = []
    stack: list[ast.AST] = list(fn.body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(node, ast.Call):
            calls.append(node)
        stack.extend(ast.iter_child_nodes(node))
    return calls


def _sleeps_then_mutates(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """If ``fn`` does ``asyncio.sleep`` AND a Discord state mutation, return a short detail, else None.

    Order (sleep before the mutation) is the canonical shape but not required — a spawned task that
    both sleeps and mutates is the deferred-recovery risk regardless of statement order.
    """
    has_sleep = False
    mutation: str | None = None
    for call in _direct_calls(fn):
        if _callee_name(call) == "sleep":
            has_sleep = True
        if _is_discord_state_mutation(call):
            mutation = _callee_name(call) or "?"
    if has_sleep and mutation is not None:
        return f".sleep() then a Discord state mutation ({mutation})"
    return None


def _spawn_target_names(tree: ast.AST) -> set[str]:
    """Callee names used as the coroutine argument of a ``tasks.spawn`` / ``create_task`` / ``ensure_future``."""
    targets: set[str] = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and _callee_name(node) in _SPAWN_CALLS):
            continue
        for arg in list(node.args) + [kw.value for kw in node.keywords]:
            if isinstance(arg, ast.Call):
                name = _callee_name(arg)
                if name:
                    targets.add(name)
    return targets


def _functions_by_name(
    tree: ast.AST,
) -> dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]]:
    out: dict[str, list] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.setdefault(node.name, []).append(node)
    return out


# ---------------------------------------------------------------------------
# Recovery detection (module-level heuristic)
# ---------------------------------------------------------------------------


def _has_recovery(source: str) -> bool:
    """True if the module shows BOTH a persisted-deadline write AND a boot-time reconcile sweep."""
    has_persist = bool(_PERSIST_SIGNAL.search(source))
    has_reconcile = bool(_RECONCILE_SIGNAL.search(source) and _BOOT_HOOK.search(source))
    return has_persist and has_reconcile


# ---------------------------------------------------------------------------
# Allowlist
# ---------------------------------------------------------------------------


def load_exceptions(path: Path | None = None) -> dict:
    p = path if path is not None else RULES_DIR / _EXCEPTIONS_FILE
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _allowlisted(file: str, spawn_target: str, exceptions: dict) -> bool:
    norm = file.replace("disbot/", "")
    for exc in exceptions.get("exceptions", []):
        pat = str(exc.get("file", "")).strip().replace("disbot/", "")
        if not pat or pat != norm:
            continue
        tgt = exc.get("spawn_target")
        if tgt is None or str(tgt) == spawn_target:
            return True
    return False


# ---------------------------------------------------------------------------
# Analysis (testable — operates on injected sources)
# ---------------------------------------------------------------------------


def analyze(sources: dict[str, str], exceptions: dict | None = None) -> list[Finding]:
    """Compute findings from ``sources`` (repo-relative path -> source text)."""
    exceptions = exceptions if exceptions is not None else {}
    findings: list[Finding] = []
    for rel, source in sources.items():
        if "test" in rel.lower():
            continue
        try:
            tree = ast.parse(source, filename=rel)
        except SyntaxError:
            continue
        targets = _spawn_target_names(tree)
        if not targets:
            continue
        if _has_recovery(source):
            continue  # module persists a deadline + reconciles on boot → recoverable
        funcs = _functions_by_name(tree)
        for name in sorted(targets):
            for fn in funcs.get(name, []):
                detail = _sleeps_then_mutates(fn)
                if detail is None:
                    continue
                if _allowlisted(rel, name, exceptions):
                    continue
                findings.append(
                    Finding(file=rel, line=fn.lineno, spawn_target=name, detail=detail),
                )
                break  # one finding per spawn-target name
    findings.sort(key=lambda f: (f.file, f.line))
    return findings


def _read_disbot_sources() -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(DISBOT_ROOT.rglob("*.py")):
        rel = str(path.relative_to(REPO_ROOT))
        try:
            out[rel] = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return out


def run_check(exceptions: dict | None = None) -> list[Finding]:
    if exceptions is None:
        exceptions = load_exceptions()
    return analyze(_read_disbot_sources(), exceptions)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _print_report(findings: list[Finding]) -> None:
    print(f"\ncheck_deferred_recovery — {len(findings)} finding(s)\n")
    if not findings:
        print("  every deferred one-shot Discord-state mutation has restart recovery ✓")
        return
    print(
        "  Deferred one-shot mutations without restart recovery — a spawned task sleeps then mutates\n"
        "  Discord state, but the module persists no deadline + has no boot reconcile sweep:\n",
    )
    for f in findings:
        print(f.display())
    print(
        "\n  Fix: persist the deadline (a DB row keyed on the identifier the timer closes over) and add a\n"
        "  boot-time reconcile sweep (on_ready / cog_load) that completes overdue actions — the "
        "proof_channel_cog\n  pattern (#1728). Or, if the deferred state is intentionally process-local "
        f"(e.g. ADR-002), allowlist it in\n  architecture_rules/{_EXCEPTIONS_FILE} with a reason.",
    )


def _print_json(findings: list[Finding]) -> None:
    print(
        json.dumps(
            {
                "findings": [
                    {
                        "file": f.file,
                        "line": f.line,
                        "spawn_target": f.spawn_target,
                        "detail": f.detail,
                    }
                    for f in findings
                ],
            },
            indent=2,
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deferred-action restart-recovery guard (warn-first)",
    )
    parser.add_argument("--mode", choices=["report", "strict"], default="report")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    findings = run_check()
    if args.json:
        _print_json(findings)
    else:
        _print_report(findings)

    if args.mode == "strict" and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
