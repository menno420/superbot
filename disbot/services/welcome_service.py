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

import logging
import random
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
    *,
    rng: random.Random | None = None,
) -> discord.Embed:
    """Build the greeting embed for a joining ``member``.

    When the join message holds multiple ``---``-separated variants, one is
    chosen at random (``rng`` injectable for deterministic tests); a
    single-variant message renders identically.
    """
    description = welcome_config.render_template(
        welcome_config.pick_message(policy.join_message, rng=rng),
        member_name=member.mention,
        guild_name=member.guild.name,
        member_count=member_count,
    )
    embed = discord.Embed(description=description, color=_JOIN_COLOR)
    avatar = getattr(member, "display_avatar", None)
    if avatar is not None:
        embed.set_thumbnail(url=avatar.url)
    return embed


def format_dm_embed(
    member: discord.Member,
    policy: welcome_config.WelcomePolicy,
    member_count: int,
    *,
    rng: random.Random | None = None,
) -> discord.Embed:
    """Build the direct-message greeting embed for a joining ``member``.

    Mirrors :func:`format_join_embed` but renders the dedicated ``dm_message``
    template (which supports the same ``---`` random variants).  No avatar
    thumbnail — a DM already shows the recipient who they are.
    """
    description = welcome_config.render_template(
        welcome_config.pick_message(policy.dm_message, rng=rng),
        member_name=member.mention,
        guild_name=member.guild.name,
        member_count=member_count,
    )
    return discord.Embed(description=description, color=_JOIN_COLOR)


def format_leave_embed(
    member: discord.Member,
    policy: welcome_config.WelcomePolicy,
    member_count: int,
    *,
    rng: random.Random | None = None,
) -> discord.Embed:
    """Build the farewell embed for a departing ``member``.

    Uses the plain name (not a mention) — the member has left, so a mention
    would render as a raw id for anyone who never shared a mutual server.
    Multiple ``---``-separated farewell variants pick one at random (``rng``
    injectable for tests); a single-variant message renders identically.
    """
    description = welcome_config.render_template(
        welcome_config.pick_message(policy.leave_message, rng=rng),
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


_WELCOME_CARD_FILENAME = "welcome.jpg"


def render_join_card(
    member: discord.Member,
    member_count: int,
) -> discord.File | None:
    """Render the phase-2 greeting card as a :class:`discord.File`, or ``None``.

    Pure / no-network (the avatar is an initials disc — the embed still carries
    the member's real avatar thumbnail).  Returns ``None`` when Pillow is
    unavailable so the caller posts the embed-only greeting unchanged.
    """
    import io

    from utils.welcome_render import render_welcome_card

    jpeg = render_welcome_card(
        member_name=member.display_name,
        server_name=member.guild.name,
        member_number=member_count,
    )
    if jpeg is None:
        return None
    return discord.File(io.BytesIO(jpeg), filename=_WELCOME_CARD_FILENAME)


async def _post(
    channel: discord.abc.Messageable,
    embed: discord.Embed,
    file: discord.File | None = None,
    *,
    delete_after: float | None = None,
) -> bool:
    """Send ``embed`` (plus optional ``file``) — fail-safe (logs, never raises).

    ``delete_after`` (ping-then-delete) is forwarded to discord.py's native
    ``send`` so the message self-deletes after that many seconds; ``None`` keeps
    it.  Only ``None`` is passed to ``send`` when unset so the call shape is
    unchanged for every existing config.
    """
    try:
        if file is not None:
            await channel.send(embed=embed, file=file, delete_after=delete_after)
        else:
            await channel.send(embed=embed, delete_after=delete_after)
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


async def _send_dm(member: discord.Member, embed: discord.Embed) -> None:
    """DM the joining ``member`` the greeting — fail-safe (logs, never raises).

    A closed-DM member raises :class:`discord.Forbidden`; that (and any other
    send fault) is swallowed so a DM that can't be delivered never affects the
    channel greeting, the entry-role grant, or the join dispatch.
    """
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        logger.info(
            "welcome: member %s has DMs closed — skipping DM greeting",
            member.id,
        )
    except discord.HTTPException as exc:
        logger.warning("welcome: HTTP error sending DM greeting: %s", exc)
    except Exception:  # noqa: BLE001 — fail-safe wrapper
        logger.exception("welcome: unexpected error sending DM greeting")


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

    Fully fail-safe: a fault loading the policy, granting the role, posting the
    channel greeting, or sending the optional DM greeting is logged and
    swallowed so the join dispatch always completes.  The actions are
    independent — any one failing does not skip the others.
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

    # Join-delay age-gating (anti-raid): a member whose account is younger than
    # the configured threshold gets NO greeting, NO DM, and NO entry role.
    # Off (skipped) when the gate is unset, so existing configs are unchanged.
    if policy.age_gate_enabled and _account_too_young(member, policy):
        logger.info(
            "welcome: member %s account too young (< %d days) — skipping "
            "greeting/DM/entry-role in guild %s",
            member.id,
            policy.min_account_age_days,
            guild.id,
        )
        return

    if policy.assigns_entry_role and policy.entry_role_id is not None:
        await _grant_entry_role(member, policy.entry_role_id)

    # The channel greeting and the optional DM greeting are independent — a
    # member with closed DMs still gets the channel greeting and vice versa.
    count = _member_count(guild)

    if policy.greet_on_join:
        channel = _resolve_text_channel(guild, policy.channel_id)
        if channel is not None:
            embed = format_join_embed(member, policy, count)
            file: discord.File | None = None
            if policy.show_join_card:
                file = render_join_card(member, count)
                if file is not None:
                    embed.set_image(url=f"attachment://{_WELCOME_CARD_FILENAME}")
            if await _post(
                channel,
                embed,
                file,
                delete_after=policy.greeting_delete_after,
            ):
                await _emit_greeted(member)

    if policy.dm_on_join:
        await _send_dm(member, format_dm_embed(member, policy, count))


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
        await _post(channel, embed, delete_after=policy.greeting_delete_after)


def _account_too_young(
    member: discord.Member,
    policy: welcome_config.WelcomePolicy,
) -> bool:
    """True when ``member``'s account is below the policy's age gate.

    Thin wrapper over the pure :func:`welcome_config.account_is_too_young` that
    supplies the current time; fail-open (greets) on a missing ``created_at``.
    """
    return welcome_config.account_is_too_young(
        getattr(member, "created_at", None),
        min_age_days=policy.min_account_age_days,
        now=discord.utils.utcnow(),
    )


def _member_count(guild: Any) -> int:
    """Best-effort live member count (0 when unavailable on a test double)."""
    return int(getattr(guild, "member_count", 0) or 0)
