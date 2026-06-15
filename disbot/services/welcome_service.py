"""Welcome service — greeting/farewell embeds + the join/leave orchestration.

welcome v1 (owner decision Q-0110).  Where automod *acts* on messages and
server-logging *observes* events, welcome *greets* members on join and bids
farewell on leave, optionally granting an entry role the moment a member joins.

Design (family-plan §3, ``docs/planning/safety-community-family-plan-2026-06-13.md``):

* **Off by default.** :class:`WelcomePolicy` gates every action behind the
  master ``enabled`` flag (see :mod:`services.welcome_config`).
* **Fail open.** A config-read fault, a missing channel, or a send error must
  never raise into the gateway's ``on_member_join`` dispatch — each step is
  isolated and logged, never propagated.
* **Route role grants through the audited seam.** The optional entry role is
  granted via :func:`services.role_automation.apply`, which preflight-guards
  the change and emits ``audit.action_recorded`` — welcome opens no parallel
  role-mutation or audit path.

The cog (:mod:`cogs.welcome_cog`) is glue: it filters bots and delegates to
:func:`handle_member_join` / :func:`handle_member_leave` here.
"""

from __future__ import annotations

import asyncio
import io
import logging
from typing import Any

import discord

from core.runtime import resources
from services import welcome_config

logger = logging.getLogger("bot.services.welcome")

EVT_WELCOME_MEMBER_GREETED = "welcome.member_greeted"

# Embed colours — green welcomes, muted farewells.
_JOIN_COLOR = discord.Color.green()
_LEAVE_COLOR = discord.Color.dark_grey()


# ---------------------------------------------------------------------------
# Embed builders (pure — no I/O, unit-testable)
# ---------------------------------------------------------------------------


def format_join_embed(
    member: discord.Member,
    policy: welcome_config.WelcomePolicy,
    member_count: int,
) -> discord.Embed:
    """Build the greeting embed for a joining ``member``."""
    description = welcome_config.render_template(
        policy.join_message,
        member_name=member.mention,
        guild_name=member.guild.name,
        member_count=member_count,
    )
    embed = discord.Embed(description=description, color=_JOIN_COLOR)
    avatar = getattr(member, "display_avatar", None)
    if avatar is not None:
        embed.set_thumbnail(url=avatar.url)
    return embed


def format_leave_embed(
    member: discord.Member,
    policy: welcome_config.WelcomePolicy,
    member_count: int,
) -> discord.Embed:
    """Build the farewell embed for a departing ``member``.

    Uses the plain name (not a mention) — the member has left, so a mention
    would render as a raw id for anyone who never shared a mutual server.
    """
    description = welcome_config.render_template(
        policy.leave_message,
        member_name=member.display_name,
        guild_name=member.guild.name,
        member_count=member_count,
    )
    return discord.Embed(description=description, color=_LEAVE_COLOR)


# ---------------------------------------------------------------------------
# Orchestration — fail-safe member-event handlers
# ---------------------------------------------------------------------------


def _resolve_text_channel(
    guild: discord.Guild,
    channel_id: int | None,
) -> discord.abc.Messageable | None:
    """Return the configured greeting channel when it is sendable, else None."""
    if channel_id is None:
        return None
    channel = resources.resolve_channel(guild, channel_id=channel_id)
    if isinstance(channel, (discord.TextChannel, discord.Thread)):
        return channel
    return None


async def _post(
    channel: discord.abc.Messageable,
    embed: discord.Embed,
    file: discord.File | None = None,
) -> bool:
    """Send ``embed`` (and an optional ``file``) — fail-safe (logs, never raises)."""
    try:
        if file is not None:
            await channel.send(embed=embed, file=file)
        else:
            await channel.send(embed=embed)
    except discord.Forbidden:
        logger.warning("welcome: missing send permission in greeting channel")
        return False
    except discord.HTTPException as exc:
        logger.warning("welcome: HTTP error posting greeting: %s", exc)
        return False
    except Exception:  # noqa: BLE001 — fail-safe wrapper
        logger.exception("welcome: unexpected error posting greeting")
        return False
    return True


def _accent_for(member: discord.Member) -> tuple[int, int, int] | None:
    """The member's top-role colour as an RGB triple, or None for the default.

    Discord's "default" role colour is 0x000000; treat it (and any read fault)
    as "no override" so the card uses its blurple accent rather than a flat
    black ring.
    """
    try:
        colour = member.top_role.color
    except Exception:  # noqa: BLE001 — top_role may be absent on a test double
        return None
    if colour is None or colour.value == 0:
        return None
    return (colour.r, colour.g, colour.b)


async def _build_welcome_card(
    member: discord.Member,
    member_count: int,
) -> discord.File | None:
    """Render the welcome card off-thread and wrap it as a ``discord.File``.

    Fail-safe: a Pillow-unavailable (``None`` bytes) or any render fault yields
    ``None`` so the caller posts the embed without an attachment — the card is
    always an enhancement, never a precondition for the greeting.
    """
    from utils import welcome_render

    try:
        png = await asyncio.to_thread(
            welcome_render.render_welcome_card,
            member_name=member.display_name,
            server_name=member.guild.name,
            member_number=member_count,
            accent=_accent_for(member),
        )
    except Exception:  # noqa: BLE001 — a render fault must not skip the greeting
        logger.exception("welcome: card render failed for member=%s", member.id)
        return None
    if png is None:
        return None
    return discord.File(io.BytesIO(png), filename=welcome_render.CARD_FILENAME)


async def _grant_entry_role(member: discord.Member, role_id: int) -> None:
    """Grant the entry role through the audited role-automation seam.

    Reuses :func:`services.role_automation.apply` so the grant is
    preflight-guarded (bot perms / role hierarchy) and emits
    ``audit.action_recorded`` — welcome adds no second role-mutation path.
    Missing role / already-held is a no-op; failures are classified and
    logged by ``apply`` itself, never raised here.
    """
    role = resources.resolve_role(member.guild, role_id=role_id)
    if role is None:
        logger.warning(
            "welcome: entry role %d not found in guild %d — skipping grant",
            role_id,
            member.guild.id,
        )
        return
    if role in getattr(member, "roles", ()):  # already held — nothing to do
        return

    from services import role_automation

    assignment = role_automation.Assignment(
        member_id=member.id,
        member_display=member.display_name,
        add_role_id=role.id,
        add_role_name=role.name,
        remove_role_ids=(),
        remove_role_names=(),
        reason="Welcome entry role (granted on join)",
        days_in_guild=0,
    )
    try:
        await role_automation.apply(
            member.guild,
            (assignment,),
            actor_id=None,
            actor_type="system",
        )
    except Exception:  # noqa: BLE001 — a role-grant fault must not crash the join
        logger.exception(
            "welcome: entry-role grant failed for member=%s in guild=%s",
            member.id,
            member.guild.id,
        )


async def _emit_greeted(member: discord.Member) -> None:
    """Emit the advisory ``welcome.member_greeted`` event (best-effort)."""
    from core.events import bus

    try:
        await bus.emit(
            EVT_WELCOME_MEMBER_GREETED,
            guild_id=member.guild.id,
            user_id=member.id,
        )
    except Exception:  # noqa: BLE001 — advisory event; never fail the handler
        logger.exception("welcome: member_greeted emit failed")


async def handle_member_join(member: discord.Member) -> None:
    """Greet a joining member + grant the entry role, per the guild policy.

    Fully fail-safe: a fault loading the policy, granting the role, or posting
    the greeting is logged and swallowed so the join dispatch always completes.
    The two actions are independent — a role-grant failure does not skip the
    greeting and vice versa.
    """
    guild = getattr(member, "guild", None)
    if guild is None:
        return
    try:
        policy = await welcome_config.load_policy(guild.id)
    except Exception:  # noqa: BLE001 — fail open on any config-read fault
        logger.exception("welcome: load_policy failed for guild=%s", guild.id)
        return

    if not policy.any_action_enabled:
        return

    if policy.assigns_entry_role and policy.entry_role_id is not None:
        await _grant_entry_role(member, policy.entry_role_id)

    if policy.greet_on_join:
        channel = _resolve_text_channel(guild, policy.channel_id)
        if channel is not None:
            member_count = _member_count(guild)
            embed = format_join_embed(member, policy, member_count)
            card = (
                await _build_welcome_card(member, member_count)
                if policy.renders_card
                else None
            )
            if await _post(channel, embed, card):
                await _emit_greeted(member)


async def handle_member_leave(member: discord.Member) -> None:
    """Post a farewell for a departing member, per the guild policy.

    Fully fail-safe (mirrors :func:`handle_member_join`).
    """
    guild = getattr(member, "guild", None)
    if guild is None:
        return
    try:
        policy = await welcome_config.load_policy(guild.id)
    except Exception:  # noqa: BLE001 — fail open on any config-read fault
        logger.exception("welcome: load_policy failed for guild=%s", guild.id)
        return

    if not policy.greet_on_leave:
        return

    channel = _resolve_text_channel(guild, policy.channel_id)
    if channel is not None:
        embed = format_leave_embed(member, policy, _member_count(guild))
        await _post(channel, embed)


def _member_count(guild: Any) -> int:
    """Best-effort live member count (0 when unavailable on a test double)."""
    return int(getattr(guild, "member_count", 0) or 0)
