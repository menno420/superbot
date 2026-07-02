"""Portable namespace / shadowing guard (Lane B6, the Q-0200 class).

Three AST-level checks over the Python roots a host configures
(``config.namespace``):

  1. **in-module shadowing** — the same top-level ``def`` / ``class`` name
     bound twice in one module; the later binding silently wins and the
     earlier one dies unnoticed (superbot's ``round_composition`` collision,
     caught only at CI).
  2. **cross-module collision** — the same public (non-underscore) top-level
     name defined in two modules of one package, unless one of the two is the
     package's ``__init__.py`` (the deliberate re-export pattern).
  3. **reserved names** — a name from the configured reserved map
     (``{"Name": "canonical/module.py"}``) defined outside its canonical
     module.

Uses only stdlib ``ast``; a file that fails to parse becomes a
``namespace-parse`` finding, never an exception. Findings reuse the
``Finding`` record from ``engine.checks.check_docs`` with paths relative to
the scanned root where possible.
"""

from __future__ import annotations

import ast
from pathlib import Path

from engine.checks.check_docs import Finding

_NS_DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _ns_rel(path: Path, root: Path) -> str:
    """Return ``path`` relative to ``root`` (posix) when possible, else str."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _ns_py_files(root: Path) -> list[Path]:
    """Return the ``*.py`` files under ``root`` (or ``root`` itself if a file)."""
    if root.is_file():
        return [root] if root.suffix == ".py" else []
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def _ns_top_level_defs(tree: ast.Module) -> list[tuple[str, int]]:
    """Return ``(name, lineno)`` for every top-level def/class in ``tree``."""
    return [
        (node.name, node.lineno)
        for node in tree.body
        if isinstance(node, _NS_DEF_NODES)
    ]


def _ns_overloaded_names(tree: ast.Module) -> set[str]:
    """Names whose top-level defs carry ``@overload`` — not shadowing.

    ``@typing.overload`` stacks re-bind the same name by design; flagging them
    as in-module shadowing was a verified false positive.
    """
    names: set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            if (
                isinstance(deco, ast.Name)
                and deco.id == "overload"
                or isinstance(deco, ast.Attribute)
                and deco.attr == "overload"
            ):
                names.add(node.name)
    return names


def _ns_dispatch_registered_names(tree: ast.Module) -> set[str]:
    """Names whose top-level defs carry ``@<x>.register`` — not shadowing.

    The ``functools.singledispatch`` idiom re-binds the same name (canonically
    ``def _``) once per registered type; the ``.register`` decorator captures
    each function, so the last global binding is irrelevant. Flagging the
    repeated defs as in-module shadowing was a verified false positive.
    Handles both ``@process.register`` and ``@process.register(int)``.
    """
    names: set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            target = deco.func if isinstance(deco, ast.Call) else deco
            if isinstance(target, ast.Attribute) and target.attr == "register":
                names.add(node.name)
    return names


def _ns_matches_canonical(rel: str, canonical: str) -> bool:
    """True when the scanned relpath is the reserved name's canonical module."""
    canon = canonical.replace("\\", "/").lstrip("./")
    return rel == canon or rel.endswith(f"/{canon}")


def check_namespace(
    roots: list[Path],
    *,
    reserved: dict[str, str] | None = None,
) -> list[Finding]:
    """Run the three namespace checks over ``roots``; return the findings.

    ``reserved`` maps a name to the canonical module relpath allowed to define
    it. Kinds: ``namespace`` for collisions, ``namespace-parse`` for files
    that fail to parse (reported, never raised).
    """
    reserved = reserved or {}
    findings: list[Finding] = []
    # (package dir, public name) -> [(rel, module filename, lineno)]
    package_defs: dict[tuple[str, str], list[tuple[str, str, int]]] = {}

    for root in roots:
        rel_base = root.parent if root.is_file() else root
        for py in _ns_py_files(root):
            rel = _ns_rel(py, rel_base)
            try:
                tree = ast.parse(py.read_text(encoding="utf-8"))
            except (SyntaxError, ValueError, OSError, UnicodeDecodeError) as exc:
                lineno = getattr(exc, "lineno", None)
                where = f"L{lineno}: " if lineno else ""
                msg = f"{where}failed to parse: {exc.__class__.__name__}: {exc}"
                findings.append(Finding(rel, "namespace-parse", msg))
                continue

            seen: dict[str, int] = {}
            # `_` is the conventional throwaway (and the canonical
            # singledispatch register target); `.register`-decorated defs are
            # the named-function dispatch form — neither is real shadowing.
            exempt_shadow = _ns_overloaded_names(tree)
            exempt_shadow |= _ns_dispatch_registered_names(tree)
            for name, lineno in _ns_top_level_defs(tree):
                if name in seen and name not in exempt_shadow and name != "_":
                    msg = (
                        f"`{name}` defined twice in one module "
                        f"(L{seen[name]} and L{lineno}) — the later def "
                        "silently shadows the earlier"
                    )
                    findings.append(Finding(rel, "namespace", msg))
                seen.setdefault(name, lineno)
                if not name.startswith("_"):
                    key = (py.parent.resolve().as_posix(), name)
                    package_defs.setdefault(key, []).append(
                        (rel, py.name, lineno),
                    )
                canonical = reserved.get(name)
                if canonical is not None and not _ns_matches_canonical(
                    rel,
                    canonical,
                ):
                    msg = (
                        f"L{lineno}: reserved name `{name}` defined outside "
                        f"its canonical module `{canonical}`"
                    )
                    findings.append(Finding(rel, "namespace", msg))

    for (_, name), sites in sorted(package_defs.items()):
        modules = {filename for _, filename, _ in sites}
        non_init = [s for s in sites if s[1] != "__init__.py"]
        if len(modules) < 2 or len({s[1] for s in non_init}) < 2:
            continue  # one module, or an __init__ re-export pair
        site_list = ", ".join(f"{rel}:L{lineno}" for rel, _, lineno in non_init)
        msg = (
            f"public name `{name}` defined in multiple modules of one "
            f"package ({site_list}) — rename or move to a shared home"
        )
        findings.append(Finding(non_init[0][0], "namespace", msg))
    return findings
