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

import pytest

import config


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
