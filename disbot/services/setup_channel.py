"""Auto-managed private setup channel.

When SuperBot joins a guild and has Manage Channels permission, it
creates a private ``#superbot-setup`` channel visible only to the bot
itself, the guild owner, and any delegated setup admins recorded on
the :class:`SetupSession`.  The launcher cog posts the setup launcher
in that channel and @mentions the owner so they discover the wizard
immediately.

This module owns the idempotent "ensure" operation.  The actual
Discord channel creation routes through
:func:`core.runtime.guild_resources.ensure_channel` — the canonical
infrastructure primitive on the S4.5 no-silent-auto-create allowlist.

Best-effort privacy contract:

* ``@everyone`` is denied ``view_channel``.
* Every role whose Discord permission set includes ``administrator``
  is denied ``view_channel`` explicitly (defence-in-depth — Discord's
  admin override means admins can still see the channel via role
  permissions, but the explicit overwrite is what an audit reads).
* Bot, server owner, and every delegated setup admin id get a
  positive overwrite granting view + send + history.

Operator-visible copy must say:

    Admins may still see this channel depending on Discord permissions.
    Setup actions are protected by interaction checks.

— because Discord's administrator permission can override a
view-channel denial regardless of overwrite order.  The real security
boundary is :func:`services.setup_access.can_apply_setup`.

Constraints preserved:

* No ``guild.create_text_channel`` call here — that lives in
  ``guild_resources.ensure_channel``.
* No DB writes here. The caller updates ``setup_session`` with the
  new channel id via the standard ``start_session`` upsert.
* No required permissions raise; missing perms / HTTP failures
  surface as ``(None, False)`` and the caller falls back to
  ``post_launcher`` (which already DMs the owner if no channel is
  sendable).

The channel name is namespaced so it does not collide with
operator-named "setup" channels.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import discord

from core.runtime.guild_resources import ensure_channel, resolve_member
from services import setup_access

if TYPE_CHECKING:
    from services.setup_session import SetupSession

logger = logging.getLogger("bot.services.setup_channel")

#: Channel name for the bot-managed setup workspace. Namespaced so
#: operator-created "setup" channels are not accidentally adopted.
SETUP_CHANNEL_NAME = "superbot-setup"

#: Public note rendered alongside any UI that surfaces the setup
#: channel.  Discord's administrator permission can override a
#: ``view_channel`` denial regardless of overwrite order, so the
#: explicit admin-role denial is best-effort.  The actual security
#: boundary for setup actions is
#: :func:`services.setup_access.can_apply_setup` — the interaction
#: checks on every mutating button.
PRIVACY_NOTE = (
    "Admins may still see this channel depending on Discord permissions. "
    "Setup actions are protected by interaction checks."
)


def _allow_overwrite() -> discord.PermissionOverwrite:
    """Standard "may use the setup channel" overwrite."""
    return discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
    )


def _bot_overwrite() -> discord.PermissionOverwrite:
    """Standard bot overwrite (includes manage_messages for clean-up)."""
    return discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        read_message_history=True,
        manage_messages=True,
    )


def _deny_view_overwrite() -> discord.PermissionOverwrite:
    """Standard "do not see this channel" overwrite."""
    return discord.PermissionOverwrite(view_channel=False)


def _private_overwrites(
    guild: discord.Guild,
    *,
    session: SetupSession | None = None,
) -> dict[discord.Member | discord.Role, discord.PermissionOverwrite]:
    """Build the permission overwrite set for the private setup channel.

    Layout:

    * ``@everyone`` — denied ``view_channel``.
    * Every role flagged ``administrator=True`` — denied
      ``view_channel`` explicitly.  Discord's admin override can still
      reveal the channel; this is defence-in-depth that an audit
      reader can see.
    * Bot — full read/write/manage.
    * Server owner — read/write.
    * Every delegated setup admin id on ``session`` — read/write.
      Ids that don't resolve to a current member are skipped (the
      member may have left the guild).

    Pass ``session=None`` (legacy call sites) for the owner-and-bot-only
    layout.  All Phase 1+ call sites should pass the resolved session
    so the overwrites match the access tier.
    """
    overwrites: dict[discord.Member | discord.Role, discord.PermissionOverwrite] = {
        guild.default_role: _deny_view_overwrite(),
    }
    # Deny administrator roles explicitly so an audit reading the
    # overwrite set sees the intent.  Discord may still let admins
    # view via the admin permission flag — see PRIVACY_NOTE.
    for role in getattr(guild, "roles", ()):
        if role.id == guild.default_role.id:
            continue
        perms = getattr(role, "permissions", None)
        if perms is not None and getattr(perms, "administrator", False):
            overwrites[role] = _deny_view_overwrite()
    if guild.me is not None:
        overwrites[guild.me] = _bot_overwrite()
    if guild.owner is not None:
        overwrites[guild.owner] = _allow_overwrite()
    if session is not None:
        for delegated_id in session.delegated_admins:
            # Cache-only lookup via the project's canonical resolver
            # (S5 invariant — no raw guild.get_member outside
            # core.runtime.guild_resources).
            member = resolve_member(guild, delegated_id)
            if member is None:
                # Member left the guild or is uncached — skip; the
                # session row still holds the id so a future
                # recompute picks them up if they rejoin.
                continue
            overwrites[member] = _allow_overwrite()
    return overwrites


def _bot_can_manage_channels(guild: discord.Guild) -> bool:
    """True iff the bot member holds Manage Channels in this guild."""
    me = guild.me
    if me is None:
        return False
    return bool(getattr(me.guild_permissions, "manage_channels", False))


async def ensure_setup_channel(
    guild: discord.Guild,
    *,
    existing_channel_id: int | None = None,
    session: SetupSession | None = None,
) -> tuple[discord.TextChannel | None, bool]:
    """Return the private setup channel for ``guild``, creating if absent.

    Idempotent.  Tries, in order:

    1. If ``existing_channel_id`` is given and the channel is still in
       the guild cache, return it after recomputing overwrites so the
       reused channel reflects the current session's delegated-admin
       set (and any newly-added admin roles get denied).
    2. Otherwise create the channel with the private overwrite set
       via :func:`core.runtime.guild_resources.ensure_channel`.

    ``session`` is the resolved :class:`SetupSession` snapshot
    (``None`` is accepted for legacy call sites that don't yet pass
    it).  When provided, the channel's overwrite set is built from
    its ``delegated_admins`` list; when ``None``, the layout falls
    back to owner-and-bot-only.

    Returns:
        ``(channel, was_just_created)`` where ``channel`` is ``None``
        when the bot lacks permission or Discord refused the create.
        Callers should fall back to the existing ``post_launcher``
        path in that case so setup still gets a launcher somewhere.
    """
    if existing_channel_id is not None:
        existing = guild.get_channel(existing_channel_id)
        if isinstance(existing, discord.TextChannel):
            # Reuse the channel, but repair its overwrites from the
            # current session snapshot — admin roles created since
            # last run get denied, newly-delegated admins gain
            # access, and revoked admins lose theirs.  Best-effort:
            # a failure is logged and the channel is still returned.
            await _apply_overwrites(existing, guild, session=session)
            return existing, False

    if not _bot_can_manage_channels(guild):
        logger.info(
            "setup_channel: bot lacks Manage Channels in guild %d; falling back",
            guild.id,
        )
        return None, False

    try:
        channel = await ensure_channel(
            guild,
            SETUP_CHANNEL_NAME,
            kind="text",
            category=None,
            overwrites=_private_overwrites(guild, session=session),
        )
    except discord.Forbidden as exc:
        logger.warning(
            "setup_channel: forbidden creating #%s in guild %d: %s",
            SETUP_CHANNEL_NAME,
            guild.id,
            exc,
        )
        return None, False
    except discord.HTTPException as exc:
        logger.warning(
            "setup_channel: HTTP error creating #%s in guild %d: %s",
            SETUP_CHANNEL_NAME,
            guild.id,
            exc,
        )
        return None, False

    if not isinstance(channel, discord.TextChannel):
        logger.warning(
            "setup_channel: guild_resources returned non-text channel for guild %d",
            guild.id,
        )
        return None, False

    return channel, True


async def recompute_setup_channel_overwrites(
    guild: discord.Guild,
    session: SetupSession | None,
    *,
    channel: discord.TextChannel | None = None,
) -> bool:
    """Rebuild and apply the setup channel's permission overwrites.

    Called from the delegate / undelegate flows so the channel's
    overwrites stay in sync with ``session.delegated_admins``, and
    from :func:`ensure_setup_channel` when reusing a cached channel
    so admin-role denials and delegate grants follow the latest
    membership snapshot.

    ``channel`` may be passed explicitly; otherwise the helper looks
    it up via ``session.setup_channel_id``.  When the channel cannot
    be resolved, the function returns ``False`` (caller can decide
    to re-create the channel).
    """
    target = channel
    if target is None and session is not None and session.setup_channel_id is not None:
        cached = guild.get_channel(session.setup_channel_id)
        if isinstance(cached, discord.TextChannel):
            target = cached
    if target is None:
        logger.info(
            "setup_channel: recompute skipped — no channel resolved (guild=%d)",
            guild.id,
        )
        return False
    return await _apply_overwrites(target, guild, session=session)


async def _apply_overwrites(
    channel: discord.TextChannel,
    guild: discord.Guild,
    *,
    session: SetupSession | None,
) -> bool:
    """Apply the computed overwrite set to ``channel``.  Best-effort.

    Returns ``True`` on a successful edit (or no-op when there is
    nothing to apply), ``False`` when Discord refused / errored.
    """
    # discord.TextChannel.edit accepts a wider Mapping union than the
    # dict[Member | Role, ...] our builder returns; cast to the
    # builder's narrower shape so mypy accepts the call without
    # losing the runtime structure check.
    from typing import cast

    overwrites_dict = _private_overwrites(guild, session=session)
    overwrites = cast(
        "dict[discord.Role | discord.Member | discord.Object, discord.PermissionOverwrite]",
        overwrites_dict,
    )
    try:
        await channel.edit(
            overwrites=overwrites,
            reason="setup_channel.recompute_overwrites",
        )
    except discord.Forbidden as exc:
        logger.warning(
            "setup_channel: forbidden editing overwrites on #%s (guild=%d): %s",
            channel.name,
            guild.id,
            exc,
        )
        return False
    except discord.HTTPException as exc:
        logger.warning(
            "setup_channel: HTTP error editing overwrites on #%s (guild=%d): %s",
            channel.name,
            guild.id,
            exc,
        )
        return False
    return True


async def delete_setup_channel(
    guild: discord.Guild,
    channel_id: int,
    *,
    reason: str = "Setup complete — operator confirmed auto-cleanup",
) -> bool:
    """Delete the bot-managed setup channel.

    Returns ``True`` when the channel was deleted (or was already
    gone), ``False`` when the deletion attempt failed. The channel
    name is verified to equal ``SETUP_CHANNEL_NAME`` before deletion
    so an operator-renamed channel is never deleted by this helper.

    Operates idempotently: a missing channel id, a channel whose
    name no longer matches the bot's naming convention, or a
    Discord HTTP failure all return cleanly. The session row is
    updated by the caller.
    """
    channel = guild.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        # Channel already gone from the cache — treat as success so
        # the caller can clear the session ids.
        return True
    if channel.name != SETUP_CHANNEL_NAME:
        # Operator renamed the channel; we treat it as no longer
        # ours and refuse to delete it.
        logger.info(
            "setup_channel: refusing to delete renamed channel %d (name=%r)",
            channel_id,
            channel.name,
        )
        return False
    try:
        await channel.delete(reason=reason)
    except discord.NotFound:
        return True
    except discord.Forbidden as exc:
        logger.warning(
            "setup_channel: forbidden deleting channel %d in guild %d: %s",
            channel_id,
            guild.id,
            exc,
        )
        return False
    except discord.HTTPException as exc:
        logger.warning(
            "setup_channel: HTTP error deleting channel %d in guild %d: %s",
            channel_id,
            guild.id,
            exc,
        )
        return False
    return True


CleanupReason = Literal[
    "ok",
    "not_complete",
    "draft_not_empty",
    "channel_id_mismatch",
    "channel_renamed",
    "channel_missing",
    "unauthorized",
    "delete_failed",
]


@dataclass(frozen=True)
class CleanupResult:
    """Outcome of :func:`cleanup_setup_channel_after_completion`.

    ``reason="ok"`` is the only success state; any other value
    surfaces an operator-facing explanation of why the cleanup was
    refused.  ``detail`` is a short human-readable string suitable
    for an ephemeral reply.
    """

    reason: CleanupReason
    detail: str


async def cleanup_setup_channel_after_completion(
    guild: discord.Guild,
    session: SetupSession | None,
    *,
    actor: discord.Member,
) -> CleanupResult:
    """Delete ``#superbot-setup`` after a successful Final Review apply.

    Phase 8 of the setup-wizard plan.  Mandatory guards, checked in
    order — any failure short-circuits with an operator-facing
    explanation rather than proceeding to the delete:

    1. ``session.setup_status == "complete"`` — the wizard must have
       finished a Final Review apply.  Without this, the operator
       hasn't actually applied their staged ops yet.
    2. ``setup_draft.count(guild_id) == 0`` — partial-recovery state
       always preserves the draft; an empty draft is the proxy for
       "no recovery in progress".  Cleaning up mid-recovery would
       strand the operator without an anchor message.
    3. ``session.setup_channel_id`` matches the channel id we're
       about to delete.  Belt-and-braces protection: callers pass
       the channel id implicitly via the session, but a future
       caller passing the wrong session would otherwise delete the
       wrong channel.
    4. The channel name is still ``#superbot-setup``.  An operator
       who renamed the channel signaled "this is mine now"; we
       refuse to delete a renamed channel even if the id still
       matches (mirrors :func:`delete_setup_channel`'s own guard).
    5. ``setup_access.can_apply_setup(actor, session)`` — only the
       server owner or a delegated setup admin can trigger the
       delete.

    Only if every guard passes:

    * Call :func:`delete_setup_channel` to perform the Discord-side
      delete (which has its own name guard, kept as defence in
      depth).
    * Null both ``setup_channel_id`` and ``setup_message_id`` on the
      session row so the next ``/setup`` re-creates a fresh channel.

    Returns a typed :class:`CleanupResult`.  The caller (typically
    the Final Review completion view) surfaces ``detail`` in an
    ephemeral reply.
    """
    if session is None or session.setup_status != "complete":
        return CleanupResult(
            reason="not_complete",
            detail=(
                "Setup isn't complete yet — finish a Final Review apply "
                "before deleting the setup channel."
            ),
        )

    try:
        from services import setup_draft as _draft

        pending = await _draft.count(guild.id)
    except Exception:
        logger.exception(
            "cleanup_setup_channel: setup_draft.count failed (guild=%d)",
            guild.id,
        )
        return CleanupResult(
            reason="delete_failed",
            detail=(
                "Couldn't read the staged-ops count — see logs.  Re-run "
                "Final Review or try again later."
            ),
        )
    if pending > 0:
        return CleanupResult(
            reason="draft_not_empty",
            detail=(
                f"There are still **{pending}** staged operation(s) — "
                "Final Review left them in the draft for recovery.  "
                "Apply them (or run `/setup-reset`) before deleting the "
                "channel."
            ),
        )

    if session.setup_channel_id is None:
        return CleanupResult(
            reason="channel_missing",
            detail=("No setup channel is recorded for this guild — nothing to delete."),
        )

    channel = guild.get_channel(session.setup_channel_id)
    if not isinstance(channel, discord.TextChannel):
        # The channel may have already been deleted out-of-band; null
        # the pointer for consistency and return a non-error reason.
        try:
            await set_session_channel_id(guild.id, None)
        except Exception:
            logger.exception(
                "cleanup_setup_channel: nulling channel id failed (guild=%d)",
                guild.id,
            )
        return CleanupResult(
            reason="channel_missing",
            detail=(
                "The setup channel is already gone — cleared the "
                "session pointer for you."
            ),
        )

    if channel.id != session.setup_channel_id:
        return CleanupResult(
            reason="channel_id_mismatch",
            detail=(
                "The session's setup_channel_id doesn't match the "
                "resolved channel; refusing to delete."
            ),
        )

    if channel.name != SETUP_CHANNEL_NAME:
        return CleanupResult(
            reason="channel_renamed",
            detail=(
                f"The channel has been renamed to `#{channel.name}` — "
                "refusing to delete an operator-renamed channel."
            ),
        )

    if not setup_access.can_apply_setup(actor, session):
        return CleanupResult(
            reason="unauthorized",
            detail=(
                "Only the server owner or a delegated setup admin can "
                "delete the setup channel."
            ),
        )

    deleted = await delete_setup_channel(guild, channel.id)
    if not deleted:
        return CleanupResult(
            reason="delete_failed",
            detail=(
                "Discord refused the delete — check the bot's Manage "
                "Channels permission and see logs."
            ),
        )

    try:
        await set_session_channel_id(guild.id, None)
    except Exception:
        logger.exception(
            "cleanup_setup_channel: nulling channel id failed after delete",
        )
    try:
        await set_session_message_id(guild.id, None)
    except Exception:
        logger.exception(
            "cleanup_setup_channel: nulling message id failed after delete",
        )

    return CleanupResult(
        reason="ok",
        detail="Setup channel deleted.  Re-run `/setup` later to recreate it.",
    )


async def set_session_channel_id(guild_id: int, channel_id: int | None) -> None:
    """Thin shim around :func:`services.setup_session.set_setup_channel_id`.

    Defined here so the cleanup helper can defer the lazy import to
    a single seam (avoiding the cyclic-import risk of pulling
    ``services.setup_session`` at module-load time).
    """
    from services import setup_session as svc

    await svc.set_setup_channel_id(guild_id, channel_id)


async def set_session_message_id(guild_id: int, message_id: int | None) -> None:
    """Thin shim around :func:`services.setup_session.set_setup_message_id`."""
    from services import setup_session as svc

    await svc.set_setup_message_id(guild_id, message_id)


__all__ = [
    "PRIVACY_NOTE",
    "SETUP_CHANNEL_NAME",
    "CleanupReason",
    "CleanupResult",
    "cleanup_setup_channel_after_completion",
    "delete_setup_channel",
    "ensure_setup_channel",
    "recompute_setup_channel_overwrites",
]
