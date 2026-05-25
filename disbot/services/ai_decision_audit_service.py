"""Persistent AI decision audit — M2 single chokepoint.

Every natural-language stage invocation produces exactly one
``ai_decision_audit`` row via :func:`record`. The diagnostic
commands (``/ai audit``, ``/ai why-no-response``, the filtered
``/btd6 why-no-response`` view) read through :func:`query`.

No raw message content is stored — the table holds the join key
(``message_id``) plus structured decision metadata. A redaction
policy that would lift raw text into the audit row is deferred.
"""

from __future__ import annotations

import logging
from typing import Any

from core.runtime.ai.contracts import PolicyDenialReason
from utils.db import ai as ai_db

logger = logging.getLogger("bot.services.ai_decision_audit")


_VALID_DECISIONS = frozenset(
    {"allowed", "denied", "skipped", "replied", "degraded", "errored"},
)


async def record(
    *,
    guild_id: int,
    channel_id: int,
    category_id: int | None,
    user_id: int,
    message_id: int | None,
    task: str | None,
    route: str | None,
    decision: str,
    reason_code: PolicyDenialReason | str,
    policy_snapshot_hash: str | None = None,
    instruction_profile_ids: list[int] | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> int:
    """Write one row; returns the new ``id``.

    Raises ``ValueError`` for unknown ``decision`` values so a typo
    surfaces at the call site rather than silently corrupting the
    audit table.
    """
    if decision not in _VALID_DECISIONS:
        raise ValueError(
            f"decision must be one of {sorted(_VALID_DECISIONS)}, "
            f"got {decision!r}",
        )
    reason_value = (
        reason_code.value if isinstance(reason_code, PolicyDenialReason)
        else str(reason_code)
    )
    # Success rows always carry the sentinel reason_code='none'.
    if decision in ("allowed", "replied") and reason_value != "none":
        reason_value = "none"

    return await ai_db.record_decision(
        guild_id=guild_id,
        channel_id=channel_id,
        category_id=category_id,
        user_id=user_id,
        message_id=message_id,
        task=task,
        route=route,
        decision=decision,
        reason_code=reason_value,
        policy_snapshot_hash=policy_snapshot_hash,
        instruction_profile_ids=instruction_profile_ids,
        provider=provider,
        model=model,
    )


async def query(
    guild_id: int,
    *,
    channel_id: int | None = None,
    user_id: int | None = None,
    decision: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    return await ai_db.query_decisions(
        guild_id,
        channel_id=channel_id,
        user_id=user_id,
        decision=decision,
        limit=limit,
    )


__all__ = ["query", "record"]
