"""Patch-notes contract: read API, write chokepoint, new-version signal.

The read API (:func:`latest`) + single write chokepoint (:func:`upsert`)
landed as the M3A seam. :func:`store_parsed_notes` is the M3B fetch-loop
sink: the ingestion service routes ``patch_notes``-kind sources here (the
``steam_btd6_news`` Steam feed is the first), and when it writes a version
strictly newer than the previously-stored latest it emits
``btd6.version_detected`` on the EventBus so
:mod:`services.btd6_version_announce` can post an announcement.
"""

from __future__ import annotations

import logging
from typing import Any

from core.events import bus
from utils.db import btd6_sources as btd6_db

logger = logging.getLogger("bot.services.btd6_patch")

# Emitted by store_parsed_notes when a strictly-newer version is ingested.
# Catalogued in core.events_catalogue.KNOWN_EVENTS; consumed by
# services.btd6_version_announce. Payload: version, previous_version,
# title, url, published_at.
EVT_BTD6_VERSION_DETECTED = "btd6.version_detected"


def _version_key(version: str) -> tuple[int, ...]:
    """Numeric sort key for a BTD6 version string (``"54.0"`` -> ``(54, 0)``).

    Stops at the first non-numeric segment so a tuple compare orders
    ``9.0 < 10.0`` correctly (a plain string compare would not). An
    unparseable version yields ``()``, which sorts below every real
    version — so it can never be mistaken for "newer".
    """
    parts: list[int] = []
    for chunk in version.split("."):
        if chunk.isdigit():
            parts.append(int(chunk))
        else:
            break
    return tuple(parts)


async def latest() -> dict[str, Any] | None:
    return await btd6_db.latest_patch_note()


async def upsert(
    *,
    source_id: int,
    version: str,
    body: str,
    published_at: Any | None = None,
) -> int:
    if not version.strip() or not body.strip():
        raise ValueError("patch note version and body must be non-empty")
    return await btd6_db.upsert_patch_note(
        source_id=source_id,
        version=version,
        body=body,
        published_at=published_at,
    )


async def store_parsed_notes(
    records: list[dict[str, Any]],
    *,
    source_id: int,
) -> list[str]:
    """Upsert a list of parsed patch-note records; return written versions.

    This is the ingestion seam for ``patch_notes``-kind sources (e.g.
    ``steam_btd6_news``): the parser returns ``{"version", "body",
    "published_at", ...}`` dicts and the ingestion service routes them
    here instead of the generic fact store. Records missing a non-empty
    ``version`` or ``body`` are skipped rather than raising, so one
    malformed item can't fail the whole run. Versions are returned in
    write order so the caller can populate ``written_entity_keys``.

    After writing, if the newest version written is strictly newer than
    the latest version already stored (and there *was* a stored latest —
    the first/baseline ingest stays silent), emits
    ``btd6.version_detected``. Detection never disturbs the writes: the
    pre-read and the emit are each guarded so a notification failure can't
    fail an ingestion run whose rows already committed.
    """
    previous_version = await _previous_latest_version()
    written: list[str] = []
    newest: dict[str, Any] | None = None
    for record in records:
        version = str(record.get("version") or "").strip()
        body = str(record.get("body") or "").strip()
        if not version or not body:
            continue
        await upsert(
            source_id=source_id,
            version=version,
            body=body,
            published_at=record.get("published_at"),
        )
        written.append(version)
        if newest is None or _version_key(version) > _version_key(
            str(newest.get("version") or ""),
        ):
            newest = record
    await _maybe_announce_new_version(previous_version, newest)
    return written


async def _previous_latest_version() -> str | None:
    """The latest stored version before this run, or ``None`` if none/error.

    A read failure degrades to ``None`` (treated as baseline), so a transient
    DB hiccup suppresses the announcement rather than failing ingestion.
    """
    try:
        previous = await latest()
    except Exception:  # noqa: BLE001 — detection must never break ingestion
        logger.warning(
            "btd6 patch: failed to read previous latest; "
            "skipping new-version detection this run",
            exc_info=True,
        )
        return None
    if not previous:
        return None
    version = str(previous.get("version") or "").strip()
    return version or None


async def _maybe_announce_new_version(
    previous_version: str | None,
    newest: dict[str, Any] | None,
) -> None:
    """Emit ``btd6.version_detected`` iff a strictly-newer version landed."""
    if newest is None:
        return
    new_version = str(newest.get("version") or "").strip()
    if not new_version:
        return
    # First-ever ingest (no prior stored latest) establishes the baseline
    # silently — we don't announce the version that was already live.
    if not previous_version:
        return
    if _version_key(new_version) <= _version_key(previous_version):
        return
    try:
        await bus.emit(
            EVT_BTD6_VERSION_DETECTED,
            version=new_version,
            previous_version=previous_version,
            title=newest.get("title"),
            url=newest.get("url"),
            published_at=newest.get("published_at"),
        )
    except Exception:  # noqa: BLE001 — emit is best-effort; rows already wrote
        logger.warning(
            "btd6 patch: new-version announce emit failed for %s",
            new_version,
            exc_info=True,
        )


__all__ = ["EVT_BTD6_VERSION_DETECTED", "latest", "store_parsed_notes", "upsert"]
