"""P0-3 arc PR 3 ratchet — the setup_delegate actor_type is a bounded bypass.

Q-0098 lets a server-owner-delegated, possibly NON-administrator member apply
staged setup operations.  ``governance.capability.actor_holds_capability``
authorizes such a write under ``actor_type="setup_delegate"`` — a real
privilege bypass of the administrator floor.  It is safe only because exactly
one seam mints it (``services.setup_operations.apply_operations``, which
re-verifies the live delegation first).  These AST fences keep that true,
modelled on ``test_game_wager_write_boundary``:

1. No call passes the literal ``actor_type="setup_delegate"`` anywhere outside
   ``services/setup_operations.py`` — a cog/view/other service can't mint the
   bypass directly.
2. The string literal ``"setup_delegate"`` appears under ``disbot/`` only in the
   five files that form the authority contract (the minter, the capability
   recognizer, and the three pipelines' allow-sets).  A new file referencing the
   token trips this guard, forcing the author to read the contract.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

_TOKEN = "setup_delegate"

# The ONLY seam that may mint actor_type="setup_delegate" (and the only file
# that may originate the token as a write actor).
_MINTER = _DISBOT / "services" / "setup_operations.py"

# Every file under disbot/ allowed to *reference* the literal token: the minter,
# the capability recognizer that authorizes it, and the three capability-gated
# pipelines that accept it in their _ALLOWED_ACTOR_TYPES allow-set.
_CONTRACT_FILES = {
    _MINTER,
    _DISBOT / "governance" / "capability.py",
    _DISBOT / "services" / "settings_mutation.py",
    _DISBOT / "services" / "resource_provisioning.py",
    _DISBOT / "services" / "binding_mutation.py",
}


def _actor_type_setup_delegate_kwargs(path: Path) -> list[int]:
    """Line numbers of ``actor_type="setup_delegate"`` keyword arguments."""
    tree = ast.parse(path.read_text(), filename=str(path))
    lines: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if (
                kw.arg == "actor_type"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value == _TOKEN
            ):
                lines.append(node.lineno)
    return lines


def _has_token_constant(path: Path) -> bool:
    """True iff the file contains the bare string constant ``"setup_delegate"``.

    Matches only an exact-value ``ast.Constant`` so docstrings that *mention*
    the word (their constant value is the whole paragraph) and identifiers like
    ``setup_delegate_slash`` (an ``ast.Name``/``FunctionDef``, not a constant)
    are not flagged.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value == _TOKEN:
            return True
    return False


def test_minter_file_exists():
    assert _MINTER.exists(), f"the setup_delegate minter is gone: {_MINTER}"


def test_setup_delegate_minted_only_by_apply_operations():
    """``actor_type="setup_delegate"`` literal-kwarg only in the minter file."""
    violations: list[str] = []
    for path in sorted(_DISBOT.rglob("*.py")):
        if "__pycache__" in path.parts or path == _MINTER:
            continue
        for lineno in _actor_type_setup_delegate_kwargs(path):
            violations.append(f"{path.relative_to(_REPO_ROOT)}:{lineno}")
    assert not violations, (
        'Q-0098 violation: actor_type="setup_delegate" minted outside '
        "services.setup_operations.apply_operations — that seam is the only "
        "minter, and it re-verifies the live delegation first:\n"
        + "\n".join(f"  {v}" for v in violations)
    )


def test_setup_delegate_token_confined_to_contract_files():
    """The ``"setup_delegate"`` literal lives only in the 5 contract files."""
    found = {
        path
        for path in _DISBOT.rglob("*.py")
        if "__pycache__" not in path.parts and _has_token_constant(path)
    }
    stray = found - _CONTRACT_FILES
    assert not stray, (
        'Q-0098 violation: the "setup_delegate" token appears outside the '
        "authority contract (minter + capability recognizer + the three "
        "pipeline allow-sets). Route delegated applies through "
        "services.setup_operations.apply_operations instead of referencing the "
        "token directly:\n"
        + "\n".join(f"  {p.relative_to(_REPO_ROOT)}" for p in sorted(stray))
    )
