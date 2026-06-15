"""Tests for the draft-render embed primitives.

Covers:

* ``render_op_line`` — confidence + risk glyphs, reason inclusion,
  fallback label derivation per op kind.
* ``render_op_block`` — multi-line shape; rollback note only when set.
* ``render_preview_embed`` — empty state, populated state, truncation
  past _MAX_OPS_PER_FIELD, footer legend.
* ``render_batch_embed`` — colour rules per outcome mix, partition
  fields appear / are skipped appropriately, failure error inlined.
"""

from __future__ import annotations

import discord

from services.setup_operations import (
    SetupOperation,
    SetupOperationBatchResult,
    SetupOperationResult,
)
from views.setup.draft_render import (
    render_batch_embed,
    render_op_block,
    render_op_line,
    render_preview_embed,
)

# ---------------------------------------------------------------------------
# render_op_line
# ---------------------------------------------------------------------------


def _set_setting_op() -> SetupOperation:
    return SetupOperation(
        kind="set_setting",
        subsystem="moderation",
        setting_name="warn_threshold",
        value=3,
    )


def test_render_op_line_uses_glyphs_for_confidence_and_risk():
    op = _set_setting_op()
    line = render_op_line(
        op,
        {"confidence": "high", "risk": "low", "reason": "operator entered"},
    )
    assert line.startswith("●")  # high
    assert "·" in line[:5]  # risk low
    assert "operator entered" in line


def test_render_op_line_defaults_to_medium_low_when_metadata_missing():
    line = render_op_line(_set_setting_op(), {})
    assert "◐" in line  # medium
    assert "·" in line  # low risk


def test_render_op_line_omits_reason_when_empty():
    line = render_op_line(_set_setting_op(), {"reason": ""})
    assert "—" not in line  # the em-dash separator only appears with reason


def test_render_op_line_falls_back_to_short_label_per_op_kind():
    # set_setting label: subsystem.setting_name = value
    op = _set_setting_op()
    line = render_op_line(op, {})
    assert "moderation.warn_threshold = 3" in line


def test_render_op_line_bind_label_includes_target_name():
    op = SetupOperation(
        kind="bind_channel",
        subsystem="logging",
        binding_name="mod_channel",
        target_id=999,
        target_name="#mod-log",
    )
    line = render_op_line(op, {})
    assert "logging.mod_channel" in line
    assert "#mod-log" in line


def test_render_op_line_clear_binding_label_has_arrow():
    op = SetupOperation(
        kind="clear_binding",
        subsystem="logging",
        binding_name="mod_channel",
    )
    line = render_op_line(op, {})
    assert "clear" in line


def test_render_op_line_create_resource_label_includes_kind():
    op = SetupOperation(
        kind="create_channel",
        subsystem="logging",
        resource_name="bot-log",
    )
    line = render_op_line(op, {})
    assert "create channel" in line
    assert "bot-log" in line


def test_render_op_line_automation_label_includes_action():
    op = SetupOperation(
        kind="enable_automation_rule",
        subsystem="automation",
        automation_rule_name="welcome",
    )
    line = render_op_line(op, {})
    assert "automation enable" in line
    assert "welcome" in line


def test_render_op_line_operator_label_takes_precedence():
    op = _set_setting_op()
    line = render_op_line(op, {}, label="Use a custom label")
    assert "Use a custom label" in line
    # Default label is not appended when an explicit one is given.
    assert "moderation.warn_threshold = 3" not in line


# ---------------------------------------------------------------------------
# render_op_block
# ---------------------------------------------------------------------------


def test_render_op_block_includes_rollback_when_set():
    block = render_op_block(
        SetupOperation(
            kind="create_channel", subsystem="logging", resource_name="bot-log"
        ),
        {
            "confidence": "high",
            "risk": "medium",
            "rollback_note": "Delete #bot-log if not needed",
        },
    )
    assert "rollback" in block.lower()
    assert "Delete #bot-log" in block


def test_render_op_block_omits_rollback_when_empty():
    block = render_op_block(_set_setting_op(), {})
    assert "rollback" not in block.lower()


def test_render_op_block_includes_source_when_non_default():
    block = render_op_block(
        _set_setting_op(),
        {"source": "preset:community"},
    )
    assert "preset:community" in block


def test_render_op_block_omits_source_when_default_manual():
    block = render_op_block(_set_setting_op(), {"source": "manual"})
    assert "source" not in block


# ---------------------------------------------------------------------------
# render_preview_embed
# ---------------------------------------------------------------------------


def test_render_preview_embed_empty_state():
    embed = render_preview_embed([])
    assert embed.title == "🛰 Setup draft · preview"
    assert "No staged operations" in embed.description
    assert embed.color == discord.Color.dark_grey()


def test_render_preview_embed_lists_op_lines():
    op1 = _set_setting_op()
    op2 = SetupOperation(
        kind="bind_channel",
        subsystem="logging",
        binding_name="mod_channel",
        target_id=999,
        target_name="#mod-log",
    )
    embed = render_preview_embed([op1, op2])
    pending_field = next(
        (f for f in embed.fields if f.name.startswith("Pending")), None
    )
    assert pending_field is not None
    assert "moderation.warn_threshold = 3" in pending_field.value
    assert "logging.mod_channel" in pending_field.value


def test_render_preview_embed_truncates_long_lists():
    ops = [
        SetupOperation(
            kind="set_setting", subsystem=f"sub{i}", setting_name=f"name{i}", value=i
        )
        for i in range(15)
    ]
    embed = render_preview_embed(ops)
    pending_field = next(
        (f for f in embed.fields if f.name.startswith("Pending")), None
    )
    assert pending_field is not None
    assert "+5 more" in pending_field.value
    # Header still reports the full count.
    assert "15" in pending_field.name


def test_render_preview_embed_uses_explicit_labels():
    op = _set_setting_op()
    embed = render_preview_embed([op], labels={0: "Custom override label"})
    pending_field = next(
        (f for f in embed.fields if f.name.startswith("Pending")), None
    )
    assert pending_field is not None
    assert "Custom override label" in pending_field.value


def test_render_preview_embed_uses_metadata_by_index():
    op = _set_setting_op()
    embed = render_preview_embed(
        [op],
        metadata_by_index={
            0: {"confidence": "high", "risk": "high", "reason": "scan match"}
        },
    )
    pending_field = next(
        (f for f in embed.fields if f.name.startswith("Pending")), None
    )
    assert pending_field is not None
    assert "●" in pending_field.value  # high confidence
    assert "⚠" in pending_field.value  # high risk
    assert "scan match" in pending_field.value


def test_render_preview_embed_footer_includes_legend():
    embed = render_preview_embed([_set_setting_op()])
    assert "Confidence" in embed.footer.text
    assert "Risk" in embed.footer.text


# ---------------------------------------------------------------------------
# render_batch_embed
# ---------------------------------------------------------------------------


def _result(
    op: SetupOperation,
    *,
    status: str = "applied",
    error: str | None = None,
    label: str | None = None,
) -> SetupOperationResult:
    return SetupOperationResult(
        status=status,
        operation=op,
        label=label or "op",
        error=error,
    )


def test_render_batch_embed_green_when_all_applied():
    batch = SetupOperationBatchResult(results=[_result(_set_setting_op())])
    embed = render_batch_embed(batch)
    assert embed.color == discord.Color.green()
    assert "Applied **1**" in embed.description


def test_render_batch_embed_red_when_all_failed():
    batch = SetupOperationBatchResult(
        results=[_result(_set_setting_op(), status="failed", error="DB down")],
    )
    embed = render_batch_embed(batch)
    assert embed.color == discord.Color.red()


def test_render_batch_embed_gold_when_mixed_applied_and_failed():
    batch = SetupOperationBatchResult(
        results=[
            _result(_set_setting_op(), status="applied"),
            _result(_set_setting_op(), status="failed", error="x"),
        ],
    )
    embed = render_batch_embed(batch)
    assert embed.color == discord.Color.gold()


def test_render_batch_embed_gold_for_skipped_only():
    batch = SetupOperationBatchResult(
        results=[_result(_set_setting_op(), status="skipped")],
    )
    embed = render_batch_embed(batch)
    assert embed.color == discord.Color.gold()


def test_render_batch_embed_populates_every_partition_field():
    op = _set_setting_op()
    batch = SetupOperationBatchResult(
        results=[
            _result(op, status="applied", label="a"),
            _result(op, status="failed", error="boom", label="b"),
            _result(op, status="skipped", label="c"),
            _result(op, status="not_yet_implemented", error="unknown kind", label="d"),
        ],
    )
    embed = render_batch_embed(batch)
    field_names = {f.name for f in embed.fields}
    # Each partition gets its own field with the count.
    assert any(n.startswith("Applied (1)") for n in field_names)
    assert any(n.startswith("Failed (1)") for n in field_names)
    assert any(n.startswith("Skipped (1)") for n in field_names)
    assert any(n.startswith("Not yet implemented (1)") for n in field_names)


def test_render_batch_embed_inlines_failure_error_with_label():
    op = _set_setting_op()
    batch = SetupOperationBatchResult(
        results=[
            _result(op, status="failed", error="DB exploded", label="warn_threshold")
        ],
    )
    embed = render_batch_embed(batch)
    failed_field = next((f for f in embed.fields if f.name.startswith("Failed")), None)
    assert failed_field is not None
    assert "DB exploded" in failed_field.value


def test_render_batch_embed_skips_empty_partitions():
    batch = SetupOperationBatchResult(
        results=[_result(_set_setting_op(), status="applied")],
    )
    embed = render_batch_embed(batch)
    field_names = {f.name for f in embed.fields}
    # Only Applied is present.
    assert any(n.startswith("Applied") for n in field_names)
    assert not any(n.startswith("Failed") for n in field_names)
    assert not any(n.startswith("Skipped") for n in field_names)


def test_render_batch_embed_uses_operator_labels_when_provided():
    op = _set_setting_op()
    batch = SetupOperationBatchResult(
        results=[_result(op, status="applied", label="default-label")],
    )
    embed = render_batch_embed(batch, labels={0: "explicit operator label"})
    applied_field = next(
        (f for f in embed.fields if f.name.startswith("Applied")), None
    )
    assert applied_field is not None
    assert "explicit operator label" in applied_field.value


def test_render_batch_embed_handles_empty_results():
    batch = SetupOperationBatchResult(results=[])
    embed = render_batch_embed(batch)
    assert "Applied **0**" in embed.description
    assert embed.color == discord.Color.green()


# ---------------------------------------------------------------------------
# metadata_from_recommendation adapter
# ---------------------------------------------------------------------------


def test_metadata_from_recommendation_populates_canonical_keys():
    from services.setup_operations import metadata_from_recommendation

    class _Rec:
        subsystem = "logging"
        binding_name = "mod_channel"
        target_kind = "channel"
        target_id = 1
        target_name = "#mod-log"
        confidence = "high"
        reason = "name pattern matched"
        source = "deterministic"

    md = metadata_from_recommendation(_Rec())
    assert md == {
        "reason": "name pattern matched",
        "confidence": "high",
        "source": "deterministic",
        "risk": "low",
        "rollback_note": "",
    }


def test_metadata_from_recommendation_defaults_when_missing_attrs():
    from services.setup_operations import metadata_from_recommendation

    class _Bare:
        pass

    md = metadata_from_recommendation(_Bare())
    assert md["confidence"] == "medium"
    assert md["source"] == "deterministic"
    assert md["risk"] == "low"
    assert md["reason"] == ""


def test_operations_from_recommendations_uses_metadata_adapter():
    """End-to-end: recommendation → operation → metadata round-trips
    through the new adapter and populates canonical keys.
    """
    from services.setup_operations import operations_from_recommendations
    from services.setup_plan import SetupRecommendation

    rec = SetupRecommendation(
        subsystem="logging",
        binding_name="mod_channel",
        target_kind="channel",
        target_id=999,
        target_name="#mod-log",
        confidence="high",
        reason="name matched mod-log",
        source="deterministic",
    )
    ops = operations_from_recommendations([rec])
    assert len(ops) == 1
    assert ops[0].metadata is not None
    assert ops[0].metadata["confidence"] == "high"
    assert ops[0].metadata["reason"] == "name matched mod-log"
    assert ops[0].metadata["source"] == "deterministic"
    assert ops[0].metadata["risk"] == "low"
    assert ops[0].metadata["rollback_note"] == ""
