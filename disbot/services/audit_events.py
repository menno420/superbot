"""Shared ``audit.action_recorded`` publisher.

Phase 9c.2 — every mutation pipeline that lands a row in an audit log
must also emit the generic ``audit.action_recorded`` event so the
audit-routing subscriber in :mod:`services.server_logging` can render
a single canonical embed to ``logging.audit_channel`` (with mod
fallback).

This module exists to keep the payload contract in one place. Pipelines
import :func:`emit_audit_action` and pass the canonical 11 fields; the
payload sent on the bus is identical regardless of pipeline.

Payload contract (11 fields, all keyword-only):

* ``mutation_id``   — pipeline-issued UUID linking the bus event back
                      to the audit DB row.
* ``subsystem``     — high-level area (``"logging"`` for rollout,
                      ``"settings"`` for settings_mutation, etc.).
* ``mutation_type`` — pipeline-specific verb token
                      (``"set_flag_state"``, ``"upsert_binding"``, …).
* ``target``        — human-resolvable identifier of the thing changed
                      (``"flag:bindings.primary"``, ``"binding:counting"``).
* ``scope``         — ``"global"`` or ``"guild"`` (string; type stays
                      open so future scopes don't require a refactor).
* ``guild_id``      — discord guild ID or ``None`` for global scope.
* ``prev_value``    — string-rendered prior value, or ``None`` for
                      first-time writes.
* ``new_value``     — string-rendered new value, or ``None`` for
                      deletes / clears.
* ``actor_id``      — discord user ID or ``None`` for system/backfill.
* ``actor_type``    — capability-resolver actor type token.
* ``occurred_at``   — ISO-8601 timestamp string serialized from the
                      DB commit ``datetime``.

Publishers may append additive, publisher-specific fields via the
optional ``extra_fields`` mapping (mineverse WRITE-contract audit rows
carry action_id/params_digest/origin etc.); the canonical 11 always win
a key collision and subscribers accept extras (``**_extras``).

The helper is failure-safe: if the event bus raises, the exception is
logged with ``exc_info=True`` and the helper returns ``False``.  DB
state is authoritative; a dropped audit event is non-fatal. Callers
do not need to check the return value, but it is provided as a
diagnostic for tests and future metric counters.
"""

from __future__ import annotations

import logging
from datetime import datetime

EVT_AUDIT_ACTION_RECORDED = "audit.action_recorded"

logger = logging.getLogger("bot.services.audit_events")


def _log_safe(value: object) -> str:
    """Newline-scrubbed rendering for log interpolation.

    Some publishers (the mineverse write endpoint) derive ``mutation_id`` /
    ``mutation_type`` from request material; scrubbing CR/LF here keeps the
    failure log line-injection-proof regardless of publisher discipline
    (CodeQL py/log-injection hygiene — enforce at the sink, not by trust).
    """
    return str(value).replace("\r", "\\r").replace("\n", "\\n")


async def emit_audit_action(
    *,
    mutation_id: str,
    subsystem: str,
    mutation_type: str,
    target: str,
    scope: str,
    guild_id: int | None,
    prev_value: str | None,
    new_value: str | None,
    actor_id: int | None,
    actor_type: str,
    occurred_at: datetime,
    extra_fields: dict[str, object] | None = None,
) -> bool:
    """Emit ``audit.action_recorded`` for a single mutation.

    See module docstring for the payload contract. Returns ``True`` on
    successful emit, ``False`` on bus failure (diagnostic only — the
    caller's DB state is authoritative either way).

    ``extra_fields`` (additive, 2026-07-13 — mineverse WRITE contract):
    optional publisher-specific payload fields merged into the bus event
    alongside the canonical 11.  The audit subscriber already tolerates
    extras (``**_extras`` in ``server_logging._on_audit_action``).  The
    canonical fields always win a key collision — publishers cannot
    shadow the shared contract.
    """
    from core.events import bus

    try:
        await bus.emit(
            EVT_AUDIT_ACTION_RECORDED,
            **{
                **(extra_fields or {}),
                "mutation_id": mutation_id,
                "subsystem": subsystem,
                "mutation_type": mutation_type,
                "target": target,
                "scope": scope,
                "guild_id": guild_id,
                "prev_value": prev_value,
                "new_value": new_value,
                "actor_id": actor_id,
                "actor_type": actor_type,
                "occurred_at": occurred_at.isoformat(),
            },
        )
    except Exception:
        logger.exception(
            "audit.action_recorded emission failed for "
            "mutation_id=%s (subsystem=%s, type=%s); DB state is correct, "
            "event lost.",
            _log_safe(mutation_id),
            _log_safe(subsystem),
            _log_safe(mutation_type),
        )
        return False
    return True
