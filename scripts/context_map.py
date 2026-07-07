#!/usr/bin/env python3
"""Context map for a SuperBot source file.

Given a path under ``disbot/``, print the connected context an agent needs
*before* editing it: the file's role and layer, its direct imports (module-level
**and** lazy function-body imports, labelled), what imports it, transitive blast
radius, ownership/authority, related docs and tests, risk flags, and a
recommended read/verify set.

This complements CodeGraph, which cannot resolve this repo's file/module edges
(``file_deps`` / ``impact_analysis`` return zero here). Importers and blast
radius are computed with **Grimp** (an import-graph library) when it is
installed, and fall back to a built-in AST scan so the tool still works without
it — Grimp lives in ``requirements-dev.txt``, not the bot runtime.

Usage:
    python scripts/context_map.py disbot/services/moderation_service.py
    python scripts/context_map.py disbot/cogs/moderation_cog.py --max-importers 30
"""

from __future__ import annotations

import argparse
import sys
from collections import deque
from pathlib import Path

import yaml

# Reuse the trusted AST import visitor + path/layer helpers from the architecture
# checker (same scripts/ dir) so the import extraction stays one source of truth.
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import check_architecture as _arch  # noqa: E402
from _review_units import classify_path as _classify_review_unit  # noqa: E402

REPO_ROOT: Path = _arch.REPO_ROOT
DISBOT_ROOT: Path = _arch.DISBOT_ROOT
OVERRIDES_PATH = REPO_ROOT / "docs" / "context-map-overrides.yml"
TESTS_ROOT = REPO_ROOT / "tests"

# Top-level packages as the code imports them (disbot/ is on sys.path at runtime,
# so a cog says ``from services.x import y``, not ``from disbot.services...``).
LAYER_PACKAGES = ("cogs", "core", "governance", "services", "utils", "views")

# Standalone top-level modules that are not inside a layer package.
# ``control_api`` extends the ``healthserver`` HTTP surface and (later) wires the
# audited service seams to the dashboard, so it is composition-root infra like
# ``healthserver`` — it cannot live in a layer (it will import ``services``).
TOP_LEVEL_MODULES = {
    "bot1",
    "config",
    "control_api",
    "guild_lifecycle",
    "healthserver",
}

HIGH_FAN_IN = 15


# ---------------------------------------------------------------------------
# Path <-> module-name helpers
# ---------------------------------------------------------------------------


def module_name(path: Path) -> str | None:
    """Return the import name for a file under ``disbot/`` (or None)."""
    try:
        rel = path.resolve().relative_to(DISBOT_ROOT)
    except ValueError:
        return None
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else None


def module_to_relpath(mod: str) -> str:
    """Best-effort display path (``disbot/...py``) for an import name."""
    base = DISBOT_ROOT / Path(*mod.split("."))
    if (base / "__init__.py").exists():
        return f"disbot/{mod.replace('.', '/')}/__init__.py"
    return f"disbot/{mod.replace('.', '/')}.py"


# ---------------------------------------------------------------------------
# Forward imports (always from AST — keeps the module-level / lazy distinction)
# ---------------------------------------------------------------------------


def _is_internal(mod: str) -> bool:
    head = mod.split(".")[0]
    return head in LAYER_PACKAGES or head in TOP_LEVEL_MODULES


def forward_imports(path: Path) -> tuple[list[str], list[str]]:
    """Return (module_level, lazy) internal imports for ``path``."""
    try:
        tree = _arch.ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return [], []
    visitor = _arch._ImportVisitor()
    visitor.visit(tree)
    mod_level = sorted({m for _, m, _ in visitor.imports if _is_internal(m)})
    lazy = sorted({m for _, m, _ in visitor.lazy_imports if _is_internal(m)})
    return mod_level, lazy


# ---------------------------------------------------------------------------
# Reverse edges — Grimp when available, AST fallback otherwise
# ---------------------------------------------------------------------------


class _Reverse:
    """Importer / blast-radius lookups, backed by Grimp or an AST scan."""

    def __init__(self, engine: str, direct: dict[str, set[str]], graph: object) -> None:
        self.engine = engine
        self._direct = direct  # only populated for the AST backend
        self._graph = graph

    def _in_graph(self, mod: str) -> bool:
        # Contract alignment with the AST backend: a module the graph doesn't
        # know (top-level files like bot1/config — outside LAYER_PACKAGES) has
        # no edges, it is not an error. grimp raises ModuleNotPresent instead
        # (observed on grimp 3.15 via test_atlas), so guard before querying.
        return mod in self._graph.modules  # type: ignore[attr-defined]

    def importers(self, mod: str) -> list[str]:
        if self.engine == "grimp":
            if not self._in_graph(mod):
                return []
            return sorted(self._graph.find_modules_that_directly_import(mod))  # type: ignore[attr-defined]
        return sorted(self._direct.get(mod, set()))

    def downstream(self, mod: str) -> set[str]:
        if self.engine == "grimp":
            if not self._in_graph(mod):
                return set()
            return set(self._graph.find_downstream_modules(mod))  # type: ignore[attr-defined]
        seen: set[str] = set()
        queue: deque[str] = deque([mod])
        while queue:
            current = queue.popleft()
            for importer in self._direct.get(current, set()):
                if importer not in seen:
                    seen.add(importer)
                    queue.append(importer)
        return seen


def _build_grimp() -> object | None:
    try:
        import grimp
    except ImportError:
        return None
    if str(DISBOT_ROOT) not in sys.path:
        sys.path.insert(0, str(DISBOT_ROOT))
    try:
        return grimp.build_graph(*LAYER_PACKAGES)
    except Exception:  # noqa: BLE001 — degrade to the AST backend on any build error
        return None


def _build_ast_reverse() -> dict[str, set[str]]:
    """Map ``imported_module -> {importer_module, ...}`` over all of disbot/."""
    direct: dict[str, set[str]] = {}
    for py in DISBOT_ROOT.rglob("*.py"):
        importer = module_name(py)
        if importer is None:
            continue
        mod_level, lazy = forward_imports(py)
        for target in set(mod_level) | set(lazy):
            direct.setdefault(target, set()).add(importer)
    return direct


def build_reverse() -> _Reverse:
    graph = _build_grimp()
    if graph is not None:
        return _Reverse("grimp", {}, graph)
    return _Reverse("ast", _build_ast_reverse(), object())


# ---------------------------------------------------------------------------
# Ownership / docs / tests / risk
# ---------------------------------------------------------------------------


def ownership_facts(mod: str) -> list[str]:
    """Mutation-owner / DB-module facts for ``mod`` from mutation_owners.yaml."""
    data = _arch._load("mutation_owners.yaml")
    facts: list[str] = []
    for name, spec in (data.get("domains") or {}).items():
        desc = spec.get("description", "")
        if spec.get("owner_module") == mod:
            facts.append(
                f"Canonical mutation owner for domain '{name}' ({desc}). "
                "Writes for this domain must route here and emit an audit event.",
            )
        if spec.get("db_module") == mod:
            facts.append(f"Canonical DB module for domain '{name}' ({desc}).")
    return facts


def extension_role_facts(rel: str) -> list[str]:
    """Role / backing-subsystem for a ``disbot/cogs/...`` file, from the extension crosswalk.

    Degrades to ``[]`` for non-cog files or if the overlay/crosswalk is unavailable —
    this is disposable convenience tooling and must never break the map. (PR #958 data.)
    """
    parts = Path(rel).parts
    if len(parts) < 3 or parts[1] != "cogs":
        return []
    short = parts[2]
    if short.endswith(".py"):
        short = short[:-3]
    short = short.removesuffix("_cog")
    try:
        import extension_crosswalk as _xwalk

        rows, _ = _xwalk.build_rows()
    except Exception:  # noqa: BLE001 — never let optional tooling break context_map
        return []
    for row in rows:
        if row.extension == short:
            backs = f" → backs `{row.backs}`" if row.backs else ""
            reg = " (registered subsystem)" if row.registered else ""
            return [f"Extension role: `{row.role}`{backs}{reg} — `{short}` surface."]
    return []


def load_overrides() -> dict:
    if not OVERRIDES_PATH.exists():
        return {}
    with OVERRIDES_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def related_docs(
    rel: str,
    layer: str | None,
    overrides: dict,
) -> tuple[str | None, list[str]]:
    """Resolve (folio, [contract docs]) using the longest matching path prefix."""
    folio: str | None = None
    docs: list[str] = []
    best = -1
    for entry in overrides.get("overrides", []):
        prefix = entry.get("prefix", "")
        if rel.startswith(prefix) and len(prefix) > best:
            best = len(prefix)
            folio = entry.get("folio")
            docs = list(entry.get("docs", []))
    if not docs and layer:
        docs = list((overrides.get("layer_docs") or {}).get(layer, []))
    return folio, docs


def related_tests(path: Path) -> list[Path]:
    """Mirror-path test + any ``test_<stem>.py`` anywhere under tests/."""
    stem = path.stem
    found: list[Path] = []
    rel_parent = path.resolve().relative_to(DISBOT_ROOT).parent
    mirror = TESTS_ROOT / "unit" / rel_parent / f"test_{stem}.py"
    if mirror.exists():
        found.append(mirror)
    for hit in TESTS_ROOT.rglob(f"test_{stem}.py"):
        if hit not in found:
            found.append(hit)
    return found


def known_arch_debt(rel: str) -> list[str]:
    """Tracked layer-boundary / raw-write violations recorded for this file."""
    notes: list[str] = []
    layers = _arch._load("layers.yaml")
    for kv in layers.get("known_violations", []):
        if kv.get("file") == rel:
            notes.append(
                f"tracked layer-boundary debt: imports `{kv.get('import')}` "
                f"({kv.get('ticket', 'n/a')})",
            )
    mutation = _arch._load("mutation_owners.yaml")
    for kv in mutation.get("known_raw_write_violations", []):
        if kv.get("file") == rel:
            notes.append(f"tracked raw-write debt ({kv.get('ticket', 'n/a')})")
    return notes


def risk_flags(
    rel: str,
    layer: str | None,
    importer_count: int,
    lazy_count: int,
    owner_facts: list[str],
) -> list[str]:
    flags: list[str] = list(known_arch_debt(rel))
    if owner_facts:
        flags.append(
            "mutation seam — no direct DB writes from cogs/views; changes here "
            "affect every caller and must stay audited.",
        )
    if importer_count >= HIGH_FAN_IN:
        flags.append(
            f"high fan-in ({importer_count} importers) — verify all call sites; "
            "blast radius is real.",
        )
    if lazy_count:
        flags.append(
            f"{lazy_count} lazy/function-body import(s) — these call edges are "
            "invisible to CodeGraph; grep-verify before moving/renaming symbols.",
        )
    if not flags:
        flags.append("no tracked architecture debt for this file.")
    return flags


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def _bullet_list(items: list[str], empty: str = "_(none)_") -> str:
    return "\n".join(f"- {i}" for i in items) if items else empty


def render(path: Path, reverse: _Reverse, overrides: dict, max_importers: int) -> str:
    rel = str(path.resolve().relative_to(REPO_ROOT))
    mod = module_name(path)
    layer = _arch._file_layer(path)
    mod_level, lazy = forward_imports(path)
    importers = reverse.importers(mod) if mod else []
    downstream = reverse.downstream(mod) if mod else set()
    owner_facts = ownership_facts(mod) if mod else []
    folio, docs = related_docs(
        str(path.resolve().relative_to(DISBOT_ROOT)),
        layer,
        overrides,
    )
    tests = related_tests(path)
    flags = risk_flags(rel, layer, len(importers), len(lazy), owner_facts)

    layers_cfg = (_arch._load("layers.yaml").get("layers") or {}).get(layer or "", {})
    may_import = (
        ", ".join(layers_cfg.get("may_import", [])) or "(leaf — stdlib/discord)"
    )

    shown = importers[:max_importers]
    extra = len(importers) - len(shown)
    importer_lines = [f"`{m}` — `{module_to_relpath(m)}`" for m in shown]
    if extra > 0:
        importer_lines.append(f"…and {extra} more")

    read_set = []
    if folio:
        read_set.append(f"{folio} (area folio — start here)")
    read_set += docs
    for fact_mod in ("services.audit_events",) if owner_facts else ():
        read_set.append(f"disbot/{fact_mod.replace('.', '/')}.py (audit emission)")
    read_set += [f"{module_to_relpath(m)} (importer)" for m in importers[:5]]

    checks = [
        "python3.10 scripts/check_quality.py --full",
        "python3.10 scripts/check_architecture.py --mode strict",
    ]
    if tests:
        checks.append(
            "python3.10 -m pytest "
            + " ".join(str(t.relative_to(REPO_ROOT)) for t in tests[:3]),
        )
    if owner_facts:
        checks.append(
            "verify an audit event is emitted (services.audit_events) for new "
            "mutations, and that no cog/view writes the DB directly.",
        )

    engine_note = (
        "Grimp import graph"
        if reverse.engine == "grimp"
        else "AST fallback (install grimp for faster, complete import edges)"
    )

    return "\n".join(
        [
            f"# Context map for {rel}",
            "",
            f"_Module:_ `{mod}`  ·  _Layer:_ `{layer or 'n/a'}`  ·  "
            f"_Reverse edges via:_ {engine_note}",
            "",
            f"_Review unit (repo-review-map.md):_ **{_classify_review_unit(rel).label()}**",
            "",
            "## File role / authority",
            "",
            _bullet_list(
                (
                    owner_facts
                    or [
                        f"`{layer or 'n/a'}`-layer module (no canonical mutation domain).",
                    ]
                )
                + extension_role_facts(rel),
            ),
            f"- Layer may import: {may_import}",
            "",
            "## Direct imports (module-level)",
            "",
            _bullet_list([f"`{m}`" for m in mod_level]),
            "",
            "## Direct imports (lazy / function-body — CodeGraph-invisible)",
            "",
            _bullet_list([f"`{m}`" for m in lazy]),
            "",
            f"## Imported by ({len(importers)})",
            "",
            _bullet_list(importer_lines),
            "",
            "## Blast radius",
            "",
            f"- {len(downstream)} module(s) transitively depend on this file.",
            "",
            "## Related docs",
            "",
            _bullet_list(([folio] if folio else []) + docs),
            "",
            "## Relevant tests",
            "",
            _bullet_list([str(t.relative_to(REPO_ROOT)) for t in tests]),
            "",
            "## Risk flags",
            "",
            _bullet_list(flags),
            "",
            "## Recommended read set before editing",
            "",
            _bullet_list(read_set),
            "",
            "## Suggested checks after editing",
            "",
            _bullet_list(checks),
            "",
        ],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Context map for a SuperBot file.")
    parser.add_argument("path", type=Path, help="File under disbot/ to map.")
    parser.add_argument(
        "--max-importers",
        type=int,
        default=25,
        help="Cap importer lines printed (default 25).",
    )
    args = parser.parse_args(argv)

    path = (
        (REPO_ROOT / args.path).resolve() if not args.path.is_absolute() else args.path
    )
    if not path.exists():
        print(f"context_map: no such file: {args.path}")
        return 2
    if module_name(path) is None:
        print(f"context_map: {args.path} is not under disbot/ — nothing to map.")
        return 2

    reverse = build_reverse()
    overrides = load_overrides()
    print(render(path, reverse, overrides, args.max_importers))
    return 0


if __name__ == "__main__":
    sys.exit(main())
