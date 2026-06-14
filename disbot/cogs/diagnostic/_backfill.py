"""Orchestration for ``!platform backfill`` (legacy-pointer → binding migration).

Kept out of ``diagnostic_cog.py`` (which is at the 800-LOC cog ceiling) and out of
``_platform_embeds.py`` (pure renderers): this helper does channel I/O + the
audited service mutation, so it lives in its own module. The cog command is a thin
wrapper that delegates here.

It completes the P0-3 pointer-lane convergence (plan §8): the retired
``xp.announce_channel`` / ``economy.log_channel`` pointers fall back to legacy KV
until their binding rows exist; ``apply`` writes those rows via the audited
``services.binding_backfill.apply_backfill`` seam, clearing the Config-arbitration
fallback consistency warning.
"""

from __future__ import annotations

from typing import Any

from cogs.diagnostic._platform_embeds import (
    build_backfill_apply_embed,
    build_backfill_dryrun_embed,
)


async def handle_platform_backfill(ctx: Any, action: str) -> None:
    """Dry-run (default) or ``apply`` the binding backfill for ``ctx.guild``.

    ``action == "apply"`` writes the ``candidate_valid`` rows (idempotent,
    advisory-lock guarded, audited as ``actor_type='backfill'``); anything else
    is a read-only dry-run preview.
    """
    from services import binding_backfill

    if ctx.guild is None:
        await ctx.send("⚠️ This command must be run in a guild.", delete_after=15)
        return

    if action.lower() == "apply":
        try:
            result = await binding_backfill.apply_backfill(
                ctx.guild,
                actor_id=ctx.author.id,
            )
        except binding_backfill.BackfillLockHeldError:
            await ctx.send(
                "⏳ A backfill is already running for this guild — "
                "try again in a moment.",
                delete_after=15,
            )
            return
        await ctx.send(embed=build_backfill_apply_embed(result))
        return

    summary = await binding_backfill.dry_run(ctx.guild)
    await ctx.send(embed=build_backfill_dryrun_embed(summary))
