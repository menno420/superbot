"""UX Lab wing 4 — embed card archetypes.

Thirteen card shapes rendered with sample data. The builders live in
``utils/ux_patterns/builders.py`` so a graduating pattern is imported, not
re-implemented.
"""

from __future__ import annotations

import discord

from utils.ux_patterns import PatternCategory, PatternSpec, PatternStatus, register
from utils.ux_patterns import builders as b
from views.ux_lab.wing import ExhibitRender, ExhibitWingView

_CAT = PatternCategory.EMBEDS
_EMBED_LIMITS = (
    "title 256 · description 4096 · 25 fields · field value 1024",
    "10 embeds / 6000 chars total per message",
)


def _archetype(
    pattern_id: str,
    title: str,
    *,
    status: PatternStatus = PatternStatus.STABLE,
    recommended_for: tuple[str, ...],
    anti_patterns: tuple[str, ...] = (),
    adopted_by: tuple[str, ...] = (),
    notes: str = "",
    extra_limits: tuple[str, ...] = (),
) -> None:
    register(
        PatternSpec(
            pattern_id=pattern_id,
            title=title,
            category=_CAT,
            status=status,
            recommended_for=recommended_for,
            anti_patterns=anti_patterns,
            adopted_by=adopted_by,
            limits=(*extra_limits, *_EMBED_LIMITS),
            notes=notes,
        ),
    )


_archetype(
    "info_card",
    "Info card",
    recommended_for=("read-only facts with one next-step hint",),
    anti_patterns=("burying an action the user must take — use a panel",),
    notes="≤3 fields, footer carries the next step.",
)
_archetype(
    "success_card",
    "Success card",
    recommended_for=("mutation results — say WHAT changed, not just 'done'",),
    notes="Green + the object's new state.",
)
_archetype(
    "warning_card",
    "Warning card",
    recommended_for=("approaching limits, degraded modes",),
    anti_patterns=("warnings without a recommended action",),
    notes="States the limit AND the next action.",
)
_archetype(
    "error_card",
    "Error card",
    recommended_for=("failures — name the cause and the fix",),
    anti_patterns=("'Something went wrong' with no cause",),
    notes="Cause + fix, never just 'failed'.",
)
_archetype(
    "audit_log_compact",
    "Compact audit line",
    recommended_for=("server-logging feeds (Q-0109) — high volume, one-line scan",),
    adopted_by=("services/server_logging (shape candidate)",),
    notes="Author line = event type; description = who/what/old→new.",
)
_archetype(
    "moderation_case",
    "Moderation case card",
    recommended_for=("mod actions with review context (prior cases inline)",),
    notes="Everything a reviewing mod needs without clicking away.",
)
_archetype(
    "user_profile",
    "User profile card",
    recommended_for=("the /myprofile read-only card (plan PR A there)",),
    notes="Identity top, numbers middle, flair last.",
)
_archetype(
    "leaderboard_fields",
    "Leaderboard — field rows",
    recommended_for=("short boards (≤10) where mentions/emoji matter",),
    anti_patterns=("long boards — rows wrap badly on mobile",),
    notes="Compare with the code-block variant (next exhibit).",
)
_archetype(
    "leaderboard_table",
    "Leaderboard — code-block table",
    recommended_for=("aligned numeric boards; mobile-stable up to ~40 chars wide",),
    anti_patterns=("rows needing mentions/emoji — code blocks render them raw",),
    notes="Monospace wins for numbers; loses mentions.",
)
_archetype(
    "setup_summary",
    "Setup final-review summary",
    recommended_for=("the draft-lane Final Review (numbered, nothing applied yet)",),
    adopted_by=("setup wizard Final Review (shape)",),
    notes="Numbered staged ops + explicit 'nothing applied' line.",
)
_archetype(
    "ai_answer_with_sources",
    "AI answer with provenance",
    recommended_for=("every AI answer — answer, method, sources, in that order",),
    anti_patterns=("AI prose with no provenance block",),
    notes="The answer-with-evidence contract, as a card.",
)
_archetype(
    "before_after_diff",
    "Before/after comparison",
    recommended_for=("permission/setting changes — scan the delta",),
    notes="Two embeds, same field order, delta in bold.",
)
_archetype(
    "embed_color_strip",
    "Subsystem colour strip",
    recommended_for=("checking palette readability on light + dark themes",),
    extra_limits=("one embed per colour — strip + spec card = 10 (the cap)",),
    notes="View this on both themes and on a phone before approving colours.",
)
_archetype(
    "embed_budget_edge",
    "Deliberately maximal embed",
    recommended_for=("seeing what the 25-field ceiling feels like (then paginating)",),
    anti_patterns=("shipping anything this dense to members",),
    notes="If a panel needs this, it wants pagination.",
)


class EmbedsWingView(ExhibitWingView):
    """Wing 4 — embed archetypes."""

    WING_TITLE = "Embeds"
    WING_EMOJI = "🪧"

    def _exhibit_ids(self) -> tuple[str, ...]:
        return (
            "info_card",
            "success_card",
            "warning_card",
            "error_card",
            "audit_log_compact",
            "moderation_case",
            "user_profile",
            "leaderboard_fields",
            "leaderboard_table",
            "setup_summary",
            "ai_answer_with_sources",
            "before_after_diff",
            "embed_color_strip",
            "embed_budget_edge",
        )

    def _render_exhibit(self, pattern_id: str) -> ExhibitRender:
        builders: dict[str, list[discord.Embed]] = {
            "info_card": [b.build_info_card()],
            "success_card": [b.build_success_card()],
            "warning_card": [b.build_warning_card()],
            "error_card": [b.build_error_card()],
            "audit_log_compact": [b.build_audit_log_card()],
            "moderation_case": [b.build_moderation_case_card()],
            "user_profile": [b.build_user_profile_card()],
            "leaderboard_fields": [b.build_leaderboard_field_card()],
            "leaderboard_table": [b.build_leaderboard_table_card()],
            "setup_summary": [b.build_setup_summary_card()],
            "ai_answer_with_sources": [b.build_ai_answer_card()],
            "before_after_diff": b.build_before_after_cards(),
            "embed_color_strip": b.build_color_strip(),
            "embed_budget_edge": [b.build_budget_edge_card()],
        }
        return (builders[pattern_id], [])
