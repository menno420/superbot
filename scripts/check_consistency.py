#!/usr/bin/env python3
"""UX / interaction-pattern consistency linter for SuperBot.

A companion to ``check_architecture.py``.  Where the architecture checker sees
*import layers*, this one sees *interaction patterns* — the mechanical UX house
rules that no import graph can catch (owner directive Q-0170, 2026-06-17):

  1. **edit-in-place** — a panel button/select callback that delivers its result
     as a standalone ephemeral message instead of updating the panel in place.
  2. **back-button** — a ``HubView`` navigation panel with its own child
     button/select callbacks but no back/nav affordance anywhere in its module.
  3. **panel base-class** — a view extending ``discord.ui.View`` directly outside
     the ``views/rps``/``views/blackjack`` game-state allowlist and the framework
     home (``views/base.py``), instead of ``BaseView``/``HubView``/``PersistentView``.
  4. **select-option truncation** — a select-building view that *front-truncates* a
     collection (``options[:25]``, ``roles[:25]``) instead of paginating.  A Discord
     select caps at 25 options, so the slice silently drops every entry past the cap
     (the #1040 class).  Windowed pagination (``x[start:start+N]``) is not flagged.
  5. **card-engine helper duplication** — an image renderer (``utils/``) that
     re-declares a primitive the shared ``utils/card_render.py`` engine already owns.
  6. **settle-once adoption** — a wager-settling site (a call to
     ``game_wager_workflow.settle_pvp`` / ``refund_pvp``, which pay out / refund the
     escrowed pot) whose path does not adopt the settle-once guard
     (``utils/terminal_guard.SettleOnceMixin`` / ``claim_settlement()``).  A money
     settlement reachable from more than one trigger (a finishing button *and*
     ``on_timeout``, or two players' callbacks) double-settles the pot without one
     atomic claim — the BUG-0013 class the mixin (PRs #1444/#1445) closed by hand.

Scope is **per-rule** (each :class:`Rule` carries a ``roots`` tuple).  Rules 1-2
scan only ``views/``; rules 3-4 also scan ``cogs/`` — cogs define inline
``discord.ui.View`` subclasses and select-building UI, so the cog layer is a real
blind spot for those two patterns (BUG-0017, the Cog-Manager ``options[:25]``
silent drop, lived in ``cogs/admin/cog_manager.py`` and slipped past the linter
precisely because rules 3-4 were once ``views/``-only).

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
    python scripts/check_consistency.py --mode strict    # exit 1 on GRADUATED-rule findings
    python scripts/check_consistency.py --file disbot/views/x.py
    python scripts/check_consistency.py --graduation     # per-rule graduation tracker

A rule graduates by flipping its ``Rule.severity`` from ``"warning"`` to
``"error"`` (which makes ``--mode strict`` fail on a finding) once it has run
clean across a few sessions; ``--graduation`` reports, per rule, whether it is
``ELIGIBLE`` / ``NOT READY`` / ``BLOCKED`` (and by what) / ``GRADUATED``.
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


def _inplace_helper_names(cls: ast.ClassDef) -> frozenset[str]:
    """Names of the class's own methods whose body edits a message in place.

    The codebase's house idiom re-renders a panel through a small same-class
    helper (``self._rerender()`` -> ``self.message.edit(...)``), not a direct
    ``interaction.response.edit_message`` in the callback.  A callback that calls
    such a helper *does* edit in place, so collecting these lets
    :func:`_calls_inplace_helper` clear that false-positive class.
    """
    return frozenset(
        m.name
        for m in cls.body
        if isinstance(m, (ast.AsyncFunctionDef, ast.FunctionDef)) and _edits_in_place(m)
    )


def _calls_inplace_helper(fn: ast.AST, helpers: frozenset[str]) -> bool:
    """True if *fn* calls ``self.<m>()`` where ``<m>`` is an in-place helper."""
    for sub in ast.walk(fn):
        if (
            isinstance(sub, ast.Call)
            and isinstance(sub.func, ast.Attribute)
            and sub.func.attr in helpers
            and isinstance(sub.func.value, ast.Name)
            and sub.func.value.id == "self"
        ):
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
# Shared scan loop
# ---------------------------------------------------------------------------


def _iter_parsed(
    files: list[Path],
    roots: tuple[str, ...],
) -> list[tuple[Path, str, ast.Module]]:
    """Yield ``(path, rel, tree)`` for each parseable file under one of *roots*.

    Centralises the per-rule scan boilerplate (relativize to ``DISBOT_ROOT``,
    skip tests, skip files outside the rule's roots, parse) so a rule opts into
    additional scope just by widening its :attr:`Rule.roots` — no copy-pasted
    loop.  *roots* are ``DISBOT_ROOT``-relative path prefixes (e.g. ``"views/"``,
    ``"cogs/"``); a file matches if its rel-path starts with any of them.
    """
    out: list[tuple[Path, str, ast.Module]] = []
    for filepath in files:
        try:
            rel = str(filepath.relative_to(DISBOT_ROOT))
        except ValueError:
            continue
        if "test" in rel.lower():
            continue
        if not rel.startswith(roots):
            continue
        try:
            tree = ast.parse(filepath.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, OSError):
            continue
        out.append((filepath, rel, tree))
    return out


# ---------------------------------------------------------------------------
# Rule 1 — edit-in-place
# ---------------------------------------------------------------------------


def rule_edit_in_place(
    files: list[Path],
    exceptions: dict,
    roots: tuple[str, ...] = ("views/",),
) -> list[Finding]:
    """Flag panel callbacks whose result is a standalone ephemeral, not an edit.

    A button/select callback that sends a *new* ephemeral message and never edits
    the panel in place delivers its outcome out-of-band — the owner's headline
    inconsistency.  Early-return validation toasts (``send; return``) are excluded;
    so are callbacks that also edit in place (a mixed/guarded path).
    """
    cfg = exceptions.get("edit_in_place", {})
    findings: list[Finding] = []

    for filepath, rel, tree in _iter_parsed(files, roots):
        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef) or not _is_view_class(cls):
                continue
            helpers = _inplace_helper_names(cls)
            for fn in cls.body:
                if not isinstance(fn, (ast.AsyncFunctionDef, ast.FunctionDef)):
                    continue
                if not _is_ui_callback(fn) or _edits_in_place(fn):
                    continue
                if _calls_inplace_helper(fn, helpers):
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
# Rule 2 — back-button presence
# ---------------------------------------------------------------------------


# The shared nav helpers (``views/navigation.py``) and the per-hub wrappers
# (``attach_back_to_community_button`` / ``attach_back_to_games_button``) — any
# one of these in the module is a back affordance.  A button labelled/keyed
# "back" or a back glyph counts too.
_BACK_HELPER_PREFIXES = ("attach_back", "chain_back")
# `transition_to(interaction, builder=...)` is the shared navigation helper
# (views/navigation.py) a panel's Home/Back button uses to swap to a parent
# panel — the UX-lab wings + compare/probes bench all route their Home button
# through it, so a module that calls it is navigable, not a dead-end.
_NAV_HELPER_NAMES = ("transition_to",)
_BACK_TOKENS = ("back", "◀", "⬅", "🔙", "↩", "←")


def _call_name(call: ast.Call) -> str:
    """The bare function name of a call (``attach_back_button(...)`` -> name)."""
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _str_consts(node: ast.AST) -> list[str]:
    """Lower-cased string constants anywhere under *node* (labels, custom_ids)."""
    out: list[str] = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            out.append(sub.value.lower())
    return out


def _module_has_back_affordance(tree: ast.Module) -> bool:
    """True if the module references any back/nav affordance.

    Signals (any one suffices — kept generous because a child panel's back
    button is very often attached *externally* by its parent, so we accept a
    module-wide reference rather than demanding it inside the class body):

    - a call to a ``attach_back*`` / ``chain_back`` helper;
    - a ``Button``/``ui.button`` whose label or ``custom_id`` names "back" or a
      back glyph;
    - any call setting a ``label`` / ``custom_id`` / ``emoji`` keyword to a back
      token — this catches a **custom back-button subclass** (e.g.
      ``class _BackToHubButton(discord.ui.Button)`` whose ``__init__`` does
      ``super().__init__(label="Back to Hub", custom_id="...back", emoji="↩")``
      and is added via ``add_item``), which the ``Button(...)``/``@ui.button``
      checks above miss because the call name is ``__init__``.
    """
    for sub in ast.walk(tree):
        if isinstance(sub, ast.Call):
            name = _call_name(sub)
            if name.startswith(_BACK_HELPER_PREFIXES) or name in _NAV_HELPER_NAMES:
                return True
            # A constructed Button(..., custom_id="...:back", label="◀ Back").
            if name in {"Button", "button"}:
                for text in _str_consts(sub):
                    if any(tok in text for tok in _BACK_TOKENS):
                        return True
            # A back-token label/custom_id/emoji on any call — covers custom
            # back-button subclasses wired through `super().__init__(...)`.
            for kw in sub.keywords:
                if (
                    kw.arg in {"label", "custom_id", "emoji"}
                    and isinstance(kw.value, ast.Constant)
                    and isinstance(kw.value.value, str)
                    and any(tok in kw.value.value.lower() for tok in _BACK_TOKENS)
                ):
                    return True
        # A @ui.button(...) decorated callback whose label/custom_id is a back.
        if isinstance(sub, (ast.AsyncFunctionDef, ast.FunctionDef)):
            for dec in sub.decorator_list:
                if isinstance(dec, ast.Call) and _decorator_attr(dec) == "button":
                    for text in _str_consts(dec):
                        if any(tok in text for tok in _BACK_TOKENS):
                            return True
    return False


def _is_hub_view_class(node: ast.ClassDef) -> bool:
    """True if the class extends ``HubView`` (the navigation-panel base)."""
    return any(base.rsplit(".", 1)[-1] == "HubView" for base in _class_bases(node))


def _class_gets_auto_nav(node: ast.ClassDef) -> bool:
    """True if the class auto-attaches standard nav (the never-stranded mechanism).

    A panel that declares a non-empty ``SUBSYSTEM`` (and does not opt out with
    ``STANDARD_NAV = False``) gets a ``📚 Help`` (+ ``↩ <hub>``) control on
    construction from ``views.navigation.attach_standard_nav`` (run in the
    ``BaseView`` / ``PersistentView`` ``__init__``). It is therefore never a
    back/nav gap, even when its module references no ``attach_back_button`` —
    the auto-nav IS the affordance. Recognising it here keeps this static rule
    from false-flagging the leaf panels the universal mechanism already covers
    (the Q-0120 "a check that contradicts the evidence is a bug in the check").
    """
    has_subsystem = False
    standard_nav_off = False
    for stmt in node.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(stmt, ast.Assign):
            targets, value = stmt.targets, stmt.value
        elif isinstance(stmt, ast.AnnAssign):
            targets, value = [stmt.target], stmt.value
        for tgt in targets:
            if not isinstance(tgt, ast.Name):
                continue
            if (
                tgt.id == "SUBSYSTEM"
                and isinstance(value, ast.Constant)
                and bool(value.value)
            ):
                has_subsystem = True
            if (
                tgt.id == "STANDARD_NAV"
                and isinstance(value, ast.Constant)
                and value.value is False
            ):
                standard_nav_off = True
    return has_subsystem and not standard_nav_off


def _class_adds_items_dynamically(node: ast.ClassDef) -> bool:
    """True if the class builds controls via ``add_item(...)`` rather than
    decorated ``@ui.button``/``@ui.select`` callbacks.

    Registry-driven hubs (the Explore world hub, the Games/Community hubs) add
    their buttons in ``__init__`` with ``self.add_item(SomeButton(...))``. Such a
    hub has no ``@ui.button`` callback in its class body, so without this signal
    :func:`rule_back_button` saw it as control-less and skipped it — the exact
    gap that let the Explore world-hub dead-end ship past this (graduated) rule.
    """
    return any(
        isinstance(sub, ast.Call)
        and isinstance(sub.func, ast.Attribute)
        and sub.func.attr == "add_item"
        for sub in ast.walk(node)
    )


def rule_back_button(
    files: list[Path],
    exceptions: dict,
    roots: tuple[str, ...] = ("views/",),
) -> list[Finding]:
    """Flag a ``HubView`` navigation panel with child controls but no back affordance.

    A ``HubView`` subclass is a navigable panel — it should offer a way back.  We
    treat it as navigable if it declares its own ``@ui.button``/``@ui.select``
    callbacks **or** builds controls dynamically via ``add_item`` (registry-driven
    hubs — the Explore world hub, Games/Community hubs — do the latter, and used to
    slip through this rule entirely).  We flag such a panel when **its whole module**
    references no back affordance — see :func:`_module_has_back_affordance` for the
    recognized signals (``attach_back*`` / ``chain_back`` / ``transition_to``, a
    back-labelled button, or a back-token ``label``/``custom_id``/``emoji`` on any
    call, which covers custom back-button subclasses).

    Known false positive: a child panel whose back button is attached *externally*
    by its parent (a different module) looks bare here — allowlist those in
    ``consistency_exceptions.yml`` (and a true top-of-stack root has no parent).
    """
    cfg = exceptions.get("back_button", {})
    findings: list[Finding] = []

    for filepath, rel, tree in _iter_parsed(files, roots):
        if _module_has_back_affordance(tree):
            continue

        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef) or not _is_hub_view_class(cls):
                continue
            has_child_control = any(
                isinstance(fn, (ast.AsyncFunctionDef, ast.FunctionDef))
                and _is_ui_callback(fn)
                for fn in cls.body
            ) or _class_adds_items_dynamically(cls)
            if not has_child_control:
                continue
            # A SUBSYSTEM-declaring panel auto-attaches standard nav in its
            # constructor (attach_standard_nav) — the affordance is present at
            # runtime even though no attach_back_button call appears statically.
            if _class_gets_auto_nav(cls):
                continue
            if _is_allowlisted(rel, cls.name, cfg):
                continue
            findings.append(
                Finding(
                    file=filepath,
                    line=cls.lineno,
                    rule="back_button",
                    qualname=cls.name,
                    message=(
                        f"`{cls.name}` is a HubView panel with child controls but "
                        "its module has no back/nav affordance — attach one via "
                        "`views.navigation.attach_back_button(...)` (allowlist in "
                        "consistency_exceptions.yml if the parent attaches it)"
                    ),
                ),
            )

    return findings


# ---------------------------------------------------------------------------
# Rule 3 — panel base-class
# ---------------------------------------------------------------------------


# Direct ``discord.ui.View`` subclassing is sanctioned only in the framework home
# (where ``BaseView``/``HubView`` are defined) and the documented specialized-lifecycle
# lanes.  These MIRROR the arch checker's own ground truth — the path exemptions in
# ``architecture_rules/canonical_helpers.yaml § base_view.exemptions`` (game-state
# views in rps/blackjack/games + the ai/* policy/tools/behavior surfaces, all with a
# documented "specialized lifecycle ownership" reason).  Keeping the two checkers in
# sync is the Q-0120 rule: a consistency verdict that re-flags an already-decided
# arch exemption is the *consistency tool's* false positive, not new debt.
_BASE_CLASS_ALLOWED_PATHS = (
    "views/rps/",
    "views/blackjack/",
    "views/casino/",
    "views/fishing/",
    "views/games/",
    "views/ai/",
    "views/base.py",
)
_DIRECT_VIEW_BASES = frozenset({"discord.ui.View", "ui.View", "View"})


def _extends_view_directly(node: ast.ClassDef) -> bool:
    """True if a direct base is ``discord.ui.View`` (not a ``BaseView`` wrapper)."""
    return any(base in _DIRECT_VIEW_BASES for base in _class_bases(node))


def rule_panel_base_class(
    files: list[Path],
    exceptions: dict,
    roots: tuple[str, ...] = ("views/",),
) -> list[Finding]:
    """Flag a view extending ``discord.ui.View`` directly outside the allowlist.

    ``docs/architecture.md`` § Views states (in prose) that UI views must extend
    ``BaseView``/``HubView``/``PersistentView``; only game-state views in
    ``views/rps``/``views/blackjack`` may extend ``discord.ui.View`` directly (with
    a comment).  This makes that prose rule mechanical.  Warn-only — many existing
    picker views extend directly for a specialized ephemeral lifecycle; triage
    them to a base class or an allowlist entry over time.
    """
    cfg = exceptions.get("panel_base_class", {})
    findings: list[Finding] = []

    for filepath, rel, tree in _iter_parsed(files, roots):
        if rel.startswith(_BASE_CLASS_ALLOWED_PATHS):
            continue

        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef) or not _extends_view_directly(cls):
                continue
            if _is_allowlisted(rel, cls.name, cfg):
                continue
            findings.append(
                Finding(
                    file=filepath,
                    line=cls.lineno,
                    rule="panel_base_class",
                    qualname=cls.name,
                    message=(
                        f"`{cls.name}` extends `discord.ui.View` directly — prefer "
                        "`BaseView`/`HubView`/`PersistentView` (allowlist in "
                        "consistency_exceptions.yml for a game-state lifecycle view)"
                    ),
                ),
            )

    return findings


# ---------------------------------------------------------------------------
# Rule 4 — select-option truncation
# ---------------------------------------------------------------------------


# A Discord select accepts at most 25 options; embed fields cap at 25 and an
# action row at 5 — every component-collection limit is <= 25.  A *front* slice
# to a constant <= 25 (``x[:25]``) therefore truncates a component collection and
# silently drops the tail.  A windowed page (``x[start:start+25]`` — variable
# bounds) is the correct pagination pattern and must NOT be flagged; a
# string-length slice (``label[:100]``, N > 25) is a Discord text limit, not a
# component drop, and is excluded by the threshold.
_SELECT_OPTION_LIMIT = 25


def _builds_select_options(tree: ast.Module) -> bool:
    """True if the module constructs a ``SelectOption`` anywhere.

    Scopes rule 4 to genuine select-building views, so a leaderboard ``rows[:10]``
    in a non-select view is not mistaken for an option truncation.
    """
    for sub in ast.walk(tree):
        if isinstance(sub, ast.Call) and _call_name(sub) == "SelectOption":
            return True
    return False


def _is_front_truncation(node: ast.Subscript) -> bool:
    """True if *node* is ``expr[:N]`` / ``expr[0:N]`` with constant ``N`` <= 25.

    Front truncation drops the tail past ``N``.  A windowed page (a non-constant
    upper bound such as ``start + PAGE``) or a step slice is not a truncation and
    returns ``False``; a string-length slice (``N`` > 25) is below the threshold.
    """
    sl = node.slice
    if not isinstance(sl, ast.Slice) or sl.step is not None:
        return False
    # Lower bound must be absent or a literal 0 (a real front slice).
    if sl.lower is not None and not (
        isinstance(sl.lower, ast.Constant) and sl.lower.value == 0
    ):
        return False
    upper = sl.upper
    return (
        isinstance(upper, ast.Constant)
        and isinstance(upper.value, int)
        and not isinstance(upper.value, bool)
        and 0 < upper.value <= _SELECT_OPTION_LIMIT
    )


def _front_truncations_with_scope(
    tree: ast.Module,
) -> list[tuple[ast.Subscript, str]]:
    """Yield each front-truncation subscript with its enclosing scope qualname.

    The qualname is the dotted path of the enclosing ``class``/``def`` names
    (e.g. ``ManagementPanel._DeleteRoleSelect`` or ``_destination_options``),
    so an allowlist entry can scope an exception to one callback via the
    ``::Class.method`` suffix (mirroring ``rule_edit_in_place``).  Without this,
    a file-prefix allowlist would coarsely mute every truncation in a file that
    mixes a genuine display slice with a real paginatable select.
    """
    results: list[tuple[ast.Subscript, str]] = []

    def visit(node: ast.AST, scope: list[str]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.ClassDef, ast.AsyncFunctionDef, ast.FunctionDef)):
                visit(child, [*scope, child.name])
                continue
            if isinstance(child, ast.Subscript) and _is_front_truncation(child):
                results.append((child, ".".join(scope)))
            visit(child, scope)

    visit(tree, [])
    return results


def rule_select_option_truncation(
    files: list[Path],
    exceptions: dict,
    roots: tuple[str, ...] = ("views/",),
) -> list[Finding]:
    """Flag a front-truncating slice in a select-building view (the #1040 class).

    A Discord select caps at 25 options, so ``options[:25]`` (or any ``[:N<=25]``)
    silently drops every entry past the cap instead of paginating — the bug that
    hid routable cogs in the setup cog-routing picker (#1040).  The fix is a
    windowed page (``x[start:start+N]``), which this rule does not flag.

    Warn-only.  Allowlist a genuine top-N display (e.g. an error message that
    intentionally lists only the first few of many) in ``consistency_exceptions.yml``.
    """
    cfg = exceptions.get("select_option_truncation", {})
    findings: list[Finding] = []

    for filepath, rel, tree in _iter_parsed(files, roots):
        if not _builds_select_options(tree):
            continue

        for sub, qualname in _front_truncations_with_scope(tree):
            if _is_allowlisted(rel, qualname, cfg):
                continue
            findings.append(
                Finding(
                    file=filepath,
                    line=sub.lineno,
                    rule="select_option_truncation",
                    qualname=qualname,
                    message=(
                        "front-truncating slice `[:N]` (N≤25) in a select-building "
                        "view silently drops options past Discord's 25-option cap "
                        "(the #1040 class) — paginate with a windowed page "
                        "`x[start:start+N]` (use the shared "
                        "`views/paginated_select.py` `PaginatedSelectView`), or "
                        "allowlist a genuine top-N display in consistency_exceptions.yml"
                    ),
                ),
            )

    return findings


# ---------------------------------------------------------------------------
# Rule 5 — card-engine helper duplication
# ---------------------------------------------------------------------------

# The private helper names the shared ``utils/card_render.py`` engine already
# provides (``dejavu_fonts``/``load_font``, ``CardCanvas.fit``, ``mix``,
# ``initials``/``CardCanvas.initials_disc``).  An image renderer that re-declares
# one of these is re-introducing the triplication the engine exists to remove.
_ENGINE_HELPERS = frozenset({"_fonts", "_fit", "_mix", "_initials", "_initials_disc"})


def _imports_pillow_or_engine(tree: ast.Module) -> bool:
    """True if the module imports Pillow or the shared card engine.

    Scopes the rule to *image-render* modules — a ``_fit``/``_mix`` in some
    unrelated ``utils/`` math helper is not the engine-duplication class.  Walks
    the whole tree so a lazy function-body ``from PIL import ...`` (the renderers'
    graceful-degradation idiom) still counts.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("PIL") or "card_render" in node.module:
                return True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("PIL") or "card_render" in alias.name:
                    return True
    return False


def rule_card_engine_helper_duplication(
    files: list[Path],
    exceptions: dict,
    roots: tuple[str, ...] = ("utils/",),
) -> list[Finding]:
    """Flag an image renderer that re-declares an engine-provided helper.

    The shared ``utils/card_render.py`` engine owns the card primitives.  Before
    the H2 migration (PR #1396) the dark-blurple palette + a ``_fonts``/``_fit``
    copy lived in *three* renderers (``welcome_render`` / ``ux_patterns.
    image_builders`` / ``role_menu_render``); the engine exists so there is one
    home.  An image-render module (one importing Pillow or the engine) that
    defines its own ``_fonts``/``_fit``/``_mix``/``_initials``/``_initials_disc``
    is re-growing that drift class — import the engine instead.

    Warn-only (Q-0105 — graduate once it has stayed clean across a few sessions).
    ``card_render.py`` itself is exempt (it *is* the home; its primitives are the
    public ``mix``/``initials``/``load_font``, not these private names anyway).  A
    genuinely engine-independent helper can be allowlisted in
    ``consistency_exceptions.yml``.
    """
    cfg = exceptions.get("card_engine_helper_duplication", {})
    findings: list[Finding] = []

    for filepath, rel, tree in _iter_parsed(files, roots):
        if rel.replace("\\", "/").endswith("utils/card_render.py"):
            continue  # the engine is the one legitimate home
        if not _imports_pillow_or_engine(tree):
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name in _ENGINE_HELPERS
                and not _is_allowlisted(rel, node.name, cfg)
            ):
                findings.append(
                    Finding(
                        file=filepath,
                        line=node.lineno,
                        rule="card_engine_helper_duplication",
                        qualname=node.name,
                        message=(
                            f"`{node.name}` re-declares a card-engine primitive — "
                            "import it from `utils.card_render` (`dejavu_fonts`/"
                            "`load_font`, `CardCanvas.fit`, `mix`, `initials`/"
                            "`CardCanvas.initials_disc`) instead of a private copy "
                            "(the pre-#1396 triplication class), or allowlist a "
                            "genuinely engine-independent helper in "
                            "consistency_exceptions.yml"
                        ),
                    ),
                )

    return findings


# ---------------------------------------------------------------------------
# Rule 6 — settle-once adoption (money-safety)
# ---------------------------------------------------------------------------

# The settle sinks.  ``settle_pvp``/``refund_pvp``/``payout_tournament`` are
# the escrow-moving wager helpers (``services/game_wager_workflow.py``) — a
# call *moves the pot* (payout / refund / tournament pot + FREE reward), so
# running one twice double-settles; ``payout_tournament``'s free-reward leg has
# no escrow rows to consume, making the caller-side claim its ONLY guard.
# ``update_leaderboard`` is the deathmatch W/L recorder — the non-wager settle
# the 2026-07-06 Gate-V Arm-D live run double-wrote through the unguarded
# ``_DuelView`` (FINAL-REVIEW §6.3 #1); its lone definition wraps
# ``db.update_deathmatch`` behind a single method, so call sites are precise.
# The fuzzier "posts a terminal result" leg the idea also sketches
# (``settle-once-architecture-guard-2026-06-24.md``) is deliberately NOT
# implemented here — static "settles via a result message reachable from
# ``on_timeout``" detection is false-positive-prone, and a warn-clean rule must
# stay precise (the idea's own "be conservative, warn-first" caution).
_WAGER_SETTLE_CALLS = frozenset(
    {"settle_pvp", "refund_pvp", "payout_tournament", "update_leaderboard"}
)

# The settle-once guard primitive (``utils/terminal_guard.py``).
_SETTLE_ONCE_MIXIN = "SettleOnceMixin"
_SETTLE_ONCE_CLAIM = "claim_settlement"


def _calls_name_within(node: ast.AST, names: frozenset[str]) -> bool:
    """True if any ``Call`` under *node* targets a name/attr in *names*.

    Matches both a bare call (``settle_pvp(...)``) and an attribute call
    (``game_wager_workflow.settle_pvp(...)`` / ``state.claim_settlement()``) by
    its trailing name — the same shape ``_call_name`` / ``_call_attr`` read.
    """
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call) and (
            _call_name(sub) in names or _call_attr(sub) in names
        ):
            return True
    return False


def _wager_settle_sites_with_scope(
    tree: ast.Module,
) -> list[tuple[ast.Call, ast.ClassDef | None, ast.AST]]:
    """Yield each wager-settle call with its enclosing class + function nodes.

    Walks with class/function scope tracked (the ``_front_truncations_with_scope``
    pattern).  Each result is ``(call, enclosing_class_or_None, enclosing_func)``
    where ``enclosing_func`` is the innermost ``def``/``async def`` containing the
    call (or the module node when a settle call somehow sits at module top level —
    that has no ``claim_settlement`` guard scope and is flagged, which is correct).
    """
    results: list[tuple[ast.Call, ast.ClassDef | None, ast.AST]] = []

    def visit(
        node: ast.AST,
        cls: ast.ClassDef | None,
        func: ast.AST,
    ) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, child, func)
                continue
            if isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef)):
                visit(child, cls, child)
                continue
            if isinstance(child, ast.Call) and _call_attr(child) in _WAGER_SETTLE_CALLS:
                results.append((child, cls, func))
            visit(child, cls, func)

    visit(tree, None, tree)
    return results


def _settle_site_is_guarded(
    enclosing_class: ast.ClassDef | None,
    enclosing_func: ast.AST,
) -> bool:
    """True if a wager-settle site adopts the settle-once guard.

    Guarded when **either**:

    - the enclosing class mixes in ``SettleOnceMixin`` (the RPS PvP / deathmatch
      bot-duel view shape), **or**
    - ``claim_settlement()`` is called anywhere in the enclosing class body (the
      claim may live in a sibling method — e.g. RPS claims in ``_resolve`` and
      settles in another method), **or**
    - ``claim_settlement()`` is called anywhere in the enclosing function (the
      blackjack module-level ``_settle(state)`` shape — ``state.claim_settlement()``
      before the ``settle_pvp`` call, no enclosing class).
    """
    if enclosing_class is not None:
        if _SETTLE_ONCE_MIXIN in _class_bases(enclosing_class):
            return True
        if _calls_name_within(enclosing_class, frozenset({_SETTLE_ONCE_CLAIM})):
            return True
    return _calls_name_within(enclosing_func, frozenset({_SETTLE_ONCE_CLAIM}))


def rule_settle_once_adoption(
    files: list[Path],
    exceptions: dict,
    roots: tuple[str, ...] = ("views/", "services/", "cogs/"),
) -> list[Finding]:
    """Flag a wager-settle site that does not adopt the settle-once guard.

    A call to ``game_wager_workflow.settle_pvp`` / ``refund_pvp`` pays out or
    refunds the escrowed pot.  When that settlement path is reachable from more
    than one trigger (a finishing button *and* ``on_timeout``, or two players'
    finish callbacks) without one atomic claim, a racy second entry double-settles
    — a redundant payout and a duplicate result post (BUG-0013 + the three more
    sites the 2026-06-24 run found by hand).  ``utils/terminal_guard.SettleOnceMixin``
    closes that with one ``claim_settlement()`` per terminal transition.

    This makes the by-hand review mechanical: every wager-settle site must adopt
    the guard — its enclosing class mixes in ``SettleOnceMixin`` / calls
    ``claim_settlement()``, or its enclosing function calls ``claim_settlement()``.
    Universal adoption is the safe money-safety stance: a genuinely single-trigger
    settle taking the claim is harmless (it always wins the first claim), so the
    rule never asks for a wrong change.

    Warn-only (Q-0105 — the mixin is young; graduate to ``error`` once it stays
    clean across a few sessions).  Runs clean today (all callers adopt).  Scopes
    ``views/`` + ``services/`` + ``cogs/`` — the 2026-07-07 widening: the
    deathmatch human-duel view lives in ``cogs/`` and its unguarded W/L write
    was live-confirmed by Gate-V Arm D, so the cog layer is in scope, and the
    tournament payout / deathmatch leaderboard sinks joined the sink set.
    ``game_wager_workflow`` itself only *defines* the wager sinks (never calls
    them), and ``Deathmatch.update_leaderboard`` — the single-trigger wrapper
    whose body calls ``db.update_deathmatch`` — is itself a definition, not a
    matched call.  Allowlist a verified single-trigger exception in
    ``consistency_exceptions.yml``.
    """
    cfg = exceptions.get("settle_once_adoption", {})
    findings: list[Finding] = []

    for filepath, rel, tree in _iter_parsed(files, roots):
        for call, enclosing_class, enclosing_func in _wager_settle_sites_with_scope(
            tree,
        ):
            if _settle_site_is_guarded(enclosing_class, enclosing_func):
                continue
            scope_parts = [
                p.name
                for p in (enclosing_class, enclosing_func)
                if isinstance(p, (ast.ClassDef, ast.AsyncFunctionDef, ast.FunctionDef))
            ]
            qualname = ".".join(scope_parts)
            if _is_allowlisted(rel, qualname, cfg):
                continue
            findings.append(
                Finding(
                    file=filepath,
                    line=call.lineno,
                    rule="settle_once_adoption",
                    qualname=qualname,
                    message=(
                        f"`{_call_attr(call)}(...)` pays out / refunds the escrow pot "
                        f"in `{qualname}` but its path takes no settle-once claim — a "
                        "second trigger (a finishing button + `on_timeout`, or two "
                        "players' callbacks) double-settles. Mix in "
                        "`utils.terminal_guard.SettleOnceMixin` and take "
                        "`claim_settlement()` at the top of the settling path (before "
                        "any `await`), or allowlist a verified single-trigger site in "
                        "consistency_exceptions.yml"
                    ),
                ),
            )

    return findings


# ---------------------------------------------------------------------------
# Rule registry — add a (name, fn) entry per future rule
# ---------------------------------------------------------------------------


@dataclass
class Rule:
    name: str
    fn: object
    description: str = field(default="")
    # The severity the rule's findings carry.  Every rule starts ``"warning"``
    # (warn-first, Q-0105) and graduates to ``"error"`` — at which point a finding
    # fails ``--mode strict`` — only once it has run clean across a few sessions.
    severity: str = "warning"
    # The *specific* thing blocking graduation to ``error``, if any (e.g. a plan
    # that must ship to clear a rule's remaining findings).  Empty means the only
    # gate left is the "stay clean a couple more sessions" soak — the
    # ``--graduation`` report turns "why is this still warn-only?" into one hop
    # (the per-rule graduation-blocker tracker, the #1060 session idea).
    graduation_blocker: str = field(default="")
    # The ``DISBOT_ROOT``-relative path prefixes the rule scans.  Default is
    # ``views/`` (where panels live); rules whose pattern also occurs in the cog
    # layer (inline ``discord.ui.View`` subclasses + select builders) widen this
    # to ``("views/", "cogs/")`` — BUG-0017's cog-layer ``options[:25]`` is why.
    roots: tuple[str, ...] = ("views/",)


RULES: list[Rule] = [
    # edit_in_place GRADUATED 2026-06-23 (ultracode consolidation fleet, PR #1375):
    # U1 (#1376) migrated ALL 17 views/ai/ findings to true in-place navigation;
    # U2 (#1377) converted the roles Create flow in place, and the remaining roles
    # sub-flow-picker / report-toast cases were source-verified as genuine and
    # allowlisted (not muted); U3b allowlisted the 3 casino/cleanup cases. 0 findings
    # on a clean tree -> severity flipped "warning"->"error" (a finding now fails
    # --mode strict, wired into code-quality.yml + check_quality.py). Reverting a
    # graduation = flip severity back to "warning" (disposable per the Q-0105 header).
    Rule(
        "edit_in_place",
        rule_edit_in_place,
        "panel callbacks that reply with a standalone ephemeral instead of editing in place",
        severity="error",
    ),
    # The three rules below GRADUATED 2026-06-19 (#1094): they ran clean (0 findings)
    # across #1056→#1062 and the `--graduation` tracker confirmed each ELIGIBLE, so
    # their `severity` is flipped `"warning"`→`"error"`. A finding now fails
    # `--mode strict` (wired into code-quality.yml + check_quality.py). Reverting a
    # graduation = flip the `severity` back to `"warning"` (the rule is disposable per
    # the Q-0105 header if it ever proves noisy).
    Rule(
        "back_button",
        rule_back_button,
        "HubView navigation panels with child controls but no back/nav affordance",
        severity="error",
    ),
    # Rules 3-4 also scan ``cogs/`` (cogs define inline view classes + select
    # builders): BUG-0017 was a cog-layer ``options[:25]`` that slipped past the
    # once-``views/``-only linter — the routed follow-up that widened the scope.
    Rule(
        "panel_base_class",
        rule_panel_base_class,
        "views extending discord.ui.View directly outside the game-state allowlist",
        severity="error",
        roots=("views/", "cogs/"),
    ),
    Rule(
        "select_option_truncation",
        rule_select_option_truncation,
        "select-building views that front-truncate a collection instead of paginating",
        severity="error",
        roots=("views/", "cogs/"),
    ),
    # Rule 5 scans ``utils/`` (where the image renderers live, not views/cogs).
    # Warn-first (Q-0105): added 2026-06-24 alongside the H2 card-engine migration
    # (PR #1396) that removed the third private palette + ``_fit`` copy — this rule
    # institutionalizes that dedup so a renderer can't re-grow the triplication.
    # It runs clean on the post-#1396 tree (0 findings); graduate to ``error``
    # once it has stayed quiet across a few sessions (the edit_in_place pattern).
    Rule(
        "card_engine_helper_duplication",
        rule_card_engine_helper_duplication,
        "image renderers re-declaring an engine helper (_fonts/_fit/_mix/_initials)",
        severity="warning",
        roots=("utils/",),
    ),
    # Rule 6 scans ``views/`` + ``services/`` (the wager-settle callers + state
    # objects live in both). Warn-first (Q-0105): added 2026-06-25, promoting the
    # ``settle-once-architecture-guard-2026-06-24.md`` idea — it mechanizes the
    # by-hand double-settlement review (BUG-0013 + the three sites the #1444/#1445
    # run found) for a money-safety class. The target primitive
    # (``SettleOnceMixin``) is young, so this stays warn-only; it runs clean on the
    # current tree (both wager-settle callers adopt the guard). Graduate to ``error``
    # once it has stayed quiet across a few sessions (the edit_in_place pattern).
    Rule(
        "settle_once_adoption",
        rule_settle_once_adoption,
        "wager-settle sites (settle_pvp/refund_pvp) not adopting the settle-once guard",
        severity="warning",
        roots=("views/", "services/"),
    ),
]


# ---------------------------------------------------------------------------
# File collection + entry point
# ---------------------------------------------------------------------------


def _all_files() -> list[Path]:
    """Every ``.py`` under the union of all rules' scan roots.

    Each rule re-filters this list to its own :attr:`Rule.roots` via
    :func:`_iter_parsed`, so collecting the union here just guarantees a rule's
    files are present when it runs the full-tree scan.
    """
    roots = {root for rule in RULES for root in rule.roots}
    files: list[Path] = []
    for root in sorted(roots):
        files += (DISBOT_ROOT / root.rstrip("/")).rglob("*.py")
    return sorted(set(files))


def _counts_by_rule(findings: list[Finding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.rule] = counts.get(f.rule, 0) + 1
    return counts


def run_checks(files: list[Path], exceptions: dict) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        rule_findings: list[Finding] = rule.fn(files, exceptions, rule.roots)  # type: ignore[operator]
        # Stamp each finding with its rule's current severity, so graduating a
        # rule to ``error`` (flip ``Rule.severity``) actually makes ``--mode
        # strict`` fail on it — no per-rule wiring needed.
        for f in rule_findings:
            f.severity = rule.severity
        findings += rule_findings
    return findings


# ---------------------------------------------------------------------------
# Graduation tracker — the self-explaining "why is this still warn-only?" view
# ---------------------------------------------------------------------------


def graduation_status(rule: Rule, count: int) -> tuple[str, str]:
    """The graduation state of *rule* given its current finding *count*.

    Returns ``(state, detail)`` where ``state`` is one of ``GRADUATED`` /
    ``BLOCKED`` / ``NOT READY`` / ``ELIGIBLE``.  This makes the graduation queue
    self-documenting (the #1060 session idea): a later session reads one line to
    know whether a warn-only rule can flip to ``error`` and, if not, exactly what
    blocks it.
    """
    if rule.severity == "error":
        return "GRADUATED", "enforced — a finding fails `--mode strict`"
    if rule.graduation_blocker:
        return "BLOCKED", rule.graduation_blocker
    if count > 0:
        return "NOT READY", f"{count} warn-only finding(s) — triage to 0 first"
    return (
        "ELIGIBLE",
        "0 findings on a clean tree — flip `Rule.severity` to 'error' after it "
        "stays clean a couple more sessions, then wire into code-quality.yml",
    )


def print_graduation_report(findings: list[Finding]) -> None:
    """Print the per-rule graduation tracker (counts + state + blocker)."""
    counts = _counts_by_rule(findings)
    print("\ncheck_consistency — graduation tracker\n")
    for rule in RULES:
        count = counts.get(rule.name, 0)
        state, detail = graduation_status(rule, count)
        print(f"  {rule.name}  [{rule.severity}]  findings={count}")
        print(f"      → {state}: {detail}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="SuperBot UX consistency linter")
    parser.add_argument(
        "--mode",
        choices=["report", "strict"],
        default="report",
        help="report: always exit 0; strict: exit 1 on a GRADUATED rule's finding",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Check a single file (relative or absolute)",
    )
    parser.add_argument(
        "--graduation",
        action="store_true",
        help="Print the per-rule graduation tracker (count + state + blocker) and exit 0",
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Positional file list (used by pre-commit pass_filenames)",
    )
    args = parser.parse_args()

    if args.graduation:
        # Graduation is a whole-tree decision: a filtered subset (--file /
        # positional) would report findings=0 / ELIGIBLE for a rule that is clean
        # only in that subset while the rest of views/ still has open findings —
        # falsely licensing a flip to error.  Always scan the full tree here,
        # ignoring any file filter.
        files = _all_files()
    elif args.files:
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

    if args.graduation:
        print_graduation_report(findings)
        return 0

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
