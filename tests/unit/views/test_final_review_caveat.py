"""Final Review no-rollback caveat + AI review button — setup-wizard PR3."""

from __future__ import annotations

from types import SimpleNamespace

from services.setup_operations import SetupOperation
from services.setup_plan import SetupRecommendation
from views.setup import final_review
from views.setup.final_review import (
    ApplySummary,
    _created_resource_names,
    build_final_review_embed,
)


def _op(binding_name="announce_channel"):
    # A real SetupOperation so the embed's render path (render_op_line →
    # _short_label) has every field it reads.
    return SetupOperation(
        kind="bind_channel",
        subsystem="xp",
        binding_name=binding_name,
        target_name="#general",
        metadata={},
    )


def _create_op(resource_name="mod-logs", kind="create_channel"):
    return SetupOperation(
        kind=kind,
        subsystem="logging",
        binding_name="mod_channel",
        resource_name=resource_name,
        resource_mode="create",
        metadata={},
    )


def _all_text(embed) -> str:
    parts = [embed.title or "", embed.description or ""]
    if embed.footer and embed.footer.text:
        parts.append(embed.footer.text)
    parts.extend(f.name + " " + f.value for f in embed.fields)
    return "\n".join(parts).lower()


def test_pre_apply_embed_shows_no_rollback_caveat():
    embed = build_final_review_embed([_op()])
    text = _all_text(embed)
    assert "no automatic rollback" in text


def test_partial_apply_footer_warns_cancel_does_not_undo():
    summary = ApplySummary(applied=["a"], failed=["b"], skipped=[])
    embed = build_final_review_embed([_op(), _op()], summary=summary)
    assert "does not undo" in _all_text(embed)


def test_full_success_embed_has_no_rollback_field():
    summary = ApplySummary(applied=["a", "b"], failed=[], skipped=[])
    embed = build_final_review_embed([_op(), _op()], summary=summary)
    # The complete state is celebratory; the heads-up belongs on the
    # pre-apply screen, not after a clean apply.
    assert "heads-up" not in {f.name.lower() for f in embed.fields}


def test_pre_apply_embed_flags_resource_creation():
    """A create op surfaces a distinct 'N new resource(s) will be created' field
    naming the resource — so creation is never rubber-stamped."""
    embed = build_final_review_embed([_create_op("mod-logs"), _op()])
    field_names = " ".join(f.name for f in embed.fields).lower()
    text = _all_text(embed)
    assert "new resource(s) will be created" in field_names
    assert "1 new resource" in field_names
    assert "mod-logs" in text


def test_bind_only_plan_has_no_create_field():
    embed = build_final_review_embed([_op(), _op("rules_channel")])
    field_names = " ".join(f.name for f in embed.fields).lower()
    assert "will be created" not in field_names


def test_create_recommendation_also_flagged():
    """The recommendation shape (mode='create') triggers the same guard."""
    rec = SetupRecommendation(
        subsystem="logging",
        binding_name="mod_channel",
        target_kind="channel",
        target_name="mod-logs",
        confidence="high",
        reason="missing",
        mode="create",
    )
    embed = build_final_review_embed([rec])
    assert "will be created" in " ".join(f.name for f in embed.fields).lower()


def test_created_resource_names_handles_both_shapes():
    rec = SetupRecommendation(
        subsystem="logging",
        binding_name="mod_channel",
        target_kind="role",
        target_name="Staff",
        confidence="medium",
        reason="m",
        mode="create",
    )
    names = _created_resource_names([_create_op("mod-logs"), _op(), rec])
    assert names == ["mod-logs", "Staff"]


def test_final_review_view_has_ai_review_button():
    view = final_review.FinalReviewView(SimpleNamespace(id=1), ops=[_op()])
    custom_ids = {
        getattr(c, "custom_id", None) for c in view.children if hasattr(c, "custom_id")
    }
    assert "setup_final_review:ai_review" in custom_ids
