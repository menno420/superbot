"""Helpers extracted from ``btd6_cog`` so the cog file stays under the
S4.6 800-LOC cap.

Two payload builders live here:

* :func:`build_refresh_source_payload` — manual ``refresh-source``
  command (was previously :meth:`BTD6Cog._build_refresh_source_payload`;
  moved as part of the admin-panel PR). Behaviour unchanged.
* :func:`build_event_payload` — new ``!btd6 event <kind> <id>`` lookup;
  fetches both the index fact and (when applicable) the ``*_metadata``
  fact so the embed can render ``_towers`` restrictions.

These are deliberately module-level functions, not methods, so the
admin view in ``views/btd6/admin_panel.py`` can also call
``build_refresh_source_payload`` without depending on the cog instance.
"""

from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.cogs.btd6")


async def build_refresh_source_payload(
    source_key: str,
    *,
    started_by_user_id: int,
    include_exception_detail: bool,
) -> discord.Embed:
    """Run one manual refresh and render the result embed.

    Routes through the public orchestration helper so we never reach
    into ``btd6_ingestion_service._DEPENDENCY_CHAINS``. Exception
    handling and the unknown-source known-keys fallback are unified
    here so prefix / slash / admin-panel surfaces can't drift.
    """
    from cogs.btd6._builders import build_refresh_source_embed
    from services import btd6_ingestion_service, btd6_source_registry

    try:
        results = await btd6_ingestion_service.refresh_source_or_dependencies(
            source_key,
            reason="manual",
            started_by_user_id=started_by_user_id,
        )
    except Exception as exc:  # noqa: BLE001 — surfaced via embed
        logger.exception("manual refresh failed for %s", source_key)
        return build_refresh_source_embed(
            source_key,
            results=[],
            exception=exc,
            include_exception_detail=include_exception_detail,
        )

    known_keys: list[str] | None = None
    if len(results) == 1 and results[0].error_code == "source_not_registered":
        try:
            rows = await btd6_source_registry.list_all()
        except Exception:  # noqa: BLE001 — best-effort enrichment
            logger.exception("failed to load BTD6 known source keys")
            rows = []
        known_keys = [row["source_key"] for row in rows]

    return build_refresh_source_embed(
        source_key,
        results,
        known_source_keys=known_keys,
    )


async def build_event_payload(kind: str, entity_key: str) -> discord.Embed:
    """Fetch the index fact + metadata fact for one event and render it.

    Accepts either the full ``btd6_<kind>`` form or the short
    ``<kind>`` form (race / boss / ct / odyssey / event). The
    ``*_metadata`` fact is only queried for kinds that have one in the
    registry — race, boss, odyssey. Missing data degrades gracefully:
    if neither row exists the builder renders an empty-state embed.
    """
    from cogs.btd6._builders import build_event_detail_embed
    from utils.db import btd6_sources as btd6_db

    norm = kind if kind.startswith("btd6_") else f"btd6_{kind}"

    row = await btd6_db.get_latest_fact(None, norm, entity_key)

    metadata_row = None
    metadata_fact_type = {
        "btd6_race": "btd6.race_metadata",
        "btd6_boss": "btd6.boss_metadata",
        "btd6_odyssey": "btd6.odyssey_diff",
    }.get(norm)
    if metadata_fact_type is not None:
        # Odyssey uses a different entity_kind for its metadata
        # (btd6_odyssey_difficulty); race / boss reuse the index kind.
        if norm == "btd6_odyssey":
            metadata_row = await btd6_db.get_latest_fact(
                metadata_fact_type,
                "btd6_odyssey_difficulty",
                entity_key,
            )
            # Try entity_key with the hardcoded difficulty suffix too —
            # the parser composes f"{odysseyID}" as the entity_key for
            # odyssey_diff facts. Best effort; either form is fine.
            if metadata_row is None:
                metadata_row = await btd6_db.get_latest_fact(
                    metadata_fact_type,
                    "btd6_odyssey_difficulty",
                    f"{entity_key}_easy",
                )
        else:
            md_entity_key = entity_key
            if norm == "btd6_boss":
                md_entity_key = f"{entity_key}_normal"  # difficulty hardcoded
            metadata_row = await btd6_db.get_latest_fact(
                metadata_fact_type,
                "btd6_boss_difficulty" if norm == "btd6_boss" else norm,
                md_entity_key,
            )

    return build_event_detail_embed(
        norm,
        entity_key,
        row,
        metadata_row=metadata_row,
    )


__all__ = [
    "build_event_payload",
    "build_refresh_source_payload",
]
