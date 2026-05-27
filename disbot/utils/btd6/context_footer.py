"""Append a stable ``ctx=<context_id>`` segment to an embed footer.

The ``context_id`` contract — pinned by :func:`services.btd6_view_model_service.make_context_handle`
to ``^btd6_[a-z_]+:[A-Za-z0-9_-]+$`` — is the handle a future Team
Panel will attach notes / assignments / strategies to. Every
stable-content BTD6 embed surfaces it in the footer so the contract
travels with the rendered message.

This module is the single source of truth for footer manipulation.
Three rules:

1. Preserve existing footer text (e.g. "Sources: x, y").
2. Preserve footer icon_url if present.
3. Idempotent — calling twice with the same context_id is a no-op.

Lives in ``utils/`` so both ``cogs/btd6/_builders.py`` (existing
embed builders) and ``views/btd6/`` (PR 2 drill-down detail views)
can apply the same footer without crossing layer boundaries.
"""

from __future__ import annotations

import discord

# The full marker including the leading separator. Used both to format
# the new segment and to detect idempotent re-application.
_MARKER_PREFIX = " • ctx="


def append_context_footer(
    embed: discord.Embed,
    context_id: str,
) -> discord.Embed:
    """Append ``" • ctx=<context_id>"`` to ``embed`` footer.

    Returns the same embed for fluent chaining.

    Raises:
        ValueError: if ``context_id`` is empty (callers must opt out
            by simply not calling this helper).
    """
    if not context_id:
        raise ValueError("context_id must not be empty")

    existing_text = embed.footer.text or ""
    existing_icon = embed.footer.icon_url

    new_segment = f"{_MARKER_PREFIX}{context_id}"

    # Idempotent: if the footer already ends with this exact segment,
    # don't append again.
    if existing_text.endswith(new_segment):
        return embed

    # If a different ctx segment exists, replace it rather than
    # appending a second one — callers that re-render the same embed
    # with a refreshed context_id deserve a single live segment.
    marker_idx = existing_text.rfind(_MARKER_PREFIX)
    if marker_idx != -1:
        existing_text = existing_text[:marker_idx]

    # When there was no prior text, the marker is the entire footer
    # (skip the leading " • " separator).
    new_text = (
        f"{existing_text}{new_segment}" if existing_text else f"ctx={context_id}"
    )

    embed.set_footer(text=new_text, icon_url=existing_icon)
    return embed


__all__ = ["append_context_footer"]
