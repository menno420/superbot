"""PR M3 — MiningCog refuses DM invocations.

Once the CRUD started requiring ``guild_id``, any mining command run in
a DM (where ``ctx.guild`` is None) would crash on ``ctx.guild.id``.
The cog uses ``cog_check`` to convert that into a clean refusal via
``commands.NoPrivateMessage`` — discord.py's own check-failure type
that produces "this command cannot be used in private messages".

The PersistentView button handlers add a defensive
``interaction.guild_id is None`` guard for the same reason; those are
covered by inspection here because spinning up a real interaction
harness is out of scope for unit tests.
"""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock

import pytest
from discord.ext import commands

# Import the cog module; do NOT instantiate it (instantiation requires
# a Bot).  ``cog_check`` is a bound coroutine method that we can call
# directly.


@pytest.mark.asyncio
async def test_cog_check_raises_noprivatemessage_in_dm():
    """The DM guard is implemented via ``cog_check`` raising
    ``commands.NoPrivateMessage``.  bot1.on_command_error handles this
    error class and emits a graceful user-facing reply.
    """
    from cogs.mining_cog import MiningCog

    cog = MiningCog.__new__(MiningCog)  # bypass __init__ — we don't need bot/recipes
    ctx = MagicMock()
    ctx.guild = None  # DM context
    with pytest.raises(commands.NoPrivateMessage):
        await cog.cog_check(ctx)


@pytest.mark.asyncio
async def test_cog_check_passes_in_guild():
    from cogs.mining_cog import MiningCog

    cog = MiningCog.__new__(MiningCog)
    ctx = MagicMock()
    ctx.guild = MagicMock(id=999)
    assert await cog.cog_check(ctx) is True


def test_persistent_view_button_handlers_check_guild_id():
    """Every MiningHubView button that touches the DB must guard
    against ``interaction.guild_id is None`` before reading.  This
    asserts the presence of the guard in source so a future refactor
    can't drop it silently.
    """
    from cogs import mining_cog

    src = inspect.getsource(mining_cog.MiningHubView)
    # The five DB-touching buttons share the same pattern.
    for btn in (
        "mine_btn",
        "harvest_btn",
        "explore_btn",
        "inventory_btn",
        "stats_btn",
    ):
        # Find the function block.
        assert f"async def {btn}(" in src, f"{btn} not found in source"
    # The guard string appears for each button.  Count must match the
    # five DB-touching buttons.
    guard_occurrences = src.count("interaction.guild_id is None")
    assert guard_occurrences >= 5, (
        f"Expected at least 5 ``interaction.guild_id is None`` guards "
        f"in MiningHubView; found {guard_occurrences}.  Each DB-touching "
        "button must guard against DM invocations."
    )


def test_build_modal_guards_dm():
    # S4.1 — _BuildModal was extracted from cogs.mining_cog to
    # views.mining.main_panel as part of the cog decomposition.
    from views.mining import main_panel

    src = inspect.getsource(main_panel._BuildModal)
    assert "interaction.guild_id is None" in src, (
        "_BuildModal.on_submit must guard against DM invocations — "
        "the modal can fire after a button click in any context."
    )
