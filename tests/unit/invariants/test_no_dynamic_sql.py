"""PR R2 — codebase-wide AST regression: no dynamic SQL identifiers.

The audit surfaced two callsites that interpolated SQL identifiers
(column names) into raw SQL via f-strings:

  * ``utils/db/games/rps.py:rps_update_stat`` — fixed in PR R1.
  * ``utils/db/economy.py:set_economy`` — fixed in PR R2.

Both were whitelist-protected at the time, but the pattern is
structurally hostile: a future maintainer extending the whitelist with
a non-static identifier would silently re-introduce a SQL injection
class.  This test fails the build if any ``pool.execute`` /
``pool.fetchone`` / ``pool.fetchall`` / ``conn.execute`` /
``conn.fetchrow`` / ``conn.fetch`` callsite under ``disbot/`` passes
an f-string with a brace-placeholder identifier inside a SQL-keyword
context.

Allowlist semantics: there are NO legitimate uses today.  Any new
identifier dynamism must come back to this test and either replace the
pattern with explicit branches (preferred) or — if absolutely
necessary — add the file to ``_ALLOWED_PATHS`` with a written
justification in the comment.

Detection scope (kept tight on purpose):
  * f-string literals only — ``f"…"`` and ``f'''…'''``.
  * Must appear as the first positional argument to one of the
    asyncpg execution helpers we use.
  * Must contain a ``{identifier}`` placeholder INSIDE one of these
    SQL-keyword contexts: ``SET``, ``FROM``, ``INTO``, ``JOIN``,
    ``UPDATE``, ``TABLE``.  Plain ``{value}`` placeholders that
    expand to literals (e.g., ``f"LIMIT {n}"``) are allowed because
    the audit found none of those today; if a contributor wants to
    add a numeric LIMIT interpolation, they should still use a
    parameter ``$N`` for consistency.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# Files allowed to use the pattern.  Currently empty.  Adding here
# requires explanation in this comment block and code review consent.
_ALLOWED_PATHS: set[Path] = set()

_SQL_EXECUTOR_NAMES = {
    "execute",
    "fetch",
    "fetchall",
    "fetchone",
    "fetchrow",
    "fetchval",
}

# Pattern for a SQL-keyword context immediately followed by an
# f-string brace placeholder.  Matched against the f-string's literal
# segments to find ``... SET {col} ...`` etc.
_SQL_KEYWORD_NEAR_PLACEHOLDER = re.compile(
    r"\b(SET|FROM|INTO|JOIN|UPDATE|TABLE)\b\s*$",
    re.IGNORECASE,
)


def _iter_disbot_py_files() -> list[Path]:
    return [
        p
        for p in _DISBOT.rglob("*.py")
        if "__pycache__" not in p.parts
    ]


def _is_executor_call(node: ast.Call) -> bool:
    """True if ``node`` looks like ``<receiver>.<execute-or-similar>(…)``."""
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr in _SQL_EXECUTOR_NAMES
    if isinstance(func, ast.Name):
        # Bare ``execute(...)`` happens to also be ``ast.Name`` for
        # cases where ``execute`` is imported from utils.db.pool; the
        # name is the same, so the check is consistent.
        return func.id in _SQL_EXECUTOR_NAMES
    return False


def _fstring_has_identifier_placeholder(node: ast.JoinedStr) -> str | None:
    """If the JoinedStr is a SQL string with an identifier-shaped
    brace placeholder right after a SQL keyword, return the offending
    snippet for the failure message.  Otherwise return None.
    """
    # ast.JoinedStr.values is a list of Str/Constant + FormattedValue.
    for i, part in enumerate(node.values):
        if not isinstance(part, ast.FormattedValue):
            continue
        # Look at the literal text immediately BEFORE this placeholder.
        if i == 0:
            continue
        prev = node.values[i - 1]
        if not isinstance(prev, ast.Constant) or not isinstance(prev.value, str):
            continue
        if _SQL_KEYWORD_NEAR_PLACEHOLDER.search(prev.value):
            return prev.value + "{...}"
    return None


def _find_violations(path: Path) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except SyntaxError:
        return []
    violations: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not _is_executor_call(node):
            continue
        if not node.args:
            continue
        first = node.args[0]
        if not isinstance(first, ast.JoinedStr):
            continue
        offending = _fstring_has_identifier_placeholder(first)
        if offending is not None:
            violations.append((node.lineno, offending.strip()))
    return violations


def test_no_dynamic_sql_identifier_interpolation():
    """No production file under disbot/ may pass an f-string with a
    brace identifier placeholder inside a SQL-keyword context to an
    asyncpg executor.
    """
    findings: list[str] = []
    for path in _iter_disbot_py_files():
        if path in _ALLOWED_PATHS:
            continue
        for lineno, snippet in _find_violations(path):
            rel = path.relative_to(_REPO_ROOT)
            findings.append(f"{rel}:{lineno}: {snippet!r}")
    assert not findings, (
        "Dynamic SQL identifier interpolation found:\n  "
        + "\n  ".join(findings)
        + "\nReplace with explicit per-column statements or a `match` "
        "over prepared queries.  See utils/db/games/rps.py (PR R1) and "
        "utils/db/economy.py (PR R2) for the canonical fix shape."
    )


@pytest.mark.parametrize(
    "fragment",
    [
        # PR R1's original bug — gone.
        'f"UPDATE rps_players SET {col}=… WHERE …"',
        # PR R2's original bug — gone.
        'f"UPDATE economy SET {sets} WHERE …"',
    ],
)
def test_known_bug_shapes_no_longer_present(fragment):
    """Defence-in-depth: spot-check the exact shapes the audit named.

    These literal patterns must not appear anywhere under disbot/.
    """
    needle_set = re.search(r"SET\s+\{(\w+)\}", fragment)
    assert needle_set, "test setup error: expected SET {ident} in fragment"
    ident = needle_set.group(1)
    pattern = re.compile(rf'f"[^"]*\bSET\s+\{{{ident}\}}', re.IGNORECASE)
    for path in _iter_disbot_py_files():
        src = path.read_text()
        assert not pattern.search(src), (
            f"Forbidden pattern reappeared at {path}: {fragment}"
        )
