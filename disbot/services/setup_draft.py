"""Setup draft staging service.

Wraps :mod:`utils.db.setup_draft` with the operator-facing surface the
Setup Wizard's sections call.  Sections never apply mutations directly;
they call :func:`append` to stage a :class:`services.setup_operations.SetupOperation`
into the per-guild draft, and Final Review later drains the draft via
:func:`list_ops` + :func:`clear`.

Lifecycle:

* :func:`append` — section emits one op; the draft replaces an
  existing slot or appends a new row.  ``session_started_at`` is
  preserved across the lifetime of one draft (it identifies the
  wizard run).  Returns the assigned ``seq``.
* :func:`list_ops` — Final Review reads the operator-ordered list.
* :func:`clear` — Final Review calls this on a successful apply, and
  :mod:`services.setup_session` calls it from ``mark_complete`` /
  ``dismiss`` so dismissing the launcher wipes any stale staged work.
* :func:`count` — hub embed shows the pending count.

Metadata convention (canonical keys on
:attr:`services.setup_operations.SetupOperation.metadata` and on the
``metadata`` argument here):

* ``reason``: short string explaining why the wizard proposes this op.
* ``confidence``: ``"high"`` / ``"medium"`` / ``"low"``.
* ``source``: ``"scan"`` / ``"preset:<slug>"`` / ``"smart_suggestion"`` /
  ``"manual"`` / ``"readiness_repair"``.
* ``risk``: ``"low"`` / ``"medium"`` / ``"high"``.
* ``rollback_note``: free-text describing how to undo the op.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from services.setup_operations import SetupOperation
from utils.db import setup_draft as db

logger = logging.getLogger("bot.services.setup_draft")


# Default risk level per op kind.  Section helpers may override.
_DEFAULT_RISK_BY_KIND: dict[str, str] = {
    "bind_channel": "low",
    "bind_role": "low",
    "bind_category": "low",
    "bind_thread": "low",
    "bind_member": "low",
    "clear_binding": "low",
    "set_setting": "low",
    "create_channel": "medium",
    "create_role": "high",
    "create_category": "medium",
    "add_automation_rule": "medium",
    "enable_automation_rule": "low",
    "disable_automation_rule": "low",
    "set_cleanup_policy": "low",
    "set_cog_routing": "medium",
}


def _serialise_value(value: Any) -> str | None:
    """Match SettingsMutationPipeline._serialize: bool → 'true'/'false',
    else ``str(value)``; ``None`` stays ``None``."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _normalised_metadata(
    op: SetupOperation,
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    """Merge operator-supplied metadata with the canonical defaults.

    Operator-supplied keys win.  Missing keys are filled with sensible
    defaults so the Final Review embed never has to handle absent
    metadata fields.
    """
    out: dict[str, Any] = {
        "reason": "",
        "confidence": "medium",
        "source": "manual",
        "risk": _DEFAULT_RISK_BY_KIND.get(op.kind, "medium"),
        "rollback_note": "",
    }
    if metadata:
        out.update({k: v for k, v in metadata.items() if v is not None})
    # Operation-supplied metadata via SetupOperation.metadata takes
    # precedence over both — the section author put it on the op for
    # a reason.
    if op.metadata:
        out.update({k: v for k, v in op.metadata.items() if v is not None})
    return out


async def append(
    op: SetupOperation,
    *,
    guild_id: int,
    actor_id: int | None,
    label: str,
    metadata: dict[str, Any] | None = None,
) -> int:
    """Stage ``op`` into the guild's draft.  Return the assigned ``seq``.

    Replace-on-conflict: a second append for the same slot
    ``(subsystem, setting_name, binding_name)`` supersedes the first
    within the draft.  This matches the operator's mental model — a
    re-edit replaces the previous draft entry; it does not duplicate.

    The DB layer enforces the slot uniqueness via a partial unique
    index on ``COALESCE(setting_name, '')`` + ``COALESCE(binding_name, '')``;
    see migration 035.
    """
    if not label:
        raise ValueError("label must be non-empty")

    session_started_at = await _session_started_at(guild_id)
    md = _normalised_metadata(op, metadata)

    seq = await db.insert(
        guild_id=guild_id,
        session_started_at=session_started_at,
        op_kind=op.kind,
        subsystem=op.subsystem,
        binding_name=op.binding_name,
        setting_name=op.setting_name,
        target_id=op.target_id,
        target_name=op.target_name,
        target_kind=op.target_kind,
        value_raw=_serialise_value(op.value),
        resource_mode=op.resource_mode,
        resource_name=op.resource_name,
        existing_id=op.existing_id,
        automation_rule_id=op.automation_rule_id,
        automation_rule_name=op.automation_rule_name,
        trigger_kind=op.trigger_kind,
        action_kind=op.action_kind,
        trigger_config=op.trigger_config,
        action_config=op.action_config,
        schedule=op.schedule,
        timezone=op.timezone,
        actor_id=actor_id,
        label=label,
        metadata=md,
    )
    logger.info(
        "setup_draft.append guild=%s kind=%s subsystem=%s seq=%s",
        guild_id,
        op.kind,
        op.subsystem,
        seq,
    )
    return seq


async def list_ops(guild_id: int) -> list[SetupOperation]:
    """Return the staged ops for ``guild_id`` ordered by ``seq`` asc.

    The DB row's ``value_raw`` is preserved as a string in the
    rebuilt :class:`SetupOperation`'s ``value`` field; the mutation
    pipelines coerce at apply time, matching their existing contract.
    """
    rows = await db.list_rows(guild_id)
    ops: list[SetupOperation] = []
    for r in rows:
        ops.append(
            SetupOperation(
                kind=r["op_kind"],
                subsystem=r["subsystem"],
                binding_name=r.get("binding_name"),
                setting_name=r.get("setting_name"),
                target_id=r.get("target_id"),
                target_name=r.get("target_name"),
                target_kind=r.get("target_kind"),
                value=r.get("value_raw"),
                resource_name=r.get("resource_name"),
                resource_mode=r.get("resource_mode"),
                existing_id=r.get("existing_id"),
                automation_rule_id=r.get("automation_rule_id"),
                automation_rule_name=r.get("automation_rule_name"),
                trigger_kind=r.get("trigger_kind"),
                action_kind=r.get("action_kind"),
                trigger_config=_load_json(r.get("trigger_config_json")),
                action_config=_load_json(r.get("action_config_json")),
                schedule=r.get("schedule"),
                timezone=r.get("timezone"),
                metadata=_load_json(r.get("metadata_json")),
            ),
        )
    return ops


async def list_rows(guild_id: int) -> list[dict[str, Any]]:
    """Return raw draft rows including operator-facing ``label`` and
    canonical metadata.  Used by Final Review to render the embed
    without rebuilding labels per row.
    """
    return await db.list_rows(guild_id)


async def clear(guild_id: int) -> int:
    """Delete every draft for ``guild_id``; return the row count."""
    n = await db.clear(guild_id)
    if n:
        logger.info("setup_draft.clear guild=%s removed=%s", guild_id, n)
    return n


async def count(guild_id: int) -> int:
    """Return the number of staged ops for ``guild_id``."""
    return await db.count(guild_id)


async def _session_started_at(guild_id: int) -> datetime:
    """Return the ``session_started_at`` to use for a new append.

    Preserves the timestamp across appends in the same draft so the
    operator-facing wizard run has one identifying timestamp.  If the
    draft is empty (count == 0), use NOW().
    """
    rows = await db.list_rows(guild_id)
    if rows:
        return rows[0]["session_started_at"]
    return datetime.now(timezone.utc)


def _load_json(payload: Any) -> Any:
    """Return ``payload`` as a Python object.

    asyncpg returns JSONB columns as already-decoded dicts/lists, so
    most callers see a dict directly.  In the codec-mode where the
    server hands back a JSON string, fall through to ``json.loads``.
    ``None`` passes through.
    """
    if payload is None:
        return None
    if isinstance(payload, (dict, list)):
        return payload
    import json

    return json.loads(payload)


__all__ = [
    "append",
    "clear",
    "count",
    "list_ops",
    "list_rows",
]
