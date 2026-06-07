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
* :func:`list_rows` — same data plus provenance (id, seq,
  section_slug, staging_kind, group_id, parent_seq) wrapped in a
  typed :class:`DraftOperationRow`.  Recovery / skip / progress code
  must use this reader, not :func:`list_ops`, because rebuilding a
  bare :class:`SetupOperation` drops the row metadata recovery
  depends on.
* :func:`clear` — Final Review calls this on a successful apply, and
  :mod:`services.setup_session` calls it from ``mark_complete`` /
  ``dismiss`` so dismissing the launcher wipes any stale staged work.
* :func:`count` — hub embed shows the pending count.
* :func:`replace_recommended_for_section` — sole writer of
  ``staging_kind='recommended'``.  Performs a transactional preflight
  that refuses to overwrite ``custom`` / ``preset`` / ``manual`` /
  ``repair`` rows at the same slot.

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
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from services.setup_operations import SetupOperation
from utils.db import setup_draft as db

logger = logging.getLogger("bot.services.setup_draft")


# Valid ``staging_kind`` values exposed to callers; mirrors the DB layer
# :data:`utils.db.setup_draft._STAGING_KINDS` minus ``"recommended"``,
# which is reserved for :func:`replace_recommended_for_section`.
_STAGING_KINDS_PUBLIC: frozenset[str] = frozenset(
    {"custom", "preset", "manual", "repair"},
)


@dataclass(frozen=True)
class DraftOperationRow:
    """Typed wrapper around one row of ``setup_draft_operations``.

    Carries the rehydrated :class:`SetupOperation` plus the row's
    provenance and identity columns.  Recovery, ``Skip section``,
    progress, and recommended-replacement code must read rows via
    :func:`list_rows` and the wrapper, because :func:`list_ops`
    intentionally returns plain :class:`SetupOperation` objects and
    loses the metadata recovery depends on.

    ``staging_kind`` is ``None`` for legacy / null-provenance rows
    that pre-date migration 045; treat null as "manual / preserve".
    """

    id: int
    seq: int
    section_slug: str | None
    staging_kind: str | None
    group_id: str | None
    parent_seq: int | None
    label: str
    op: SetupOperation


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
    "set_role_threshold": "medium",
}


def _serialise_value(value: Any) -> str | None:
    """Match SettingsMutationPipeline._serialize: bool → 'true'/'false',
    else ``str(value)``; ``None`` stays ``None``.
    """
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
    section_slug: str | None = None,
    staging_kind: str | None = None,
    group_id: str | None = None,
    parent_seq: int | None = None,
) -> int:
    """Stage ``op`` into the guild's draft.  Return the assigned ``seq``.

    Replace-on-conflict: a second append for the same slot
    ``(subsystem, setting_name, binding_name)`` supersedes the first
    within the draft.  This matches the operator's mental model — a
    re-edit replaces the previous draft entry; it does not duplicate.

    The DB layer enforces the slot uniqueness via a partial unique
    index on ``COALESCE(setting_name, '')`` + ``COALESCE(binding_name, '')``;
    see migration 035.

    ``staging_kind`` defaults to ``None`` (= legacy / manual /
    preserve) and may be one of ``custom`` / ``preset`` / ``manual`` /
    ``repair``.  Writing ``'recommended'`` through this entry point
    is rejected; the only writer of recommended rows is
    :func:`replace_recommended_for_section`, which performs a
    transactional preflight that refuses to overwrite non-recommended
    rows.
    """
    if not label:
        raise ValueError("label must be non-empty")
    if staging_kind == "recommended":
        raise ValueError(
            "staging_kind='recommended' may only be written by "
            "replace_recommended_for_section",
        )
    if staging_kind is not None and staging_kind not in _STAGING_KINDS_PUBLIC:
        raise ValueError(
            f"staging_kind must be one of {sorted(_STAGING_KINDS_PUBLIC)} or "
            f"None (got {staging_kind!r})",
        )

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
        section_slug=section_slug,
        staging_kind=staging_kind,
        group_id=group_id,
        parent_seq=parent_seq,
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


async def list_rows(guild_id: int) -> list[DraftOperationRow]:
    """Return staged rows for ``guild_id`` as :class:`DraftOperationRow`.

    Recovery, ``Skip section``, progress, and recommended-replacement
    code must use this reader rather than :func:`list_ops`, because
    rebuilding a bare :class:`SetupOperation` drops the row metadata
    (``id``, ``seq``, ``section_slug``, ``staging_kind``, ``group_id``,
    ``parent_seq``, ``label``) that recovery flows depend on.

    Rows are ordered by ``seq`` ascending.
    """
    raw = await db.list_rows(guild_id)
    return [_wrap_row(r) for r in raw]


async def list_raw_rows(guild_id: int) -> list[dict[str, Any]]:
    """Return raw draft rows including operator-facing ``label`` and
    canonical metadata.  Used by Final Review's render layer where
    a typed wrapper would be more work than a dict.

    Recovery / skip / progress code must use :func:`list_rows`
    instead; this helper exists only for label-rendering paths that
    pre-date the typed wrapper.
    """
    return await db.list_rows(guild_id)


async def list_by_section(
    guild_id: int,
    section_slug: str,
) -> list[DraftOperationRow]:
    """Return draft rows for one section as :class:`DraftOperationRow`.

    Rows with ``section_slug IS NULL`` (legacy / null-provenance) are
    not returned; the caller is expected to use :func:`list_rows`
    plus a Python filter when null-provenance rows are also needed.
    """
    raw = await db.list_by_section(guild_id, section_slug)
    return [_wrap_row(r) for r in raw]


async def delete_by_ids(guild_id: int, ids: list[int]) -> int:
    """Delete rows by stable ``id``.  Return rows deleted.  No-op on empty."""
    if not ids:
        return 0
    n = await db.delete_by_ids(guild_id, ids)
    if n:
        logger.info(
            "setup_draft.delete_by_ids guild=%s ids=%s removed=%s",
            guild_id,
            ids,
            n,
        )
    return n


async def delete_by_seqs(guild_id: int, seqs: list[int]) -> int:
    """Delete rows by ``seq``.  Return rows deleted.  No-op on empty."""
    if not seqs:
        return 0
    n = await db.delete_by_seqs(guild_id, seqs)
    if n:
        logger.info(
            "setup_draft.delete_by_seqs guild=%s seqs=%s removed=%s",
            guild_id,
            seqs,
            n,
        )
    return n


async def clear(guild_id: int) -> int:
    """Delete every draft for ``guild_id``; return the row count."""
    n = await db.clear(guild_id)
    if n:
        logger.info("setup_draft.clear guild=%s removed=%s", guild_id, n)
    return n


async def count(guild_id: int) -> int:
    """Return the number of staged ops for ``guild_id``."""
    return await db.count(guild_id)


@dataclass(frozen=True)
class RecommendedConflict:
    """One slot that ``replace_recommended_for_section`` refused to write
    because a non-recommended row already occupies it.

    The Final Review recovery view surfaces these to the operator;
    nothing is overwritten unless the operator explicitly confirms.
    """

    op: SetupOperation
    label: str
    existing_row: DraftOperationRow


@dataclass(frozen=True)
class ReplaceRecommendedResult:
    """Outcome of :func:`replace_recommended_for_section`.

    ``inserted_seqs`` are the rows successfully written as
    ``staging_kind='recommended'`` for the section.  ``deleted_count``
    is the prior-recommended rows removed for the same section before
    the new inserts.  ``conflicts`` lists slots whose insert was
    refused because a non-recommended row exists; those slots are not
    written.
    """

    inserted_seqs: list[int]
    deleted_count: int
    conflicts: list[RecommendedConflict]


async def replace_recommended_for_section(
    guild_id: int,
    section_slug: str,
    ops: list[SetupOperation],
    *,
    actor_id: int | None,
    labels: dict[int, str] | None = None,
    group_id: str | None = None,
) -> ReplaceRecommendedResult:
    """Replace this section's ``staging_kind='recommended'`` rows with
    fresh ones built from ``ops``.

    Sole writer of ``staging_kind='recommended'``.  Operation:

    1. Read existing draft rows for the guild via :func:`list_rows`.
    2. Within that snapshot, partition by slot
       ``(op_kind, subsystem, COALESCE(setting_name, ''),
       COALESCE(binding_name, ''))``:

       * existing recommended rows for **this section** → delete by
         id (clears stale recommendations before re-staging);
       * non-recommended rows at any slot the new ops would occupy
         → record as :class:`RecommendedConflict` and skip the
         insert (do not overwrite ``custom`` / ``preset`` / ``manual``
         / ``repair``);
       * other rows → leave alone.
    3. Insert each non-conflicting op via :func:`db.insert` with
       ``staging_kind='recommended'`` and the supplied
       ``section_slug`` / ``group_id``.

    This is not strictly one transaction — the delete and insert
    calls happen sequentially against the connection pool — but it
    closes the duplication window for repeated
    ``Apply recommended`` clicks and never invokes the upsert's
    ``ON CONFLICT DO UPDATE`` path against a non-recommended row.

    ``labels`` is an optional ``{seq_or_index: label}`` map; when an
    op was previously appended elsewhere its label can be reused.
    Missing entries are filled with a derived ``"<kind>: <subsystem>"``
    label since :class:`SetupOperation` does not carry one natively.
    """
    if not section_slug:
        raise ValueError("section_slug must be non-empty")

    existing = await list_rows(guild_id)

    # Index existing rows by slot key + by id.
    existing_by_slot: dict[tuple[str, str, str, str], DraftOperationRow] = {}
    for row in existing:
        key = (
            row.op.kind,
            row.op.subsystem,
            row.op.setting_name or "",
            row.op.binding_name or "",
        )
        existing_by_slot[key] = row

    # Step 1: delete prior recommended rows owned by this section.
    to_delete_ids = [
        row.id
        for row in existing
        if row.section_slug == section_slug and row.staging_kind == "recommended"
    ]
    deleted = await delete_by_ids(guild_id, to_delete_ids)

    # Refresh the slot snapshot so we don't see rows we just deleted.
    deleted_ids = set(to_delete_ids)
    surviving_by_slot: dict[tuple[str, str, str, str], DraftOperationRow] = {
        key: row for key, row in existing_by_slot.items() if row.id not in deleted_ids
    }

    inserted_seqs: list[int] = []
    conflicts: list[RecommendedConflict] = []
    session_started_at = await _session_started_at(guild_id)

    for idx, op in enumerate(ops):
        key = (
            op.kind,
            op.subsystem,
            op.setting_name or "",
            op.binding_name or "",
        )
        label = (labels or {}).get(idx) or f"{op.kind}: {op.subsystem}"

        conflict = surviving_by_slot.get(key)
        if conflict is not None and conflict.staging_kind != "recommended":
            conflicts.append(
                RecommendedConflict(op=op, label=label, existing_row=conflict),
            )
            continue

        md = _normalised_metadata(op, None)
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
            section_slug=section_slug,
            staging_kind="recommended",
            group_id=group_id,
        )
        inserted_seqs.append(seq)

    logger.info(
        "setup_draft.replace_recommended_for_section guild=%s section=%s "
        "deleted=%s inserted=%s conflicts=%s",
        guild_id,
        section_slug,
        deleted,
        len(inserted_seqs),
        len(conflicts),
    )
    return ReplaceRecommendedResult(
        inserted_seqs=inserted_seqs,
        deleted_count=deleted,
        conflicts=conflicts,
    )


def _wrap_row(r: dict[str, Any]) -> DraftOperationRow:
    """Build a :class:`DraftOperationRow` from one ``list_rows`` dict."""
    op = SetupOperation(
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
    )
    return DraftOperationRow(
        id=int(r["id"]),
        seq=int(r["seq"]),
        section_slug=r.get("section_slug"),
        staging_kind=r.get("staging_kind"),
        group_id=r.get("group_id"),
        parent_seq=r.get("parent_seq"),
        label=r.get("label", ""),
        op=op,
    )


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
    "DraftOperationRow",
    "RecommendedConflict",
    "ReplaceRecommendedResult",
    "append",
    "clear",
    "count",
    "delete_by_ids",
    "delete_by_seqs",
    "list_by_section",
    "list_ops",
    "list_raw_rows",
    "list_rows",
    "replace_recommended_for_section",
]
