"""Live sign-up counter for role menus — the member-facing headcount.

When a role menu has ``show_counts`` on (migration 103), its public embed shows a
**live participant count** beside each role plus a distinct-member total — the
event-RSVP counter the owner asked for ("how many people pressed the button").

Two design choices make it correct and cheap:

* **Current holders, not a stored tally.** The count is derived live from the
  member cache (``guild.members`` ∩ the menu's roles) at render time, so it is
  self-correcting — it drops when a member un-signs or leaves, and there is no
  counter to drift. (This is deliberately *distinct* from the operator-only
  cumulative ``role_menu_pickup_stats`` rollup, which counts lifetime pickup
  EVENTS for Diagnostics.) The bot runs the members intent + startup chunking,
  so the cache is populated.
* **Debounced refresh.** A click schedules a trailing-edge message edit
  (:data:`_DEBOUNCE_SECONDS`); a burst of clicks on a popular event coalesces
  into at most one edit per window per message, so the counter feels live without
  risking Discord's edit rate-limit. The refresh re-reads counts live, so clicks
  during the window are captured by the single trailing edit.

Layer: a ``views`` helper over the audited ``reaction_role_service`` reads (no DB
writes, no role math). The view module imports the pure helpers here; this module
imports the view's embed builder lazily inside the refresh to avoid an import cycle.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

import discord

from core.runtime import resources
from utils import role_menu_presentation as presentation

logger = logging.getLogger("bot.views.role_menu_counter")

# Discord's embed-field value cap; a roster option's member list is truncated to
# fit, with an "…and N more" tail naming how many were elided.
_ROSTER_FIELD_CAP = 1024

# Coalesce a click-burst into one message edit per window per message. In-memory
# only: a refresh lost to a restart is harmless — the next click re-renders and
# the underlying count is always read live (game/UI state is not restart-safe by
# design, ADR-002).
_DEBOUNCE_SECONDS = 2.5
_pending: dict[int, asyncio.Task] = {}


def collect_counts(
    guild: discord.Guild,
    role_ids: Sequence[int],
) -> tuple[dict[int, int], int]:
    """Per-role current-holder counts + the distinct-member total, in ONE pass.

    Returns ``({role_id: holders}, distinct_total)`` where ``distinct_total`` is
    the number of members holding **at least one** of ``role_ids`` (so a member
    with two of the menu's roles counts once — never double-counted). Derived live
    from the member cache; roles absent from the cache count as 0. One pass over
    ``guild.members`` keeps it ``O(members × |role_ids|)`` regardless of role count.
    """
    wanted = {int(r) for r in role_ids}
    per_role: dict[int, int] = {rid: 0 for rid in wanted}
    distinct = 0
    if not wanted:
        return per_role, distinct
    for member in getattr(guild, "members", None) or []:
        held = wanted.intersection(r.id for r in member.roles)
        if held:
            distinct += 1
            for rid in held:
                per_role[rid] += 1
    return per_role, distinct


def format_count(n: int) -> str:
    """Render a holder count as a compact inline badge (e.g. ``👥 12``)."""
    return f"👥 {n}"


def format_total(total: int) -> str:
    """Render the distinct-member total as the footer headcount line."""
    noun = "person" if total == 1 else "people"
    return f"👥 {total} {noun} signed up"


def _join_members(members: Sequence[discord.Member]) -> str:
    """Join member mentions, truncated to one embed field with an "…and N more" tail.

    Mentions render as clickable names and never ping inside an embed. A busy
    option (hundreds of holders) is cut to fit Discord's 1024-char field cap;
    the tail names how many were elided so the count still reads honestly.
    """
    mentions = [m.mention for m in members]
    if not mentions:
        return "—"
    shown: list[str] = []
    used = 0
    for mention in mentions:
        sep = 1 if shown else 0
        # Reserve room for a possible "…and N more" tail.
        if used + sep + len(mention) > _ROSTER_FIELD_CAP - 20 and shown:
            break
        shown.append(mention)
        used += sep + len(mention)
    text = " ".join(shown)
    hidden = len(mentions) - len(shown)
    if hidden:
        text += f"\n…and {hidden} more"
    return text


def build_roster_embed(
    menu: dict | None,
    options: Sequence[dict],
    guild: discord.Guild,
) -> discord.Embed:
    """Render "who's in" for a counted menu — one field per option + its holders.

    The roster reads **current holders** live (``role.members``) — the same
    primitive as the counter — so it never needs stored per-user history. Options
    whose role was deleted are skipped; an option with no holders reads "—". The
    member list per option is truncated to fit the embed (see :func:`_join_members`).
    """
    theme = presentation.get_theme((menu or {}).get("theme"))
    title = (menu or {}).get("title") or "Pick your roles"
    embed = discord.Embed(title=f"👥 Who's in — {title}", color=theme.color)
    any_option = False
    for opt in options:
        role = resources.resolve_role(guild, role_id=int(opt["role_id"]))
        if role is None:
            continue
        any_option = True
        label = opt.get("label") or role.name
        members = sorted(
            getattr(role, "members", []),
            key=lambda m: (m.display_name or "").lower(),
        )
        embed.add_field(
            name=f"{label} · {len(members)}",
            value=_join_members(members),
            inline=False,
        )
    if not any_option:
        embed.description = "This menu has no live roles right now."
    return embed


def schedule_count_refresh(
    message: discord.Message | None,
    menu_id: int,
) -> None:
    """Debounced: re-render a counted menu's embed so its live counts update.

    Coalesces a click-burst into one trailing edit per :data:`_DEBOUNCE_SECONDS`
    window per message. No-op when there is no message or a refresh is already
    pending for it, or when called outside a running event loop (e.g. a unit test
    that asserts on the scheduling decision). Best-effort — see :func:`_run_refresh`.
    """
    if message is None:
        return
    mid = message.id
    existing = _pending.get(mid)
    if existing is not None and not existing.done():
        return  # a trailing edit is already scheduled; it re-reads live counts
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # pragma: no cover - only outside an event loop
        return
    _pending[mid] = loop.create_task(_run_refresh(message, menu_id))


async def _run_refresh(message: discord.Message, menu_id: int) -> None:
    """Wait out the debounce window, then edit the menu message with live counts.

    Re-reads the menu + options + counts at edit time so the figure is current.
    Bails cleanly if the menu was deleted or its counts were turned off mid-window.
    Cosmetic, so every failure mode is swallowed — the role mutation that
    triggered the refresh already succeeded and must never be undone by a bad edit.
    """
    # Lazy imports: the view module imports this one at top level, so importing it
    # back here would be a cycle.
    from services import reaction_role_service
    from views.roles.role_menu_view import build_menu_embed

    try:
        await asyncio.sleep(_DEBOUNCE_SECONDS)
        guild = message.guild
        if guild is None:
            return
        menu = await reaction_role_service.get_menu(menu_id)
        if menu is None or not menu.get("show_counts"):
            return
        opts = await reaction_role_service.get_menu_options(menu_id)
        options = [
            {"role_id": o.role_id, "emoji": o.emoji, "label": o.label} for o in opts
        ]
        embed = build_menu_embed(menu, options, guild)
        # Re-reference an existing banner-card attachment without re-uploading it
        # (editing the embed alone keeps the message's current attachments).
        if message.attachments:
            embed.set_image(url=f"attachment://{message.attachments[0].filename}")
        await message.edit(embed=embed)
    except discord.HTTPException:
        pass  # message gone / not editable / rate-limited — counter is cosmetic
    except Exception:  # noqa: BLE001 — a refresh must never crash the click path
        logger.debug("role_menu_counter: count refresh failed", exc_info=True)
    finally:
        _pending.pop(message.id, None)


__all__ = [
    "build_roster_embed",
    "collect_counts",
    "format_count",
    "format_total",
    "schedule_count_refresh",
]
