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


def _top_level_command_claims() -> dict[str, list[str]]:
    """Map every top-level prefix-command token -> the *commands* that claim it.

    A "token" is a command's ``name`` or one of its ``aliases``. discord.py's
    ``Bot`` keeps a single global namespace for top-level prefix commands
    (``Bot.all_commands`` is keyed by name *and* every alias), so two *distinct
    commands* that each claim the same token collide at ``add_cog`` — whether
    they live in the same cog or in two different cogs. Group **subcommands**
    live in their group's own namespace (e.g. ``!karma add`` is scoped to the
    ``karma`` group, not the global table), so only commands with no parent are
    global and are counted here.

    Each claimant is labelled ``"<CogName>.<command>"`` and de-duplicated by
    command **identity** (``id``), so a single command claiming a token through
    both its name and one of its own aliases counts once (no false
    self-collision), while two *different* commands claiming the same token —
    the crash class — surface as two labels.

    Read from each cog's class-level ``__cog_commands__`` via ``importlib`` —
    no Discord runtime, no DB, no cog instantiation.
    """
    # token -> {id(command): "<CogName>.<command>"} — identity-deduped claimants,
    # so name+alias on one command is a single claim but two commands are two.
    claims: dict[str, dict[int, str]] = defaultdict(dict)
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
                label = f"{obj.__name__}.{cmd.name}"
                for token in (cmd.name, *(cmd.aliases or ())):
                    claims[token][id(cmd)] = label
    return {token: sorted(labels.values()) for token, labels in claims.items()}


def test_no_duplicate_top_level_command_tokens() -> None:
    """No two distinct commands may claim the same top-level prefix token.

    (Formerly ``test_no_duplicate_top_level_command_names_across_cogs``;
    broadened 2026-07-01 to also catch *same-cog* collisions — the fishing
    ``dock`` incident below.)

    The "bot offline" class has two shapes, both of which crash
    ``bot.load_extension`` at boot with the *same*
    ``CommandRegistrationError: The command <x> is already an existing command
    or alias`` → the cog's declared entry points go missing → STRICT
    identity-contract aborts startup → crash loop, never reaching the gateway:

    * **cross-cog** (2026-06-29): two cogs each declared a top-level ``give``
      (economy peer-transfer vs mining admin grant).
    * **same-cog** (2026-07-01): inside ``FishingCog`` the new ``!dock``
      structure command's *name* collided with the pre-existing ``dock``
      *alias* of ``!sail``. The first guard version de-duplicated claimants by
      **cog**, so one cog claiming a token twice looked like a single claimant
      and slipped through — the exact hole this version closes by counting
      distinct **commands**. (Q-0200's exact-name guard is same-*module* only
      and matches ``def`` names, so it too missed a name-vs-alias clash.)

    The runtime ``command_surface_ledger`` only sees duplicates *after* every
    cog has loaded, which is exactly what a collision prevents — so it cannot
    catch either shape. This static check does, pre-merge. A failure here means
    the bot would crash on boot: rename or remove one side of each listed clash.
    """
    collisions = {
        token: claimants
        for token, claimants in _top_level_command_claims().items()
        if len(claimants) > 1
    }
    assert not collisions, (
        "Top-level prefix command token claimed by more than one command — "
        "this crashes bot.load_extension at boot (CommandRegistrationError):\n"
        + "\n".join(
            f"  !{token}: {', '.join(claimants)}"
            for token, claimants in sorted(collisions.items())
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
    :func:`_top_level_command_claims` (global-namespace collisions only), the ban
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
