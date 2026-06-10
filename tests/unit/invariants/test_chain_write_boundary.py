"""RS07 fence — every ``chain_channels`` write flows through chain_service.

The chain game was the last named service-boundary hole from the
2026-06-10 runtime/services map (FIND-RS07): the cog + its four panel
modals called the ``utils.db.games.chain`` writers directly, each with
its own duplicated existence check and no audit trail. After the
extraction, ``services/chain_service.py`` is the **sole writer** —
config writes are audited there (Batch 3 pattern), and even the
unaudited ``chain_count`` game-state increment routes through it so the
table has exactly one writing module.

AST scan modeled on ``test_mining_write_boundary.py``: attribute calls
named like a chain write primitive are flagged regardless of receiver
(the names are unique to the chain DB layer). Reads
(``get_chain_channel`` / ``get_all_chain_channels``) stay free.

Scans ALL of ``disbot/`` except the service itself and the owning DB
module, so a new writer can't appear in any layer unnoticed.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# The only modules allowed to reference the write primitives: the owner
# (defines them) and the service (the sole caller).
_ALLOWED_FILES = {
    _DISBOT / "services" / "chain_service.py",
    _DISBOT / "utils" / "db" / "games" / "chain.py",
}

# Names unique to the chain DB layer — forbidden on ANY receiver.
_FORBIDDEN_WRITERS = {
    "set_chain_channel",
    "delete_chain_channel",
    "set_chain_limit",
    "increment_chain_count",
}


def _write_calls(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    found: list[str] = []
    for n in ast.walk(tree):
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr in _FORBIDDEN_WRITERS
        ):
            found.append(f"{n.func.attr} (line {n.lineno})")
    return found


def test_no_direct_chain_writes_outside_service():
    violations: list[tuple[str, list[str]]] = []
    for path in sorted(_DISBOT.rglob("*.py")):
        if "__pycache__" in path.parts or path in _ALLOWED_FILES:
            continue
        calls = _write_calls(path)
        if calls:
            violations.append((str(path.relative_to(_REPO_ROOT)), calls))
    assert not violations, (
        "RS07 violation: direct chain_channels writes outside "
        "services/chain_service.py (route through the audited service):\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )


def test_audited_chain_seam_exists():
    """Positive check — the canonical seam exists and emits the audit
    companion (not a silent write)."""
    src = (_DISBOT / "services" / "chain_service.py").read_text()
    assert "async def create_chain(" in src
    assert "async def delete_chain(" in src
    assert "async def set_word_limit(" in src
    assert "async def record_chain_progress(" in src
    assert "emit_audit_action(" in src
