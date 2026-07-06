"""RPS tournament persistence + recovery helpers (S4.6).

Each function corresponds to one of the two persisted RPS subsystems:

  rps_pvp_pending     — pending PvP-challenge match state (cleared
                        on recovery, no refund — match never pre-debits)
  rps_tournament      — per-player tournament entry rows (refund on
                        recovery, entries are pre-debited at registration)

Test patches that previously targeted
``cogs.rps_tournament_cog.<thing>`` should now target the function-
defining module (``cogs.rps_tournament._persistence``).  See A1 and
A4 for the same migration pattern in xp and blackjack.

The cog methods (_recover_rps_tournament, _recover_rps_pvp_pending,
on_guild_remove, try_register_player) are preserved as thin
delegators so existing tests that call them via cog.<method>() keep
working.  The inspect.getsource test for try_register_player was
migrated to inspect ``save_tournament_entry`` instead — the literal
strings (``game_state_service.save``, ``RPS_TOURNAMENT_SUBSYSTEM``,
``RPS_TOURNAMENT_VERSION``, ``"bet":``) now live here.
"""

from __future__ import annotations

import logging

from services import economy_service, game_state_service

logger = logging.getLogger("bot")

# PR G6 — RPS tournament persistence constants.  Kept in this module
# so the inspect.getsource(save_tournament_entry) invariant has a
# stable target.  The cog re-exports them for back-compat imports.
RPS_TOURNAMENT_SUBSYSTEM = "rps_tournament"
RPS_TOURNAMENT_VERSION = 1


# ---------------------------------------------------------------------------
# rps_tournament — paid entry-fee persistence
# ---------------------------------------------------------------------------


async def save_tournament_entry(
    *,
    guild_id: int,
    user_id: int,
    entry_fee: int,
) -> None:
    """Persist a registered player's paid-entry row.

    Channel_id sentinel (0) because an RPS tournament is guild-wide,
    not channel-local — the natural game_state UNIQUE constraint on
    ``(guild_id, user_id, channel_id, subsystem)`` then enforces
    "one tournament entry per user per guild".

    The ``bet`` payload key matches the G0 GC convention so even if
    the bot loses both the cog_load recovery AND the on_guild_remove
    listener, the 24 h sweep still issues the refund.

    Failures are logged WARN and swallowed — the cog's in-memory
    state is authoritative while the bot is alive.
    """
    try:
        await game_state_service.save(
            guild_id=guild_id,
            user_id=user_id,
            channel_id=0,  # sentinel — tournament is guild-wide, not channel-local
            subsystem=RPS_TOURNAMENT_SUBSYSTEM,
            state={"bet": entry_fee},
            version=RPS_TOURNAMENT_VERSION,
        )
    except Exception as exc:
        logger.warning(
            "rps_tournament save failed (user=%d guild=%d): %s",
            user_id,
            guild_id,
            exc,
        )


async def recover_rps_tournament() -> None:
    """Refund every stranded RPS tournament entry then clear the row.

    Same shape as ``BlackjackCog._recover_blackjack_tournament``:
    entry fees were debited at registration, never paid back if the
    bot crashed before ``check_tournament_progress`` settled the pot.
    Refund failures are logged WARN but the row is still cleared to
    avoid an infinite retry loop.
    """
    try:
        rows = await game_state_service.list_active_for_subsystem(
            RPS_TOURNAMENT_SUBSYSTEM,
        )
    except Exception as exc:
        logger.warning("rps_tournament recovery skipped: %s", exc)
        return
    if not rows:
        return
    cleared = 0
    refunded = 0
    for row in rows:
        try:
            version = row.get("version")
            if version != RPS_TOURNAMENT_VERSION:
                logger.info(
                    "rps_tournament recovery: dropping version-"
                    "mismatch row id=%s (saved=%s, current=%s)",
                    row["id"],
                    version,
                    RPS_TOURNAMENT_VERSION,
                )
                await game_state_service.clear_by_id(row["id"])
                cleared += 1
                continue
            state = row.get("state") or {}
            bet = state.get("bet")
            if isinstance(bet, int) and bet > 0:
                try:
                    await economy_service.refund(
                        guild_id=row["guild_id"],
                        user_id=row["user_id"],
                        amount=bet,
                        reason="rps_tournament:restart_refund",
                    )
                    refunded += 1
                except Exception as exc:
                    logger.warning(
                        "rps_tournament refund failed for user=%d guild=%d: %s",
                        row.get("user_id"),
                        row.get("guild_id"),
                        exc,
                    )
            await game_state_service.clear_by_id(row["id"])
            cleared += 1
        except Exception as exc:
            logger.warning(
                "rps_tournament recovery: row id=%s failed: %s",
                row.get("id"),
                exc,
            )
    if cleared or refunded:
        logger.info(
            "rps_tournament recovery: cleared %d row(s), issued %d refund(s)",
            cleared,
            refunded,
        )


# ---------------------------------------------------------------------------
# rps_pvp_pending — pending PvP-challenge persistence (clear-only)
# ---------------------------------------------------------------------------


async def recover_rps_pvp_pending() -> None:
    """Drop every stranded rps_pvp_pending row.

    Live views cannot be re-attached after a process bounce, so the
    only safe action is to clear.  No coins are refunded — RPS PvP
    does not pre-debit (the bet is exchanged at resolve time).

    The 24 h GC sweep would handle this anyway; acting at cog_load
    is just faster recovery.
    """
    try:
        from views.rps._helpers import (
            RPS_PVP_PENDING_SUBSYSTEM,
            RPS_PVP_PENDING_VERSION,
        )

        rows = await game_state_service.list_active_for_subsystem(
            RPS_PVP_PENDING_SUBSYSTEM,
        )
    except Exception as exc:
        logger.warning("rps pvp_pending recovery skipped: %s", exc)
        return
    if not rows:
        return
    cleared = 0
    for row in rows:
        try:
            # Drop both up-to-date and version-mismatched payloads.
            # The view cannot be resumed either way.
            version = row.get("version")
            if version != RPS_PVP_PENDING_VERSION:
                logger.info(
                    "rps_pvp_pending recovery: dropping version-mismatch "
                    "row id=%s (saved=%s, current=%s)",
                    row["id"],
                    version,
                    RPS_PVP_PENDING_VERSION,
                )
            await game_state_service.clear_by_id(row["id"])
            cleared += 1
        except Exception as exc:
            logger.warning(
                "rps_pvp_pending recovery: clear failed for id=%s: %s",
                row.get("id"),
                exc,
            )
    if cleared:
        logger.info(
            "rps_pvp_pending recovery: cleared %d stranded match(es)",
            cleared,
        )


# ---------------------------------------------------------------------------
# on_guild_remove — clear both subsystems for a departed guild
# ---------------------------------------------------------------------------


async def on_guild_remove_rps(guild_id: int) -> None:
    """Wipe rps subsystem rows for a departed guild.

    rps_pvp_pending rows clear without refund (no pre-debit).
    rps_tournament rows trigger refunds — guild removal mid-
    tournament is equivalent to a crash from the player's
    perspective.
    """
    # rps_pvp_pending — clear, no refund.
    try:
        from views.rps._helpers import RPS_PVP_PENDING_SUBSYSTEM

        rows = await game_state_service.list_active_for_subsystem(
            RPS_PVP_PENDING_SUBSYSTEM,
            guild_id=guild_id,
        )
        for row in rows:
            try:
                await game_state_service.clear_by_id(row["id"])
            except Exception as exc:
                logger.warning(
                    "rps_pvp_pending on_guild_remove: clear id=%s failed: %s",
                    row.get("id"),
                    exc,
                )
    except Exception as exc:
        logger.warning(
            "rps_pvp_pending on_guild_remove failed for guild=%d: %s",
            guild_id,
            exc,
        )

    # rps_tournament — refund + clear.
    try:
        rows = await game_state_service.list_active_for_subsystem(
            RPS_TOURNAMENT_SUBSYSTEM,
            guild_id=guild_id,
        )
        for row in rows:
            state = row.get("state") or {}
            bet = state.get("bet")
            if isinstance(bet, int) and bet > 0:
                try:
                    await economy_service.refund(
                        guild_id=row["guild_id"],
                        user_id=row["user_id"],
                        amount=bet,
                        reason="rps_tournament:guild_remove_refund",
                    )
                except Exception as exc:
                    logger.warning(
                        "rps_tournament on_guild_remove refund failed for user=%d: %s",
                        row.get("user_id"),
                        exc,
                    )
            try:
                await game_state_service.clear_by_id(row["id"])
            except Exception as exc:
                logger.warning(
                    "rps_tournament on_guild_remove: clear id=%s failed: %s",
                    row.get("id"),
                    exc,
                )
    except Exception as exc:
        logger.warning(
            "rps_tournament on_guild_remove failed for guild=%d: %s",
            guild_id,
            exc,
        )
