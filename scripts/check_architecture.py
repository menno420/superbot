#!/usr/bin/env python3
"""Architecture rule engine for SuperBot.

Checks:
  1. Layer boundary violations  (services importing views, etc.)
  2. Raw SQL usage outside utils/db/
  3. Settings key string literals  (should use settings_keys constants)
  4. Direct discord.ui.View inheritance  (should use BaseView unless exempt)

Usage:
    python scripts/check_architecture.py                    # report mode (exit 0)
    python scripts/check_architecture.py --mode strict      # exit 1 on errors
    python scripts/check_architecture.py --changed-only     # only files changed vs main
    python scripts/check_architecture.py --file disbot/x.py # single file
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DISBOT_ROOT = REPO_ROOT / "disbot"
RULES_DIR = REPO_ROOT / "architecture_rules"
PROJECT_LAYERS = frozenset({"utils", "core", "services", "governance", "views", "cogs"})


# ---------------------------------------------------------------------------
# Violation model
# ---------------------------------------------------------------------------


@dataclass
class Violation:
    file: Path
    line: int
    check: str
    message: str
    severity: str = "error"  # "error" | "warning"

    def display(self, root: Path) -> str:
        try:
            rel = self.file.relative_to(root)
        except ValueError:
            rel = self.file
        tag = "ERROR" if self.severity == "error" else " WARN"
        return f"  [{tag}] {rel}:{self.line}  ({self.check})  {self.message}"


# ---------------------------------------------------------------------------
# YAML loader
# ---------------------------------------------------------------------------


def _load(name: str) -> dict:
    p = RULES_DIR / name
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# Check 1 — Layer boundary violations
# ---------------------------------------------------------------------------


def _file_layer(filepath: Path) -> str | None:
    try:
        rel = filepath.relative_to(DISBOT_ROOT)
    except ValueError:
        return None
    return rel.parts[0] if rel.parts and rel.parts[0] in PROJECT_LAYERS else None


def _import_layer(module: str) -> str | None:
    first = module.split(".")[0]
    return first if first in PROJECT_LAYERS else None


class _ImportVisitor(ast.NodeVisitor):
    """Collect absolute imports, split into module-level vs lazy, tracking
    TYPE_CHECKING context.

    Module-level imports land in ``self.imports`` — they are the binding
    import-graph contract.  Lazy function-body imports (``from X import Y``
    inside a def / async def) land in ``self.lazy_imports``.  Lazy imports are
    a legitimate cycle-breaking pattern here, but they still create real
    cross-layer call edges the module-import graph misses (RC-1), so the
    boundary check can *report* them on request without treating them as hard
    errors.
    """

    def __init__(self) -> None:
        self._fn_depth = 0  # >0 means we're inside a function body
        self._in_tc = False  # inside `if TYPE_CHECKING:` block
        self.imports: list[tuple[int, str, bool]] = []  # lineno, module, is_tc
        self.lazy_imports: list[tuple[int, str, bool]] = []  # function-body imports

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._fn_depth += 1
        self.generic_visit(node)
        self._fn_depth -= 1

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_If(self, node: ast.If) -> None:
        test = node.test
        enters_tc = (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
            isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
        )
        prev = self._in_tc
        if enters_tc:
            self._in_tc = True
        self.generic_visit(node)
        self._in_tc = prev

    def visit_Import(self, node: ast.Import) -> None:
        bucket = self.lazy_imports if self._fn_depth > 0 else self.imports
        for alias in node.names:
            bucket.append((node.lineno, alias.name, self._in_tc))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if not node.module or node.level != 0:
            return
        bucket = self.lazy_imports if self._fn_depth > 0 else self.imports
        bucket.append((node.lineno, node.module, self._in_tc))


def _crosses_layer(
    module: str,
    file_layer: str,
    may_import: set[str],
    is_tc: bool,
    tc_exempt: bool,
) -> str | None:
    """Return the disallowed target layer for ``module``, or None if allowed."""
    import_layer = _import_layer(module)
    if import_layer is None or import_layer == file_layer:
        return None
    if import_layer in may_import:
        return None
    if is_tc and tc_exempt:
        return None
    return import_layer


def _is_known(rel_file: str, module: str, known: list[dict]) -> bool:
    """True if (rel_file, module) is allowlisted.

    An entry matches when ``module`` starts with its ``import`` prefix AND the
    file matches either ``file`` (exact) or ``file_prefix`` (directory prefix).
    ``file_prefix`` lets a documented layer-pair seam (e.g. the core → services
    lazy-resolution cycle-breaker) be allowlisted with one rationale entry
    instead of one per file.
    """
    for kv in known:
        if not module.startswith(kv.get("import", "")):
            continue
        exact = kv.get("file")
        prefix = kv.get("file_prefix")
        if exact is not None and rel_file == exact:
            return True
        if prefix is not None and rel_file.startswith(prefix):
            return True
    return False


def check_layer_boundaries(
    files: list[Path],
    rules: dict,
    *,
    report_lazy: bool = False,
) -> list[Violation]:
    layers_cfg = rules.get("layers", {})
    known: list[dict] = rules.get("known_violations", [])
    known_lazy: list[dict] = rules.get("known_lazy_violations", [])
    violations: list[Violation] = []

    for filepath in files:
        file_layer = _file_layer(filepath)
        if file_layer is None or file_layer not in layers_cfg:
            continue

        cfg = layers_cfg[file_layer]
        may_import: set[str] = set(cfg.get("may_import", []))
        tc_exempt: bool = cfg.get("type_checking_exempt", False)

        try:
            source = filepath.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(filepath))
        except SyntaxError:
            continue

        visitor = _ImportVisitor()
        visitor.visit(tree)

        rel_file = str(filepath.relative_to(DISBOT_ROOT))

        # Module-level imports — the binding contract (error unless allowlisted).
        for lineno, module, is_tc in visitor.imports:
            import_layer = _crosses_layer(
                module,
                file_layer,
                may_import,
                is_tc,
                tc_exempt,
            )
            if import_layer is None:
                continue
            is_known = _is_known(rel_file, module, known)
            violations.append(
                Violation(
                    file=filepath,
                    line=lineno,
                    check="layer_boundary",
                    message=(
                        f"{'[known] ' if is_known else ''}"
                        f"{file_layer} → {import_layer}: `{module}` is not allowed"
                    ),
                    severity="warning" if is_known else "error",
                ),
            )

        # Lazy (function-body) imports — RC-1 report mode.  Reported only when
        # requested, and ALWAYS as warnings: they break import cycles on purpose
        # but still form real cross-layer call edges worth surfacing.  Entries
        # in ``known_lazy_violations`` are the documented cycle-breakers; the
        # rest are new lazy edges to triage.
        if report_lazy:
            for lineno, module, is_tc in visitor.lazy_imports:
                import_layer = _crosses_layer(
                    module,
                    file_layer,
                    may_import,
                    is_tc,
                    tc_exempt,
                )
                if import_layer is None:
                    continue
                is_known = _is_known(rel_file, module, known_lazy)
                violations.append(
                    Violation(
                        file=filepath,
                        line=lineno,
                        check="lazy_layer_boundary",
                        message=(
                            f"{'[known] ' if is_known else ''}"
                            f"{file_layer} → {import_layer}: lazy `{module}` "
                            "(function-body cross-layer import)"
                        ),
                        severity="warning",
                    ),
                )

    return violations


# ---------------------------------------------------------------------------
# Check 2 — Raw SQL outside utils/db/
# ---------------------------------------------------------------------------

_RAW_SQL_RE = re.compile(
    r'\.execute\s*\(\s*(?:f?b?["\']|f?b?""")'
    r".*?(?:UPDATE|INSERT|DELETE|CREATE|DROP|ALTER)",
    re.IGNORECASE | re.DOTALL,
)
_POOL_EXECUTE_RE = re.compile(r"\bpool\s*\.\s*(?:execute|fetchone|fetchall|get)\s*\(")


def check_raw_sql(files: list[Path], rules: dict) -> list[Violation]:
    known_files = {kv["file"] for kv in rules.get("known_raw_write_violations", [])}
    violations: list[Violation] = []

    for filepath in files:
        rel = str(filepath.relative_to(DISBOT_ROOT))
        if rel.startswith("utils/db") or "test" in rel.lower():
            continue

        try:
            source = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lines = source.splitlines()
        for i, line in enumerate(lines, 1):
            if _RAW_SQL_RE.search(line) or _POOL_EXECUTE_RE.search(line):
                is_known = rel in known_files
                violations.append(
                    Violation(
                        file=filepath,
                        line=i,
                        check="raw_sql",
                        message=(
                            f"{'[known] ' if is_known else ''}"
                            "Raw SQL / pool primitive outside utils/db/ — use utils.db.* functions"
                        ),
                        severity="warning" if is_known else "error",
                    ),
                )

    return violations


# ---------------------------------------------------------------------------
# Check 3 — Settings key string literals
# ---------------------------------------------------------------------------

_SETTINGS_LITERAL_RE = re.compile(
    r'\bget_setting\s*\([^,)]+,\s*["\']([a-z][a-z0-9_]*)["\']',
)


def check_settings_key_literals(files: list[Path], _rules: dict) -> list[Violation]:
    violations: list[Violation] = []
    for filepath in files:
        rel = str(filepath.relative_to(DISBOT_ROOT))
        if "settings_keys" in rel or "test" in rel.lower():
            continue
        try:
            source = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(source.splitlines(), 1):
            m = _SETTINGS_LITERAL_RE.search(line)
            if m:
                violations.append(
                    Violation(
                        file=filepath,
                        line=i,
                        check="settings_key_literal",
                        message=(
                            f"Hardcoded settings key `{m.group(1)}` — "
                            "import the constant from utils.settings_keys"
                        ),
                        severity="warning",
                    ),
                )
    return violations


# ---------------------------------------------------------------------------
# Check 4 — BaseView inheritance
# ---------------------------------------------------------------------------


def _class_bases(node: ast.ClassDef) -> list[str]:
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


# The in-tree convention that documents a *justified* direct discord.ui.View
# extension (the rule text has always asked for "a comment"; #1871 standardized
# the wording): a comment block immediately above the class def containing this
# phrase. The checker recognizes it so a documented view stops warning — before
# this, documented views warned forever and the rule could never converge
# (friction→guard Q-0194, checker tier; shift-plan Q2, 2026-07-10).
_BASEVIEW_JUSTIFIED_MARKER = "discord.ui.View directly"
# How many lines above the class def to scan for the justifying comment.
_BASEVIEW_COMMENT_LOOKBACK = 6


def _has_baseview_justification(lines: list[str], class_lineno: int) -> bool:
    """True when a justifying comment sits directly above ``class_lineno``.

    Scans the ``_BASEVIEW_COMMENT_LOOKBACK`` lines immediately preceding the
    class definition for a ``#`` comment carrying the convention marker. Only
    comment lines count — the marker inside code/strings is ignored.
    """
    start = max(0, class_lineno - 1 - _BASEVIEW_COMMENT_LOOKBACK)
    for raw in lines[start : class_lineno - 1]:
        stripped = raw.strip()
        if stripped.startswith("#") and _BASEVIEW_JUSTIFIED_MARKER in stripped:
            return True
    return False


def check_baseview_inheritance(files: list[Path], rules: dict) -> list[Violation]:
    cfg = rules.get("base_view", {})
    exemption_prefixes = [
        e["pattern"].replace("disbot/", "") for e in cfg.get("exemptions", [])
    ]
    violations: list[Violation] = []

    for filepath in files:
        rel = str(filepath.relative_to(DISBOT_ROOT))
        if not (rel.startswith("views/") or rel.startswith("cogs/")):
            continue
        if "test" in rel.lower():
            continue
        if any(rel.startswith(prefix) for prefix in exemption_prefixes):
            continue

        try:
            source = filepath.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(filepath))
        except (SyntaxError, OSError):
            continue
        source_lines = source.splitlines()

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = _class_bases(node)
            if "discord.ui.View" in bases or "View" in bases:
                # Avoid flagging BaseView itself
                if node.name in ("BaseView", "HubView", "PersistentView"):
                    continue
                # A documented direct extension is the rule's sanctioned path:
                # a justifying comment right above the class silences the warn.
                if _has_baseview_justification(source_lines, node.lineno):
                    continue
                violations.append(
                    Violation(
                        file=filepath,
                        line=node.lineno,
                        check="baseview_inheritance",
                        message=(
                            f"`{node.name}` extends discord.ui.View directly — "
                            "use BaseView / HubView / PersistentView unless "
                            "specialized game or lifecycle ownership is required "
                            "(document the reason in a `# Extends "
                            "discord.ui.View directly (not BaseView): ...` "
                            "comment right above the class to silence this)"
                        ),
                        severity="warning",
                    ),
                )

    return violations


# ---------------------------------------------------------------------------
# No-dead-end terminal views (friction->guard, Q-0194)
# ---------------------------------------------------------------------------

_VIEW_BASES = {"discord.ui.View", "View", "BaseView", "HubView", "PersistentView"}
# Message-producing calls — rendering a terminal message to the user.
_MSG_CALLS = {"edit", "send", "edit_message", "safe_edit", "respond", "send_message"}


def _call_name(call: ast.Call) -> str | None:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _analyze_terminal_handler(
    fn: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[bool, bool, bool]:
    """Return (stops, renders_message, swaps_or_delegates) for one method body.

    - stops: calls ``self.stop()`` (marks it a terminal handler)
    - renders_message: awaits/calls a message-producing call (edit/send/...)
    - swaps_or_delegates: constructs a ``*View`` (a swap) OR awaits a non-message
      coroutine (delegation that may render the swap elsewhere, e.g. ``_start_pvp``)
    """
    stops = renders = swaps = False
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if (
                name == "stop"
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"
            ):
                stops = True
            if name and name.endswith("View") and name != "super":
                swaps = True  # constructs a (result) view -> a swap
        if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
            name = _call_name(node.value)
            if name in _MSG_CALLS:
                renders = True
            elif name and name.endswith("View"):
                swaps = True
            elif name not in (None, "stop"):
                swaps = True  # delegates to another coroutine
    return stops, renders, swaps


def check_no_dead_end_terminal_views(files: list[Path], rules: dict) -> list[Violation]:
    cfg = rules.get("no_dead_end", {})
    if not cfg:
        return []
    game_dirs = tuple(cfg.get("game_dirs", []))
    exemptions = {
        (e["view"], e["method"]) for e in cfg.get("exemptions", []) if "method" in e
    }
    severity = cfg.get("severity", "warning")
    violations: list[Violation] = []

    for filepath in files:
        rel = str(filepath.relative_to(DISBOT_ROOT))
        if not rel.startswith(game_dirs):
            continue
        if "test" in rel.lower():
            continue
        try:
            tree = ast.parse(
                filepath.read_text(encoding="utf-8", errors="replace"),
                filename=str(filepath),
            )
        except (SyntaxError, OSError):
            continue

        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef):
                continue
            if not (set(_class_bases(cls)) & _VIEW_BASES):
                continue
            for fn in cls.body:
                if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if (cls.name, fn.name) in exemptions:
                    continue
                stops, renders, swaps = _analyze_terminal_handler(fn)
                if stops and renders and not swaps:
                    violations.append(
                        Violation(
                            file=filepath,
                            line=fn.lineno,
                            check="no_dead_end",
                            message=(
                                f"`{cls.name}.{fn.name}` is a terminal handler "
                                "(calls self.stop()) that renders a message but "
                                "does not swap to a nav-carrying view — a finished "
                                "game/duel must never be a dead-end (Q-0194). Swap to "
                                "a result view with standard nav, or allowlist it in "
                                "architecture_rules/canonical_helpers.yaml (no_dead_end) "
                                "if it is genuinely terminal (e.g. a declined invite)."
                            ),
                            severity=severity,
                        ),
                    )

    return violations


# ---------------------------------------------------------------------------
# File collection
# ---------------------------------------------------------------------------


def _all_files() -> list[Path]:
    return sorted(DISBOT_ROOT.rglob("*.py"))


def _changed_files() -> list[Path]:
    for cmd in (
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        ["git", "diff", "--name-only", "HEAD"],
    ):
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        if result.returncode == 0 and result.stdout.strip():
            break
    files = []
    for line in result.stdout.splitlines():
        p = (REPO_ROOT / line.strip()).resolve()
        if p.suffix == ".py" and p.exists():
            try:
                p.relative_to(DISBOT_ROOT)
                files.append(p)
            except ValueError:
                pass
    return files


# ---------------------------------------------------------------------------
# Summary (RC-1 companion — architecture-warning summary)
# ---------------------------------------------------------------------------


def _counts_by_check(violations: list[Violation]) -> dict[str, int]:
    """Count violations grouped by check name (for the output summary)."""
    counts: dict[str, int] = {}
    for v in violations:
        counts[v.check] = counts.get(v.check, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="SuperBot architecture checker")
    parser.add_argument(
        "--mode",
        choices=["report", "strict"],
        default="report",
        help="report: always exit 0; strict: exit 1 if any errors",
    )
    parser.add_argument(
        "--changed-only",
        action="store_true",
        help="Only check files changed vs origin/main",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Check a single file (relative or absolute)",
    )
    parser.add_argument(
        "--report-lazy-imports",
        action="store_true",
        help=(
            "Also report function-body (lazy) cross-layer imports as warnings "
            "(RC-1). Off by default; the count is high by design."
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Positional file list (used by pre-commit pass_filenames)",
    )
    args = parser.parse_args()

    layers_rules = _load("layers.yaml")
    mutation_rules = _load("mutation_owners.yaml")
    helpers_rules = _load("canonical_helpers.yaml")

    if args.files:
        files = [
            (REPO_ROOT / f).resolve()
            for f in args.files
            if (REPO_ROOT / f).resolve().suffix == ".py"
        ]
    elif args.file:
        files = [(REPO_ROOT / args.file).resolve()]
    elif args.changed_only:
        files = _changed_files()
    else:
        files = _all_files()

    if not files:
        print("check_architecture: no files to check")
        return 0

    all_violations: list[Violation] = []
    all_violations += check_layer_boundaries(
        files,
        layers_rules,
        report_lazy=args.report_lazy_imports,
    )
    all_violations += check_raw_sql(files, mutation_rules)
    all_violations += check_settings_key_literals(files, helpers_rules)
    all_violations += check_baseview_inheritance(files, helpers_rules)
    all_violations += check_no_dead_end_terminal_views(files, helpers_rules)

    errors = [v for v in all_violations if v.severity == "error"]
    warnings = [v for v in all_violations if v.severity == "warning"]

    if not all_violations:
        print("check_architecture: all checks passed ✓")
        return 0

    label = f"{len(errors)} error(s)  {len(warnings)} warning(s)"
    print(f"\ncheck_architecture — {label}\n")

    # Per-check breakdown so operators can see at a glance which rule is
    # accumulating findings (RC-1 companion — architecture-warning summary).
    counts = _counts_by_check(all_violations)
    print("  by check: " + ", ".join(f"{k}={counts[k]}" for k in sorted(counts)))
    print()

    if errors:
        print("ERRORS — must fix before merge:")
        for v in sorted(errors, key=lambda x: (str(x.file), x.line)):
            print(v.display(REPO_ROOT))

    if warnings:
        print("\nWARNINGS — tracked, fix in follow-up PR:")
        for v in sorted(warnings, key=lambda x: (str(x.file), x.line)):
            print(v.display(REPO_ROOT))

    print()
    if args.mode == "strict" and errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
