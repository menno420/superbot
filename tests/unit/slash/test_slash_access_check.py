"""PR-5 — slash command admission via the bootstrap cog's
``tree.interaction_check``.

Pins the slash-side mirror of the prefix admission contract:

* :func:`setup` installs the cog's bound ``_slash_access_check`` on
  ``bot.tree.interaction_check``.
* :meth:`BootstrapAccessCog.cog_unload` restores ``tree.interaction_check``
  to a trivial always-allow coroutine (matches discord.py's default
  semantics) so a hot-reload doesn't leave a stale bound method
  pinned to a previous cog instance.
* The check delegates to ``resolve_command_access`` via the
  interaction adapter; allow paths return ``True`` and never touch
  the interaction response.
* Denials post **ephemeral** feedback so only the invoker sees the
  policy reason; lifecycle / DM denials stay silent.
* Bootstrap slash commands (incl. hyphenated ``setup-hub`` etc.) keep
  their operator-only bypass under restrictive modes.
* When the interaction's initial response is already consumed (rare),
  the helper falls back to ``followup.send`` so we don't 404 the
  invoker.
* ``send_message`` failures (channel deleted, missing perms) are
  swallowed — the check still returns False rather than propagating
  into the app-command dispatcher.

The resolver's policy lookup is stubbed via
``utils.guild_config_accessors.get_command_access_policy`` so the
tests are asyncpg-free.  Each test patches a fresh
:class:`CommandAccessPolicySnapshot` for the scenario.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from discord.ext import commands

from cogs.bootstrap_access_cog import BootstrapAccessCog, setup
from utils.guild_config_accessors import CommandAccessPolicySnapshot

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_bot():
    """Build a ``commands.Bot`` mock that exposes ``tree.interaction_check``
    as a writable attribute the way discord.py does.
    """
    bot = MagicMock(spec=commands.Bot)
    bot._checks = []
    bot.remove_check = MagicMock(side_effect=bot._checks.remove)
    bot.add_check = MagicMock(side_effect=bot._checks.append)
    bot.add_cog = AsyncMock()
    # Real attribute so ``getattr(bot, "tree", None)`` returns a stable
    # object the tests can inspect.  ``interaction_check`` starts as
    # ``None`` so the test can tell the difference between "before
    # setup" and "after setup".
    bot.tree = SimpleNamespace(interaction_check=None)
    return bot


def _make_interaction(
    *,
    guild_id: int | None = 10,
    channel_id: int | None = 100,
    user_id: int = 42,
    owner_id: int = 42,
    administrator: bool = False,
    command_qualified_name: str | None = "blackjack",
    is_bot_owner: bool = False,
    response_done: bool = False,
):
    guild = (
        SimpleNamespace(id=guild_id, owner_id=owner_id)
        if guild_id is not None
        else None
    )
    channel = SimpleNamespace(id=channel_id) if channel_id is not None else None
    user = SimpleNamespace(
        id=user_id,
        guild_permissions=SimpleNamespace(
            administrator=administrator,
            manage_guild=False,
        ),
    )
    if command_qualified_name is None:
        command = None
    else:
        command = SimpleNamespace(
            name=command_qualified_name.split()[0],
            qualified_name=command_qualified_name,
        )
    response = SimpleNamespace(
        is_done=MagicMock(return_value=response_done),
        send_message=AsyncMock(),
    )
    followup = SimpleNamespace(send=AsyncMock())
    client = SimpleNamespace(is_owner=AsyncMock(return_value=is_bot_owner))
    return SimpleNamespace(
        guild=guild,
        channel=channel,
        user=user,
        command=command,
        response=response,
        followup=followup,
        client=client,
    )


def _patch_policy(monkeypatch, mode: str | None, *allowed_channels: int) -> None:
    snapshot = CommandAccessPolicySnapshot(
        mode=mode,
        allowed_channels=frozenset(allowed_channels),
    )
    monkeypatch.setattr(
        "utils.guild_config_accessors.get_command_access_policy",
        AsyncMock(return_value=snapshot),
    )


# ---------------------------------------------------------------------------
# setup() installs the tree gate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_setup_installs_tree_interaction_check():
    bot = _make_bot()
    await setup(bot)
    cog = bot.add_cog.await_args.args[0]
    assert isinstance(cog, BootstrapAccessCog)
    # The installed attribute is the cog's bound method.
    # Bound methods are not ``is``-identical across attribute lookups;
    # compare the underlying function + bound instance instead.
    assert bot.tree.interaction_check.__func__ is BootstrapAccessCog._slash_access_check
    assert bot.tree.interaction_check.__self__ is cog


@pytest.mark.asyncio
async def test_setup_overwrites_remnant_from_previous_bootstrap_cog():
    """Reload from a previous BootstrapAccessCog leaves the old bound
    method on ``tree.interaction_check``.  ``setup()`` overwrites it
    with the new cog's method so the gate isn't pinned to a stale
    instance with stale closures.
    """
    bot = _make_bot()
    prev_cog = BootstrapAccessCog(bot)
    bot.tree.interaction_check = prev_cog._slash_access_check

    await setup(bot)

    new_cog = bot.add_cog.await_args.args[0]
    assert bot.tree.interaction_check.__func__ is BootstrapAccessCog._slash_access_check
    assert bot.tree.interaction_check.__self__ is new_cog
    assert bot.tree.interaction_check.__self__ is not prev_cog


# ---------------------------------------------------------------------------
# cog_unload restores the default
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cog_unload_restores_default_interaction_check():
    """After ``cog_unload`` the tree's interaction_check must not still
    point at the dead cog instance.  Restored to a trivial always-True
    coroutine that mirrors discord.py's default semantics; the next
    setup() can overwrite it again without spurious warnings.
    """
    from cogs.bootstrap_access_cog import _default_interaction_check

    bot = _make_bot()
    await setup(bot)
    cog = bot.add_cog.await_args.args[0]
    # Bound methods are not ``is``-identical across attribute lookups;
    # compare the underlying function + bound instance instead.
    assert bot.tree.interaction_check.__func__ is BootstrapAccessCog._slash_access_check
    assert bot.tree.interaction_check.__self__ is cog

    cog.cog_unload()
    assert bot.tree.interaction_check is _default_interaction_check


@pytest.mark.asyncio
async def test_cog_unload_does_not_clobber_third_party_check():
    """If a downstream cog later overwrote our installed check with
    its own value, ``cog_unload`` must leave that value alone — we
    only own the slot while it points at our own bound method.
    """
    bot = _make_bot()
    await setup(bot)
    cog = bot.add_cog.await_args.args[0]
    third_party = AsyncMock(return_value=True)
    bot.tree.interaction_check = third_party

    cog.cog_unload()
    assert bot.tree.interaction_check is third_party


# ---------------------------------------------------------------------------
# Resolver delegation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slash_check_allows_under_default_all_channels(monkeypatch):
    """Unconfigured guild — resolver returns the safe default
    (``all_channels``), so any slash command runs anywhere.
    """
    _patch_policy(monkeypatch, mode=None)
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    interaction = _make_interaction(channel_id=999, command_qualified_name="blackjack")

    assert await cog._slash_access_check(interaction) is True
    interaction.response.send_message.assert_not_called()
    interaction.followup.send.assert_not_called()


@pytest.mark.asyncio
async def test_slash_check_allows_inside_selected_channel(monkeypatch):
    _patch_policy(monkeypatch, "selected_channels", 12345)
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    interaction = _make_interaction(channel_id=12345)

    assert await cog._slash_access_check(interaction) is True
    interaction.response.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_slash_check_denies_outside_selected_channel_with_ephemeral_feedback(
    monkeypatch,
):
    """The core slash-side fix: a denied slash command posts a visible
    ephemeral message rather than failing silently.
    """
    _patch_policy(monkeypatch, "selected_channels", 12345)
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    interaction = _make_interaction(channel_id=999)

    assert await cog._slash_access_check(interaction) is False
    interaction.response.send_message.assert_awaited_once()
    _args, kwargs = (
        interaction.response.send_message.await_args.args,
        interaction.response.send_message.await_args.kwargs,
    )
    assert kwargs.get("ephemeral") is True
    # Feedback points at the recovery path.
    message = interaction.response.send_message.await_args.args[0]
    assert "channel" in message.lower() or "settings" in message.lower()


@pytest.mark.asyncio
async def test_slash_check_denies_under_disabled_mode_with_feedback(monkeypatch):
    _patch_policy(monkeypatch, "disabled_except_bootstrap")
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    interaction = _make_interaction()  # non-bootstrap, non-operator

    assert await cog._slash_access_check(interaction) is False
    interaction.response.send_message.assert_awaited_once()
    message = interaction.response.send_message.await_args.args[0]
    assert "!setup" in message or "settings" in message.lower()


# ---------------------------------------------------------------------------
# Bootstrap bypass — slash flavour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slash_check_allows_owner_for_bootstrap_command(monkeypatch):
    _patch_policy(monkeypatch, "disabled_except_bootstrap")
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    interaction = _make_interaction(
        channel_id=999,
        user_id=42,
        owner_id=42,
        command_qualified_name="setup",
    )

    assert await cog._slash_access_check(interaction) is True
    interaction.response.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_slash_check_allows_admin_for_hyphenated_bootstrap_command(monkeypatch):
    """Slash commands forbid whitespace in names, so multi-token
    bootstrap commands ship as hyphenated (``setup-hub``,
    ``setup-status``).  The resolver's
    :func:`is_bootstrap_command` recognises the hyphen-namespaced
    form so admins keep their bypass without each new ``setup-*``
    needing its own allowlist entry.
    """
    _patch_policy(monkeypatch, "selected_channels")
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    interaction = _make_interaction(
        channel_id=999,
        owner_id=42,
        administrator=True,
        command_qualified_name="setup-hub",
    )

    assert await cog._slash_access_check(interaction) is True


@pytest.mark.asyncio
async def test_slash_check_denies_bootstrap_for_non_operator(monkeypatch):
    """Bootstrap bypass is operator-only.  A regular user invoking
    ``/setup`` under a restrictive policy still gets denied with
    feedback (so they know to ask an admin, not so they can self-
    promote).
    """
    _patch_policy(monkeypatch, "selected_channels", 12345)
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    interaction = _make_interaction(
        channel_id=999,
        user_id=99,
        owner_id=42,
        command_qualified_name="setup",
    )

    assert await cog._slash_access_check(interaction) is False
    interaction.response.send_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# Lifecycle drain / DM — silent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slash_check_denies_dm_silently(monkeypatch):
    _patch_policy(monkeypatch, None)
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    interaction = _make_interaction(guild_id=None, channel_id=None)

    assert await cog._slash_access_check(interaction) is False
    interaction.response.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_slash_check_denies_during_lifecycle_drain_silently(monkeypatch):
    """Surfacing a message during shutdown would race the connection
    close; the resolver's lifecycle branch sets ``feedback=None`` and
    this check must respect that by NOT calling send_message.
    """
    from core.runtime import lifecycle

    _patch_policy(monkeypatch, None)
    lifecycle.reset_for_tests()
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("test")
    try:
        cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
        interaction = _make_interaction()

        assert await cog._slash_access_check(interaction) is False
        interaction.response.send_message.assert_not_called()
        interaction.followup.send.assert_not_called()
    finally:
        lifecycle.reset_for_tests()


# ---------------------------------------------------------------------------
# Response-state handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slash_check_uses_followup_when_response_already_done(monkeypatch):
    """If something raced ahead and consumed the initial response,
    ``response.send_message`` would 404; fall back to followup.send
    so the invoker still gets feedback.
    """
    _patch_policy(monkeypatch, "selected_channels")
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    interaction = _make_interaction(response_done=True)

    assert await cog._slash_access_check(interaction) is False
    interaction.response.send_message.assert_not_called()
    interaction.followup.send.assert_awaited_once()
    assert interaction.followup.send.await_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_slash_check_tolerates_send_message_failure(monkeypatch):
    """A ``send_message`` raise (channel deleted, missing perms,
    interaction expired) must not propagate into the app-command
    dispatcher.  Check still returns False.
    """
    _patch_policy(monkeypatch, "selected_channels")
    cog = BootstrapAccessCog(MagicMock(spec=commands.Bot))
    interaction = _make_interaction()
    interaction.response.send_message = AsyncMock(side_effect=RuntimeError("boom"))

    assert await cog._slash_access_check(interaction) is False
