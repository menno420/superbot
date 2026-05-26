"""PR-2 — command-access resolver tests.

Exercises the full decision matrix of
:func:`core.runtime.command_access.resolve_command_access`:

* lifecycle gate (draining → silent deny)
* DM / guildless invocations
* bootstrap bypass for guild operators + bot owners
* unconfigured guild (default ``all_channels`` semantic, source
  ``DEFAULT_UNCONFIGURED``)
* ``all_channels`` mode (allow anywhere)
* ``selected_channels`` mode (allow inside / deny outside, with feedback)
* ``disabled_except_bootstrap`` mode (deny normal commands with feedback,
  bypass still works for bootstrap)

Plus adapters (``from_prefix_ctx`` / ``from_interaction``) that build a
:class:`CommandAccessContext` from Discord-shaped inputs.

Loaders are stubbed via ``patch.object`` on
``utils.guild_config_accessors.get_command_access_policy`` so the
resolver's hot path is exercised without going through the typed
accessor cache or the DB.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from core.runtime import command_access
from core.runtime.command_access import (
    AccessMode,
    CommandAccessContext,
    DecisionReason,
    DecisionSource,
    resolve_command_access,
)
from utils.guild_config_accessors import CommandAccessPolicySnapshot


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _ctx(
    *,
    command_name: str | None = "blackjack",
    invocation_type: str = "prefix",
    guild_id: int | None = 10,
    channel_id: int | None = 100,
    user_id: int | None = 42,
    is_guild_operator: bool = False,
    is_bot_owner: bool = False,
    is_dm: bool = False,
) -> CommandAccessContext:
    return CommandAccessContext(
        guild_id=guild_id,
        channel_id=channel_id,
        user_id=user_id,
        command_name=command_name,
        invocation_type=invocation_type,
        is_guild_operator=is_guild_operator,
        is_bot_owner=is_bot_owner,
        is_dm=is_dm,
    )


def _snapshot(
    mode: str | None,
    *channel_ids: int,
) -> CommandAccessPolicySnapshot:
    return CommandAccessPolicySnapshot(
        mode=mode,
        allowed_channels=frozenset(channel_ids),
    )


def _patch_policy(snapshot: CommandAccessPolicySnapshot):
    """Patch the typed-accessor read used by the resolver.

    The resolver imports ``get_command_access_policy`` lazily from
    ``utils.guild_config_accessors`` inside ``resolve_command_access``,
    so we patch the symbol on that module (not on the resolver) — the
    lazy import then resolves to the patched coroutine.
    """
    return patch(
        "utils.guild_config_accessors.get_command_access_policy",
        new=AsyncMock(return_value=snapshot),
    )


def _patch_lifecycle(*, accepting: bool = True):
    return patch(
        "core.runtime.lifecycle.can_accept_commands",
        return_value=accepting,
    )


# ---------------------------------------------------------------------------
# Lifecycle gate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolver_denies_silently_when_lifecycle_draining():
    """Shutdown / restart phase — every command denied, no feedback
    (feedback would race the connection close).
    """
    with _patch_lifecycle(accepting=False):
        decision = await resolve_command_access(_ctx())
    assert decision.allowed is False
    assert decision.reason is DecisionReason.LIFECYCLE_DRAINING
    assert decision.source is DecisionSource.LIFECYCLE_DENY
    assert decision.mode is None
    assert decision.feedback is None


# ---------------------------------------------------------------------------
# DM / guildless
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolver_denies_dm_invocations_without_feedback():
    """DMs do not flow through this resolver — entry-points route them
    through the per-command DM opt-in instead.  No feedback because
    silence is the existing pre-PR-2 behaviour.
    """
    with _patch_lifecycle():
        decision = await resolve_command_access(
            _ctx(guild_id=None, channel_id=None, is_dm=True),
        )
    assert decision.allowed is False
    assert decision.reason is DecisionReason.DM_NOT_SUPPORTED
    assert decision.source is DecisionSource.DEFAULT_UNCONFIGURED
    assert decision.feedback is None


@pytest.mark.asyncio
async def test_resolver_treats_missing_guild_id_as_dm():
    """Defence-in-depth: even if ``is_dm`` weren't set, ``guild_id=None``
    must reach the DM branch — never fall through to the policy lookup
    where ``guild_id`` would be passed as ``None`` to the DB layer.
    """
    with _patch_lifecycle():
        decision = await resolve_command_access(
            _ctx(guild_id=None, channel_id=100, is_dm=False),
        )
    assert decision.reason is DecisionReason.DM_NOT_SUPPORTED


# ---------------------------------------------------------------------------
# Bootstrap bypass
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bootstrap_command_bypasses_for_guild_operator():
    """Operator (owner / admin / manage_guild) running a bootstrap
    command — admitted regardless of mode or channel.  Policy lookup
    must NOT be consulted (the bypass is unconditional).
    """
    with _patch_lifecycle(), _patch_policy(_snapshot("disabled_except_bootstrap")):
        decision = await resolve_command_access(
            _ctx(command_name="setup", is_guild_operator=True),
        )
    assert decision.allowed is True
    assert decision.reason is DecisionReason.BOOTSTRAP_BYPASS
    assert decision.source is DecisionSource.BOOTSTRAP_BYPASS
    assert decision.feedback is None


@pytest.mark.asyncio
async def test_bootstrap_command_bypasses_for_bot_owner():
    with _patch_lifecycle(), _patch_policy(_snapshot("selected_channels")):
        decision = await resolve_command_access(
            _ctx(
                command_name="syncslash",
                channel_id=999,
                is_bot_owner=True,
            ),
        )
    assert decision.allowed is True
    assert decision.source is DecisionSource.BOOTSTRAP_BYPASS


@pytest.mark.asyncio
async def test_non_operator_cannot_bypass_with_bootstrap_command():
    """Non-operator running a bootstrap command — falls through to
    policy mode.  Under ``selected_channels`` they get denied if not in
    an allowed channel.
    """
    with _patch_lifecycle(), _patch_policy(_snapshot("selected_channels", 100)):
        decision = await resolve_command_access(
            _ctx(command_name="help", channel_id=999),
        )
    assert decision.allowed is False
    assert decision.reason is DecisionReason.CHANNEL_NOT_ALLOWED


@pytest.mark.asyncio
async def test_operator_running_normal_command_does_not_bypass():
    """Operators don't get a blanket bypass — only for bootstrap
    commands.  ``!blackjack`` from the guild owner under
    ``selected_channels`` mode outside the allowlist must still be
    denied.
    """
    with _patch_lifecycle(), _patch_policy(_snapshot("selected_channels", 100)):
        decision = await resolve_command_access(
            _ctx(
                command_name="blackjack",
                channel_id=999,
                is_guild_operator=True,
            ),
        )
    assert decision.allowed is False
    assert decision.reason is DecisionReason.CHANNEL_NOT_ALLOWED


# ---------------------------------------------------------------------------
# Unconfigured guild (default = all_channels)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unconfigured_guild_allows_normal_commands_anywhere():
    """No DB policy row — resolver applies the chosen product default
    (``all_channels``) with source ``DEFAULT_UNCONFIGURED`` so logs
    distinguish "policy says yes" from "no policy, defaulting yes".
    """
    with _patch_lifecycle(), _patch_policy(_snapshot(None)):
        decision = await resolve_command_access(_ctx())
    assert decision.allowed is True
    assert decision.reason is DecisionReason.ALLOWED
    assert decision.source is DecisionSource.DEFAULT_UNCONFIGURED
    assert decision.mode is AccessMode.ALL_CHANNELS
    assert decision.feedback is None


# ---------------------------------------------------------------------------
# all_channels mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_channels_mode_allows_normal_command_anywhere():
    with _patch_lifecycle(), _patch_policy(_snapshot("all_channels")):
        decision = await resolve_command_access(_ctx(channel_id=999))
    assert decision.allowed is True
    assert decision.reason is DecisionReason.ALLOWED
    assert decision.source is DecisionSource.DB_POLICY
    assert decision.mode is AccessMode.ALL_CHANNELS


@pytest.mark.asyncio
async def test_all_channels_mode_allows_slash_invocations_too():
    """Same chain for slash: invocation_type is informational only,
    the policy logic does not branch on it.
    """
    with _patch_lifecycle(), _patch_policy(_snapshot("all_channels")):
        decision = await resolve_command_access(
            _ctx(invocation_type="slash", channel_id=999),
        )
    assert decision.allowed is True


# ---------------------------------------------------------------------------
# selected_channels mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_selected_channels_mode_allows_inside_allowlist():
    with _patch_lifecycle(), _patch_policy(_snapshot("selected_channels", 100, 200)):
        decision = await resolve_command_access(_ctx(channel_id=200))
    assert decision.allowed is True
    assert decision.reason is DecisionReason.ALLOWED
    assert decision.source is DecisionSource.DB_POLICY
    assert decision.mode is AccessMode.SELECTED_CHANNELS


@pytest.mark.asyncio
async def test_selected_channels_mode_denies_outside_with_feedback():
    with _patch_lifecycle(), _patch_policy(_snapshot("selected_channels", 100)):
        decision = await resolve_command_access(_ctx(channel_id=999))
    assert decision.allowed is False
    assert decision.reason is DecisionReason.CHANNEL_NOT_ALLOWED
    assert decision.source is DecisionSource.DB_POLICY
    assert decision.mode is AccessMode.SELECTED_CHANNELS
    assert decision.feedback is not None
    # Feedback must point operators at the recovery path, not at the
    # raw policy state.
    assert "settings" in decision.feedback.lower()


@pytest.mark.asyncio
async def test_selected_channels_mode_denies_when_allowlist_empty():
    """Empty allowlist + ``selected_channels`` mode is a deliberate
    "no normal commands run anywhere" — different from
    ``disabled_except_bootstrap`` because operators still see the
    "wrong channel" feedback (which points them at settings) rather
    than the harder "commands disabled" wording.
    """
    with _patch_lifecycle(), _patch_policy(_snapshot("selected_channels")):
        decision = await resolve_command_access(_ctx(channel_id=100))
    assert decision.allowed is False
    assert decision.reason is DecisionReason.CHANNEL_NOT_ALLOWED


# ---------------------------------------------------------------------------
# disabled_except_bootstrap mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_disabled_mode_denies_normal_command_with_feedback():
    with _patch_lifecycle(), _patch_policy(_snapshot("disabled_except_bootstrap")):
        decision = await resolve_command_access(_ctx(command_name="blackjack"))
    assert decision.allowed is False
    assert decision.reason is DecisionReason.COMMANDS_DISABLED
    assert decision.source is DecisionSource.DB_POLICY
    assert decision.mode is AccessMode.DISABLED_EXCEPT_BOOTSTRAP
    assert decision.feedback is not None
    # Feedback should mention the recovery command so confused
    # operators know how to re-enable.
    assert "!setup" in decision.feedback or "settings" in decision.feedback.lower()


@pytest.mark.asyncio
async def test_disabled_mode_admits_bootstrap_for_operator():
    """Bootstrap branch fires before policy lookup, so even
    ``disabled_except_bootstrap`` mode admits ``!setup`` for the guild
    owner.  Otherwise an operator could lock themselves out
    irrecoverably.
    """
    with _patch_lifecycle(), _patch_policy(_snapshot("disabled_except_bootstrap")):
        decision = await resolve_command_access(
            _ctx(command_name="setup", is_guild_operator=True),
        )
    assert decision.allowed is True
    assert decision.reason is DecisionReason.BOOTSTRAP_BYPASS


@pytest.mark.asyncio
async def test_disabled_mode_denies_bootstrap_for_non_operator():
    """A non-operator running ``!help`` under disabled mode falls
    through past the bootstrap-bypass branch (they aren't an operator)
    and hits ``COMMANDS_DISABLED``.  This is intentional — bootstrap
    bypass is an operator-only escape hatch, not a public bypass.
    """
    with _patch_lifecycle(), _patch_policy(_snapshot("disabled_except_bootstrap")):
        decision = await resolve_command_access(_ctx(command_name="help"))
    assert decision.allowed is False
    assert decision.reason is DecisionReason.COMMANDS_DISABLED


# ---------------------------------------------------------------------------
# Adapters
# ---------------------------------------------------------------------------


def _build_prefix_ctx(
    *,
    guild_id: int | None = 10,
    channel_id: int | None = 100,
    author_id: int = 42,
    owner_id: int = 42,
    administrator: bool = False,
    manage_guild: bool = False,
    command_name: str = "blackjack",
    qualified_name: str | None = None,
    aliases: tuple[str, ...] = (),
    invoked_with: str | None = None,
    is_bot_owner: bool = False,
):
    guild = (
        SimpleNamespace(id=guild_id, owner_id=owner_id) if guild_id is not None else None
    )
    channel = (
        SimpleNamespace(id=channel_id) if channel_id is not None else None
    )
    author = SimpleNamespace(
        id=author_id,
        guild_permissions=SimpleNamespace(
            administrator=administrator,
            manage_guild=manage_guild,
        ),
    )
    command = SimpleNamespace(
        name=command_name,
        qualified_name=qualified_name or command_name,
        aliases=aliases,
    )
    bot = SimpleNamespace(is_owner=AsyncMock(return_value=is_bot_owner))
    return SimpleNamespace(
        guild=guild,
        channel=channel,
        author=author,
        command=command,
        invoked_with=invoked_with or command_name,
        bot=bot,
    )


@pytest.mark.asyncio
async def test_from_prefix_ctx_extracts_ids_and_operator_flag():
    ctx = _build_prefix_ctx(
        guild_id=10,
        channel_id=100,
        author_id=42,
        owner_id=42,
        command_name="blackjack",
    )
    access_ctx = await command_access.from_prefix_ctx(ctx)
    assert access_ctx.guild_id == 10
    assert access_ctx.channel_id == 100
    assert access_ctx.user_id == 42
    assert access_ctx.is_guild_operator is True  # owner_id matches author_id
    assert access_ctx.is_bot_owner is False
    assert access_ctx.is_dm is False
    assert access_ctx.invocation_type == "prefix"
    assert access_ctx.command_name == "blackjack"


@pytest.mark.asyncio
async def test_from_prefix_ctx_prefers_bootstrap_spelling_when_alias():
    """``!diag`` is an alias for ``!diagnostics``; the adapter must
    surface the bootstrap-classified spelling to the resolver so the
    bypass branch fires.
    """
    ctx = _build_prefix_ctx(
        command_name="diagnostics",
        aliases=("diag",),
        invoked_with="diag",
    )
    access_ctx = await command_access.from_prefix_ctx(ctx)
    # Either spelling is acceptable as long as ``is_bootstrap_command``
    # accepts it — the adapter explicitly prefers the bootstrap
    # spelling so the resolver doesn't have to re-check every alias.
    assert command_access.is_bootstrap_command(access_ctx.command_name)


@pytest.mark.asyncio
async def test_from_prefix_ctx_dm_context_marks_is_dm():
    ctx = _build_prefix_ctx(guild_id=None, channel_id=None)
    access_ctx = await command_access.from_prefix_ctx(ctx)
    assert access_ctx.is_dm is True
    assert access_ctx.guild_id is None


def _build_interaction(
    *,
    guild_id: int | None = 10,
    channel_id: int | None = 100,
    user_id: int = 42,
    owner_id: int = 42,
    administrator: bool = False,
    command_qualified_name: str = "blackjack",
    is_bot_owner: bool = False,
):
    guild = (
        SimpleNamespace(id=guild_id, owner_id=owner_id) if guild_id is not None else None
    )
    channel = SimpleNamespace(id=channel_id) if channel_id is not None else None
    user = SimpleNamespace(
        id=user_id,
        guild_permissions=SimpleNamespace(
            administrator=administrator,
            manage_guild=False,
        ),
    )
    command = SimpleNamespace(
        name=command_qualified_name.split()[0],
        qualified_name=command_qualified_name,
    )
    client = SimpleNamespace(is_owner=AsyncMock(return_value=is_bot_owner))
    return SimpleNamespace(
        guild=guild,
        channel=channel,
        user=user,
        command=command,
        client=client,
    )


@pytest.mark.asyncio
async def test_from_interaction_extracts_qualified_slash_command_name():
    interaction = _build_interaction(command_qualified_name="settings access")
    access_ctx = await command_access.from_interaction(interaction)
    assert access_ctx.invocation_type == "slash"
    assert access_ctx.command_name == "settings access"
    assert access_ctx.is_guild_operator is True  # owner_id matches user_id


@pytest.mark.asyncio
async def test_from_interaction_component_interaction_has_no_command_name():
    """Button / select interactions arrive with ``command=None``.  The
    adapter must not crash — it surfaces ``command_name=None`` and the
    resolver treats it as a non-bootstrap invocation.
    """
    interaction = _build_interaction()
    interaction.command = None
    access_ctx = await command_access.from_interaction(interaction)
    assert access_ctx.command_name is None
    assert command_access.is_bootstrap_command(access_ctx.command_name) is False
