"""Command-access resolver + bootstrap helpers.

Two responsibilities, owned together because they share the bootstrap
allowlist and the operator-privilege check:

1. **Resolver** (PR-2 of the command-access onboarding fix) — given a
   normalized :class:`CommandAccessContext` (built by an adapter from
   either ``commands.Context`` or ``discord.Interaction``), returns a
   :class:`CommandAccessDecision` describing whether the command may
   run, why, and what user-facing feedback the entry-point should
   surface on denial.  Reads cached per-guild policy through the
   ``utils.guild_config_accessors`` typed accessor.

2. **Bootstrap helpers** (existing pre-PR-2 API, retained) —
   :data:`BOOTSTRAP_COMMANDS`, :func:`is_bootstrap_command`, and
   :func:`can_bypass_channel_guard`.  Other modules still import these
   directly; keeping the public surface stable lets PR-2 ship without
   touching every existing caller.

The resolver does not bypass per-command permission decorators.  It
only answers whether the *entry-point* (prefix global check, slash
``tree.interaction_check``) should let the command through to the
normal discord.py check chain.
"""

from __future__ import annotations

import enum
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import discord
    from discord.ext import commands

# ---------------------------------------------------------------------------
# Bootstrap allowlist (existing API)
# ---------------------------------------------------------------------------

BOOTSTRAP_COMMANDS: frozenset[str] = frozenset(
    {
        "admin",
        "adminmenu",
        "check_database",
        "checkdb",
        "diag",
        "diag_status",
        "diagnostic_bot_status",
        "diagnostics",
        "find_command",
        "findcmd",
        "help",
        "latency",
        "list_commands_detailed",
        "listcmds",
        "ping",
        "platform",
        "settings",
        "setup",
        "slashes",
        "slashlist",
        "syncs",
        "syncslash",
        "system_info",
        "sysinfo",
    },
)


def is_bootstrap_command(command_name: str | None) -> bool:
    """Return ``True`` if ``command_name`` is a bootstrap command.

    Accepts both bare names (``"help"``) and qualified group names
    (``"platform identity"``).  The root of a qualified name is checked so
    existing platform/settings/admin subcommands inherit their parent gate.
    """
    if not command_name:
        return False
    normalized = command_name.strip().lower()
    if not normalized:
        return False
    root = normalized.split(maxsplit=1)[0]
    return normalized in BOOTSTRAP_COMMANDS or root in BOOTSTRAP_COMMANDS


def _candidate_command_names(ctx: commands.Context) -> Iterable[str]:
    """Yield every command spelling worth checking for bootstrap access."""
    command = getattr(ctx, "command", None)
    if command is not None:
        name = getattr(command, "name", None)
        if name:
            yield str(name)
        qualified_name = getattr(command, "qualified_name", None)
        if qualified_name:
            yield str(qualified_name)
        for alias in getattr(command, "aliases", ()) or ():
            if alias:
                yield str(alias)
    invoked_with = getattr(ctx, "invoked_with", None)
    if invoked_with:
        yield str(invoked_with)


def _is_guild_operator(author: Any, guild: Any) -> bool:
    """Return whether ``author`` can bootstrap configuration for ``guild``."""
    author_id = getattr(author, "id", None)
    if author_id is not None and author_id == getattr(guild, "owner_id", None):
        return True

    permissions = getattr(author, "guild_permissions", None)
    if permissions is None:
        return False
    return bool(
        getattr(permissions, "administrator", False)
        or getattr(permissions, "manage_guild", False),
    )


async def _is_bot_owner_from_ctx(ctx: commands.Context) -> bool:
    """Best-effort bot-owner check used as an operator escape hatch."""
    bot = getattr(ctx, "bot", None)
    is_owner = getattr(bot, "is_owner", None)
    if not callable(is_owner):
        return False
    try:
        return bool(await is_owner(getattr(ctx, "author", None)))
    except Exception:
        return False


async def can_bypass_channel_guard(ctx: commands.Context) -> bool:
    """Return whether ``ctx`` may bypass the global channel allowlist.

    Pre-PR-2 entry point used directly by ``BootstrapAccessCog._channel_guard``;
    retained so prefix-path callers do not break while PR-4 wires the
    cog over to the full resolver.  Behaviour is identical to the
    pre-PR-2 implementation:

    * DMs never bypass; setup is guild-scoped.
    * Non-bootstrap commands never bypass.
    * The guild owner, administrators, members with ``manage_guild``, and
      bot owners may bypass for bootstrap commands only.
    """
    guild = getattr(ctx, "guild", None)
    if guild is None:
        return False

    if not any(is_bootstrap_command(name) for name in _candidate_command_names(ctx)):
        return False

    author = getattr(ctx, "author", None)
    if _is_guild_operator(author, guild):
        return True

    return await _is_bot_owner_from_ctx(ctx)


# ---------------------------------------------------------------------------
# Resolver — decision model (PR-2)
# ---------------------------------------------------------------------------


class AccessMode(enum.Enum):
    """Per-guild command-access modes (mirrors the DB CHECK constraint)."""

    ALL_CHANNELS = "all_channels"
    SELECTED_CHANNELS = "selected_channels"
    DISABLED_EXCEPT_BOOTSTRAP = "disabled_except_bootstrap"


class DecisionSource(enum.Enum):
    """Where the admission decision came from."""

    DB_POLICY = "db_policy"
    BOOTSTRAP_BYPASS = "bootstrap_bypass"
    DEFAULT_UNCONFIGURED = "default_unconfigured"
    LIFECYCLE_DENY = "lifecycle_deny"


class DecisionReason(enum.Enum):
    """Machine-readable reason for the decision — used by logs + metrics."""

    ALLOWED = "allowed"
    BOOTSTRAP_BYPASS = "bootstrap_bypass"
    LIFECYCLE_DRAINING = "lifecycle_draining"
    DM_NOT_SUPPORTED = "dm_not_supported"
    CHANNEL_NOT_ALLOWED = "channel_not_allowed"
    COMMANDS_DISABLED = "commands_disabled"


@dataclass(frozen=True)
class CommandAccessContext:
    """Normalized input to the resolver — see :func:`from_prefix_ctx` and
    :func:`from_interaction` for the adapters that build one from a
    ``commands.Context`` or a ``discord.Interaction``.
    """

    guild_id: int | None
    channel_id: int | None
    user_id: int | None
    command_name: str | None
    invocation_type: str  # "prefix" | "slash"
    is_guild_operator: bool
    is_bot_owner: bool
    is_dm: bool


@dataclass(frozen=True)
class CommandAccessDecision:
    """Result of :func:`resolve_command_access`.

    ``feedback`` is the user-facing message the entry-point should
    surface (ephemeral for slash; ``ctx.send`` with ``delete_after`` for
    prefix).  ``None`` means no message — either the command is allowed,
    or the denial is deliberately silent (lifecycle drain).
    """

    allowed: bool
    reason: DecisionReason
    source: DecisionSource
    mode: AccessMode | None
    feedback: str | None


_FEEDBACK_COMMANDS_DISABLED = (
    "Commands are disabled in this server. "
    "Ask a server admin to enable them via `!setup` or the "
    "Command Access settings panel."
)

_FEEDBACK_CHANNEL_NOT_ALLOWED = (
    "Commands aren't enabled in this channel. "
    "Use one of the configured command channels or ask an admin to "
    "update Command Access in `!settings`."
)


async def resolve_command_access(
    ctx: CommandAccessContext,
) -> CommandAccessDecision:
    """Resolve admission for a single command invocation.

    Order of checks (matches the admission chain in the plan):

    1. **Lifecycle drain** — when the bot is shutting down / restarting,
       every command is denied silently.  Surfacing feedback would race
       with the connection close.
    2. **DM** — this resolver does not own DM admission.  DMs always
       reach the existing per-command handler unchanged: the resolver
       reports the decision but with ``allowed=False`` so the
       entry-point can route them past the channel-policy check.
    3. **Bootstrap bypass** — guild operators (owner / admin /
       manage_guild) and bot owners may run bootstrap commands
       regardless of policy.  Per-command permission decorators still
       run after this bypass.
    4. **Policy mode** — looks up the cached per-guild policy.  Absence
       of a policy is the safe default: ``ALL_CHANNELS`` with
       ``DEFAULT_UNCONFIGURED`` source.
    """
    # Local import avoids a hard dep at module import time so test
    # fixtures that monkeypatch ``lifecycle.can_accept_commands`` keep
    # working.  ``core.runtime.lifecycle`` has no transitive Discord
    # imports — this is a deferral for clarity, not necessity.
    from core.runtime import lifecycle

    if not lifecycle.can_accept_commands():
        return CommandAccessDecision(
            allowed=False,
            reason=DecisionReason.LIFECYCLE_DRAINING,
            source=DecisionSource.LIFECYCLE_DENY,
            mode=None,
            feedback=None,
        )

    if ctx.is_dm or ctx.guild_id is None:
        # The resolver is guild-scoped.  Entry-points may still permit
        # DM commands via the per-command opt-in (commands.dm_only,
        # app_commands.allowed_contexts) — that path runs after this
        # decision is returned.
        return CommandAccessDecision(
            allowed=False,
            reason=DecisionReason.DM_NOT_SUPPORTED,
            source=DecisionSource.DEFAULT_UNCONFIGURED,
            mode=None,
            feedback=None,
        )

    if is_bootstrap_command(ctx.command_name) and (
        ctx.is_guild_operator or ctx.is_bot_owner
    ):
        return CommandAccessDecision(
            allowed=True,
            reason=DecisionReason.BOOTSTRAP_BYPASS,
            source=DecisionSource.BOOTSTRAP_BYPASS,
            mode=None,
            feedback=None,
        )

    # Hot-path cached read.  Loader returns ``None`` when no policy row
    # exists; the resolver treats that as the safe default.
    from utils.guild_config_accessors import get_command_access_policy

    snapshot = await get_command_access_policy(ctx.guild_id)
    if snapshot.mode is None:
        return CommandAccessDecision(
            allowed=True,
            reason=DecisionReason.ALLOWED,
            source=DecisionSource.DEFAULT_UNCONFIGURED,
            mode=AccessMode.ALL_CHANNELS,
            feedback=None,
        )

    mode = AccessMode(snapshot.mode)

    if mode is AccessMode.ALL_CHANNELS:
        return CommandAccessDecision(
            allowed=True,
            reason=DecisionReason.ALLOWED,
            source=DecisionSource.DB_POLICY,
            mode=mode,
            feedback=None,
        )

    if mode is AccessMode.DISABLED_EXCEPT_BOOTSTRAP:
        # Bootstrap commands by authorized operators were already
        # admitted at step 3.  Anything reaching here is either a
        # non-bootstrap command or a non-operator running one — deny.
        return CommandAccessDecision(
            allowed=False,
            reason=DecisionReason.COMMANDS_DISABLED,
            source=DecisionSource.DB_POLICY,
            mode=mode,
            feedback=_FEEDBACK_COMMANDS_DISABLED,
        )

    # mode is AccessMode.SELECTED_CHANNELS
    if ctx.channel_id is not None and ctx.channel_id in snapshot.allowed_channels:
        return CommandAccessDecision(
            allowed=True,
            reason=DecisionReason.ALLOWED,
            source=DecisionSource.DB_POLICY,
            mode=mode,
            feedback=None,
        )
    return CommandAccessDecision(
        allowed=False,
        reason=DecisionReason.CHANNEL_NOT_ALLOWED,
        source=DecisionSource.DB_POLICY,
        mode=mode,
        feedback=_FEEDBACK_CHANNEL_NOT_ALLOWED,
    )


# ---------------------------------------------------------------------------
# Adapters — build a CommandAccessContext from Discord-shaped inputs
# ---------------------------------------------------------------------------


def _first_bootstrap_name(ctx: commands.Context) -> str | None:
    """Return the first command spelling that classifies as bootstrap,
    or the canonical name when nothing matches.

    Adapter helper: the resolver only needs one command_name string,
    but a ``commands.Context`` can expose several (name, qualified
    name, aliases, invoked_with) and any of them might be the
    bootstrap spelling (``!diag`` is an alias for ``!diagnostics``).
    Picking the bootstrap-matching spelling preferentially keeps the
    resolver's classifier simple — it sees the spelling that matters.
    """
    canonical: str | None = None
    for candidate in _candidate_command_names(ctx):
        canonical = canonical or candidate
        if is_bootstrap_command(candidate):
            return candidate
    return canonical


async def from_prefix_ctx(ctx: commands.Context) -> CommandAccessContext:
    """Build a :class:`CommandAccessContext` from a ``commands.Context``.

    Async because the bot-owner check is async — kept in the adapter
    so callers don't have to thread two awaits through the call chain.
    """
    guild = getattr(ctx, "guild", None)
    channel = getattr(ctx, "channel", None)
    author = getattr(ctx, "author", None)
    return CommandAccessContext(
        guild_id=getattr(guild, "id", None),
        channel_id=getattr(channel, "id", None),
        user_id=getattr(author, "id", None),
        command_name=_first_bootstrap_name(ctx),
        invocation_type="prefix",
        is_guild_operator=bool(guild and _is_guild_operator(author, guild)),
        is_bot_owner=await _is_bot_owner_from_ctx(ctx),
        is_dm=guild is None,
    )


async def from_interaction(
    interaction: discord.Interaction,
) -> CommandAccessContext:
    """Build a :class:`CommandAccessContext` from a ``discord.Interaction``.

    Reads slash-command name from ``interaction.command``.  Component
    interactions (buttons/selects) have ``command=None``; the resolver
    treats those as non-bootstrap and applies the normal policy check,
    which is the desired behaviour — buttons in a disabled channel
    should not work either.
    """
    guild = interaction.guild
    channel = interaction.channel
    user = interaction.user
    command = interaction.command
    command_name = getattr(command, "qualified_name", None) or getattr(
        command,
        "name",
        None,
    )

    is_operator = bool(guild and _is_guild_operator(user, guild))

    bot = getattr(interaction, "client", None)
    is_owner = getattr(bot, "is_owner", None)
    bot_owner = False
    if callable(is_owner):
        try:
            bot_owner = bool(await is_owner(user))
        except Exception:
            bot_owner = False

    return CommandAccessContext(
        guild_id=getattr(guild, "id", None),
        channel_id=getattr(channel, "id", None),
        user_id=getattr(user, "id", None),
        command_name=command_name,
        invocation_type="slash",
        is_guild_operator=is_operator,
        is_bot_owner=bot_owner,
        is_dm=guild is None,
    )


# ---------------------------------------------------------------------------
# Guild teardown — registered by ``guild_lifecycle.teardown`` in PR-3
# ---------------------------------------------------------------------------


async def forget_guild(guild_id: int) -> None:
    """Drop cached + persisted command-access state for ``guild_id``.

    Called by the guild-lifecycle teardown path (PR-3 wiring).  Defined
    here rather than in ``utils/db`` so the cache invalidation and the
    DB delete are paired — forgetting only one leaves a stale entry
    that can re-appear on the next read.
    """
    from utils.db import command_access as db_command_access
    from utils.guild_config_accessors import invalidate_command_access_policy

    invalidate_command_access_policy(guild_id)
    await db_command_access.forget_guild(guild_id)


__all__ = [
    "BOOTSTRAP_COMMANDS",
    "AccessMode",
    "CommandAccessContext",
    "CommandAccessDecision",
    "DecisionReason",
    "DecisionSource",
    "can_bypass_channel_guard",
    "forget_guild",
    "from_interaction",
    "from_prefix_ctx",
    "is_bootstrap_command",
    "resolve_command_access",
]
