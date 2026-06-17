"""Panel manifest — slice 2 of the dashboard manifest spine (Q-0162).

A typed, bot-owned projection of the live **persistent panels** — the Discord
UI views that survive restart (`core.runtime.persistent_views`) and therefore
carry stable, static ``custom_id``s. These are exactly the manageable panels
the panel-layout editor (track H / L3 "move buttons") needs to address.

Like the command manifest (PR1), this is built **at startup from the runtime
registry** — not from an AST guess. Each registered ``PersistentView`` class is
instantiated arg-free and its real components are introspected, so the manifest
records what the bot will actually render (the "custom IDs match real
components" reconciliation property). The AST scanner stays a drift-detection
layer (PR3), never the source of truth.

This slice ships the panel half. The vision doc
(``docs/planning/dashboard-vision-finalized-state.md`` § "The manifest spine")
also has it back-populate ``CommandManifestEntry.panels`` by subsystem — done in
``command_manifest`` via the cached panel manifest. Fields that need later
slices — each button's ``command`` (no declared button→command binding yet) and
the panel ``source`` (file/line, needs the AST join, PR3) — are present in the
schema but deferred (``None``) so the shape is stable as the spine grows.

Public surface (mirrors the command manifest):

    PanelButton                — frozen dataclass per addressable component
    PanelManifestEntry         — frozen dataclass per persistent panel
    PanelManifest              — frozen aggregate (envelope + entries)
    PANEL_MANIFEST_VERSION     — schema version int
    build_panel_manifest(...)  — pure projection over view classes
    build_and_cache(...)       — project + cache, returns the manifest
    get_cached_manifest()      — last-built manifest, or None
    panels_by_subsystem(...)   — subsystem → (panel_id, ...) join helper

Diagnostics provider name: ``"panel_manifest"``.

Cycle discipline: top-level imports are stdlib + the same-package
``persistent_views`` module only; ``services`` is imported function-locally
(mirrors the ledger / command-manifest pattern).
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass, field
from typing import Any

from core.runtime.persistent_views import (
    PersistentView,
    iter_registered_view_classes,
    panel_id_of,
)

logger = logging.getLogger("bot.runtime.panel_manifest")

# Schema version — bump when the exported shape changes (consumers gate on it).
PANEL_MANIFEST_VERSION = 1


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PanelButton:
    """One addressable component (button / select) on a persistent panel.

    ``action_id`` is the logical action id; ``custom_id`` is the Discord
    component id. They are identical today (custom_ids are fully static) — the
    field is kept distinct so a future dynamic-suffix custom_id can still expose
    a stable logical action. ``command`` (which command this action invokes) is
    deferred: there is no declared button→command binding yet, and the manifest
    spine exists to eliminate *unverified* metadata, so it stays ``None`` rather
    than be guessed.
    """

    action_id: str
    custom_id: str
    label: str | None
    row: int | None
    # Deferred — populated when a button→command binding is declared.
    command: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "custom_id": self.custom_id,
            "label": self.label,
            "row": self.row,
            "command": self.command,
        }


@dataclass(frozen=True)
class PanelManifestEntry:
    """One persistent panel, projected from its registered view class."""

    panel_id: str
    view_class: str
    subsystem: str
    # "hardcoded" now; PR4's DB overlay introduces "db_overlay".
    layout_source: str = "hardcoded"
    # PR3 — joined from the AST scanner (file/line provenance).
    source: dict[str, Any] | None = None
    buttons: tuple[PanelButton, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "panel_id": self.panel_id,
            "view_class": self.view_class,
            "subsystem": self.subsystem,
            "layout_source": self.layout_source,
            "source": self.source,
            "buttons": [b.to_dict() for b in self.buttons],
        }


@dataclass(frozen=True)
class PanelManifest:
    """Typed snapshot of every persistent panel at a point in time."""

    version: int
    generated_at: str  # ISO-8601 (tz-aware)
    panels: tuple[PanelManifestEntry, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "panels": [p.to_dict() for p in self.panels],
            # Reserved (PR3) — drift findings vs the AST scanner.
            "findings": [],
        }


# ---------------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------------


def _button_from_component(item: Any) -> PanelButton | None:
    """Project a discord.ui component into a ``PanelButton``, or ``None``.

    Only components carrying a static ``custom_id`` are addressable panel
    actions (buttons and registered selects); URL buttons and id-less items
    are skipped.
    """
    custom_id = getattr(item, "custom_id", None)
    if not custom_id:
        return None
    label = getattr(item, "label", None)
    row = getattr(item, "row", None)
    return PanelButton(
        action_id=custom_id,
        custom_id=custom_id,
        label=label,
        row=row,
    )


def _entry_from_view_class(cls: type[PersistentView]) -> PanelManifestEntry:
    """Instantiate *cls* arg-free and introspect its real components.

    Buttons are recorded in component order (the order discord.py renders /
    the editor reorders); this is the faithful runtime view, not an AST guess.
    """
    view = cls()
    buttons = tuple(
        b for b in (_button_from_component(c) for c in view.children) if b is not None
    )
    return PanelManifestEntry(
        panel_id=panel_id_of(cls),
        view_class=cls.__name__,
        subsystem=cls.SUBSYSTEM,
        buttons=buttons,
    )


def build_panel_manifest(
    view_classes: tuple[type[PersistentView], ...] | None = None,
    *,
    now: datetime.datetime | None = None,
) -> PanelManifest:
    """Project the registered persistent-view classes into a ``PanelManifest``.

    Pure and side-effect-free (does not touch the cache). ``view_classes``
    defaults to every registered class (faithful — includes both panels of a
    subsystem that owns more than one). A class that cannot be instantiated /
    introspected is skipped with a warning rather than failing the build, so a
    single broken panel never blocks the manifest. Entries are sorted by
    ``panel_id`` for stable output.
    """
    classes = (
        view_classes if view_classes is not None else iter_registered_view_classes()
    )
    generated_at = (now or datetime.datetime.now(datetime.timezone.utc)).isoformat()
    entries: list[PanelManifestEntry] = []
    for cls in classes:
        try:
            entries.append(_entry_from_view_class(cls))
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Panel manifest: skipped %s (instantiation/introspection failed): %s",
                getattr(cls, "__name__", cls),
                exc,
            )
    entries.sort(key=lambda e: e.panel_id)
    return PanelManifest(
        version=PANEL_MANIFEST_VERSION,
        generated_at=generated_at,
        panels=tuple(entries),
    )


def panels_by_subsystem(manifest: PanelManifest) -> dict[str, tuple[str, ...]]:
    """``subsystem -> (panel_id, ...)`` — the join the command manifest uses
    to back-populate ``CommandManifestEntry.panels``.
    """
    out: dict[str, list[str]] = {}
    for p in manifest.panels:
        out.setdefault(p.subsystem, []).append(p.panel_id)
    return {sub: tuple(sorted(ids)) for sub, ids in out.items()}


# ---------------------------------------------------------------------------
# Module state — cached last-built manifest
# ---------------------------------------------------------------------------


_CACHED: PanelManifest | None = None


def build_and_cache(
    view_classes: tuple[type[PersistentView], ...] | None = None,
) -> PanelManifest:
    """Project the registry and cache the result for diagnostics / the join."""
    global _CACHED
    manifest = build_panel_manifest(view_classes)
    _CACHED = manifest
    return manifest


def get_cached_manifest() -> PanelManifest | None:
    """The last-built panel manifest, or ``None`` if not built yet."""
    return _CACHED


def _reset_for_tests() -> None:
    """Test helper — clear the cache."""
    global _CACHED
    _CACHED = None


# ---------------------------------------------------------------------------
# Diagnostics provider — registers at import time
# ---------------------------------------------------------------------------


def _snapshot() -> dict[str, Any]:
    """Stable diagnostics snapshot for ``!platform`` / consistency."""
    manifest = _CACHED
    if manifest is None:
        return {
            "built": False,
            "hint": "call panel_manifest.build_and_cache() after the persistent "
            "views are registered (startup).",
        }
    by_subsystem = {p.panel_id: len(p.buttons) for p in manifest.panels}
    return {
        "built": True,
        "version": manifest.version,
        "generated_at": manifest.generated_at,
        "panel_count": len(manifest.panels),
        "button_count": sum(len(p.buttons) for p in manifest.panels),
        "buttons_by_panel": by_subsystem,
    }


def _register_diagnostics() -> None:
    from services import diagnostics_service

    diagnostics_service.register("panel_manifest", _snapshot)


_register_diagnostics()


__all__ = [
    "PANEL_MANIFEST_VERSION",
    "PanelButton",
    "PanelManifest",
    "PanelManifestEntry",
    "build_and_cache",
    "build_panel_manifest",
    "get_cached_manifest",
    "panels_by_subsystem",
]
