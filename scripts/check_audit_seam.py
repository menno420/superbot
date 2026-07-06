#!/usr/bin/env python3.10
"""Audit-seam coverage guard for SuperBot — catch unaudited mutations at authoring time.

A repo-wide, **per-function reachability** checker (same AST + ``architecture_rules/``
allowlist family as ``scripts/check_architecture.py``) for the mutation-seam contract in
``docs/ownership.md`` + ``.claude/CLAUDE.md``: *every auditable state mutation must reach the
audited seam ``services.audit_events.emit_audit_action``.*

THE FINDING: an in-scope function (``cogs``/``views``/``services``/``governance``/``core``)
that performs a **direct write signal** on its own body but whose success path **never reaches
``emit_audit_action``** — directly, or through any function it calls (transitively). That is the
exact defect class the Stage-2 subsystem walk surfaced by hand in #1728 (the "save-fixes"):

  * bug #5 — the raid-lockdown slowmode called ``channel.edit()`` directly, bypassing the audited
    ``ChannelLifecycleService`` seam.
  * bug #6 — the word/strict toggles wrote ``utils.db`` directly (no audit), and ``!cleanuphistory``
    called the plan fn directly while moderation routed the *same* write through the audited seam.

This checker turns "did we remember to audit this?" from a subsystem-walk discovery into a CI
signal — it would have caught 3 of the 8 #1728 bugs at authoring time.

WHY PER-FUNCTION, NOT PER-MODULE (calibration, ``docs/ideas/audit-seam-coverage-checker-2026-07-05.md``):
    A module-level ``*_mutation.py`` heuristic is ~42% false-positive (5 of 12 mutation modules
    legitimately never audit — AI-config / BTD6-data writes) AND misses the bug class entirely
    (the real #1728 bugs lived *outside* ``*_mutation.py``). So the scope is per-function,
    repo-wide.

WRITE SIGNALS (direct, body-local — precise, low false-positive):
  1. **Raw write SQL** — a ``.execute()/.executemany()`` whose SQL literal contains a write verb
     (INSERT/UPDATE/DELETE/CREATE/DROP/ALTER/TRUNCATE), outside ``utils/db/`` (the sanctioned
     raw-write layer, which is excluded from findings).
  2. **Discord state mutation** — ``.edit/.delete/.set_permissions/.clone/.ban/.kick/.add_roles/
     .remove_roles/.move_to/.timeout/.edit_role`` on a non-message receiver (``.edit``/``.delete``
     on a ``message``/``msg`` receiver are panel re-renders, not state mutations — mirrors
     ``tests/unit/invariants/test_no_direct_channel_mutations.py``).
  3. **utils.db write helper** — a call to a ``utils/db/`` function that writes (computed by
     fixpoint: has raw write SQL, or calls another db write helper), invoked as a db call
     (``db.set_x(...)`` where ``db`` is a ``utils.db`` import alias, or a bare ``set_x(...)``
     imported ``from utils.db.*``). The import-qualified match is what makes this collision-safe:
     ``self.add_item(...)`` (a ``discord.ui.View`` method that shares a name with the ``inventory``
     db helper) is NOT a db call — its receiver is ``self``, not a db alias.

AUDIT REACHABILITY (transitive — the safe direction to over-approximate):
    A function audits if it calls ``emit_audit_action`` directly, or calls any function that is
    audit-reachable (name-based fixpoint over the whole ``disbot/`` call graph). Name collisions
    make audit reachability *over*-approximate → a missed bug (false negative), never a spurious
    finding (false positive). For a warn-first guard that is the correct bias — the subsystem walk
    is the backstop. This is why a caller of an audited ``*_mutation``/lifecycle seam is never
    flagged (it reaches ``emit_audit_action`` through the seam), and why a mutation service that
    writes-then-emits in the same function is clean.

PROVENANCE / RELIABILITY (Q-0105):
  - Added 2026-07-06 (CI-setup arc, handoff item #5) from the calibrated spec
    (``docs/ideas/audit-seam-coverage-checker-2026-07-05.md`` · design of record
    ``docs/planning/ci-setup-redesign-2026-07-05.md`` §C.5).
  - **Unverified:** the name-based call graph over-approximates audit reachability (collisions) and
    the ``.edit``/``.delete`` Discord signal is overloaded (a non-Discord ``.delete()`` on e.g. a
    cache is a possible false positive). Confirm a flagged function really performs an *unaudited*
    mutation against source before "fixing" it, and keep it **warn-first** (wired
    ``continue-on-error`` in ``code-quality.yml``) until it has run clean across a few sessions.
    Promotion to a hard gate is owner-gated (Q-0239 **G4**).
  - **Disposable:** if it proves noisy across multiple sessions, widen
    ``architecture_rules/audit_seam_exceptions.yml`` or **delete this script** — the subsystem
    walk is the backstop, not this convenience guard.

Usage::

    python3.10 scripts/check_audit_seam.py                 # report (exit 0)
    python3.10 scripts/check_audit_seam.py --mode strict    # exit 1 on any finding
    python3.10 scripts/check_audit_seam.py --json           # machine-readable
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
UTILS_DB_PREFIX = "disbot/utils/db"
RULES_DIR = REPO_ROOT / "architecture_rules"
_EXCEPTIONS_FILE = "audit_seam_exceptions.yml"

# Layers that own auditable mutation paths — the finding scope. utils/ (incl. the utils/db raw-write
# primitive layer) is used to build the call graph + write-helper set but never itself flagged.
_SCOPE_LAYERS = ("cogs", "views", "services", "governance", "core")

# The audited seam anchor. A function is "audit-reachable" iff it calls this (directly) or reaches a
# function that does. Wrappers like moderation's ``_record_action`` / a mutation's ``_emit_event``
# are covered transitively — only the one canonical primitive needs naming here.
_AUDIT_SEAM_CALLS = frozenset({"emit_audit_action"})

# Discord state-mutation methods (calibration spec list + the obvious member/role siblings).
_DISCORD_MUT_ATTRS = frozenset(
    {
        "set_permissions",
        "clone",
        "ban",
        "kick",
        "add_roles",
        "remove_roles",
        "move_to",
        "timeout",
        "edit_role",
    },
)
# ``edit``/``delete`` are overloaded — a state mutation on a channel/role/member, but a message op
# (panel re-render) on a message receiver. Pin them, excluding message ops two ways:
#   (a) the receiver reads as a message (``message``/``msg`` or a ``*_message``/``*_msg`` tail like
#       ``parent_message`` / ``t.reg_message``) — extends the {message,msg} set in
#       tests/unit/invariants/test_no_direct_channel_mutations.py; and
#   (b) an ``.edit(...)`` whose keywords are ALL message-edit kwargs (``embed``/``view``/``content``/
#       …) — sound because channel/role/member edits never take those (they use ``name``/
#       ``overwrites``/``topic``/``nick``/``slowmode_delay``/…), so this distinguishes a
#       ``m.edit(embed=…)`` re-render from a ``channel.edit(name=…)`` state mutation by what it writes.
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
        "allowed_mentions",
        "flags",
    },
)

# Raw write SQL verbs — a ``.execute()/.executemany()`` string arg containing one of these is a write.
_WRITE_VERBS = re.compile(
    r"\b(?:INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE)\b",
    re.IGNORECASE,
)
_EXECUTE_ATTRS = frozenset({"execute", "executemany"})


# ---------------------------------------------------------------------------
# Finding model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    file: str  # repo-relative, e.g. "disbot/services/security_service.py"
    line: int
    qualname: str  # e.g. "SecurityService.apply_lockdown"
    signals: tuple[str, ...]  # human descriptions of the write signal(s) found

    def key(self) -> tuple[str, str]:
        """Stable identity used by any baseline ratchet: (file, qualname)."""
        return (self.file, self.qualname)

    def display(self) -> str:
        sig = "; ".join(self.signals)
        return f"  [FINDING] {self.file}:{self.line}  {self.qualname}  —  {sig}"


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _direct_calls(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.Call]:
    """Every ``ast.Call`` in ``fn``'s body, NOT descending into nested def/class bodies.

    Calls made inside a nested function belong to that nested function (it is collected as its own
    node), so the signal is attributed to the innermost enclosing def.
    """
    calls: list[ast.Call] = []
    stack: list[ast.AST] = list(fn.body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue  # a separate collected node owns this
        if isinstance(node, ast.Call):
            calls.append(node)
        stack.extend(ast.iter_child_nodes(node))
    return calls


def _callee_name(call: ast.Call) -> str | None:
    """The short callee name of a call (``foo`` for ``foo()`` and for ``x.foo()``)."""
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _string_arg(node: ast.expr) -> str | None:
    """The string value of a literal / f-string node (else None)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            v.value
            for v in node.values
            if isinstance(v, ast.Constant) and isinstance(v.value, str)
        )
    return None


def _is_raw_write_call(call: ast.Call) -> bool:
    """True if ``call`` is ``<x>.execute(...)`` with a write-verb SQL literal."""
    func = call.func
    if not (isinstance(func, ast.Attribute) and func.attr in _EXECUTE_ATTRS):
        return False
    for arg in call.args:
        sql = _string_arg(arg)
        if sql and _WRITE_VERBS.search(sql):
            return True
    return False


def _receiver_tail(value: ast.expr) -> str:
    """Trailing name of a call receiver (``message`` for ``self.message``)."""
    try:
        return ast.unparse(value).rsplit(".", 1)[-1]
    except Exception:  # pragma: no cover - defensive
        return ""


def _is_message_receiver(value: ast.expr) -> bool:
    """True if the receiver reads as a message object (``message``/``msg``/``*_message``/``*_msg``)."""
    tail = _receiver_tail(value)
    return tail in _MESSAGE_RECEIVERS or tail.endswith(("_message", "_msg"))


def _is_message_edit(call: ast.Call) -> bool:
    """True if an ``.edit(...)`` writes only message fields (embed/view/content/…) — a re-render."""
    return bool(call.keywords) and all(
        kw.arg in _MESSAGE_EDIT_KWARGS for kw in call.keywords if kw.arg is not None
    )


def _discord_mutation(call: ast.Call) -> str | None:
    """Return the Discord state-mutation attr name if ``call`` is one, else None."""
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None
    attr = func.attr
    if attr in _DISCORD_MUT_ATTRS:
        return attr
    if attr in _OVERLOADED_MUT_ATTRS:
        if _is_message_receiver(func.value):
            return None  # a message re-render, not a state mutation
        if attr == "edit" and _is_message_edit(call):
            return None  # edits only message fields → a re-render on a non-message-named var
        return attr
    return None


def _db_write_call(
    call: ast.Call,
    db_aliases: frozenset[str],
    bare_db_names: frozenset[str],
    write_helpers: frozenset[str],
) -> str | None:
    """Return the db write-helper name if ``call`` is an import-qualified db write, else None.

    Collision-safe: an attribute call counts only when its receiver is a ``utils.db`` import alias
    (so ``self.add_item`` / ``view.add_item`` — the ``discord.ui.View`` method that shares a name
    with the ``inventory`` db helper — never matches); a bare call counts only when the name was
    imported ``from utils.db.*``.
    """
    func = call.func
    if (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id in db_aliases
        and func.attr in write_helpers
    ):
        return func.attr
    if (
        isinstance(func, ast.Name)
        and func.id in bare_db_names
        and func.id in write_helpers
    ):
        return func.id
    return None


def _is_db_qualified_call(call: ast.Call, dbi: _DbImports) -> bool:
    """True if the call resolves to the ``utils.db`` layer (``db.foo`` / a bare ``from utils.db.*``).

    Such a call — read or write — targets the raw-write primitive layer, which never audits, so it
    must not contribute to audit reachability (see ``_analyze_fn``).
    """
    func = call.func
    if (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id in dbi.aliases
    ):
        return True
    return isinstance(func, ast.Name) and func.id in dbi.bare


# ---------------------------------------------------------------------------
# Per-file imports (which names are utils.db calls)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _DbImports:
    aliases: frozenset[
        str
    ]  # names bound to utils.db or a utils.db submodule (db.x, btd.x, ...)
    bare: frozenset[str]  # function names imported `from utils.db.* import name`


def _db_imports(tree: ast.AST) -> _DbImports:
    aliases: set[str] = set()
    bare: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mod = node.module
            if mod == "utils.db":
                # `from utils.db import settings` — a submodule alias (settings.set_x(...)).
                for a in node.names:
                    aliases.add(a.asname or a.name)
            elif mod.startswith("utils.db."):
                # `from utils.db.settings import set_setting` — bare callable names.
                for a in node.names:
                    bare.add(a.asname or a.name)
            elif mod == "utils":
                for a in node.names:
                    if a.name == "db":
                        aliases.add(a.asname or "db")
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "utils.db" or a.name.startswith("utils.db."):
                    # `import utils.db as X` / `import utils.db.settings as Y`.
                    aliases.add(a.asname or a.name.split(".")[-1])
    return _DbImports(frozenset(aliases), frozenset(bare))


# ---------------------------------------------------------------------------
# utils.db write-helper set (fixpoint)
# ---------------------------------------------------------------------------


def build_db_write_helpers(db_sources: dict[str, str]) -> frozenset[str]:
    """Names of ``utils/db/`` functions that write (fixpoint over ``db_sources``).

    A db function is a write helper if its own body has a raw write SQL call, or it calls another
    db write helper (thin wrappers like ``delete_for_guild`` → ``delete_by_ids``).
    """
    # name -> (has_raw_write, callee_names)
    fns: dict[str, tuple[bool, frozenset[str]]] = {}
    for source in db_sources.values():
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            calls = _direct_calls(node)
            has_raw = any(_is_raw_write_call(c) for c in calls)
            callees = frozenset(n for c in calls if (n := _callee_name(c)) is not None)
            prev = fns.get(node.name)
            # A name can appear in several db modules; OR their signals together.
            if prev is None:
                fns[node.name] = (has_raw, callees)
            else:
                fns[node.name] = (prev[0] or has_raw, prev[1] | callees)

    writers = {name for name, (has_raw, _) in fns.items() if has_raw}
    changed = True
    while changed:
        changed = False
        for name, (_, callees) in fns.items():
            if name not in writers and (callees & writers):
                writers.add(name)
                changed = True
    return frozenset(writers)


# ---------------------------------------------------------------------------
# Function collection (call graph nodes)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _FnInfo:
    file: str
    line: int
    name: str
    qualname: str
    callees: frozenset[str]
    direct_audit: bool
    # Always-on write signals (raw SQL / Discord state mutation) — these are inherently auditable.
    always_signals: tuple[str, ...]
    # utils.db write-helper calls: (helper_name, lineno). Conditional — a db write is only a finding
    # when its helper is *auditable-class* (some audit-reachable function writes it; see ``analyze``).
    db_calls: tuple[tuple[str, int], ...]
    in_scope: bool


def _collect_functions(
    file: str,
    tree: ast.AST,
    dbi: _DbImports,
    write_helpers: frozenset[str],
    *,
    in_scope: bool,
) -> list[_FnInfo]:
    out: list[_FnInfo] = []

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, f"{prefix}{child.name}.")
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.append(
                    _analyze_fn(file, child, prefix, dbi, write_helpers, in_scope)
                )
                visit(child, f"{prefix}{child.name}.")
            else:
                visit(child, prefix)

    visit(tree, "")
    return out


def _analyze_fn(
    file: str,
    fn: ast.FunctionDef | ast.AsyncFunctionDef,
    prefix: str,
    dbi: _DbImports,
    write_helpers: frozenset[str],
    in_scope: bool,
) -> _FnInfo:
    calls = _direct_calls(fn)
    callees: set[str] = set()
    direct_audit = False
    always: list[str] = []
    db_calls: list[tuple[str, int]] = []

    for call in calls:
        name = _callee_name(call)
        if name is not None:
            # A db-qualified call (``db.set_x`` / a bare name imported ``from utils.db.*``) resolves
            # to the utils.db raw-write layer, which is NEVER an audit seam — so it must not feed the
            # audit-reachability set. Skipping it defeats the name collision where a db helper shares
            # a name with its audited service wrapper (``db.set_wordfilter_strict`` vs
            # ``prohibited_words_service.set_wordfilter_strict``): without this, a direct db call would
            # borrow the wrapper's audit reachability and the unaudited bypass (bug #6) would hide.
            if not _is_db_qualified_call(call, dbi):
                callees.add(name)
            if name in _AUDIT_SEAM_CALLS:
                direct_audit = True
        if _is_raw_write_call(call):
            always.append(f"raw write SQL (.{call.func.attr}) @ L{call.lineno}")  # type: ignore[attr-defined]
        elif (mut := _discord_mutation(call)) is not None:
            always.append(f"Discord state mutation .{mut}() @ L{call.lineno}")
        elif (
            helper := _db_write_call(call, dbi.aliases, dbi.bare, write_helpers)
        ) is not None:
            db_calls.append((helper, call.lineno))

    return _FnInfo(
        file=file,
        line=fn.lineno,
        name=fn.name,
        qualname=f"{prefix}{fn.name}",
        callees=frozenset(callees),
        direct_audit=direct_audit,
        always_signals=tuple(always),
        db_calls=tuple(db_calls),
        in_scope=in_scope,
    )


# ---------------------------------------------------------------------------
# Audit reachability (name-based fixpoint)
# ---------------------------------------------------------------------------


def _audit_reachable_names(functions: list[_FnInfo]) -> frozenset[str]:
    """Set of function names that reach ``emit_audit_action`` (directly or transitively).

    Name-merged (a name is reachable if ANY def with it reaches audit) → over-approximates in the
    safe direction: a collision hides a real finding (false negative), never invents one.
    """
    by_name: dict[str, list[_FnInfo]] = {}
    for fn in functions:
        by_name.setdefault(fn.name, []).append(fn)

    reachable: set[str] = {
        name for name, fns in by_name.items() if any(f.direct_audit for f in fns)
    }
    changed = True
    while changed:
        changed = False
        for name, fns in by_name.items():
            if name in reachable:
                continue
            if any(f.callees & reachable for f in fns):
                reachable.add(name)
                changed = True
    return frozenset(reachable)


# ---------------------------------------------------------------------------
# Allowlist
# ---------------------------------------------------------------------------


def load_exceptions(path: Path | None = None) -> dict:
    p = path if path is not None else RULES_DIR / _EXCEPTIONS_FILE
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _allowlisted(file: str, qualname: str, exceptions: dict) -> bool:
    """True if (file[, function]) is allowlisted.

    An entry with only ``file`` exempts every function in that file; adding ``function`` narrows it
    to a qualname (``Class.method``) or a bare method name. Paths match with the ``disbot/`` prefix
    optional.
    """
    norm_file = file.replace("disbot/", "")
    bare = qualname.rsplit(".", 1)[-1]
    for exc in exceptions.get("exceptions", []):
        pat = str(exc.get("file", "")).strip().replace("disbot/", "")
        if not pat or pat != norm_file:
            continue
        fn = exc.get("function")
        if fn is None or str(fn) in (qualname, bare):
            return True
    return False


# ---------------------------------------------------------------------------
# Analysis entry point (testable — operates on injected sources)
# ---------------------------------------------------------------------------


def _layer_of(rel: str) -> str | None:
    parts = rel.split("/")
    return parts[1] if len(parts) > 2 and parts[0] == "disbot" else None


def analyze(sources: dict[str, str], exceptions: dict | None = None) -> list[Finding]:
    """Compute findings from ``sources`` (repo-relative path -> source text).

    Fully injectable so tests need no disk: any path under ``disbot/utils/db`` feeds the write-helper
    set; any path in a scope layer is finding-eligible; all paths feed the audit call graph.
    """
    exceptions = exceptions if exceptions is not None else {}
    db_sources = {p: s for p, s in sources.items() if p.startswith(UTILS_DB_PREFIX)}
    write_helpers = build_db_write_helpers(db_sources)

    functions: list[_FnInfo] = []
    for rel, source in sources.items():
        try:
            tree = ast.parse(source, filename=rel)
        except SyntaxError:
            continue
        dbi = _db_imports(tree)
        in_scope = (
            _layer_of(rel) in _SCOPE_LAYERS
            and not rel.startswith(UTILS_DB_PREFIX)
            and "test" not in rel.lower()
        )
        functions.extend(
            _collect_functions(rel, tree, dbi, write_helpers, in_scope=in_scope),
        )

    audit_names = _audit_reachable_names(functions)

    def _audits(fn: _FnInfo) -> bool:
        return fn.direct_audit or bool(fn.callees & audit_names)

    # Auditable-class db helpers: a utils.db write helper is "auditable" iff some function writes it
    # AND emits audit *in the same body* (``direct_audit``) — the audited service-wrapper shape
    # (``prohibited_words_service.set_wordfilter_strict`` → ``db.set_wordfilter_strict`` +
    # ``emit_audit_action``). Scoping the db-write signal this way is what keeps it honest: it fires
    # for a domain proven auditable (moderation / settings / roles / …) done UNaudited (bug #6), and
    # never for economy / games / sessions / state writes that no audited wrapper touches — the ~42%
    # false-positive class the calibration warned about. Self-calibrating from the repo's own audit
    # patterns, so it needs no hand-maintained "auditable tables" list.
    #
    # DIRECT audit only (not transitive ``_audits``): the name-merged call graph marks generic verbs
    # (``credit`` / ``award``) audit-reachable off one namesake, which would spuriously mark whole game
    # domains auditable. Requiring write+emit in ONE body is collision-proof — it reads the wrapper
    # itself, not a reachability chain.
    auditable_db: set[str] = set()
    for fn in functions:
        if fn.direct_audit:
            auditable_db.update(helper for helper, _ in fn.db_calls)

    findings: list[Finding] = []
    for fn in functions:
        if not fn.in_scope or _audits(fn):
            continue
        signals = list(fn.always_signals)
        signals += [
            f"utils.db write helper {helper}() @ L{ln}"
            for helper, ln in fn.db_calls
            if helper in auditable_db
        ]
        if not signals:
            continue
        if _allowlisted(fn.file, fn.qualname, exceptions):
            continue
        findings.append(
            Finding(
                file=fn.file,
                line=fn.line,
                qualname=fn.qualname,
                signals=tuple(signals),
            ),
        )
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
    """Read ``disbot/`` from disk and analyze."""
    if exceptions is None:
        exceptions = load_exceptions()
    return analyze(_read_disbot_sources(), exceptions)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _print_report(findings: list[Finding]) -> None:
    print(f"\ncheck_audit_seam — {len(findings)} finding(s)\n")
    if not findings:
        print("  every in-scope mutation reaches the audited seam ✓")
        return
    print(
        "  Unaudited mutations — a function performs a write signal but its success path never\n"
        "  reaches services.audit_events.emit_audit_action:\n",
    )
    by_file: dict[str, list[Finding]] = {}
    for f in findings:
        by_file.setdefault(f.file, []).append(f)
    for file in sorted(by_file):
        print(f"  {file}")
        for f in by_file[file]:
            print(f"      L{f.line:<5} {f.qualname}")
            for sig in f.signals:
                print(f"              · {sig}")
    print(
        "\n  Fix: route the mutation through the domain's audited *_mutation / lifecycle service "
        "(which calls emit_audit_action), or\n  add emit_audit_action to this function — or, if it "
        f"is a legitimately non-auditable write, allowlist it in\n  architecture_rules/{_EXCEPTIONS_FILE} "
        "with a reason.",
    )


def _print_json(findings: list[Finding]) -> None:
    print(
        json.dumps(
            {
                "findings": [
                    {
                        "file": f.file,
                        "line": f.line,
                        "qualname": f.qualname,
                        "signals": list(f.signals),
                    }
                    for f in findings
                ],
            },
            indent=2,
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit-seam coverage guard (warn-first — unaudited mutation finder)",
    )
    parser.add_argument(
        "--mode",
        choices=["report", "strict"],
        default="report",
        help="report: always exit 0; strict: exit 1 if any finding",
    )
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
