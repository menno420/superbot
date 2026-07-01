"""Invariant: the bot actually boots — every ``config.INITIAL_EXTENSIONS`` entry
loads onto a real ``commands.Bot`` without raising.

**Why this exists (two prod outages, same class).** Twice a merged change took the
`worker` into a boot crash loop by making a cog fail to load at ``add_cog``:

* the ``give`` collision (2026-06-29, #1541) — two cogs claimed the same top-level
  command name; and
* the ``dock`` collision (2026-07-01, #1599) — a new ``!dock`` command name clashed
  with ``!sail``'s ``dock`` **alias** *inside the same cog*.

Both surfaced only at boot (``discord.py`` raises ``CommandRegistrationError`` when
the second claimant registers), never in CI — the formatters, mypy, the unit suite,
the arch check, and the command-surface ledger all stayed green because **none of
them load the cogs onto a bot the way startup does**. The static
``test_extension_integrity`` guard catches the *command-token* subclass, but a
static AST scan can't see everything ``add_cog`` rejects.

This test closes the whole class at the root: it constructs a bot mirroring
``bot1`` (``help_command=None``, ``case_insensitive=True``) and loads **every**
extension, exactly as ``bot1._load_cogs`` does — so *any* boot-breaking load
failure (a command/alias collision, a bad import, a raising ``cog_load``, a
duplicate app-command) fails **here, pre-merge**, instead of in production.

Offline + no DB / no gateway: ``add_cog`` command registration is synchronous and
network-free. The only runtime concession is that cog ``@tasks.loop`` background
loops (which call ``wait_until_ready``) are prevented from auto-starting — they play
no part in the load/registration path this guards, and need a live gateway.
"""

from __future__ import annotations

import asyncio

import discord
import pytest
from discord.ext import commands, tasks

import config
from core.runtime import tasks as runtime_tasks


@pytest.mark.asyncio
async def test_every_initial_extension_loads_onto_a_bot(monkeypatch) -> None:
    """Load all of ``config.INITIAL_EXTENSIONS`` — assert none fail (== the bot boots).

    A failure here is a **boot-breaking** change: the listed extension would raise
    at ``bot.load_extension`` on startup, its subsystem's entry-point commands would
    go missing, and the STRICT identity-contract would abort the whole boot (a crash
    loop, never reaching the gateway). Rename/remove the colliding command or alias,
    or fix the import, before merging.
    """
    # Cog task-loops auto-start on ``add_cog`` and call ``wait_until_ready`` — they
    # need a live gateway and are irrelevant to the load/registration path this
    # guards. Neutralise ``start`` so loading a cog never spins one up.
    monkeypatch.setattr(tasks.Loop, "start", lambda self, *args, **kwargs: self)

    # Some cogs schedule a ``core.runtime.tasks.spawn`` background task on load
    # (e.g. a ``wait_until_ready`` warm-up). Those also need a live gateway and are
    # not part of the registration path; neutralise ``spawn`` so it schedules
    # nothing but still returns an awaitable callers can store.
    def _no_spawn(name, coro, *args, **kwargs):
        coro.close()  # avoid an un-awaited-coroutine warning
        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        fut.set_result(None)
        return fut

    monkeypatch.setattr(runtime_tasks, "spawn", _no_spawn)

    # Mirror bot1's construction exactly (disbot/bot1.py): the default help command
    # is disabled (``help_command=None``) and commands resolve case-insensitively —
    # both change the command namespace, so a faithful collision check needs them.
    intents = discord.Intents.all()
    bot = commands.Bot(
        command_prefix=config.PREFIX,
        intents=intents,
        help_command=None,
        case_insensitive=True,
    )

    failures: dict[str, str] = {}
    for ext in config.INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(ext)
        except Exception as exc:  # noqa: BLE001 - the failure message is the value
            failures[ext] = f"{type(exc).__name__}: {exc}"

    assert not failures, (
        "Extension(s) fail to load onto a bot — this crashes startup "
        "(the bot would boot-loop, never reaching the gateway):\n"
        + "\n".join(f"  {ext}: {err}" for ext, err in sorted(failures.items()))
    )
