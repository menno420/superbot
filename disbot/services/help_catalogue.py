"""Help Catalogue — read-only Help inventory with stable keys (HLP-2 Phase 1).

The unified Help architecture (help audit §9) needs **one inventory** of
everything Help can show — mother hubs and subsystems, with their stable
keys, default presentation metadata, and relationships — instead of each
render path re-deriving its own slice from the raw registries. This module
is that inventory: a frozen composition over
:mod:`utils.hub_registry` and :mod:`utils.subsystem_registry`.

**Read-only.** The catalogue owns no policy and no storage: governance
remains canonical for visibility, command access/routing for execution, and
the registries for the metadata itself. It exists so the Help projection
(:mod:`services.help_projection`) and the future guild overlay (HLP-3) have
one stable-keyed surface to validate against, and so registry drift becomes
**findings data** instead of silent divergence:

* ``hub_without_subsystem`` — a hub key with no same-key subsystem (the
  host-subsystem convention every hub satisfies today).
* ``unknown_parent_hub`` — a subsystem ``parent_hub`` that names no hub.
* ``tier_mismatch`` — a hub whose ``minimum_tier`` disagrees with its host
  subsystem's ``visibility_tier`` (display placement vs governance would
  contradict — the FIND-B03 / Q-0074 drift class).
* ``roster_drift`` — ``parent_hub`` declarations and the hub's
  ``primary_children`` roster disagree in either direction (the duplicated
  child-roster metadata the audit §3 flags).

All four finding kinds are pinned **empty** by test — new drift reddens CI.

Cycle discipline (mirrors :mod:`services.access_projection`): every
cross-package import is function-local; top-level imports are stdlib only.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover — typing only, keeps imports lazy
    from utils.hub_registry import HubEntry

logger = logging.getLogger("bot.services.help_catalogue")


# ---------------------------------------------------------------------------
# Rows
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HelpHubRow:
    """One mother hub in the Help inventory.

    ``entry`` is the canonical :class:`utils.hub_registry.HubEntry`
    (presentation metadata passthrough — this catalogue does not copy
    display fields it does not need to reason about).
    ``host_subsystem`` is the same-key subsystem that hosts the hub's
    panel, or ``None`` when the convention is broken (also a finding).
    """

    key: str
    entry: HubEntry
    host_subsystem: str | None


@dataclass(frozen=True)
class HelpSubsystemRow:
    """One subsystem in the Help inventory (registry metadata snapshot)."""

    key: str
    display_name: str
    description: str
    emoji: str
    visibility_tier: str
    parent_hub: str | None
    entry_points: tuple[str, ...]
    top_level: bool  # no parent_hub → eligible for the Advanced browser


@dataclass(frozen=True)
class CatalogueFinding:
    """A registry-drift observation (data, not an exception)."""

    kind: (
        str  # hub_without_subsystem | unknown_parent_hub | tier_mismatch | roster_drift
    )
    key: str
    detail: str


@dataclass(frozen=True)
class HelpCatalogue:
    """The frozen Help inventory: hubs in registry order, subsystems in
    ``ui_priority`` order (the order every Help list renders in), plus
    drift findings.
    """

    hubs: tuple[HelpHubRow, ...]
    subsystems: tuple[HelpSubsystemRow, ...]
    findings: tuple[CatalogueFinding, ...]

    def hub(self, key: str) -> HelpHubRow | None:
        return next((h for h in self.hubs if h.key == key), None)

    def subsystem(self, key: str) -> HelpSubsystemRow | None:
        return next((s for s in self.subsystems if s.key == key), None)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

_cached: HelpCatalogue | None = None


def build_help_catalogue() -> HelpCatalogue:
    """Compose the catalogue from the static registries (cached).

    The registries are immutable after startup validation, so the
    composition is computed once per process. Tests that monkeypatch
    registry content must call :func:`invalidate_help_catalogue_cache`.
    """
    global _cached
    if _cached is not None:
        return _cached

    from utils.hub_registry import HUBS
    from utils.subsystem_registry import SUBSYSTEMS, all_subsystems_sorted

    findings: list[CatalogueFinding] = []

    subsystems: list[HelpSubsystemRow] = []
    for key, meta in all_subsystems_sorted():
        parent_hub = meta.get("parent_hub") or None
        subsystems.append(
            HelpSubsystemRow(
                key=key,
                display_name=meta.get("display_name", key),
                description=meta.get("description", ""),
                emoji=meta.get("emoji", "•"),
                visibility_tier=meta.get("visibility_tier", "user"),
                parent_hub=parent_hub,
                entry_points=tuple(meta.get("entry_points") or ()),
                top_level=parent_hub is None,
            ),
        )

    hub_keys = {hub.key for hub in HUBS}

    hubs: list[HelpHubRow] = []
    for hub in HUBS:
        host = hub.key if hub.key in SUBSYSTEMS else None
        if host is None:
            findings.append(
                CatalogueFinding(
                    kind="hub_without_subsystem",
                    key=hub.key,
                    detail="hub key has no same-key subsystem entry",
                ),
            )
        else:
            host_tier = SUBSYSTEMS[host].get("visibility_tier", "user")
            if host_tier != hub.minimum_tier:
                findings.append(
                    CatalogueFinding(
                        kind="tier_mismatch",
                        key=hub.key,
                        detail=(
                            f"hub minimum_tier={hub.minimum_tier!r} vs host "
                            f"subsystem visibility_tier={host_tier!r}"
                        ),
                    ),
                )
        hubs.append(HelpHubRow(key=hub.key, entry=hub, host_subsystem=host))

        # Roster direction 1: every primary child must declare this hub back.
        for child in hub.primary_children:
            child_meta = SUBSYSTEMS.get(child)
            if child_meta is None or child_meta.get("parent_hub") != hub.key:
                findings.append(
                    CatalogueFinding(
                        kind="roster_drift",
                        key=child,
                        detail=(
                            f"listed in hub {hub.key!r} primary_children but "
                            "does not declare it as parent_hub"
                        ),
                    ),
                )

    # Roster direction 2 + parent validity: every parent_hub declaration
    # must name a real hub that lists the subsystem as a primary child.
    for row in subsystems:
        if row.parent_hub is None:
            continue
        if row.parent_hub not in hub_keys:
            findings.append(
                CatalogueFinding(
                    kind="unknown_parent_hub",
                    key=row.key,
                    detail=f"parent_hub={row.parent_hub!r} names no registered hub",
                ),
            )
            continue
        parent = next(h for h in HUBS if h.key == row.parent_hub)
        if row.key not in parent.primary_children:
            findings.append(
                CatalogueFinding(
                    kind="roster_drift",
                    key=row.key,
                    detail=(
                        f"declares parent_hub={row.parent_hub!r} but is missing "
                        "from that hub's primary_children roster"
                    ),
                ),
            )

    if findings:
        logger.warning(
            "help_catalogue: %d registry-drift finding(s): %s",
            len(findings),
            "; ".join(f"{f.kind}:{f.key}" for f in findings),
        )

    _cached = HelpCatalogue(
        hubs=tuple(hubs),
        subsystems=tuple(subsystems),
        findings=tuple(findings),
    )
    return _cached


def invalidate_help_catalogue_cache() -> None:
    """Drop the cached catalogue (tests that patch registry content)."""
    global _cached
    _cached = None


__all__ = [
    "CatalogueFinding",
    "HelpCatalogue",
    "HelpHubRow",
    "HelpSubsystemRow",
    "build_help_catalogue",
    "invalidate_help_catalogue_cache",
]
