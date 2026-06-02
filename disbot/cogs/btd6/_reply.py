"""Shared ephemeral reply backbone for BTD6 slash twins.

Extracted from ``BTD6Cog._reply`` when the BTD6 command surface was split
across sibling cogs (``btd6_reference_cog`` / ``btd6_events_cog`` /
``btd6_strategy_cog``). All four cogs route their single-payload slash
commands through :func:`reply_ephemeral` so the ``safe_defer → build →
safe_followup`` ordering lives in exactly one place rather than being
duplicated per cog (helper-policy: a function needed by multiple cogs in
the same domain belongs in the shared ``cogs/btd6`` helper package).

Commands that need a non-standard response shape — multiple followups
(``pending``), a modal (``submit``), or a synchronous
``interaction.response.send_message`` — keep their own inline handling and
do not use this helper.
"""

from __future__ import annotations

from collections.abc import Awaitable

import discord

from core.runtime.interaction_helpers import safe_defer, safe_followup


async def reply_ephemeral(
    interaction: discord.Interaction,
    payload_coro: Awaitable[discord.Embed | str],
) -> None:
    """Defer ephemerally, await the builder, then follow up.

    ``str`` payloads go as content, embeds as embeds. Deferring *before*
    awaiting the builder keeps DB/service latency from tripping the 3-second
    interaction token window.
    """
    if not await safe_defer(interaction, ephemeral=True):
        return
    payload = await payload_coro
    key = "content" if isinstance(payload, str) else "embed"
    await safe_followup(interaction, ephemeral=True, **{key: payload})
