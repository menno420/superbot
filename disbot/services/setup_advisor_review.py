"""Optional AI setup-advisor review — setup-wizard finalization PR3.

A thin, **read-only** wrapper that lets the Final Review screen offer an
optional "Ask AI to review this setup" action.  It consumes the live
guild snapshot, asks the configured advisor (deterministic by default —
CI and dev never reach an external API) for recommendations, and returns
**advisory text only**.

Hard contract (enforced by
``tests/unit/invariants/test_setup_advisor_readonly.py``):

* **No mutation.**  This module never writes to the DB, never calls a
  ``*MutationPipeline``, never calls ``guild.create_*`` /
  ``edit`` / ``delete``, and never touches the setup draft or session.
  It reads a snapshot and returns text.
* **Never on the critical path.**  Every failure mode (missing API key,
  timeout, snapshot error, advisor raise) degrades to an ``ok=False``
  :class:`AdvisorReview` with a human message — it never raises into the
  caller, so AI latency / outage can never block the linear wizard.

Placement (plan §D3): the advisor is invoked only from the optional
review action on the preview/commit screen; it does not run during apply.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("bot.services.setup_advisor_review")

# Bound on how many recommendation lines we render so the ephemeral reply
# stays well under Discord's limits.
_MAX_LINES = 10


@dataclass(frozen=True)
class AdvisorReview:
    """Result of an optional advisor review — advisory text only."""

    ok: bool
    summary: str
    lines: tuple[str, ...] = field(default_factory=tuple)
    provider: str = "deterministic"


def _format_recommendation(rec: object) -> str:
    """One redacted-enough advisory line for a single recommendation.

    Uses only the recommendation's own declared fields (subsystem,
    binding name, rationale) — never resolves or prints live IDs.
    """
    subsystem = getattr(rec, "subsystem", "?")
    binding = getattr(rec, "binding_name", "?")
    rationale = getattr(rec, "rationale", "") or ""
    confidence = getattr(rec, "confidence", "") or ""
    suffix = f" — {rationale}" if rationale else ""
    conf = f" ({confidence})" if confidence else ""
    return f"`{subsystem}.{binding}`{conf}{suffix}"


async def review_draft(guild: object) -> AdvisorReview:
    """Return an advisory review of the guild's setup state.

    Read-only and fail-safe: any error is caught and returned as an
    ``ok=False`` review so the caller (Final Review) can show a friendly
    "couldn't run" message rather than crashing or blocking apply.

    The ``provider`` defaults to the deterministic advisor unless
    ``SETUP_ADVISOR_PROVIDER`` selects another and its prerequisites are
    present; ``build_advisor`` silently falls back to deterministic when
    they are not, so this is safe in CI.
    """
    # Function-local imports keep this module's import graph light and
    # avoid pulling the AI/snapshot chain in until the action is used.
    try:
        from services import guild_snapshot
        from services.setup_ai_advisor import build_advisor
    except Exception as exc:  # noqa: BLE001 — advisory only; never raise
        logger.warning("setup_advisor_review: import failed: %s", exc)
        return AdvisorReview(
            ok=False,
            summary="AI review is unavailable in this build.",
        )

    try:
        snapshot = await guild_snapshot.collect(guild)  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001 — advisory only; never raise
        logger.warning("setup_advisor_review: snapshot collect failed: %s", exc)
        return AdvisorReview(
            ok=False,
            summary="Couldn't read this server's state for an AI review.",
        )

    advisor = build_advisor()
    provider = type(advisor).__name__
    try:
        draft = await advisor.suggest(snapshot)
    except Exception as exc:  # noqa: BLE001 — advisory only; never raise
        logger.warning("setup_advisor_review: advisor.suggest failed: %s", exc)
        return AdvisorReview(
            ok=False,
            summary="The AI advisor couldn't produce a review right now.",
            provider=provider,
        )

    recommendations = tuple(getattr(draft, "recommendations", ()) or ())
    notes = getattr(draft, "notes", "") or ""
    if not recommendations:
        summary = notes or "No additional changes recommended — your setup looks good."
        return AdvisorReview(ok=True, summary=summary, provider=provider)

    lines = tuple(_format_recommendation(r) for r in recommendations[:_MAX_LINES])
    extra = len(recommendations) - len(lines)
    summary = (
        f"{len(recommendations)} suggestion(s) from the advisor "
        "(advisory only — nothing has been staged or applied):"
    )
    if extra > 0:
        lines = (*lines, f"_+{extra} more_")
    return AdvisorReview(ok=True, summary=summary, lines=lines, provider=provider)


__all__ = ["AdvisorReview", "review_draft"]
