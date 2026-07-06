"""Draft-operation preview & result rendering primitives.

Shared embed-building surface for the Setup Wizard's draft list, Final
Review preview, and post-apply outcome.  Sections build their own
ephemeral confirmation messages from these helpers; Final Review uses
:func:`render_batch_embed` to render the full pending list and the
post-apply summary.

The metadata convention these helpers consume is the canonical one
documented in :mod:`services.setup_draft`:

* ``reason``        — free-form explanation
* ``confidence``    — ``"high"`` / ``"medium"`` / ``"low"``
* ``source``        — ``"scan"`` / ``"preset:<slug>"`` / ``"smart_suggestion"`` /
                      ``"manual"`` / ``"readiness_repair"``
* ``risk``          — ``"low"`` / ``"medium"`` / ``"high"``
* ``rollback_note`` — operator-facing undo guidance for resource-create ops

Display rules:

* Confidence and risk get glyphs (●○◇) so the operator can eyeball a
  list quickly.
* ``rollback_note`` is only shown when present (most non-create ops
  have an empty rollback note).
* The embed truncates per-field values at 1000 chars (Discord caps
  field values around 1024); long batches surface ``+N more`` instead
  of overflowing.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import discord

from services.setup_operations import (
    SetupOperation,
    SetupOperationBatchResult,
    SetupOperationResult,
)

# ---------------------------------------------------------------------------
# Display constants
# ---------------------------------------------------------------------------


_FIELD_VALUE_CAP = 1000
_MAX_OPS_PER_FIELD = 10

# Each canonical confidence / risk gets a single-glyph marker.
_CONFIDENCE_GLYPH: dict[str, str] = {
    "high": "●",
    "medium": "◐",
    "low": "○",
}

_RISK_GLYPH: dict[str, str] = {
    "low": "·",
    "medium": "▲",
    "high": "⚠",
}


_DEFAULT_METADATA: dict[str, str] = {
    "reason": "",
    "confidence": "medium",
    "source": "manual",
    "risk": "low",
    "rollback_note": "",
}


def _md(metadata: dict[str, Any] | None, key: str) -> str:
    """Return ``metadata[key]`` as a string with a sensible default."""
    if not metadata:
        return _DEFAULT_METADATA.get(key, "")
    value = metadata.get(key)
    if value is None or value == "":
        return _DEFAULT_METADATA.get(key, "")
    return str(value)


# ---------------------------------------------------------------------------
# Op label helpers
# ---------------------------------------------------------------------------


def _short_label(op: SetupOperation, fallback: str | None = None) -> str:
    """Best-effort one-liner identifying an op when no operator label exists.

    Sections build operator labels at draft time; this helper is for
    the rare path where Final Review renders an op without a stored
    label (e.g. ops constructed in-memory for preview).
    """
    if fallback:
        return fallback
    if op.kind == "set_setting" and op.setting_name:
        v = op.value if op.value is not None else "(default)"
        return f"{op.subsystem}.{op.setting_name} = {v}"
    if op.kind == "clear_binding" and op.binding_name:
        return f"{op.subsystem}.{op.binding_name} ← clear"
    if op.kind.startswith("bind_") and op.binding_name:
        target = op.target_name or (f"<{op.target_id}>" if op.target_id else "?")
        return f"{op.subsystem}.{op.binding_name} → {target}"
    if op.kind.startswith("create_"):
        kind_label = op.kind[len("create_") :]
        name = op.resource_name or op.target_name or "?"
        return f"create {kind_label} {name!r}"
    if op.kind.endswith("_automation_rule"):
        action = op.kind.replace("_automation_rule", "")
        rule = op.automation_rule_name or (
            f"<{op.automation_rule_id}>" if op.automation_rule_id else "?"
        )
        return f"automation {action} {rule}"
    return f"{op.kind} ({op.subsystem})"


# ---------------------------------------------------------------------------
# Per-line render
# ---------------------------------------------------------------------------


def render_op_line(
    op: SetupOperation,
    metadata: dict[str, Any] | None = None,
    *,
    label: str | None = None,
) -> str:
    """Render one op as a single line for embed lists.

    Format: ``<conf> <risk> <label>  — <reason>``.  Glyph defaults
    apply when metadata keys are missing.  ``rollback_note`` is not
    included here; surface it on a separate line via
    :func:`render_op_block` when the operator needs the full detail.
    """
    confidence = _md(metadata, "confidence")
    risk = _md(metadata, "risk")
    reason = _md(metadata, "reason")

    conf_glyph = _CONFIDENCE_GLYPH.get(confidence, "?")
    risk_glyph = _RISK_GLYPH.get(risk, "·")
    line_label = _short_label(op, fallback=label)

    parts = [f"{conf_glyph}{risk_glyph} `{line_label}`"]
    if reason:
        parts.append(f"— {reason}")
    return " ".join(parts)


def render_op_block(
    op: SetupOperation,
    metadata: dict[str, Any] | None = None,
    *,
    label: str | None = None,
) -> str:
    """Render one op as a multi-line block including rollback note.

    Used when the operator zooms in on a single draft op (e.g. an
    expandable detail row in Final Review).  Returns at most three
    lines: the op line, the source line, and the rollback note.
    """
    base = render_op_line(op, metadata, label=label)
    extras: list[str] = [base]

    source = _md(metadata, "source")
    if source and source != _DEFAULT_METADATA["source"]:
        extras.append(f"  source: `{source}`")

    rollback = _md(metadata, "rollback_note")
    if rollback:
        extras.append(f"  ↩ rollback: {rollback}")

    return "\n".join(extras)


# ---------------------------------------------------------------------------
# Batch / preview embed
# ---------------------------------------------------------------------------


def _truncate(text: str, *, limit: int = _FIELD_VALUE_CAP) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _format_field_value(
    items: Iterable[tuple[SetupOperation, dict[str, Any] | None, str | None]],
    *,
    max_items: int = _MAX_OPS_PER_FIELD,
) -> str:
    rows = list(items)
    if not rows:
        return "_empty_"
    visible = rows[:max_items]
    lines = [f"• {render_op_line(op, md, label=label)}" for op, md, label in visible]
    if len(rows) > max_items:
        lines.append(f"_+{len(rows) - max_items} more_")
    return _truncate("\n".join(lines))


def render_preview_embed(
    ops: Iterable[SetupOperation],
    *,
    labels: dict[int, str] | None = None,
    metadata_by_index: dict[int, dict[str, Any]] | None = None,
) -> discord.Embed:
    """Render a pre-apply draft list as a single embed.

    ``ops`` order is preserved.  ``labels`` and ``metadata_by_index``
    let Final Review pass per-op labels and metadata pulled from the
    draft DB rows without re-deriving them in this module.
    """
    op_list = list(ops)
    if not op_list:
        return discord.Embed(
            title="🛰 Setup draft · preview",
            description=(
                "No staged operations.  Visit a wizard section to draft "
                "the first change, then return to Final Review."
            ),
            color=discord.Color.dark_grey(),
        )

    embed = discord.Embed(
        title="🛰 Setup draft · preview",
        description=(
            f"**{len(op_list)}** staged operation(s) — nothing has applied "
            "yet.  Click **Apply** in Final Review to route each through "
            "the audited mutation pipelines."
        ),
        color=discord.Color.blurple(),
    )

    triples = [
        (
            op,
            (metadata_by_index or {}).get(idx) or op.metadata,
            (labels or {}).get(idx),
        )
        for idx, op in enumerate(op_list)
    ]
    embed.add_field(
        name=f"Pending ({len(op_list)})",
        value=_format_field_value(triples),
        inline=False,
    )
    embed.set_footer(text=_legend_footer())
    return embed


def render_batch_embed(
    batch: SetupOperationBatchResult,
    *,
    labels: dict[int, str] | None = None,
    metadata_by_index: dict[int, dict[str, Any]] | None = None,
) -> discord.Embed:
    """Render the post-apply outcome of a SetupOperationBatchResult.

    Surfaces the canonical four-way partition
    (applied / failed / skipped / not_yet_implemented) in fixed-order
    fields.  Each populated partition gets its own field; empty
    partitions are omitted.
    """
    counts = {
        "applied": len(batch.applied),
        "failed": len(batch.failed),
        "skipped": len(batch.skipped),
        "not_yet_implemented": len(batch.not_yet_implemented),
    }
    color = discord.Color.green()
    if counts["failed"]:
        color = discord.Color.gold() if counts["applied"] else discord.Color.red()
    elif counts["skipped"] or counts["not_yet_implemented"]:
        color = discord.Color.gold()

    embed = discord.Embed(
        title="🛰 Setup draft · applied",
        description=(
            f"Applied **{counts['applied']}**, "
            f"failed **{counts['failed']}**, "
            f"skipped **{counts['skipped']}**, "
            f"not yet implemented **{counts['not_yet_implemented']}**."
        ),
        color=color,
    )

    by_index: dict[int, int] = {id(r): idx for idx, r in enumerate(batch.results)}
    label_for = labels or {}
    metadata_for = metadata_by_index or {}

    def _resolve(
        result: SetupOperationResult,
    ) -> tuple[
        SetupOperation,
        dict[str, Any] | None,
        str | None,
    ]:
        idx = by_index.get(id(result))
        op = result.operation
        md = (metadata_for.get(idx) if idx is not None else None) or op.metadata
        operator_label = label_for.get(idx) if idx is not None else None
        # Fall back to the result's pre-built label when nothing else
        # was supplied.
        if operator_label is None:
            operator_label = result.label
        # On failure, append the error to the label so the operator
        # sees both at a glance.
        if result.error and result.status in ("failed", "not_yet_implemented"):
            operator_label = f"{operator_label}: {result.error}"
        return op, md, operator_label

    if batch.applied:
        embed.add_field(
            name=f"Applied ({counts['applied']})",
            value=_format_field_value(_resolve(r) for r in batch.applied),
            inline=False,
        )
    if batch.failed:
        embed.add_field(
            name=f"Failed ({counts['failed']})",
            value=_format_field_value(_resolve(r) for r in batch.failed),
            inline=False,
        )
    if batch.skipped:
        embed.add_field(
            name=f"Skipped ({counts['skipped']})",
            value=_format_field_value(_resolve(r) for r in batch.skipped),
            inline=False,
        )
    if batch.not_yet_implemented:
        embed.add_field(
            name=f"Not yet implemented ({counts['not_yet_implemented']})",
            value=_format_field_value(_resolve(r) for r in batch.not_yet_implemented),
            inline=False,
        )

    embed.set_footer(text=_legend_footer())
    return embed


def _legend_footer() -> str:
    return "Confidence: ● high · ◐ medium · ○ low   Risk: ⚠ high · ▲ medium · · low"


__all__ = [
    "render_batch_embed",
    "render_op_block",
    "render_op_line",
    "render_preview_embed",
]
