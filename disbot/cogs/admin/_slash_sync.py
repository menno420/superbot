"""Global slash-tree sync rendering for ``!syncslash global``.

Extracted from ``cogs/admin_cog.py`` to keep that file under the S4.6 800-LOC
ceiling. The module owns the *logic + operator-message rendering* for the
``global`` scope; the cog method stays a thin "run it and send the string".

The default (un-forced) global path flows through the diff-gated
:func:`services.command_tree_sync.auto_sync_if_changed` — the same helper the
startup auto-sync uses — so a manual sync only burns a (rate-limited) global
sync when the command *paths* actually changed, and previews the diff. ``force``
keeps the old unconditional ``tree.sync()`` for parameter/description-only
changes the conservative path-diff deliberately misses.
"""

from __future__ import annotations

import discord

from services import command_tree_sync


def format_sync_diff(
    added: tuple[str, ...],
    removed: tuple[str, ...],
) -> str:
    """One-line ``+N added / -M removed`` summary with a short path preview."""
    summary = f"+{len(added)} added, -{len(removed)} removed"
    preview = list(added[:5]) + [f"-{p}" for p in removed[:5]]
    if preview:
        summary += " — " + ", ".join(f"`{p}`" for p in preview)
    return summary


async def run_global_sync(bot: object, *, force: bool) -> str:
    """Sync (or diff-check) the global command tree and return the operator
    message to display. Never raises — a sync failure is rendered as text.
    """
    tree = bot.tree  # type: ignore[attr-defined]

    if force:
        try:
            synced = await tree.sync()
        except discord.HTTPException as exc:
            return f"⚠️ Global sync failed: `{type(exc).__name__}`: {exc}"
        return (
            f"✅ Force-synced **{len(synced)}** slash commands globally. "
            "Propagation may take up to an hour."
        )

    outcome = await command_tree_sync.auto_sync_if_changed(bot, enabled=True)
    if outcome.reason == "fetch_failed":
        return (
            "⚠️ Couldn't fetch the live command list from Discord (logged). "
            "Try again, or `!syncslash global force` to sync anyway."
        )
    if outcome.reason == "unchanged":
        return (
            "✅ Global command tree already in sync — nothing to do. "
            "(Use `!syncslash global force` to resync param/description-only "
            "changes the path diff doesn't see.)"
        )

    diff = format_sync_diff(outcome.added, outcome.removed)
    if outcome.reason == "sync_failed":
        return (
            f"⚠️ The tree changed ({diff}) but `tree.sync()` failed (logged). "
            "Try again shortly."
        )
    return (
        f"✅ Synced global slash commands ({diff}). Propagation may take up to an hour."
    )
