"""Integration-mode behavior policies (plan section 3 — the adoption-pace axis).

The ``mode`` state field (observe | guided | active) existed since PR 1 but nothing
read it; this module is the single place its *behavior* is defined, so every
consumer (interview quota, orientation depth, trigger mandates, actuator gating,
graduation) asks one policy table instead of re-deriving the semantics.

The three modes, per the approved plan:

- **observe** — the kit imposes nothing: each session writes a light note, asks
  only 1-2 observation questions, and passively profiles how the user already
  works; after enough sessions it *proposes* a tailored workflow (never
  auto-graduates — proposal only).
- **guided** — the default: the workflow rolls out one practice at a time in a
  fixed order (session logs → idea lifecycle → question router → session-enders
  → gates), each arriving only after the prior is established; triggers may
  mandate questions.
- **active** — the full workflow from session 1; the interview runs aggressively
  (no quota) to fill slots fast.

``promotion_rights`` is the *separate* autonomy axis: what the agent may change
without sign-off. Actuators (economy prunes, maintenance writes) may apply only
when the mode allows it AND promotion_rights is ``"promote"`` — otherwise they
stay dry-run/propose.
"""

from __future__ import annotations

from typing import Any

MODES = ("observe", "guided", "active")

# The guided-mode rollout order is fixed by the plan; only the pacing is ours.
GUIDED_ROLLOUT = (
    "session_logs",
    "idea_lifecycle",
    "question_router",
    "session_enders",
    "gates",
)

DEFAULT_MODE = "guided"

# One behavior record per mode. quota None = unlimited questions per session.
_MODE_POLICIES: dict[str, dict[str, Any]] = {
    "observe": {
        "question_quota": 2,
        "orientation_depth": "minimal",
        "practices": "none",
        "triggers_mandate": False,
        "actuators_allowed": False,
        "auto_graduate": False,
        "workflow_proposal_after_sessions": 5,
    },
    "guided": {
        "question_quota": 3,
        "orientation_depth": "standard",
        "practices": "rollout",
        "triggers_mandate": True,
        "actuators_allowed": True,
        "auto_graduate": True,
        "workflow_proposal_after_sessions": None,
    },
    "active": {
        "question_quota": None,
        "orientation_depth": "full",
        "practices": "all",
        "triggers_mandate": True,
        "actuators_allowed": True,
        "auto_graduate": True,
        "workflow_proposal_after_sessions": None,
    },
}


def mode_policy(state: dict[str, Any]) -> dict[str, Any]:
    """Return the behavior policy for the state's active mode.

    An unknown or missing mode falls back to the default (``guided``) so every
    consumer fails open onto sane behavior rather than crashing on bad state.
    """
    mode = state.get("mode", DEFAULT_MODE)
    return dict(_MODE_POLICIES.get(mode, _MODE_POLICIES[DEFAULT_MODE]))


def question_quota(state: dict[str, Any]) -> int | None:
    """Return the per-session interview question quota (None = unlimited)."""
    quota = mode_policy(state)["question_quota"]
    return quota if quota is None else int(quota)


def orientation_depth(state: dict[str, Any]) -> str:
    """Return the orientation-injection depth: minimal | standard | full."""
    return str(mode_policy(state)["orientation_depth"])


def triggers_mandate(state: dict[str, Any]) -> bool:
    """True when fired triggers may *mandate* questions (guided/active only)."""
    return bool(mode_policy(state)["triggers_mandate"])


def actuators_may_apply(state: dict[str, Any]) -> bool:
    """True when actuators may apply changes (mode allows AND rights say promote).

    This is the promotion-rights enforcement point: whatever the mode, an agent
    whose ``promotion_rights`` is ``"propose"`` (or ``"observe"``) only ever
    produces dry-run reports.
    """
    if not mode_policy(state)["actuators_allowed"]:
        return False
    return state.get("promotion_rights") == "promote"


def may_auto_graduate(state: dict[str, Any]) -> bool:
    """True when graduation may fire automatically (observe mode proposes only)."""
    return bool(mode_policy(state)["auto_graduate"])


def workflow_proposal_due(state: dict[str, Any]) -> bool:
    """True when observe mode has watched long enough to propose its workflow."""
    threshold = mode_policy(state)["workflow_proposal_after_sessions"]
    if threshold is None:
        return False
    return int(state.get("session_count", 0)) >= int(threshold)


def active_practices(
    state: dict[str, Any],
    cadence: dict[str, int] | None = None,
) -> list[str]:
    """Return the workflow practices currently active under the mode's pacing.

    observe: none (the kit imposes nothing). active: all from session 1.
    guided: one practice unlocks per ``guided_practice_sessions`` sessions
    (config cadence, default 3), in the fixed rollout order — the "only after
    the prior is established" pacing, made deterministic.
    """
    practices = mode_policy(state)["practices"]
    if practices == "none":
        return []
    if practices == "all":
        return list(GUIDED_ROLLOUT)
    interval = int((cadence or {}).get("guided_practice_sessions", 3))
    interval = max(interval, 1)
    sessions = int(state.get("session_count", 0))
    unlocked = 1 + sessions // interval
    return list(GUIDED_ROLLOUT[:unlocked])
