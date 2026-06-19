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
    """Every MiningHubView button that touches the DB (or opens a sub-hub that
    will) must guard against ``interaction.guild_id is None`` before acting.
    This asserts the guard's presence in source so a future refactor can't drop
    it silently. Updated for the Option A 6-button hub (declutter PR2,
    2026-06-19): Inventory / Stats moved into the Character sub-hub.
    """
    from cogs import mining_cog

    src = inspect.getsource(mining_cog.MiningHubView)
    # The six Option A top-level buttons; all guard before acting.
    for btn in (
        "mine_btn",
        "harvest_btn",
        "explore_btn",
        "character_btn",
        "gear_btn",
        "workshop_btn",
    ):
        assert f"async def {btn}(" in src, f"{btn} not found in source"
    # The guard string appears for each button — six on the main hub.
    guard_occurrences = src.count("interaction.guild_id is None")
    assert guard_occurrences >= 6, (
        f"Expected at least 6 ``interaction.guild_id is None`` guards "
        f"in MiningHubView; found {guard_occurrences}.  Each top-level "
        "button must guard against DM invocations."
    )


def test_character_and_explore_subhub_handlers_check_guild_id():
    """The Character sub-hub's DB-touching buttons guard against DMs just like
    the main hub (the moved Inventory / Stats / Overview etc.). The Explore
    stub doesn't read the DB, so it needs no guild guard.
    """
    from views.mining import character_hub

    src = inspect.getsource(character_hub.MiningCharacterHubView)
    for btn in ("overview_btn", "inventory_btn", "stats_btn", "skills_btn",
                "vault_btn", "home_btn"):
        assert f"async def {btn}(" in src, f"{btn} not found in source"
    # Six DB-touching sub-hub buttons each carry the guard.
    assert src.count("interaction.guild_id is None") >= 6


def test_build_modal_guards_dm():
    # S4.1 — _BuildModal was extracted from cogs.mining_cog to
    # views.mining.main_panel as part of the cog decomposition.
    from views.mining import main_panel

    src = inspect.getsource(main_panel._BuildModal)
    assert "interaction.guild_id is None" in src, (
        "_BuildModal.on_submit must guard against DM invocations — "
        "the modal can fire after a button click in any context."
    )
