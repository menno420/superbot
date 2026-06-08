"""Deterministic setup-wizard role templates (server-management PR13).

Built-in, **opt-in** role bundles the setup wizard can suggest.  A template is a
named set of :class:`RoleSuggestion`s — a role name, a short purpose, cosmetic
defaults (colour / hoist / mentionable), and an *optional* time- or XP-based
auto-role tier.  The setup ``role_templates`` section previews a template
against the guild's current roles, then stages a ``create_managed_role``
:class:`~services.setup_operations.SetupOperation` for each role that does not
yet exist.  Nothing is created until **Final Review** applies the draft.

**Not** :mod:`governance.role_templates` — that module declares
*permission-tier-mapped* governance roles (each carries a ``permission_tier``)
for the governance role-provisioning substrate.  This module is the setup
wizard's user-facing, **permission-free** cosmetic role bundles; the two are
deliberately separate concerns (and this one lives in ``services`` so a view
may import it, which the ``governance`` layer would forbid).

Two safety properties are structural, not incidental:

* **Templates never grant Discord permissions.**  :class:`RoleSuggestion` has
  *no permissions field* by design (roadmap §"AI-generated per-guild role
  templates": "no permissions unless a separately constrained future policy
  explicitly supports them").  A created template role is a cosmetic /
  organisational label until an operator grants it permissions by hand.
* **Templates never auto-create.**  This module is pure data + validation +
  planning; it performs no Discord or DB I/O.  Creation flows through the
  audited :class:`services.role_lifecycle_service.RoleLifecycleService` at apply
  time, behind the Final-Review gate.

This module is the deterministic foundation the future *AI role-template
generator* layers on: an AI suggestion is validated/safety-filtered into the
same :class:`RoleTemplate` shape, then staged through the same path.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import discord

logger = logging.getLogger("bot.services.setup_role_templates")

# ---------------------------------------------------------------------------
# Safety bounds — a template/suggestion is rejected by validation if it
# exceeds these.  The time/XP ceilings mirror the manual roles section
# (views.setup.sections.roles) so a template tier and a hand-set tier share
# the same legal range.
# ---------------------------------------------------------------------------

MAX_ROLES_PER_TEMPLATE = 25  # Discord single-select option cap + sanity
MAX_NAME_LEN = 100  # Discord role-name maximum
MAX_PURPOSE_LEN = 120
MAX_TIME_DAYS = 3650  # ~10 years
MAX_XP_LEVEL = 1000

# Planned-role actions (a suggestion either already exists in the guild or is
# proposed for creation).
ACTION_CREATE = "create"
ACTION_EXISTS = "exists"


@dataclass(frozen=True)
class RoleSuggestion:
    """One role a template proposes.

    Carries **no permissions field** on purpose — see the module docstring.
    """

    name: str
    purpose: str = ""
    color: str | None = None  # "#RRGGBB" hex (discord.Color.from_str), or None
    hoist: bool = False  # show separately in the member list
    mentionable: bool = False
    time_days: int | None = None  # optional time-in-server auto-role tier
    xp_level: int | None = None  # optional XP-level auto-role tier


@dataclass(frozen=True)
class RoleTemplate:
    """A named bundle of role suggestions."""

    slug: str
    display_name: str
    description: str
    category: str
    suggestions: tuple[RoleSuggestion, ...] = ()

    @property
    def role_count(self) -> int:
        return len(self.suggestions)


# ---------------------------------------------------------------------------
# Validation / safety
# ---------------------------------------------------------------------------


def parse_color(raw: str | None) -> discord.Color | None:
    """Parse a hex colour string to :class:`discord.Color`, or ``None``.

    Fail-safe: an unparseable / empty value returns ``None`` (the role is
    created with Discord's default colour) rather than raising.
    """
    if not raw:
        return None
    try:
        return discord.Color.from_str(str(raw).strip())
    except (ValueError, TypeError):
        return None


def validate_suggestion(s: RoleSuggestion) -> list[str]:
    """Return a list of validation errors for ``s`` (empty == valid).

    Used to vet both the built-in catalogue (a startup-pinned test) and, in a
    later slice, AI-generated suggestions before they are ever staged.
    """
    errors: list[str] = []
    name = (s.name or "").strip()
    if not name:
        errors.append("role name is empty")
    elif len(name) > MAX_NAME_LEN:
        errors.append(f"role name exceeds {MAX_NAME_LEN} chars: {name!r}")
    if name.lower() in ("@everyone", "everyone"):
        errors.append("a template must not create @everyone")
    if len(s.purpose or "") > MAX_PURPOSE_LEN:
        errors.append(f"purpose exceeds {MAX_PURPOSE_LEN} chars")
    if s.color is not None and parse_color(s.color) is None:
        errors.append(f"unparseable color {s.color!r}")
    if s.time_days is not None and not (1 <= s.time_days <= MAX_TIME_DAYS):
        errors.append(f"time_days {s.time_days!r} out of range 1..{MAX_TIME_DAYS}")
    if s.xp_level is not None and not (1 <= s.xp_level <= MAX_XP_LEVEL):
        errors.append(f"xp_level {s.xp_level!r} out of range 1..{MAX_XP_LEVEL}")
    return errors


def validate_template(t: RoleTemplate) -> list[str]:
    """Return a list of validation errors for ``t`` (empty == valid)."""
    errors: list[str] = []
    if not t.slug:
        errors.append("template slug is empty")
    if not t.suggestions:
        errors.append(f"template {t.slug!r} has no roles")
    if len(t.suggestions) > MAX_ROLES_PER_TEMPLATE:
        errors.append(
            f"template {t.slug!r} has {len(t.suggestions)} roles "
            f"(max {MAX_ROLES_PER_TEMPLATE})",
        )
    seen: set[str] = set()
    for s in t.suggestions:
        key = (s.name or "").strip().lower()
        if key and key in seen:
            errors.append(f"duplicate role name in template {t.slug!r}: {s.name!r}")
        seen.add(key)
        errors.extend(f"{t.slug}.{s.name}: {e}" for e in validate_suggestion(s))
    return errors


# ---------------------------------------------------------------------------
# Planning (pure — no Discord / DB I/O)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlannedRole:
    """One template suggestion resolved against the guild's current roles."""

    suggestion: RoleSuggestion
    action: str  # ACTION_CREATE | ACTION_EXISTS
    existing_role_id: int | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class TemplatePlan:
    """A template resolved against a guild: what would be created vs. reused."""

    template_slug: str
    planned: tuple[PlannedRole, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def to_create(self) -> tuple[PlannedRole, ...]:
        return tuple(p for p in self.planned if p.action == ACTION_CREATE)

    @property
    def existing(self) -> tuple[PlannedRole, ...]:
        return tuple(p for p in self.planned if p.action == ACTION_EXISTS)

    @property
    def create_count(self) -> int:
        return len(self.to_create)

    @property
    def exists_count(self) -> int:
        return len(self.existing)


def plan_template(
    template: RoleTemplate,
    *,
    existing_roles: dict[str, int] | None = None,
    bot_can_manage_roles: bool = True,
) -> TemplatePlan:
    """Partition a template's roles into *create* vs *already-exists*.

    Pure: no Discord or DB access.  ``existing_roles`` maps
    ``role_name.lower()`` → role id (the operator's current guild roles); a
    suggestion whose name matches an existing role is marked
    :data:`ACTION_EXISTS` (and skipped at staging — re-creating would
    duplicate it).  When ``bot_can_manage_roles`` is ``False`` a plan-level
    warning is added so the preview can tell the operator creation will be
    blocked at Final Review until Manage Roles is granted.
    """
    existing = {k.lower(): v for k, v in (existing_roles or {}).items()}
    planned: list[PlannedRole] = []
    warnings: list[str] = []
    if not bot_can_manage_roles:
        warnings.append(
            "the bot lacks the Manage Roles permission — creation will be "
            "blocked at Final Review until it is granted",
        )
    for s in template.suggestions:
        key = (s.name or "").strip().lower()
        existing_id = existing.get(key)
        if existing_id is not None:
            planned.append(
                PlannedRole(
                    suggestion=s,
                    action=ACTION_EXISTS,
                    existing_role_id=existing_id,
                ),
            )
        else:
            planned.append(
                PlannedRole(
                    suggestion=s,
                    action=ACTION_CREATE,
                    warnings=tuple(validate_suggestion(s)),
                ),
            )
    return TemplatePlan(
        template_slug=template.slug,
        planned=tuple(planned),
        warnings=tuple(warnings),
    )


def suggestion_to_spec(s: RoleSuggestion, *, template_slug: str) -> dict[str, Any]:
    """Serialise a suggestion to the ``metadata["role_template"]`` payload.

    This is the single source of truth for the role-spec shape carried on a
    ``create_managed_role`` :class:`~services.setup_operations.SetupOperation`
    (the wizard section builds it; the dispatcher reads it back).  Plain
    JSON-serialisable scalars only, so it round-trips through the draft store's
    JSONB ``metadata`` column unchanged.
    """
    return {
        "color": s.color,
        "hoist": bool(s.hoist),
        "mentionable": bool(s.mentionable),
        "time_days": s.time_days,
        "xp_level": s.xp_level,
        "purpose": s.purpose,
        "template_slug": template_slug,
    }


# ---------------------------------------------------------------------------
# Built-in deterministic catalogue
# ---------------------------------------------------------------------------
#
# Opt-in suggestions, never automatic creation.  Colours are plain hex so the
# data stays declarative; tiers are only on the progression templates.  None
# of these grant permissions — that is configured separately (e.g. the
# moderator-tier role in `!settings → Moderation`, ADR-008).

_TEMPLATES: tuple[RoleTemplate, ...] = (
    RoleTemplate(
        slug="community-hierarchy",
        display_name="Community hierarchy",
        description=(
            "A basic community ladder: owner / admin / moderator / member "
            "label roles (no permissions granted — wire those up separately)."
        ),
        category="community",
        suggestions=(
            RoleSuggestion("Owner", "Server owner / founder", "#E91E63", hoist=True),
            RoleSuggestion("Admin", "Trusted administrator", "#E74C3C", hoist=True),
            RoleSuggestion("Moderator", "Day-to-day moderation", "#3498DB", hoist=True),
            RoleSuggestion("Member", "Verified community member", "#2ECC71"),
        ),
    ),
    RoleTemplate(
        slug="moderation-team",
        display_name="Moderation team",
        description=(
            "Staff tiers for a moderation team. Pair the top tier with the "
            "`moderator_role` capability setting to actually grant powers."
        ),
        category="moderation",
        suggestions=(
            RoleSuggestion(
                "Head Moderator",
                "Lead of the mod team",
                "#C0392B",
                hoist=True,
            ),
            RoleSuggestion("Moderator", "Full moderator", "#2980B9", hoist=True),
            RoleSuggestion(
                "Trial Moderator",
                "Moderator in training",
                "#16A085",
                hoist=True,
            ),
            RoleSuggestion("Helper", "Answers questions, escalates issues", "#27AE60"),
        ),
    ),
    RoleTemplate(
        slug="gaming-community",
        display_name="Gaming / event community",
        description=(
            "Cosmetic roles for a gaming or events server — recognition and "
            "event labels members can earn or be assigned."
        ),
        category="gaming",
        suggestions=(
            RoleSuggestion("Veteran", "Long-time member", "#8E44AD", hoist=True),
            RoleSuggestion("Regular", "Active participant", "#9B59B6"),
            RoleSuggestion("Newcomer", "Recently joined", "#95A5A6"),
            RoleSuggestion(
                "Event Winner",
                "Won a community event",
                "#F1C40F",
                mentionable=True,
            ),
            RoleSuggestion(
                "Tournament Champion",
                "Tournament champion",
                "#F39C12",
                hoist=True,
            ),
        ),
    ),
    RoleTemplate(
        slug="time-progression",
        display_name="Time-in-server progression",
        description=(
            "Auto-granted tenure roles: members earn each role after N days "
            "in the server (auto-role time tiers)."
        ),
        category="progression",
        suggestions=(
            RoleSuggestion(
                "Regular",
                "7 days in the server",
                "#1ABC9C",
                hoist=True,
                time_days=7,
            ),
            RoleSuggestion(
                "Veteran",
                "30 days in the server",
                "#3498DB",
                hoist=True,
                time_days=30,
            ),
            RoleSuggestion(
                "Elder",
                "90 days in the server",
                "#9B59B6",
                hoist=True,
                time_days=90,
            ),
            RoleSuggestion(
                "Legend",
                "365 days in the server",
                "#F1C40F",
                hoist=True,
                time_days=365,
            ),
        ),
    ),
    RoleTemplate(
        slug="xp-progression",
        display_name="XP-level progression",
        description=(
            "Auto-granted XP roles: members earn each role at an XP level "
            "(auto-role XP tiers; needs the XP system enabled)."
        ),
        category="progression",
        suggestions=(
            RoleSuggestion("Level 5", "Reached XP level 5", "#2ECC71", xp_level=5),
            RoleSuggestion("Level 10", "Reached XP level 10", "#1ABC9C", xp_level=10),
            RoleSuggestion(
                "Level 25",
                "Reached XP level 25",
                "#3498DB",
                hoist=True,
                xp_level=25,
            ),
            RoleSuggestion(
                "Level 50",
                "Reached XP level 50",
                "#9B59B6",
                hoist=True,
                xp_level=50,
            ),
            RoleSuggestion(
                "Level 100",
                "Reached XP level 100",
                "#F1C40F",
                hoist=True,
                xp_level=100,
            ),
        ),
    ),
    RoleTemplate(
        slug="support-server",
        display_name="Support server",
        description=(
            "Roles for a product / support server: a support team label plus "
            "verification and recognition roles for members."
        ),
        category="support",
        suggestions=(
            RoleSuggestion(
                "Support Team",
                "Handles support tickets",
                "#E67E22",
                hoist=True,
            ),
            RoleSuggestion("Verified", "Verified customer / user", "#2ECC71"),
            RoleSuggestion("Contributor", "Contributes fixes or content", "#3498DB"),
            RoleSuggestion(
                "Bug Hunter",
                "Reported a confirmed bug",
                "#E74C3C",
                mentionable=True,
            ),
        ),
    ),
)


def list_templates() -> tuple[RoleTemplate, ...]:
    """Return the built-in template catalogue."""
    return _TEMPLATES


def known_template_slugs() -> frozenset[str]:
    return frozenset(t.slug for t in _TEMPLATES)


def get_template(slug: str) -> RoleTemplate | None:
    for t in _TEMPLATES:
        if t.slug == slug:
            return t
    return None


def list_templates_by_category(category: str) -> tuple[RoleTemplate, ...]:
    return tuple(t for t in _TEMPLATES if t.category == category)


__all__ = [
    "ACTION_CREATE",
    "ACTION_EXISTS",
    "MAX_NAME_LEN",
    "MAX_ROLES_PER_TEMPLATE",
    "MAX_TIME_DAYS",
    "MAX_XP_LEVEL",
    "PlannedRole",
    "RoleSuggestion",
    "RoleTemplate",
    "TemplatePlan",
    "get_template",
    "known_template_slugs",
    "list_templates",
    "list_templates_by_category",
    "parse_color",
    "plan_template",
    "suggestion_to_spec",
    "validate_suggestion",
    "validate_template",
]
