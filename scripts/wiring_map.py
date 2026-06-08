#!/usr/bin/env python3.10
"""EventBus wiring map — the runtime edges CodeGraph *and* Grimp miss.

SuperBot decouples emitters from subscribers through a string-keyed
``EventBus`` (``core/events.py``).  An emitter calls
``bus.emit("audit.action_recorded", …)``; a subscriber registers
``bus.on("audit.action_recorded", handler)``.  The two sides share **no
import and no call edge** — so neither the import graph (Grimp /
``scripts/context_map.py``) nor the call graph (CodeGraph) connects them.
That is the documented gap in ``.claude/CLAUDE.md`` ("Some edges are
invisible to *both* tools").

This script closes it by resolving the wiring the way the codebase
actually writes it — AST-scanning ``bus.emit`` / ``bus.on`` callsites,
resolving the event name (an ``EVT_*`` module constant or a string
literal) the same way the runtime does, and **joining emitter↔subscriber
by event-name string**.  It is a deliberate sibling of
``scripts/context_map.py``: small, stdlib-only (no new dependency), built
on the repo's own conventions, and **honest about being a lower bound**
(dynamic event names, non-``bus`` receivers, and ``getattr`` dispatch are
not resolved and are reported as ``unresolved``).

Usage::

    python3.10 scripts/wiring_map.py                 # full map + orphans
    python3.10 scripts/wiring_map.py <file_or_dir>   # only this path's wiring
    python3.10 scripts/wiring_map.py --event xp.awarded
    python3.10 scripts/wiring_map.py --check         # exit 1 on orphans/drift

``--check`` gates (exit 1) on the one **high-confidence** problem and
prints the rest as advisories:

* **catalogue drift** (gate) — an emitted/subscribed event name absent
  from ``core/events_catalogue.KNOWN_EVENTS`` (the typo guard the
  catalogue exists for); resolved from a literal/constant, so no false
  positives.
* **dead subscriber** (advisory, never gates) — ``bus.on`` for an event
  nothing emits *in a form this tool can resolve*.  It is FP-prone: an
  event emitted only through a **parametrized forwarder** (e.g.
  governance's ``_emit_governance_event(event_name, …)``) looks
  unemitted.  Reported as a hint, not a failure.

Emitted-with-no-subscriber is never flagged — many SuperBot events are
intentionally advisory "for future consumers" (see
``core/events_catalogue.py``).

Full reference: ``docs/context-map-tooling.md`` (wiring-map section).
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
from pathlib import Path

# Receivers we treat as the EventBus.  ``from core.events import bus`` is the
# canonical form; ``as _event_bus`` is used in a couple of cycle-sensitive
# modules.  A ``self._bus`` / ``get_bus()`` style receiver is NOT matched and
# would surface as a missing edge — documented limitation, not a silent drop.
_BUS_NAMES: frozenset[str] = frozenset({"bus", "_event_bus", "event_bus", "_bus"})

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DISBOT = _REPO_ROOT / "disbot"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CallSite:
    """One ``bus.emit`` or ``bus.on`` callsite."""

    kind: str  # "emit" | "on"
    event: str | None  # resolved event name, or None when unresolvable
    handler: str | None  # subscriber handler name (``on`` only)
    path: str  # repo-relative path
    line: int
    raw_event: str  # how the event was written (e.g. "EVT_MOD_ACTION")


@dataclass
class EventWiring:
    """Emitters + subscribers joined for one event name."""

    event: str
    emitters: list[CallSite] = field(default_factory=list)
    subscribers: list[CallSite] = field(default_factory=list)
    catalogued: bool = False


@dataclass
class WiringMap:
    """The full resolved map plus the unresolved + drift tails."""

    events: dict[str, EventWiring]
    unresolved: list[CallSite]  # emit/on whose event arg could not be resolved
    known_events: frozenset[str]

    def sorted_events(self) -> list[EventWiring]:
        return [self.events[name] for name in sorted(self.events)]

    # -- orphan / drift queries (the --check signals) -----------------------

    def dead_subscribers(self) -> list[CallSite]:
        """``bus.on`` for an event no in-repo callsite emits."""
        out: list[CallSite] = []
        for w in self.events.values():
            if w.subscribers and not w.emitters:
                out.extend(w.subscribers)
        return sorted(out, key=lambda c: (c.path, c.line))

    def uncatalogued(self) -> list[str]:
        """Emitted/subscribed event names absent from KNOWN_EVENTS."""
        if not self.known_events:
            return []  # catalogue unreadable → don't cry wolf
        return sorted(e for e in self.events if e not in self.known_events)


# ---------------------------------------------------------------------------
# AST extraction (pure; operate on source text so they're unit-testable)
# ---------------------------------------------------------------------------


def extract_event_constants(source: str) -> dict[str, str]:
    """Return ``{CONST_NAME: "event.string"}`` for ``EVT_* = "…"`` assigns.

    Covers plain ``EVT_X = "a.b"`` and annotated ``EVT_X: str = "a.b"`` at
    module level — the only forms the codebase uses for event constants.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    out: dict[str, str] = {}
    for node in tree.body:  # module level only
        target_name: str | None = None
        value: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Name):
                target_name, value = tgt.id, node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_name, value = node.target.id, node.value
        if (
            target_name
            and target_name.startswith("EVT_")
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
        ):
            out[target_name] = value.value
    return out


def _resolve_event(arg: ast.expr, constants: dict[str, str]) -> tuple[str | None, str]:
    """Resolve an emit/on first arg to ``(event_name, raw_repr)``.

    A bare string literal resolves to itself; an ``EVT_*`` name (or
    ``module.EVT_*`` attribute) resolves through ``constants``; anything
    else is left unresolved (``None``) and reported, never guessed.
    """
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value, repr(arg.value)
    if isinstance(arg, ast.Name):
        return constants.get(arg.id), arg.id
    if isinstance(arg, ast.Attribute):
        return constants.get(arg.attr), arg.attr
    return None, type(arg).__name__


def _handler_name(arg: ast.expr) -> str:
    if isinstance(arg, ast.Name):
        return arg.id
    if isinstance(arg, ast.Attribute):
        return arg.attr
    if isinstance(arg, ast.Lambda):
        return "<lambda>"
    return f"<{type(arg).__name__}>"


def extract_callsites(
    source: str,
    path: str,
    constants: dict[str, str],
) -> list[CallSite]:
    """Return every ``bus.emit`` / ``bus.on`` callsite in ``source``."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    sites: list[CallSite] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        attr = node.func.attr
        if attr not in ("emit", "on"):
            continue
        recv = node.func.value
        if not (isinstance(recv, ast.Name) and recv.id in _BUS_NAMES):
            continue
        if not node.args:
            continue
        event, raw = _resolve_event(node.args[0], constants)
        handler = (
            _handler_name(node.args[1]) if attr == "on" and len(node.args) > 1 else None
        )
        sites.append(
            CallSite(
                kind=attr,
                event=event,
                handler=handler,
                path=path,
                line=node.lineno,
                raw_event=raw,
            ),
        )
    return sites


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def analyze_sources(sources: dict[str, str]) -> WiringMap:
    """Build a :class:`WiringMap` from ``{path: source}`` (the testable core).

    Two passes: collect ``EVT_*`` constants across **all** files first (an
    emitter may reference a constant defined in another module), then resolve
    callsites against that global map.
    """
    constants: dict[str, str] = {}
    for src in sources.values():
        for name, val in extract_event_constants(src).items():
            constants[name] = val

    emits: list[CallSite] = []
    subs: list[CallSite] = []
    unresolved: list[CallSite] = []
    for path, src in sources.items():
        for site in extract_callsites(src, path, constants):
            if site.event is None:
                unresolved.append(site)
            elif site.kind == "emit":
                emits.append(site)
            else:
                subs.append(site)

    known = _resolve_known_events(sources, constants)
    events: dict[str, EventWiring] = {}
    for site in emits + subs:
        event = site.event
        if event is None:  # emits/subs are pre-filtered; defensive narrowing
            continue
        w = events.setdefault(event, EventWiring(event=event))
        (w.emitters if site.kind == "emit" else w.subscribers).append(site)
    for name, w in events.items():
        w.catalogued = (not known) or (name in known)
    return WiringMap(events=events, unresolved=unresolved, known_events=known)


def _resolve_known_events(
    sources: dict[str, str],
    constants: dict[str, str],
) -> frozenset[str]:
    """Resolve ``core/events_catalogue.KNOWN_EVENTS`` to its string set.

    Elements are string literals or ``EVT_*`` names; the latter resolve via
    the same constant map.  Returns an empty set if the catalogue can't be
    found/parsed, which makes the catalogue-drift check fail safe (silent).
    """
    cat = next(
        (s for p, s in sources.items() if p.endswith("core/events_catalogue.py")),
        None,
    )
    if cat is None:
        return frozenset()
    try:
        tree = ast.parse(cat)
    except SyntaxError:
        return frozenset()
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(t, ast.Name) and t.id == "KNOWN_EVENTS" for t in node.targets
        ):
            continue
        # value is frozenset({...}) — dig out the set elements.
        for elt in ast.walk(node.value):
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                names.add(elt.value)
            elif isinstance(elt, ast.Name) and elt.id in constants:
                names.add(constants[elt.id])
    return frozenset(names)


def analyze_repo(paths: list[Path] | None = None) -> WiringMap:
    """Build the map from the live ``disbot/`` tree (CLI entry helper)."""
    files = _python_files(paths)
    sources: dict[str, str] = {}
    for f in files:
        try:
            sources[_rel(f)] = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
    # The catalogue + constant defs may live outside a scoped path; always
    # include enough of the tree to resolve names even when scoping output.
    if paths is not None:
        for f in _python_files(None):
            sources.setdefault(_rel(f), f.read_text(encoding="utf-8", errors="ignore"))
    return analyze_sources(sources)


def _python_files(paths: list[Path] | None) -> list[Path]:
    roots = paths or [_DISBOT]
    out: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            out.append(root)
        elif root.is_dir():
            out.extend(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)
    return out


def _rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(_REPO_ROOT))
    except ValueError:
        return str(p)


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def render_map(m: WiringMap, *, scope_paths: set[str] | None = None) -> str:
    """Render the wiring map as markdown.

    ``scope_paths`` (repo-relative) limits the event list to events touched
    by those files, for the per-file / per-dir invocation.
    """
    lines: list[str] = ["# EventBus wiring map", ""]
    lines.append(
        "_Runtime emit↔subscribe edges (string-keyed) — invisible to both "
        "CodeGraph (no call edge) and Grimp (no import edge). Lower bound: "
        "dynamic names / non-`bus` receivers show as unresolved._",
    )
    lines.append("")

    events = m.sorted_events()
    if scope_paths is not None:
        events = [
            w
            for w in events
            if any(c.path in scope_paths for c in (*w.emitters, *w.subscribers))
        ]

    lines.append(f"## Events ({len(events)})")
    for w in events:
        badge = "✓ catalogued" if w.catalogued else "⚠ NOT in KNOWN_EVENTS"
        lines.append(f"### `{w.event}`  ·  {badge}")
        if w.emitters:
            for c in sorted(w.emitters, key=lambda c: (c.path, c.line)):
                lines.append(f"- emit → `{c.path}:{c.line}`")
        else:
            lines.append("- emit → _(none in-repo — advisory/external?)_")
        if w.subscribers:
            for c in sorted(w.subscribers, key=lambda c: (c.path, c.line)):
                lines.append(f"- on   → `{c.path}:{c.line}` → `{c.handler}`")
        else:
            lines.append("- on   → _(no subscriber)_")
        lines.append("")

    dead = m.dead_subscribers()
    drift = m.uncatalogued()
    if dead or drift or m.unresolved:
        lines.append("## ⚠ Findings")
        for c in dead:
            lines.append(
                f"- _advisory: possible dead subscriber_ — `{c.event}` handled "
                f"at `{c.path}:{c.line}` (`{c.handler}`) with no resolvable "
                "emitter (could be a parametrized forwarder — grep to confirm)",
            )
        for e in drift:
            lines.append(f"- **catalogue drift** — `{e}` is not in KNOWN_EVENTS")
        for c in m.unresolved:
            lines.append(
                f"- _unresolved {c.kind}_ — `{c.path}:{c.line}` "
                f"(event arg: `{c.raw_event}`) — grep to confirm",
            )
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="EventBus emit↔subscribe wiring map (the both-tools-blind gap).",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Limit output to events touched by this file/dir (default: all disbot/).",
    )
    parser.add_argument("--event", help="Show wiring for one event name only.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 on a dead subscriber or catalogue drift (CI gate).",
    )
    args = parser.parse_args(argv)

    scope: set[str] | None = None
    if args.path:
        target = Path(args.path)
        m = analyze_repo([target])
        scope = {_rel(p) for p in _python_files([target])}
    else:
        m = analyze_repo()

    if args.check:
        # Advisories print but never fail the gate (FP-prone — see module
        # docstring); only catalogue drift, which is resolved from a
        # literal/constant, is a hard failure.
        for c in m.dead_subscribers():
            print(
                f"  · advisory: possible dead subscriber {c.event} @ "
                f"{c.path}:{c.line} ({c.handler}) — confirm vs parametrized "
                "emitters",
            )
        drift = m.uncatalogued()
        if drift:
            print("EventBus wiring check FAILED:")
            for e in drift:
                print(f"  ✗ catalogue drift: {e} not in KNOWN_EVENTS")
            return 1
        print("EventBus wiring check passed ✓")
        return 0

    if args.event:
        w = m.events.get(args.event)
        if w is None:
            print(f"No emit/subscribe callsites found for event {args.event!r}.")
            return 0
        single = WiringMap(
            events={args.event: w},
            unresolved=[],
            known_events=m.known_events,
        )
        print(render_map(single))
        return 0

    print(render_map(m, scope_paths=scope))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
