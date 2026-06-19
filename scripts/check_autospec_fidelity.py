#!/usr/bin/env python3.10
"""AST guard: flag signature-blind mocks that replace ``disbot.*`` callables (stdlib only).

WHY (idea: ``docs/ideas/autospec-mock-fidelity-guard-2026-06-16.md``, 2026-06-19):
the BTD6 race-event drill-down crashed on **every** production click because a test
replaced a real DB facade with a *bare* mock::

    monkeypatch.setattr(btd6_db, "search_facts", AsyncMock(return_value=[...]))

A bare ``Mock``/``MagicMock``/``AsyncMock`` accepts *any* args and *any* kwargs, so the
call-site typo ``search_facts(entity_key=…)`` (no such parameter) passed the test yet
raised ``TypeError`` on the first real call. The mock was **more permissive than the
real function** — exactly how a signature mismatch slips past CI. This guard scans
``tests/`` for that shape and steers the author toward a signature-faithful double
(``create_autospec(real_fn)`` / ``AsyncMock(spec=real_fn)`` / ``patch.object(..., autospec=True)``).

What it flags (AST, so quoting/formatting never matters): a ``monkeypatch.setattr`` or
``patch.object`` call whose *replacement value* is a directly-constructed
``Mock``/``MagicMock``/``AsyncMock``/``NonCallableMock`` **without** a ``spec=`` /
``spec_set=`` / ``autospec=`` / ``wraps=`` argument, when the target object the attribute
is set on is a project (``disbot.*``) module/facade. Third-party targets and already-spec'd
mocks are never flagged.

Scope notes / deliberate non-flags (kept narrow to stay quiet — a noisy guard trains
people to ignore it, the Q-0120 / ``dead-unresolved`` discipline):

* Only ``monkeypatch.setattr`` and ``patch.object`` call sites are inspected — the two
  shapes that swap a *named attribute* on a real object. A free ``AsyncMock()`` passed as
  a plain argument is *not* a facade replacement and is not flagged.
* The replacement must be a *direct* ``Mock(...)`` construction at the call site. A mock
  bound to a variable first, or built by a helper, is out of scope (the cheap-AST limit).
* A ``patch.object`` used as a context manager / decorator with ``autospec=True`` (or any
  ``spec`` / ``wraps``) is faithful and not flagged.
* The target heuristic resolves the object name (``btd6_db`` in the example) to an
  imported **project** module via the file's import table; an unresolved / third-party
  target is **not** flagged (no false positives on ``discord``/stdlib mocks). The bot's
  package root ``disbot/`` is on ``sys.path`` in the test env (see ``conftest.py``), so
  project modules import as ``utils.*`` / ``cogs.*`` / ``services.*`` / ``views.*`` /
  ``core.*`` / ``governance.*`` — those bare roots (plus the rare fully-qualified
  ``disbot.*``) are the project surface :data:`_PROJECT_ROOTS` matches.

RELIABILITY (Q-0105): **unverified** — confirm this guard's findings against ground truth
a few times across sessions before trusting its output; it is **warn-only by default**
(``--mode report`` exits 0 even with findings) so it lands without forcing edits to
existing tests. **Disposable: delete this script (and its test) if it proves unreliable or
noisy over multiple sessions** rather than working around it. It is a convenience guard,
not load-bearing runtime code.

Usage::

    python3.10 scripts/check_autospec_fidelity.py                 # report mode (exit 0)
    python3.10 scripts/check_autospec_fidelity.py --mode strict   # exit 1 on any finding
    python3.10 scripts/check_autospec_fidelity.py --file tests/unit/cogs/test_btd6_cog.py
    python3.10 scripts/check_autospec_fidelity.py --json          # machine-readable findings
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCAN_ROOT = REPO_ROOT / "tests"

# The bare mock classes that accept any signature. A construction of one of these
# *without* a faithfulness kwarg is the permissive double we steer away from.
_BARE_MOCK_NAMES = frozenset(
    {"Mock", "MagicMock", "AsyncMock", "NonCallableMock", "NonCallableMagicMock"},
)

# Kwargs that make a mock signature-faithful (or bind it to a real object), so the
# construction is *not* flagged. ``spec``/``spec_set`` enforce the attribute surface;
# ``autospec`` enforces the call signature; ``wraps`` delegates to the real object.
_FAITHFUL_KWARGS = frozenset({"spec", "spec_set", "autospec", "wraps"})

# The two setattr-shaped call sites that swap a named attribute on a real object.
_SETATTR_FUNCS = frozenset({"setattr"})  # matched as ``<x>.setattr`` (monkeypatch)
# ``patch.object`` is matched structurally below.

# A target object resolves to project code when its import root is one of these. The
# bot package ``disbot/`` is added to ``sys.path`` by ``conftest.py``, so its
# subpackages import under bare top-level names (``utils.db.btd6_db``), not under a
# ``disbot.`` prefix. We match those package roots plus the rare fully-qualified
# ``disbot.*`` form. Kept to the bot's own layers so third-party (discord, stdlib,
# dashboard) mocks are never flagged.
_PROJECT_ROOTS = frozenset(
    {"disbot", "utils", "cogs", "services", "views", "core", "governance"},
)


@dataclass(frozen=True)
class Finding:
    """One signature-blind mock replacement of a project callable."""

    file: str
    line: int
    target: str  # the object the attribute is set on, e.g. ``btd6_db``
    attr: str  # the attribute name being replaced, e.g. ``search_facts``
    mock: str  # the bare mock class, e.g. ``AsyncMock``

    def display(self) -> str:
        return (
            f"  [WARN] {self.file}:{self.line}  "
            f"{self.target}.{self.attr} <- {self.mock}(...)  "
            f"(no spec=/autospec=/wraps= — add create_autospec / spec=real_fn)"
        )

    def as_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "target": self.target,
            "attr": self.attr,
            "mock": self.mock,
        }


def _dotted_name(node: ast.expr) -> str | None:
    """Return the dotted name for a ``Name``/``Attribute`` expression, else ``None``.

    ``btd6_db`` -> ``"btd6_db"``; ``counting_cog.db`` -> ``"counting_cog.db"``;
    ``monkeypatch`` -> ``"monkeypatch"``. A call/subscript/etc. returns ``None``.
    """
    parts: list[str] = []
    cur: ast.expr = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return ".".join(reversed(parts))
    return None


def _const_str(node: ast.expr | None) -> str | None:
    """Return ``node``'s value if it is a string literal, else ``None``."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _is_bare_mock_construction(node: ast.expr) -> str | None:
    """If *node* is a bare ``Mock(...)`` without a faithfulness kwarg, return its name.

    Returns the mock class name (e.g. ``"AsyncMock"``) when *node* constructs one of
    :data:`_BARE_MOCK_NAMES` and carries **no** ``spec=``/``spec_set=``/``autospec=``/
    ``wraps=`` keyword. Returns ``None`` otherwise (not a mock, or already faithful).

    Matches both ``AsyncMock(...)`` and ``mock.AsyncMock(...)`` call forms.
    """
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if isinstance(func, ast.Name):
        name = func.id
    elif isinstance(func, ast.Attribute):
        name = func.attr  # ``unittest.mock.AsyncMock`` / ``mock.AsyncMock``
    else:
        return None
    if name not in _BARE_MOCK_NAMES:
        return None
    for kw in node.keywords:
        # ``**kwargs`` (kw.arg is None) is opaque — treat as possibly-faithful, skip.
        if kw.arg is None or kw.arg in _FAITHFUL_KWARGS:
            return None
    return name


class _ImportTable:
    """Maps a local name to the dotted module it was imported from.

    Lets the visitor decide whether a ``setattr`` target (``btd6_db``) resolves to a
    ``disbot.*`` module. Handles ``import disbot.x.y as z``,
    ``from disbot.x import y``, and ``from disbot.x import y as z``.
    """

    def __init__(self) -> None:
        self._local_to_module: dict[str, str] = {}

    def add_import(self, node: ast.Import) -> None:
        for alias in node.names:
            local = alias.asname or alias.name.split(".")[0]
            # ``import disbot.cogs.btd6 as btd6`` -> btd6 == disbot.cogs.btd6;
            # ``import disbot.cogs.btd6`` -> the bound local is ``disbot``.
            module = alias.name if alias.asname else alias.name.split(".")[0]
            self._local_to_module[local] = module

    def add_import_from(self, node: ast.ImportFrom) -> None:
        if not node.module:
            return
        for alias in node.names:
            local = alias.asname or alias.name
            self._local_to_module[local] = f"{node.module}.{alias.name}"

    def root_of(self, target: str) -> str | None:
        """Return the import-root package of *target*'s leading name, or ``None``.

        ``btd6_db`` imported ``from disbot.utils.db import btd6_db`` resolves to
        ``disbot`` (the root of ``disbot.utils.db.btd6_db``). For a dotted target
        (``counting_cog.db``) only the *leading* local (``counting_cog``) is resolved.
        """
        head = target.split(".")[0]
        module = self._local_to_module.get(head)
        if module is None:
            return None
        return module.split(".")[0]


class _MockFidelityVisitor(ast.NodeVisitor):
    """Collect :class:`Finding`s for signature-blind project-callable replacements."""

    def __init__(self, rel_file: str) -> None:
        self.rel_file = rel_file
        self.imports = _ImportTable()
        self.findings: list[Finding] = []

    # -- import table (populate before the call sites are judged) ------------
    def visit_Import(self, node: ast.Import) -> None:
        self.imports.add_import(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.imports.add_import_from(node)
        self.generic_visit(node)

    # -- call sites ----------------------------------------------------------
    def visit_Call(self, node: ast.Call) -> None:
        self._check_setattr(node)
        self._check_patch_object(node)
        self.generic_visit(node)

    def _record(self, node: ast.Call, target: str, attr: str, mock: str) -> None:
        if self.imports.root_of(target) in _PROJECT_ROOTS:
            self.findings.append(
                Finding(self.rel_file, node.lineno, target, attr, mock),
            )

    def _check_setattr(self, node: ast.Call) -> None:
        """Flag ``<x>.setattr(<target>, "<attr>", <bare-mock>)`` (monkeypatch shape)."""
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr in _SETATTR_FUNCS):
            return
        # Three positional args: (target_obj, "attr_name", replacement). The
        # two-arg ``setattr(obj_with_dotted_path, value)`` form has no string attr
        # to flag and is skipped.
        if len(node.args) < 3:
            return
        attr = _const_str(node.args[1])
        if attr is None:
            return
        mock = _is_bare_mock_construction(node.args[2])
        if mock is None:
            return
        target = _dotted_name(node.args[0])
        if target is None:
            return
        self._record(node, target, attr, mock)

    def _check_patch_object(self, node: ast.Call) -> None:
        """Flag ``patch.object(<target>, "<attr>", <bare-mock>)`` (no autospec)."""
        func = node.func
        # Match ``patch.object`` / ``mock.patch.object`` (attr chain ending .object).
        if not (isinstance(func, ast.Attribute) and func.attr == "object"):
            return
        owner = func.value
        owner_name = (
            owner.attr
            if isinstance(owner, ast.Attribute)
            else (owner.id if isinstance(owner, ast.Name) else None)
        )
        if owner_name != "patch":
            return
        # ``patch.object`` carrying autospec/spec/wraps as a kwarg is faithful — and a
        # bare ``patch.object(obj, "attr")`` with no replacement positional auto-specs
        # by default only when ``autospec=True``; without it the default new mock is a
        # bare MagicMock. We flag the *explicit bare-mock replacement* form only, to
        # stay precise and quiet.
        for kw in node.keywords:
            if kw.arg in _FAITHFUL_KWARGS:
                return
        if len(node.args) < 3:
            return
        attr = _const_str(node.args[1])
        if attr is None:
            return
        mock = _is_bare_mock_construction(node.args[2])
        if mock is None:
            return
        target = _dotted_name(node.args[0])
        if target is None:
            return
        self._record(node, target, attr, mock)


def scan_source(source: str, rel_file: str = "<source>") -> list[Finding]:
    """Return the signature-blind mock-replacement findings in one module source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    visitor = _MockFidelityVisitor(rel_file)
    visitor.visit(tree)
    return visitor.findings


def scan_tree(
    scan_root: Path = DEFAULT_SCAN_ROOT,
    repo_root: Path = REPO_ROOT,
) -> list[Finding]:
    """Scan every ``*.py`` under *scan_root* and return all findings, file-sorted."""
    findings: list[Finding] = []
    for path in sorted(scan_root.rglob("*.py")):
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            rel_file = str(path.relative_to(repo_root))
        except ValueError:
            rel_file = str(path)
        findings.extend(scan_source(source, rel_file))
    findings.sort(key=lambda f: (f.file, f.line))
    return findings


def _resolve_files(args: argparse.Namespace) -> list[Path]:
    """Resolve the file set from --file / positional args, or default to the tree."""
    if args.file:
        return [(REPO_ROOT / args.file).resolve()]
    if args.files:
        return [
            (REPO_ROOT / f).resolve()
            for f in args.files
            if (REPO_ROOT / f).resolve().suffix == ".py"
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: report (always exit 0) or strict (exit 1 on any finding)."""
    parser = argparse.ArgumentParser(
        description=(
            "Flag signature-blind mocks replacing disbot.* callables in tests/ "
            "(steer toward create_autospec / spec=real_fn). Warn-only by default."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["report", "strict"],
        default="report",
        help="report: always exit 0 (warn-only); strict: exit 1 if any finding",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="check a single file (relative to repo root or absolute)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print findings as a JSON array instead of the human report",
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="positional file list (used by pre-commit pass_filenames)",
    )
    args = parser.parse_args(argv)

    explicit = _resolve_files(args)
    if explicit:
        findings: list[Finding] = []
        for path in explicit:
            if not path.exists():
                continue
            try:
                rel = str(path.relative_to(REPO_ROOT))
            except ValueError:
                rel = str(path)
            findings.extend(scan_source(path.read_text(encoding="utf-8"), rel))
        findings.sort(key=lambda f: (f.file, f.line))
    else:
        findings = scan_tree()

    if args.json:
        print(json.dumps([f.as_dict() for f in findings], indent=2))
    elif not findings:
        print("check_autospec_fidelity: no signature-blind mock replacements found.")
    else:
        print(
            f"check_autospec_fidelity: {len(findings)} signature-blind mock "
            f"replacement(s) of disbot.* callables (warn-only):",
        )
        for finding in findings:
            print(finding.display())
        print(
            "\nMake these mocks signature-faithful so a bad-arg call fails the test:\n"
            "  create_autospec(real_fn)  |  AsyncMock(spec=real_fn)  |  "
            "patch.object(..., autospec=True)",
        )

    if args.mode == "strict" and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
