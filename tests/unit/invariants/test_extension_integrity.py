"""Invariant: every ``config.INITIAL_EXTENSIONS`` entry is importable and exposes
an awaitable ``setup``.

The "boot caught it, CI didn't" gap (previous-session Q-0089 idea, 2026-06-21): the
cog list is a plain string tuple, so a typo in an entry, a module that fails to
import, or a cog missing an ``async def setup(bot)`` would only surface at **boot**
(``bot.load_extension`` raises), not in CI. discord.py's loader requires each
extension module to define a coroutine ``setup`` — this test asserts exactly that
for every listed extension, catching the whole class pre-merge.

Pure + stdlib (``importlib`` + ``inspect``); no Discord runtime, no DB.
"""

from __future__ import annotations

import importlib
import inspect
from collections import defaultdict

import pytest

import config
from discord.ext import commands


@pytest.mark.parametrize("extension", config.INITIAL_EXTENSIONS)
def test_extension_is_importable_with_coroutine_setup(extension: str) -> None:
    try:
        module = importlib.import_module(extension)
    except Exception as exc:  # pragma: no cover - the failure message is the value
        pytest.fail(
            f"config.INITIAL_EXTENSIONS entry {extension!r} failed to import "
            f"(would crash bot.load_extension at boot): {exc!r}",
        )

    setup = getattr(module, "setup", None)
    assert setup is not None, (
        f"extension {extension!r} defines no module-level `setup` — "
        "discord.py's load_extension requires `async def setup(bot)`."
    )
    assert inspect.iscoroutinefunction(setup), (
        f"extension {extension!r} has a `setup` that is not a coroutine function — "
        "discord.py requires `async def setup(bot)` (a sync setup raises at boot)."
    )


def _top_level_command_tokens() -> dict[str, list[str]]:
    """Map every top-level prefix-command token -> the cogs that declare it.

    A "token" is a command's ``name`` or one of its ``aliases``. discord.py's
    ``Bot`` keeps a single global namespace for top-level prefix commands
    (``Bot.all_commands`` is keyed by name *and* every alias), so two cogs that
    each claim the same token collide. Group **subcommands** live in their
    group's own namespace (e.g. ``!karma add`` is scoped to the ``karma`` group,
    not the global table), so only commands with no parent are global and are
    counted here.

    Read from each cog's class-level ``__cog_commands__`` via ``importlib`` —
    no Discord runtime, no DB, no cog instantiation.
    """
    tokens: dict[str, list[str]] = defaultdict(list)
    for extension in config.INITIAL_EXTENSIONS:
        module = importlib.import_module(extension)
        for _name, obj in inspect.getmembers(module, inspect.isclass):
            # Only cogs *defined in this module* — skip imported base classes
            # so a shared base's commands are not double-counted.
            if not issubclass(obj, commands.Cog) or obj is commands.Cog:
                continue
            if obj.__module__ != module.__name__:
                continue
            for cmd in getattr(obj, "__cog_commands__", ()):
                if getattr(cmd, "parent", None) is not None:
                    continue  # subcommand — namespaced under its group
                for token in (cmd.name, *(cmd.aliases or ())):
                    tokens[token].append(obj.__name__)
    return tokens


def test_no_duplicate_top_level_command_names_across_cogs() -> None:
    """No two cogs may claim the same top-level prefix command name/alias.

    The "bot offline" class (2026-06-29): two cogs each declared a top-level
    ``give`` (economy's peer-transfer vs mining's admin grant). At boot the
    second ``add_cog`` raised ``CommandRegistrationError: The command give is
    already an existing command or alias``, so the whole cog failed to load,
    its declared entry points went missing, and the STRICT identity-contract
    check aborted startup — a crash loop, never reaching the gateway.

    The runtime ``command_surface_ledger`` only sees duplicates *after* every
    cog has loaded, which is exactly what a collision prevents — so it cannot
    catch this. This static check does, pre-merge. A failure here means the
    bot would crash on boot: rename or remove one side of each listed clash.
    """
    collisions = {
        token: sorted(set(cogs))
        for token, cogs in _top_level_command_tokens().items()
        if len(set(cogs)) > 1
    }
    assert not collisions, (
        "Top-level prefix command name/alias claimed by more than one cog — "
        "this crashes bot.load_extension at boot (CommandRegistrationError):\n"
        + "\n".join(
            f"  !{token}: {', '.join(cogs)}" for token, cogs in sorted(collisions.items())
        )
    )


#: Command names/aliases that are permanently banned from the prefix surface.
#: Owner directive (2026-06-29): after a ``give`` collision took the bot offline,
#: "remove every give command and make sure none is ever added again." ``give`` is
#: a generic, high-collision verb (economy peer-transfer, mining admin grant,
#: karma point — all three existed at once); it is retired surface-wide. Use a
#: specific verb instead (e.g. ``add`` / ``grant`` / ``transfer``).
BANNED_COMMAND_TOKENS = frozenset({"give"})


def _walk_cog_commands(cog_cls: type) -> list[object]:
    """Every command a cog declares, recursing into groups (subcommands too).

    ``__cog_commands__`` holds the cog's top-level commands; a group's children
    are reached via the group's ``commands`` attribute. Unlike
    :func:`_top_level_command_tokens` (global-namespace collisions only), the ban
    applies to **every** command including subcommands like ``!karma give``.
    """
    out: list[object] = []
    seen: set[int] = set()

    def _recurse(cmd: object) -> None:
        if id(cmd) in seen:
            return
        seen.add(id(cmd))
        out.append(cmd)
        for sub in getattr(cmd, "commands", ()) or ():
            _recurse(sub)

    for cmd in getattr(cog_cls, "__cog_commands__", ()):
        _recurse(cmd)
    return out


def test_no_banned_command_tokens_anywhere() -> None:
    """No command (top-level or subcommand) may use a banned name/alias.

    Enforces the owner directive that retired ``give`` surface-wide (2026-06-29):
    a ``give`` collision crash-looped the bot, so the verb is banned outright, not
    just de-duplicated. This catches a re-introduction at CI — under any cog, as a
    primary name *or* an alias, at any nesting depth — before it can ship.
    """
    offenders: list[str] = []
    for extension in config.INITIAL_EXTENSIONS:
        module = importlib.import_module(extension)
        for _name, obj in inspect.getmembers(module, inspect.isclass):
            if not issubclass(obj, commands.Cog) or obj is commands.Cog:
                continue
            if obj.__module__ != module.__name__:
                continue
            for cmd in _walk_cog_commands(obj):
                for token in (cmd.name, *(cmd.aliases or ())):
                    if token in BANNED_COMMAND_TOKENS:
                        kind = "name" if token == cmd.name else "alias"
                        offenders.append(
                            f"  {kind} {token!r} on !{cmd.qualified_name} "
                            f"({obj.__name__} in {extension})"
                        )
    assert not offenders, (
        "Banned command token(s) found — these names are retired surface-wide "
        f"({', '.join(sorted(BANNED_COMMAND_TOKENS))}); use a specific verb "
        "(add / grant / transfer) instead:\n" + "\n".join(offenders)
    )
