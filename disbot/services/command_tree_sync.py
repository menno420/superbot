"""Diff-gated startup auto-sync of the application-command tree.

After a command change (e.g. the BTD6 unification, #1419) Discord's registered
slash commands lag the bot's local tree until someone runs ``!syncslash``. This
service closes that gap automatically **and safely**: on startup it fetches the
live global commands from Discord and compares their *structure* — the set of
qualified command paths — to the local tree, and calls ``tree.sync()`` **only**
when they differ. An unchanged tree never burns a (rate-limited) global sync.

Conservative on purpose: it compares command **paths** (add / remove / rename of
commands and subcommands), not parameter or description details, because Discord
normalises option payloads and a fuller comparison would false-positive and
re-sync on every boot. Parameter/description-only changes still use manual
``!syncslash``. This bias — *miss a cosmetic change rather than re-sync every
boot* — is deliberate: an auto sync that fires spuriously would be worse than
none (it would chew the global-sync rate limit).

Wiring: called once per process from ``bot1.on_ready`` (reconnect-safe one-shot).
Kill-switch: ``AUTO_SYNC_COMMANDS=0`` (env; default on). Every failure path is
non-fatal — a fetch or sync error is logged and reported, never raised, so it
cannot crash startup.

Reliability (Q-0105): **unverified** — added 2026-06-24; confirm it fires
correctly across a few real deploys before fully trusting it (the kill-switch +
manual ``!syncslash`` remain the backstop). Delete this seam if it proves flaky.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass

import discord
from discord import app_commands

logger = logging.getLogger("bot.command_sync")

# Option types that denote a *nested command* (vs. a parameter) on a fetched
# AppCommand — used to walk the remote tree to the same leaf paths as the local.
_SUBCOMMAND_TYPES = {
    discord.AppCommandOptionType.subcommand,
    discord.AppCommandOptionType.subcommand_group,
}


def env_enabled(raw: str | None) -> bool:
    """Parse the ``AUTO_SYNC_COMMANDS`` flag — default-on; only explicit falsy
    strings disable (mirrors the ``BTD6_AUTO_SEED`` convention: unset/empty = on).
    """
    return (raw or "").strip().lower() not in ("0", "false", "no", "off")


def _local_paths(commands: Iterable[object], prefix: str = "") -> set[str]:
    """Qualified command paths for the LOCAL tree (``Command`` / ``Group``)."""
    out: set[str] = set()
    for cmd in commands:
        path = f"{prefix}{cmd.name}"  # type: ignore[attr-defined]
        out.add(path)
        if isinstance(cmd, app_commands.Group):
            out |= _local_paths(cmd.commands, prefix=f"{path} ")
    return out


def _remote_paths(commands: Iterable[object], prefix: str = "") -> set[str]:
    """Qualified command paths for the REMOTE tree (fetched ``AppCommand`` objects).

    ``AppCommand`` and ``AppCommandGroup`` both expose ``.name`` + ``.options``;
    an option is a nested command iff its ``.type`` is a (sub)command type — a
    parameter has a value type and is skipped — so the same recursion reaches the
    same leaf paths the local walk produces.
    """
    out: set[str] = set()
    for cmd in commands:
        path = f"{prefix}{cmd.name}"  # type: ignore[attr-defined]
        out.add(path)
        subs = [
            opt
            for opt in (getattr(cmd, "options", None) or [])
            if getattr(opt, "type", None) in _SUBCOMMAND_TYPES
        ]
        out |= _remote_paths(subs, prefix=f"{path} ")
    return out


@dataclass(frozen=True)
class SyncOutcome:
    """What the auto-sync did, for logging + tests (it never raises)."""

    synced: bool
    reason: str  # disabled | fetch_failed | unchanged | sync_failed | synced
    added: tuple[str, ...] = ()  # paths now present locally but not on Discord
    removed: tuple[str, ...] = ()  # paths on Discord but gone locally


async def auto_sync_if_changed(bot: object, *, enabled: bool) -> SyncOutcome:
    """Sync the global command tree iff its paths differ from Discord's.

    Returns a :class:`SyncOutcome`; never raises (a fetch/sync failure is logged
    and reported so it cannot crash startup).
    """
    if not enabled:
        logger.debug("auto-sync: disabled via AUTO_SYNC_COMMANDS")
        return SyncOutcome(False, "disabled")

    tree = bot.tree  # type: ignore[attr-defined]
    try:
        local = _local_paths(tree.get_commands())
        remote = _remote_paths(await tree.fetch_commands())
    except Exception:
        logger.warning("auto-sync: fetch/compare failed (non-fatal)", exc_info=True)
        return SyncOutcome(False, "fetch_failed")

    if local == remote:
        logger.info(
            "auto-sync: command tree already in sync (%d commands) — skipped",
            len(local),
        )
        return SyncOutcome(False, "unchanged")

    added = tuple(sorted(local - remote))
    removed = tuple(sorted(remote - local))
    try:
        synced = await tree.sync()
    except discord.HTTPException as exc:
        logger.warning("auto-sync: tree.sync() failed (non-fatal): %s", exc)
        return SyncOutcome(False, "sync_failed", added, removed)

    logger.info(
        "auto-sync: tree changed (+%d/-%d) — synced %d global commands. "
        "added=%s removed=%s",
        len(added),
        len(removed),
        len(synced),
        list(added[:8]),
        list(removed[:8]),
    )
    return SyncOutcome(True, "synced", added, removed)
