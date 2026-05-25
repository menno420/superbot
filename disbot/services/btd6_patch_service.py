"""Patch-notes contract (M3A seam).

M3A ships the read API + a single write chokepoint; M3B wires the
fetch loop once the patch-notes endpoint format is captured.
"""

from __future__ import annotations

import logging
from typing import Any

from utils.db import btd6_sources as btd6_db

logger = logging.getLogger("bot.services.btd6_patch")


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


__all__ = ["latest", "upsert"]
