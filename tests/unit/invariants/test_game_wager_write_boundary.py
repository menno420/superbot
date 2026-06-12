"""P0-1 ratchet — wagered game money flows through game_wager_workflow.

Two-party (PvP) and paid-entry (tournament) coin movement in the games
stack must compose the atomic ``economy_service`` primitives **inside**
``services.game_wager_workflow`` — never as a bare
``economy_service.credit`` / ``.debit`` pair from a view or cog, which is
the crash-window that minted coins (credit the winner, then a failure
skips the loser's debit) or short-paid the loser via overdraft.

Two checks, modelled on ``test_mining_write_boundary`` /
``test_inv_f_economy_service``:

1. The migrated PvP + tournament files may not call
   ``economy_service.credit`` / ``.debit`` directly — wagered money moves
   only through the workflow.  Recovery ``economy_service.refund`` (single
   -sided, no mint risk) and the **solo** files (single player vs the
   house — no second party to mint against) stay free; solo is explicitly
   out of P0-1 scope.
2. ``allow_overdraft=True`` — the exact mint/short-pay signature — is
   forbidden anywhere under ``views/`` / ``cogs/`` except the two solo
   game views, which floor a solo loss at zero with no counterparty.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# The PvP + tournament money paths migrated in P0-1.  After migration
# none of these may call economy_service.credit / .debit directly.
_WAGER_FILES = (
    _DISBOT / "views" / "rps" / "pvp_play.py",
    _DISBOT / "views" / "rps" / "pvp_challenge.py",
    _DISBOT / "views" / "blackjack" / "pvp_view.py",
    _DISBOT / "views" / "blackjack" / "tournament_views.py",
    _DISBOT / "cogs" / "rps_tournament_cog.py",
    _DISBOT / "cogs" / "rps_tournament" / "_persistence.py",
    _DISBOT / "cogs" / "blackjack" / "_persistence.py",
)

_FORBIDDEN_ATTRS = {"credit", "debit"}
_ECONOMY_RECEIVERS = {"economy_service"}

# Solo game views legitimately floor a single-player loss at zero — no
# counterparty, so no mint risk.  Only these may pass allow_overdraft.
_OVERDRAFT_ALLOWED = {
    _DISBOT / "views" / "rps" / "solo_play.py",
    _DISBOT / "views" / "blackjack" / "solo_view.py",
}


def _economy_credit_debit_calls(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    found: list[str] = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        if n.func.attr not in _FORBIDDEN_ATTRS:
            continue
        rcv = n.func.value
        if isinstance(rcv, ast.Name) and rcv.id in _ECONOMY_RECEIVERS:
            found.append(f"economy_service.{n.func.attr} (line {n.lineno})")
    return found


def _overdraft_calls(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(), filename=str(path))
    lines: list[int] = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        for kw in n.keywords:
            if (
                kw.arg == "allow_overdraft"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value is True
            ):
                lines.append(n.lineno)
    return lines


def test_no_direct_economy_credit_debit_in_wager_files():
    """The PvP/tournament money paths route every wager through the workflow."""
    violations: list[tuple[str, list[str]]] = []
    for path in _WAGER_FILES:
        assert path.exists(), f"wager-fence file list is stale: {path} is gone"
        calls = _economy_credit_debit_calls(path)
        if calls:
            violations.append((str(path.relative_to(_REPO_ROOT)), calls))
    assert not violations, (
        "P0-1 violation: direct economy_service.credit/.debit in a wagered "
        "game path — route the two-party/paid-entry money through "
        "services.game_wager_workflow:\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )


def test_no_overdraft_outside_solo_game_views():
    """``allow_overdraft=True`` is the mint signature — solo views only."""
    violations: list[str] = []
    for base in (_DISBOT / "views", _DISBOT / "cogs"):
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts or path in _OVERDRAFT_ALLOWED:
                continue
            for lineno in _overdraft_calls(path):
                violations.append(
                    f"{path.relative_to(_REPO_ROOT)}:{lineno}",
                )
    assert not violations, (
        "P0-1 violation: allow_overdraft=True outside the solo game views "
        "(the credit-then-overdraft-debit mint pattern). Two-party wagers "
        "escrow at accept through services.game_wager_workflow:\n"
        + "\n".join(f"  {v}" for v in violations)
    )
