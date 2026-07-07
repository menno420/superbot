"""Settle-once guard for game-state views (cross-game terminal contract).

A game-state view can reach its *settlement* path more than once:

- a player double-clicks the finishing button,
- a timeout fires while a final move is already resolving,
- a duplicate component interaction is delivered late.

When settlement pays out, records a result, or posts a result message, running
it twice **double-settles** — a redundant payout attempt and a duplicate result
post. :class:`SettleOnceMixin` gives a view one atomic claim on that transition:
the first caller of :meth:`claim_settlement` wins and proceeds; every later
caller gets ``False`` and must short-circuit.

The claim is a plain *synchronous* check-and-set. discord.py dispatches every
component callback and ``on_timeout`` on the one asyncio event loop, and no
``await`` runs between the read and the write, so the critical section is
race-free **as long as the claim is taken before the handler's first await**.
That ordering is the contract — take ``claim_settlement()`` at the very top of
the settling path, before any ``await``.

Production-readiness map: this closes the *"no cross-game test proves terminal
controls cannot trigger a second settlement"* row in
``docs/planning/production-readiness/games-production-readiness-map-2026-06-12.md``
and continues the BUG-0013 challenge-timer lineage (``docs/health/bug-book.md``).

Lives in ``utils/`` (not ``views/``) because the terminal state it guards lives
in different layers: a ``discord.ui.View`` subclass for RPS PvP / the deathmatch
bot-duel, but a plain ``services`` state object (``_PvPState``) for blackjack
PvP. A shared helper needed by both ``services/`` and ``views/`` belongs in
``utils/`` (``docs/helper-policy.md``), and ``services/`` may not import
``views/`` at all. It is a mixin, not a base class, so it composes onto views
that intentionally extend ``discord.ui.View`` directly (the documented
divergence in ``views/base.py``) and onto bare state objects alike. It declares
no ``__init__`` — the class-level ``_settlement_claimed = False`` default is the
unclaimed state, and the first claim writes a per-instance attribute (``bool``
is immutable, so the class attribute is never mutated and no state leaks between
instances).
"""

from __future__ import annotations


class SettleOnceMixin:
    """Give a game-state view one atomic claim on its terminal transition."""

    _settlement_claimed: bool = False

    def claim_settlement(self) -> bool:
        """Atomically claim the view's terminal transition. ``True`` = you won.

        Call this **synchronously at the very top** of every settling path
        (finishing button, ``_resolve``, ``on_timeout``) *before any* ``await``.
        Returns ``True`` exactly once per view instance; later calls return
        ``False`` and the caller must return without re-settling.
        """
        if self._settlement_claimed:
            return False
        self._settlement_claimed = True
        return True

    @property
    def is_settled(self) -> bool:
        """Whether the terminal transition has already been claimed."""
        return self._settlement_claimed

    def rearm_settlement(self) -> None:
        """Reset the claim for a NEW terminal cycle.

        For long-lived holders whose terminal transition recurs per cycle
        (a cog holding per-tournament state), call this exactly once at the
        start of each cycle — never from a settling path.
        """
        self._settlement_claimed = False
