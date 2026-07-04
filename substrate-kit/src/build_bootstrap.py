"""Build ``dist/bootstrap.py`` from the readable ``src/engine`` tree.

This is the manifest->artifact step (the same shape as the host repo's
``build_pack.py`` — but that script is **inspiration only, not a trusted
reference**: it carries a Q-0105 "delete if unreliable" header, so this builder
owns its own discipline and a recursion test). It reads the engine modules in
dependency order, strips their intra-package imports, concatenates the bodies
into one stdlib-only file, and appends an embedded manifest of the same sources
so a future ``init --unpack`` can write editable copies.

Regenerate with::

    python3 substrate-kit/src/build_bootstrap.py
"""

from __future__ import annotations

import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = KIT_ROOT / "src" / "engine"
TEMPLATES_ROOT = KIT_ROOT / "src" / "engine" / "templates"
DIST_PATH = KIT_ROOT / "dist" / "bootstrap.py"

# Dependency order: a module appears after everything it references.
MODULE_ORDER = (
    "lib/atomicio.py",
    "lib/config.py",
    "lib/state.py",
    "lib/guardrail.py",
    "lib/modes.py",
    "interview/question_bank.py",
    "interview/stages.py",
    "interview/interview.py",
    "checks/check_docs.py",
    "checks/check_session_log.py",
    "checks/check_namespace.py",
    "checks/check_seam_authority.py",
    "checks/check_orientation_budget.py",
    "ledger.py",
    "loop/kpis.py",
    "loop/reflections.py",
    "loop/episodes.py",
    "loop/triggers.py",
    "loop/maintenance.py",
    "loop/review_seam.py",
    "economy/engine.py",
    "economy/harvest.py",
    "economy/simulator.py",
    "stances/stances.py",
    "skills/skills.py",
    "agents/agents.py",
    "hooks/stance_guard.py",
    "hooks/session_start.py",
    "hooks/post_edit.py",
    "hooks/stop_check.py",
    "hooks/settings.py",
    "render.py",
    "contextpack.py",
    "adopt.py",
    "cli.py",
)
PACKAGE_FILES = (
    "__init__.py",
    "lib/__init__.py",
    "interview/__init__.py",
    "checks/__init__.py",
    "loop/__init__.py",
    "economy/__init__.py",
    "stances/__init__.py",
    "skills/__init__.py",
    "agents/__init__.py",
    "hooks/__init__.py",
)

# Intra-package imports are dropped: in the concatenated file the referenced
# names already live in the same module namespace.
_INTRA_PKG_PREFIXES = ("from engine", "import engine", "from .")

_HEADER = '''"""substrate-kit bootstrap — GENERATED, DO NOT EDIT.

Single-file, stdlib-only. Regenerate from source with:
    python3 substrate-kit/src/build_bootstrap.py
Source of truth: substrate-kit/src/engine/. Edits here are overwritten.
"""'''


def _read(rel: str) -> str:
    """Return the text of an engine-relative source file."""
    return (ENGINE_ROOT / rel).read_text(encoding="utf-8")


def _triple_quote_toggles(line: str, active: str | None) -> str | None:
    """Track triple-quoted string state across a line; return the new state.

    ``active`` is the open triple-quote delimiter (double or single form) or
    None. Naive by design (counts delimiter occurrences; a line mixing both
    delimiter forms is not handled) — module docstrings and the embedded prose
    blocks this builder must survive are all well-formed.
    """
    if active is not None:
        return None if line.count(active) % 2 == 1 else active
    for delim in ('"""', "'''"):
        if line.count(delim) % 2 == 1:
            return delim
    return None


def _split_imports(source: str) -> tuple[list[str], list[str], list[str]]:
    """Split a module into (future imports, kept imports, body lines).

    Intra-package imports are dropped — in the concatenated file their names
    already live in the same namespace. A *parenthesized multi-line* intra-package
    import is dropped **whole**: its continuation lines must not leak into the body
    (that produced an ``IndentationError`` in the generated bootstrap). Lines
    inside triple-quoted strings are never treated as imports — a docstring
    sentence starting with ``from ...`` once got hoisted into the import block
    and broke the generated file's syntax.
    """
    future: list[str] = []
    imports: list[str] = []
    body: list[str] = []
    dropping_multiline = False
    in_string: str | None = None
    for line in source.splitlines():
        if in_string is not None:
            body.append(line)
            in_string = _triple_quote_toggles(line, in_string)
            continue
        if dropping_multiline:
            if ")" in line:
                dropping_multiline = False
            continue
        if line.startswith("from __future__"):
            future.append(line)
        elif any(line.startswith(p) for p in _INTRA_PKG_PREFIXES):
            if "(" in line and ")" not in line:
                dropping_multiline = True
            continue
        elif line.startswith(("import ", "from ")):
            imports.append(line)
        else:
            body.append(line)
            in_string = _triple_quote_toggles(line, None)
    return future, imports, body


def build() -> str:
    """Assemble the full text of ``dist/bootstrap.py``."""
    future: list[str] = []
    imports: list[str] = []
    body: list[str] = []
    manifest: dict[str, str] = {}

    for rel in PACKAGE_FILES:
        manifest[f"engine/{rel}"] = _read(rel)

    for rel in MODULE_ORDER:
        source = _read(rel)
        manifest[f"engine/{rel}"] = source
        mod_future, mod_imports, mod_body = _split_imports(source)
        for line in mod_future:
            if line not in future:
                future.append(line)
        for line in mod_imports:
            if line not in imports:
                imports.append(line)
        body.append(f"\n# --- engine/{rel} ---")
        body.extend(mod_body)

    lines: list[str] = [_HEADER, ""]
    lines.extend(future)
    lines.append("")
    lines.extend(sorted(imports))
    lines.extend(body)
    lines.append("")
    lines.append("_ENGINE_MANIFEST = {")
    for path, text in manifest.items():
        lines.append(f"    {path!r}: {text!r},")
    lines.append("}")
    lines.append("")
    lines.append("_TEMPLATES = {")
    for tpath in sorted(TEMPLATES_ROOT.glob("*")):
        lines.append(f"    {tpath.name!r}: {tpath.read_text(encoding='utf-8')!r},")
    lines.append("}")
    lines.append("")
    lines.append('if __name__ == "__main__":')
    lines.append("    raise SystemExit(main())")
    return "\n".join(lines) + "\n"


def main() -> int:
    """Generate ``dist/bootstrap.py`` from ``src/engine``."""
    content = build()
    DIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    DIST_PATH.write_text(content, encoding="utf-8")
    sys.stdout.write(f"wrote {DIST_PATH} ({len(content)} bytes)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
