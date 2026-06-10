"""Help projection — the one effective-access seam for Help (HLP-2 Phase 2).

Before this seam, the five Help render paths applied **five different filter
sets** (help audit §3): Home filtered hubs by tier only and discarded the
resolved governance set; Advanced consumed governance; typed/dropdown routes
checked nothing about the target; the single-command embed skipped the
classification filter the command-list embed applied; dedicated panels did
whatever their builder did. This module replaces those local filters with
**one reason-coded decision model** every path consumes.

**States** (audit §9 vocabulary, exactly):

==================  ========================================================
 state               meaning
==================  ========================================================
 shown               advertised by Help
 display_hidden      presentation-level hide (ledger classification,
                     Discord-hidden/disabled command, ``panel_available``
                     = False, or an HLP-3 guild-overlay hide — Q-0055:
                     display-only, never execution)
 governance_hidden   governance says this audience cannot see it here
                     (tier floor or scope visibility) — hides
 routed_off          cog routing disables it here — **still advertised**
 command_locked      command access denies it here — **still advertised**
 unavailable         availability policy denies (future axis — §6.6)
 orphaned_override   an overlay row references a key the catalogue no
                     longer knows — preserved + reported on
                     ``HelpProjection.orphaned_overrides``, never rendered
                     by Help, never a crash
==================  ========================================================

Only ``display_hidden`` and ``governance_hidden`` hide an entry. Help
deliberately **advertises locked features** (``routed_off`` /
``command_locked`` / ``unavailable``): execution is denied by the owning
policy with its own safe copy, and the P1B ``help_advertises_locked`` drift
provider is the surface that warns operators about the gap. Display-only
hiding is never execution denial (HLP-4).

**Construction paths:**

* :meth:`HelpProjection.from_visibility` — the render hot path: synchronous,
  built from the :class:`governance.models.VisibilityResult` Help already
  resolves once per invocation. Governance is the only hiding owner today,
  so no further I/O happens.
* :meth:`HelpProjection.registry_defaults` — the no-governance baseline
  (registry tier defaults), used for persistent-view restore symmetry and
  tests. Not a substitute for governance in live render paths.
* :func:`project_help` — resolves governance itself, then delegates.
* :func:`project_help_with_execution` — the enriched form: composes
  :func:`services.access_projection.project_access_map` so routing /
  command-access / availability denials surface as their non-hiding states.
  Built for operator surfaces — consumed by the staff-hub **Help Preview**
  (``views/server_management/access_map.py``, migrated 2026-06-10 after the
  past-day audit's Tier-2 finding; the future HLP-3 overlay editor is the
  next consumer). The live render paths do not need this form to decide
  visibility.

The projection owns **no policy**: every hide traces to governance or a
static presentation rule, and every lock state carries the owning axis's
reason code verbatim (the :mod:`services.access_projection` vocabulary).

Cycle discipline (mirrors :mod:`services.access_projection`): every
cross-package import is function-local; top-level imports are stdlib only.
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:  # pragma: no cover — typing only, keeps imports lazy
    from governance.models import GovernanceContext, VisibilityResult
    from services.access_projection import AccessContext
    from services.help_overlay import GuildHelpOverlay

logger = logging.getLogger("bot.services.help_projection")


# ---------------------------------------------------------------------------
# Decision model
# ---------------------------------------------------------------------------


class HelpEntryState(enum.Enum):
    """Reason-coded display state for one Help entry (audit §9)."""

    SHOWN = "shown"
    DISPLAY_HIDDEN = "display_hidden"
    GOVERNANCE_HIDDEN = "governance_hidden"
    ROUTED_OFF = "routed_off"
    COMMAND_LOCKED = "command_locked"
    UNAVAILABLE = "unavailable"
    ORPHANED_OVERRIDE = "orphaned_override"


# The states that remove an entry from Help output. Everything else stays
# advertised — Help intentionally shows locked features (HLP-4: display-only
# hiding is never execution denial, and lock states never hide).
_HIDING_STATES = frozenset(
    {HelpEntryState.DISPLAY_HIDDEN, HelpEntryState.GOVERNANCE_HIDDEN},
)


@dataclass(frozen=True)
class HelpDecision:
    """One entry's projection decision.

    ``reason_code`` is a stable machine code (this module's presentation
    codes, or the ``access_projection`` reason vocabulary verbatim for the
    enriched lock states). ``detail`` is an internal diagnostic string —
    never rendered to users.
    """

    key: str
    kind: Literal["hub", "subsystem"]
    state: HelpEntryState
    reason_code: str | None = None
    detail: str | None = None

    @property
    def advertised(self) -> bool:
        """``True`` when Help shows this entry (locked states included)."""
        return self.state not in _HIDING_STATES


@dataclass(frozen=True)
class HubPresentation:
    """A hub's *effective* display fields (registry defaults ± overlay).

    Q-0056: custom names render in Help only — these presentations are
    consumed by Help surfaces exclusively. Q-0058: the defaults ride along
    (``default_display_name`` / ``default_purpose``) so admin/debug views
    can show custom + default + stable key.
    """

    key: str
    display_name: str
    purpose: str
    emoji: str
    entry_command: str
    default_display_name: str
    default_purpose: str

    @property
    def renamed(self) -> bool:
        return (
            self.display_name != self.default_display_name
            or self.purpose != self.default_purpose
        )


@dataclass(frozen=True)
class SubsystemPresentation:
    """A subsystem's *effective* display fields (registry defaults ± overlay)."""

    key: str
    display_name: str
    description: str
    emoji: str
    default_display_name: str
    default_description: str

    @property
    def renamed(self) -> bool:
        return (
            self.display_name != self.default_display_name
            or self.description != self.default_description
        )


@dataclass(frozen=True)
class HelpProjection:
    """The composed Help render model for one audience in one context.

    ``source`` records which construction path produced it:
    ``"governance"`` (live visibility), ``"registry_defaults"`` (static
    fallback), or ``"access_projection"`` (execution-enriched).

    ``overlay`` is the guild's presentation-deviation store (HLP-3) — or
    ``None``, which renders byte-identical registry defaults.
    ``orphaned_overrides`` reports overlay rows whose keys the catalogue
    no longer knows (operator surfaces only; Help never renders them).
    """

    member_tier: str
    hubs: tuple[HelpDecision, ...]
    subsystems: tuple[HelpDecision, ...]
    source: str = "governance"
    overlay: GuildHelpOverlay | None = None
    orphaned_overrides: tuple[HelpDecision, ...] = ()

    # -- accessors -----------------------------------------------------

    def hub_decision(self, key: str) -> HelpDecision | None:
        return next((d for d in self.hubs if d.key == key), None)

    def subsystem_decision(self, key: str) -> HelpDecision | None:
        return next((d for d in self.subsystems if d.key == key), None)

    def hub_presentation(self, key: str) -> HubPresentation | None:
        """Effective display fields for one hub (any visibility state)."""
        from services.help_catalogue import build_help_catalogue

        row = build_help_catalogue().hub(key)
        if row is None:
            return None
        override = self.overlay.get("hub", key) if self.overlay is not None else None
        return HubPresentation(
            key=key,
            display_name=(
                override.display_name
                if override is not None and override.display_name is not None
                else row.entry.display_name
            ),
            purpose=(
                override.description
                if override is not None and override.description is not None
                else row.entry.purpose
            ),
            emoji=row.entry.emoji,
            entry_command=row.entry.entry_command,
            default_display_name=row.entry.display_name,
            default_purpose=row.entry.purpose,
        )

    def subsystem_presentation(self, key: str) -> SubsystemPresentation | None:
        """Effective display fields for one subsystem (any visibility state)."""
        from services.help_catalogue import build_help_catalogue

        row = build_help_catalogue().subsystem(key)
        if row is None:
            return None
        override = (
            self.overlay.get("subsystem", key) if self.overlay is not None else None
        )
        return SubsystemPresentation(
            key=key,
            display_name=(
                override.display_name
                if override is not None and override.display_name is not None
                else row.display_name
            ),
            description=(
                override.description
                if override is not None and override.description is not None
                else row.description
            ),
            emoji=row.emoji,
            default_display_name=row.display_name,
            default_description=row.description,
        )

    def visible_hubs(self) -> list[HubPresentation]:
        """Hub presentations Help Home shows, in registry order."""
        out: list[HubPresentation] = []
        for decision in self.hubs:
            if not decision.advertised:
                continue
            presentation = self.hub_presentation(decision.key)
            if presentation is not None:
                out.append(presentation)
        return out

    def advanced_subsystems(self) -> list[str]:
        """Top-level subsystem keys the Advanced browser lists, in
        ``ui_priority`` order (parent-hub children stay inside their hub).
        """
        from services.help_catalogue import build_help_catalogue

        catalogue = build_help_catalogue()
        return [
            d.key
            for d in self.subsystems
            if d.advertised
            and (row := catalogue.subsystem(d.key)) is not None
            and row.top_level
        ]

    def is_subsystem_advertised(self, key: str) -> bool:
        decision = self.subsystem_decision(key)
        return decision is not None and decision.advertised

    def is_hub_advertised(self, key: str) -> bool:
        decision = self.hub_decision(key)
        return decision is not None and decision.advertised

    # -- constructors ----------------------------------------------------

    @classmethod
    def from_visibility(
        cls,
        vis_result: VisibilityResult,
        *,
        overlay: GuildHelpOverlay | None = None,
    ) -> HelpProjection:
        """Build from an already-resolved governance result (the hot path).

        ``overlay`` is the guild's HLP-3 presentation-deviation store
        (``await services.help_overlay.get_guild_help_overlay(guild_id)``);
        ``None`` or an empty overlay renders byte-identical defaults.
        """
        return cls._compose(
            member_tier=vis_result.member_tier,
            visible_subsystems=frozenset(vis_result.visible_subsystems),
            source="governance",
            overlay=overlay,
        )

    @classmethod
    def registry_defaults(cls, member_tier: str) -> HelpProjection:
        """The static no-governance baseline (registry tier defaults).

        Visibility equals :func:`utils.visibility_rules.get_subsystems_for_tier`
        — the same canonical tier table governance starts from before
        applying per-scope overrides. Cannot reflect guild overrides or
        runtime-failed subsystems; live render paths must use
        :meth:`from_visibility`.
        """
        from utils.visibility_rules import get_subsystems_for_tier

        return cls._compose(
            member_tier=member_tier,
            visible_subsystems=frozenset(get_subsystems_for_tier(member_tier)),
            source="registry_defaults",
        )

    @classmethod
    def _compose(
        cls,
        *,
        member_tier: str,
        visible_subsystems: frozenset[str],
        source: str,
        overlay: GuildHelpOverlay | None = None,
    ) -> HelpProjection:
        from services.help_catalogue import build_help_catalogue

        catalogue = build_help_catalogue()

        subsystem_decisions = tuple(
            _apply_overlay_hide(
                HelpDecision(
                    key=row.key,
                    kind="subsystem",
                    state=(
                        HelpEntryState.SHOWN
                        if row.key in visible_subsystems
                        else HelpEntryState.GOVERNANCE_HIDDEN
                    ),
                    reason_code=(
                        None if row.key in visible_subsystems else "subsystem_hidden"
                    ),
                ),
                overlay,
            )
            for row in catalogue.subsystems
        )

        hub_decisions = tuple(
            _apply_overlay_hide(
                _hub_decision(
                    hub_key=row.key,
                    minimum_tier=row.entry.minimum_tier,
                    panel_available=row.entry.panel_available,
                    host_subsystem=row.host_subsystem,
                    member_tier=member_tier,
                    visible_subsystems=visible_subsystems,
                ),
                overlay,
            )
            for row in catalogue.hubs
        )

        return cls(
            member_tier=member_tier,
            hubs=hub_decisions,
            subsystems=subsystem_decisions,
            source=source,
            overlay=overlay,
            orphaned_overrides=_orphaned_overrides(overlay, catalogue),
        )


def _apply_overlay_hide(
    decision: HelpDecision,
    overlay: GuildHelpOverlay | None,
) -> HelpDecision:
    """Apply the guild overlay's display-hide to a non-hidden decision.

    Q-0055 semantics: the overlay can only *add* a presentation hide
    (``display_hidden`` with reason ``overlay_hidden``) on entries no
    other rule already hides — it never reveals a governance-hidden entry
    and never carries execution meaning. Policy states win over the
    cosmetic hide so explanations stay truthful.
    """
    if overlay is None or not decision.advertised:
        return decision
    row = overlay.get(decision.kind, decision.key)
    if row is None or row.display_hidden is not True:
        return decision
    return HelpDecision(
        key=decision.key,
        kind=decision.kind,
        state=HelpEntryState.DISPLAY_HIDDEN,
        reason_code="overlay_hidden",
        detail="guild help overlay display-hide",
    )


def _orphaned_overrides(
    overlay: GuildHelpOverlay | None,
    catalogue: Any,
) -> tuple[HelpDecision, ...]:
    """Overlay rows whose keys the catalogue no longer knows (reported,
    never rendered, never a crash — audit §9 orphan contract).
    """
    if overlay is None or overlay.is_empty:
        return ()
    orphans: list[HelpDecision] = []
    for row in overlay.rows:
        known = (
            catalogue.hub(row.entity_key)
            if row.entity_kind == "hub"
            else catalogue.subsystem(row.entity_key)
        )
        if known is None:
            orphans.append(
                HelpDecision(
                    key=row.entity_key,
                    kind=row.entity_kind,  # type: ignore[arg-type]
                    state=HelpEntryState.ORPHANED_OVERRIDE,
                    reason_code="unknown_key",
                    detail="overlay row references a retired catalogue entity",
                ),
            )
    return tuple(orphans)


def _hub_decision(
    *,
    hub_key: str,
    minimum_tier: str,
    panel_available: bool,
    host_subsystem: str | None,
    member_tier: str,
    visible_subsystems: frozenset[str],
) -> HelpDecision:
    """One hub's display decision.

    Order: presentation availability → hub tier floor → host-subsystem
    governance visibility. The tier floor is the hub registry's own
    presentation metadata (it can be stricter than the subsystem tier);
    governance owns the scope/override-aware part via the host subsystem.
    """
    from governance.permission_tiers import tier_at_or_above

    if not panel_available:
        return HelpDecision(
            key=hub_key,
            kind="hub",
            state=HelpEntryState.DISPLAY_HIDDEN,
            reason_code="panel_unavailable",
        )
    try:
        tier_ok = tier_at_or_above(member_tier, minimum_tier)
    except ValueError:
        # Unknown/legacy tier string — same defensive floor hubs_for_tier used.
        tier_ok = tier_at_or_above("user", minimum_tier)
    if not tier_ok:
        return HelpDecision(
            key=hub_key,
            kind="hub",
            state=HelpEntryState.GOVERNANCE_HIDDEN,
            reason_code="tier_floor",
            detail=f"hub minimum_tier={minimum_tier}",
        )
    if host_subsystem is not None and host_subsystem not in visible_subsystems:
        return HelpDecision(
            key=hub_key,
            kind="hub",
            state=HelpEntryState.GOVERNANCE_HIDDEN,
            reason_code="subsystem_hidden",
            detail=f"host subsystem {host_subsystem!r} not governance-visible",
        )
    return HelpDecision(key=hub_key, kind="hub", state=HelpEntryState.SHOWN)


# ---------------------------------------------------------------------------
# Command-level display decision (shared by every command-rendering surface)
# ---------------------------------------------------------------------------


def command_display_state(cmd: Any) -> HelpDecision:
    """Display decision for one live ``commands.Command``.

    One policy for the command-list embed, the single-command embed, and
    any future panel surface: Discord-hidden, disabled, and
    ledger-classification-hidden commands are ``display_hidden``;
    everything else is ``shown``. Context-free on purpose — per-context
    lock states are the entry-level projection's job.
    """
    from core.runtime.command_surface_ledger import is_command_hidden_from_help

    name = getattr(cmd, "name", "?")
    if getattr(cmd, "hidden", False):
        return HelpDecision(
            key=name,
            kind="subsystem",
            state=HelpEntryState.DISPLAY_HIDDEN,
            reason_code="discord_hidden",
        )
    if not getattr(cmd, "enabled", True):
        return HelpDecision(
            key=name,
            kind="subsystem",
            state=HelpEntryState.DISPLAY_HIDDEN,
            reason_code="disabled",
        )
    if is_command_hidden_from_help(cmd):
        return HelpDecision(
            key=name,
            kind="subsystem",
            state=HelpEntryState.DISPLAY_HIDDEN,
            reason_code="classification_hidden",
        )
    return HelpDecision(key=name, kind="subsystem", state=HelpEntryState.SHOWN)


def is_command_displayable(cmd: Any) -> bool:
    """``True`` when Help may render ``cmd`` (the shared filter)."""
    return command_display_state(cmd).advertised


# ---------------------------------------------------------------------------
# Service entry points
# ---------------------------------------------------------------------------


async def project_help(gctx: GovernanceContext) -> HelpProjection:
    """The one-call render entry: governance + guild overlay → projection.

    Every live Help render path uses this (HLP-2 + HLP-3): it resolves
    governance for ``gctx`` and fetches the guild's cached presentation
    overlay (empty for DMs / faults), then composes both.
    """
    from governance import resolve_visibility
    from services.help_overlay import get_guild_help_overlay

    vis_result = await resolve_visibility(gctx)
    overlay = await get_guild_help_overlay(gctx.guild_id or None)
    return HelpProjection.from_visibility(vis_result, overlay=overlay)


# Maps an AccessDecision's deciding axis to the enriched entry state.
_AXIS_STATE: dict[str, HelpEntryState] = {
    "routing": HelpEntryState.ROUTED_OFF,
    "command_access": HelpEntryState.COMMAND_LOCKED,
    "governance": HelpEntryState.GOVERNANCE_HIDDEN,
    "availability": HelpEntryState.UNAVAILABLE,
}


async def project_help_with_execution(ctx: AccessContext) -> HelpProjection:
    """Execution-enriched projection over the P1A access map.

    Composes :func:`services.access_projection.project_access_map` so each
    subsystem carries the owning axis's denial as its non-hiding lock state
    (``routed_off`` / ``command_locked`` / ``unavailable``) — or
    ``governance_hidden`` when governance itself denies. ``allow`` and
    ``unknown`` both project as ``shown``: the model never hides what it
    could not verify-deny (matching the render paths, which do not consume
    execution axes at all).

    Requires ``ctx.member_tier`` — this is the Q-0045 declared-tier
    simulation path operator surfaces use; renderings of the result must
    carry the §16.4 simulation-limit label.
    """
    if ctx.member_tier is None:
        raise ValueError(
            "project_help_with_execution requires AccessContext.member_tier "
            "(the declared-tier simulation input)",
        )
    from services.access_projection import project_access_map
    from services.help_overlay import get_guild_help_overlay

    overlay = await get_guild_help_overlay(ctx.guild_id)
    decisions = await project_access_map(ctx)
    state_by_subsystem: dict[str, HelpDecision] = {}
    for decision in decisions:
        if decision.effective == "deny" and decision.deciding_axis is not None:
            state = _AXIS_STATE.get(
                decision.deciding_axis.value,
                HelpEntryState.COMMAND_LOCKED,
            )
            state_by_subsystem[decision.feature] = HelpDecision(
                key=decision.feature,
                kind="subsystem",
                state=state,
                reason_code=(
                    decision.reason.code if decision.reason is not None else None
                ),
                detail=f"axis={decision.deciding_axis.value}",
            )
        else:
            state_by_subsystem[decision.feature] = HelpDecision(
                key=decision.feature,
                kind="subsystem",
                state=HelpEntryState.SHOWN,
                detail=(
                    "effective=unknown" if decision.effective == "unknown" else None
                ),
            )

    # Hubs reuse the same rules as the governance path; the governance-visible
    # set is exactly the features governance did not deny.
    visible = frozenset(
        key
        for key, d in state_by_subsystem.items()
        if d.state is not HelpEntryState.GOVERNANCE_HIDDEN
    )
    from services.help_catalogue import build_help_catalogue

    catalogue = build_help_catalogue()
    hub_decisions = tuple(
        _apply_overlay_hide(
            _hub_decision(
                hub_key=row.key,
                minimum_tier=row.entry.minimum_tier,
                panel_available=row.entry.panel_available,
                host_subsystem=row.host_subsystem,
                member_tier=ctx.member_tier,
                visible_subsystems=visible,
            ),
            overlay,
        )
        for row in catalogue.hubs
    )
    subsystem_decisions = tuple(
        _apply_overlay_hide(
            state_by_subsystem.get(
                row.key,
                # Defensive: a catalogue row the access map did not cover
                # projects as shown (the model hides only verified denials).
                HelpDecision(
                    key=row.key,
                    kind="subsystem",
                    state=HelpEntryState.SHOWN,
                    detail="not in access map",
                ),
            ),
            overlay,
        )
        for row in catalogue.subsystems
    )
    return HelpProjection(
        member_tier=ctx.member_tier,
        hubs=hub_decisions,
        subsystems=subsystem_decisions,
        source="access_projection",
        overlay=overlay,
        orphaned_overrides=_orphaned_overrides(overlay, catalogue),
    )


__all__ = [
    "HelpDecision",
    "HelpEntryState",
    "HelpProjection",
    "HubPresentation",
    "SubsystemPresentation",
    "command_display_state",
    "is_command_displayable",
    "project_help",
    "project_help_with_execution",
]
