"""Invariant: the bot actually boots — every ``config.INITIAL_EXTENSIONS`` entry
loads onto a real ``commands.Bot`` without raising.

**Why this exists (two prod outages, same class).** Twice a merged change took the
`worker` into a boot crash loop by making a cog fail to load at ``add_cog``:

* the ``give`` collision (2026-06-29, #1541) — two cogs claimed the same top-level
  command name; and
* the ``dock`` collision (2026-07-01, #1599 → BUG-0030) — a new ``!dock`` command
  name clashed with ``!sail``'s ``dock`` **alias** *inside the same cog*.

Both surfaced only at boot (``discord.py`` raises ``CommandRegistrationError`` when
the second claimant registers), never in CI — the formatters, mypy, the unit suite,
the arch check, and the command-surface ledger all stayed green because **none of
them load the cogs onto a bot the way startup does**. The static
``test_extension_integrity`` guard catches the *command-token* subclass; this test
closes the whole class: *any* boot-breaking load failure (a command/alias collision,
a bad import, a raising ``cog_load``, a duplicate app-command) fails here, pre-merge.

**Why a subprocess.** Loading every cog into the pytest process is not hermetic —
cogs register EventBus subscriptions, module-level singletons, and other global
state that leaks into unrelated tests by run order. Booting in a fresh interpreter
is both the correct isolation *and* the more faithful "does a clean process boot?"
check. It is offline: ``add_cog`` command registration is synchronous and
network-free (no DB, no gateway); cog ``@tasks.loop``s and ``core.runtime.tasks``
background tasks (which need a live gateway) are neutralised so only the
load/registration path runs.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]

# Runs in a fresh interpreter (argv[1] = repo root). Mirrors bot1's construction
# (help_command=None, case_insensitive=True — both change the command namespace),
# neutralises the gateway-dependent background schedulers, loads every extension,
# and exits non-zero (printing the offenders) if any fails to load.
_BOOT_PROBE = r"""
import sys, os, asyncio
sys.path.insert(0, os.path.join(sys.argv[1], "disbot"))
import discord
from discord.ext import commands, tasks
import config
from core.runtime import tasks as runtime_tasks

# Cog @tasks.loop + core.runtime.tasks.spawn background tasks need a live gateway
# (they call wait_until_ready) and are not part of the load/registration path.
tasks.Loop.start = lambda self, *a, **k: self


def _no_spawn(name, coro, *a, **k):
    coro.close()  # avoid an un-awaited-coroutine warning
    fut = asyncio.get_event_loop().create_future()
    fut.set_result(None)
    return fut


runtime_tasks.spawn = _no_spawn


async def main():
    bot = commands.Bot(
        command_prefix=config.PREFIX,
        intents=discord.Intents.all(),
        help_command=None,
        case_insensitive=True,
    )
    failures = {}
    for ext in config.INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(ext)
        except Exception as exc:  # the failure message is the value
            failures[ext] = f"{type(exc).__name__}: {exc}"
    for ext, err in sorted(failures.items()):
        print(f"{ext}: {err}")
    sys.exit(1 if failures else 0)


asyncio.run(main())
"""


def test_every_initial_extension_loads_onto_a_bot() -> None:
    """Load all of ``config.INITIAL_EXTENSIONS`` in a fresh process — assert the
    bot boots.

    A failure here is a **boot-breaking** change: the listed extension would raise
    at ``bot.load_extension`` on startup, its subsystem's entry-point commands would
    go missing, and the STRICT identity-contract would abort the whole boot (a crash
    loop, never reaching the gateway). Rename/remove the colliding command or alias,
    or fix the import, before merging.
    """
    proc = subprocess.run(
        [sys.executable, "-c", _BOOT_PROBE, str(_REPO_ROOT)],
        capture_output=True,
        text=True,
        timeout=240,
    )
    assert proc.returncode == 0, (
        "Extension(s) fail to load onto a bot — this crashes startup (the bot "
        "would boot-loop, never reaching the gateway):\n"
        + (proc.stdout or "")
        + (f"\n[stderr]\n{proc.stderr}" if proc.returncode != 1 else "")
    )
