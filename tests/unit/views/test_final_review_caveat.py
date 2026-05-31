"""Final Review no-rollback caveat + AI review button — setup-wizard PR3."""

from __future__ import annotations

from types import SimpleNamespace

from services.setup_operations import SetupOperation
from views.setup import final_review
from views.setup.final_review import ApplySummary, build_final_review_embed


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


def test_final_review_view_has_ai_review_button():
    view = final_review.FinalReviewView(SimpleNamespace(id=1), ops=[_op()])
    custom_ids = {
        getattr(c, "custom_id", None) for c in view.children if hasattr(c, "custom_id")
    }
    assert "setup_final_review:ai_review" in custom_ids
