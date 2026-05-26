"""Legacy command-surface snapshot guard.

The :mod:`core.runtime.command_surface_ledger` already enumerates every
prefix + slash entrypoint at startup, but nothing currently asserts
*which* commands must remain registered. Lost prefix commands —
especially old typing shortcuts like ``!bj`` or top-level prefix
groups like ``!ai`` — can regress silently across refactors.

This module pins two sets:

* ``EXPECTED_LIVE`` — commands that must currently appear in the
  cogs' decorator-registered surface. A missing entry means a
  regression: either restore the binding or, if the removal was
  intentional, move it into ``LEGACY_DEPRECATED`` with a replacement
  documented.
* ``LEGACY_DEPRECATED`` — commands intentionally retired. Each entry
  carries a replacement and the PR/commit that removed it. The test
  asserts these stay absent so a resurrected binding is flagged
  during review.

Discovery is via AST scanning of ``disbot/cogs/**/*.py`` rather than
building a live ``commands.Bot`` because cog ``cog_load`` paths touch
DB and external services that the unit-test sandbox does not have.
This guards the *decorator surface* — the same surface the live ledger
walks at startup — which is the regression to catch.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

COGS_ROOT = Path(__file__).resolve().parents[3] / "disbot" / "cogs"

# ---------------------------------------------------------------------------
# EXPECTED_LIVE — commands the audit pinned as visible / typed by users.
#
# Each entry is (name, surface) where surface ∈ {"prefix", "slash"}.
# Aliases register as their own (alias_name, "prefix") entry so renames
# are also detected.
# ---------------------------------------------------------------------------

EXPECTED_LIVE: frozenset[tuple[str, str]] = frozenset(
    {
        # Game prefix commands typed in the screenshots.
        ("blackjack", "prefix"),
        ("bj", "prefix"),  # alias of blackjack
        ("games", "prefix"),
        ("ai", "prefix"),
        # Setup surface (prefix + slash).
        ("setup", "prefix"),
        ("setup", "slash"),
        ("setup-status", "slash"),
        ("setup-skip", "slash"),
        ("setup-unskip", "slash"),
        ("setup-depth", "slash"),
        ("setup-reset", "slash"),
        ("setup-hub", "slash"),
        # Top-level slash command panels referenced by /games etc.
        ("games", "slash"),
        ("help", "slash"),
    }
)

# ---------------------------------------------------------------------------
# LEGACY_DEPRECATED — intentionally retired commands. Add an entry here
# when removing a command instead of letting it disappear silently.
#
# Each entry is (name, surface, replacement). The replacement value is
# informational only (read by humans during review); the test only
# asserts the name does not re-appear in the live decorator surface.
# ---------------------------------------------------------------------------

LEGACY_DEPRECATED: tuple[tuple[str, str, str], ...] = ()


# ---------------------------------------------------------------------------
# AST visitor: extract @commands.command / @app_commands.command names.
# ---------------------------------------------------------------------------


def _decorator_call_name(dec: ast.expr) -> str | None:
    """Return ``"<module>.<attr>"`` for ``@module.attr(...)`` decorators.

    Examples:
      ``@commands.command(...)``       → ``"commands.command"``
      ``@app_commands.command(...)``   → ``"app_commands.command"``
      ``@commands.hybrid_command(...)``→ ``"commands.hybrid_command"``
      ``@bot.event``                   → ``None``  (no call)
    """
    if not isinstance(dec, ast.Call):
        return None
    func = dec.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return f"{func.value.id}.{func.attr}"
    return None


def _name_kwarg(dec: ast.Call) -> str | None:
    for kw in dec.keywords:
        if kw.arg == "name" and isinstance(kw.value, ast.Constant):
            value = kw.value.value
            if isinstance(value, str):
                return value
    return None


def _aliases_kwarg(dec: ast.Call) -> list[str]:
    for kw in dec.keywords:
        if kw.arg == "aliases" and isinstance(kw.value, (ast.List, ast.Tuple)):
            out: list[str] = []
            for el in kw.value.elts:
                if isinstance(el, ast.Constant) and isinstance(el.value, str):
                    out.append(el.value)
            return out
    return []


_PREFIX_DECORATORS = frozenset(
    {
        "commands.command",
        "commands.group",
        "commands.hybrid_command",
        "commands.hybrid_group",
    }
)

_SLASH_DECORATORS = frozenset(
    {
        "app_commands.command",
        "app_commands.group",
    }
)


def _scan_cogs_for_decorator_surface() -> set[tuple[str, str]]:
    surface: set[tuple[str, str]] = set()
    for py_file in COGS_ROOT.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                call_name = _decorator_call_name(dec)
                if call_name is None:
                    continue
                assert isinstance(dec, ast.Call)
                cmd_name = _name_kwarg(dec) or node.name
                if call_name in _PREFIX_DECORATORS:
                    surface.add((cmd_name, "prefix"))
                    for alias in _aliases_kwarg(dec):
                        surface.add((alias, "prefix"))
                elif call_name in _SLASH_DECORATORS:
                    # app_commands.command sometimes uses the function
                    # name as a fallback; honor either source.
                    surface.add((cmd_name, "slash"))
    return surface


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def decorator_surface() -> set[tuple[str, str]]:
    return _scan_cogs_for_decorator_surface()


def test_expected_live_commands_remain_registered(decorator_surface):
    """Every command in ``EXPECTED_LIVE`` must appear in the live
    decorator surface scanned from ``disbot/cogs/``.

    Failure means a typed-by-users command vanished without making it
    into ``LEGACY_DEPRECATED`` — a silent regression. Restore the
    binding or, if removal is intended, move it into
    ``LEGACY_DEPRECATED`` with a replacement.
    """
    missing = sorted(EXPECTED_LIVE - decorator_surface)
    assert not missing, (
        "Legacy commands missing from disbot/cogs/ decorator surface:\n"
        + "\n".join(f"  - {name} ({surface})" for name, surface in missing)
        + "\n\nIf the removal was intentional, add an entry to "
        "LEGACY_DEPRECATED in tests/unit/runtime/test_legacy_command_surface.py "
        "naming the replacement command."
    )


def test_deprecated_commands_do_not_reappear(decorator_surface):
    """Commands moved to ``LEGACY_DEPRECATED`` must stay absent.

    Catches accidental re-registration of an intentionally retired
    command (e.g. someone copy-pastes an old cog without realizing the
    binding was retired).
    """
    resurrected = [
        (name, surface, replacement)
        for (name, surface, replacement) in LEGACY_DEPRECATED
        if (name, surface) in decorator_surface
    ]
    assert (
        not resurrected
    ), "Retired commands have reappeared in the decorator surface:\n" + "\n".join(
        f"  - {n} ({s}) → replaced by {repl}" for n, s, repl in resurrected
    )


def test_decorator_surface_has_no_obvious_gaps():
    """Sanity: the AST scan finds *some* commands. If the scan returns
    empty the test would pass vacuously on a missing-cogs disaster.
    """
    surface = _scan_cogs_for_decorator_surface()
    assert len(surface) >= 50, (
        f"AST scan found only {len(surface)} decorated commands — "
        "expected dozens. The scan or the cogs tree is broken."
    )
