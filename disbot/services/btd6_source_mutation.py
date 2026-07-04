"""Single mutation owner for ``btd6_source_registry`` (M3A).

Every write goes through here so the ``btd6_source_audit`` row is
recorded in the same transaction. No cog / view / direct DB write
may touch the registry — pinned by
``tests/unit/services/test_btd6_source_mutation.py``.

M3A adds the contract; M3B extends with cadence updates and the
``enabled=TRUE`` flip for first-priority NK API endpoints.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from utils.db import btd6_sources as btd6_db

logger = logging.getLogger("bot.services.btd6_source_mutation")


class BTD6SourceMutationError(Exception):
    pass


class UnauthorizedSourceMutationError(BTD6SourceMutationError):
    pass


class InvalidSourceValueError(BTD6SourceMutationError):
    pass


@dataclass(frozen=True)
class SourceMutationResult:
    mutation_id: str
    source_key: str
    action: str
    source_id: int


_VALID_KINDS = frozenset({"webpage", "official_api", "patch_notes"})
_VALID_TIERS = frozenset({1, 2})


def _check_admin(actor: Any) -> int | None:
    if actor is None:
        raise UnauthorizedSourceMutationError("actor is required")
    # Platform-owner override: the configured bot owner administers config in any
    # guild, even without Discord admin there (single source: config).
    from config import is_platform_owner

    actor_id = getattr(actor, "id", None)
    if is_platform_owner(actor_id):
        return actor_id
    perms = getattr(actor, "guild_permissions", None)
    if perms is None or not getattr(perms, "administrator", False):
        raise UnauthorizedSourceMutationError(
            "btd6 source mutations require administrator permission",
        )
    return actor_id


async def upsert_source(
    *,
    source_key: str,
    source_name: str,
    source_owner: str,
    source_kind: str,
    trust_tier: int,
    base_url: str | None,
    path_template: str | None,
    cache_policy_key: str | None = None,
    enabled: bool = False,
    notes: str = "",
    actor: Any,
    reason: str | None = None,
) -> SourceMutationResult:
    """Create or update a source row + write the matching audit row."""
    actor_id = _check_admin(actor)
    if source_kind not in _VALID_KINDS:
        raise InvalidSourceValueError(
            f"source_kind must be one of {sorted(_VALID_KINDS)}, "
            f"got {source_kind!r}",
        )
    if trust_tier not in _VALID_TIERS:
        raise InvalidSourceValueError(
            f"trust_tier must be one of {sorted(_VALID_TIERS)}, got {trust_tier!r}",
        )
    if not source_key.strip():
        raise InvalidSourceValueError("source_key must be non-empty")

    before = await btd6_db.get_source_by_key(source_key)
    full_url = (
        f"{base_url.rstrip('/')}{path_template}" if base_url and path_template else None
    )

    source_id = await btd6_db.upsert_source(
        source_key=source_key,
        source_name=source_name,
        source_owner=source_owner,
        source_kind=source_kind,
        trust_tier=trust_tier,
        base_url=base_url,
        path_template=path_template,
        full_url=full_url,
        cache_policy_key=cache_policy_key,
        enabled=enabled,
        notes=notes,
        updated_by=actor_id,
    )

    action = "created" if before is None else "updated"
    if before is not None and bool(before.get("enabled")) != bool(enabled):
        action = "enabled" if enabled else "disabled"
    if before is not None and int(before.get("trust_tier", 0)) != int(trust_tier):
        action = "tier_changed"

    await btd6_db.record_source_audit(
        source_key=source_key,
        action=action,
        old_value=before,
        new_value={
            "source_key": source_key,
            "source_name": source_name,
            "source_owner": source_owner,
            "source_kind": source_kind,
            "trust_tier": trust_tier,
            "base_url": base_url,
            "path_template": path_template,
            "enabled": enabled,
            "notes": notes,
        },
        actor_id=actor_id,
        guild_id=None,
        reason=reason,
    )

    return SourceMutationResult(
        mutation_id=uuid.uuid4().hex,
        source_key=source_key,
        action=action,
        source_id=source_id,
    )


async def set_enabled(
    source_key: str,
    *,
    enabled: bool,
    actor: Any,
    reason: str | None = None,
) -> SourceMutationResult:
    """Flip ``enabled`` for an existing row; records an audit row."""
    actor_id = _check_admin(actor)
    before = await btd6_db.get_source_by_key(source_key)
    if before is None:
        raise InvalidSourceValueError(
            f"unknown source_key={source_key!r}; create it first",
        )
    if enabled and not before.get("base_url"):
        raise InvalidSourceValueError(
            f"refusing to enable {source_key!r}: base_url is NULL — "
            "confirm the NK API base URL before flipping",
        )

    source_id = await btd6_db.upsert_source(
        source_key=before["source_key"],
        source_name=before["source_name"],
        source_owner=before["source_owner"],
        source_kind=before["source_kind"],
        trust_tier=int(before["trust_tier"]),
        base_url=before.get("base_url"),
        path_template=before.get("path_template"),
        full_url=before.get("full_url"),
        cache_policy_key=before.get("cache_policy_key"),
        enabled=enabled,
        notes=before.get("notes", ""),
        updated_by=actor_id,
    )
    await btd6_db.record_source_audit(
        source_key=source_key,
        action="enabled" if enabled else "disabled",
        old_value=before,
        new_value={**before, "enabled": enabled},
        actor_id=actor_id,
        guild_id=None,
        reason=reason,
    )
    return SourceMutationResult(
        mutation_id=uuid.uuid4().hex,
        source_key=source_key,
        action="enabled" if enabled else "disabled",
        source_id=source_id,
    )


__all__ = [
    "BTD6SourceMutationError",
    "InvalidSourceValueError",
    "SourceMutationResult",
    "UnauthorizedSourceMutationError",
    "set_enabled",
    "upsert_source",
]
