"""Command manifest — slice 1 of the dashboard manifest spine (Q-0162).

A typed, bot-owned projection of the live command surface, built **at
startup from the cached** :class:`core.runtime.command_surface_ledger.CommandSurfaceLedger`
— not from an AST scan. The vision doc (``docs/planning/dashboard-vision-finalized-state.md``
§ "The manifest spine") makes the manifest the reliable read artifact for
command management and demotes the AST scanner to a drift-detection layer.

This slice ships the **commands half** only. It composes the ledger (no
duplicate surface walk) into the finalized #998 command schema and exports
it via :meth:`CommandManifest.to_dict`. Fields that need later slices —
``source`` (file/line, needs the AST join), ``panels`` / ``actions`` (need
the panel registry, PR2), ``related_settings`` / ``capability_required``
(need the ``SettingSpec`` / capability bindings) — are present in the schema
but deferred (empty / ``None``) with documented TODOs so the shape is stable
as the spine grows.

Public surface (mirrors the ledger's builder-driven + cached pattern):

    CommandManifestEntry      — frozen dataclass per command
    CommandManifest           — frozen aggregate (envelope + entries)
    MANIFEST_VERSION          — schema version int
    build_command_manifest(ledger) — pure projection over a ledger
    build_and_cache(ledger)        — project + cache, returns the manifest
    build_and_cache_from_bot(bot)  — build/reuse the ledger, then cache
    get_cached_manifest()          — last-built manifest, or None

Diagnostics provider name: ``"command_manifest"``.

Cycle discipline: top-level imports are stdlib + the same-package ledger
module only; ``services`` is imported function-locally (mirrors the
ledger's ``_register_diagnostics``).
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from typing import Any

from core.runtime.command_surface_ledger import (
    CommandSurfaceEntry,
    CommandSurfaceLedger,
)

logger = logging.getLogger("bot.runtime.command_manifest")

# Schema version — bump when the exported shape changes (consumers gate
# on this). Matches the ``"version": 1`` envelope in the #998 schema.
MANIFEST_VERSION = 1


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CommandManifestEntry:
    """One command entrypoint, projected from a ``CommandSurfaceEntry``.

    Carries every field the ledger already knows; the deferred fields
    (``source`` / ``panels`` / ``actions`` / ``related_settings`` /
    ``capability_required``) are reserved for later spine slices and stay
    at their empty defaults until then.
    """

    qualified_name: str
    kind: str  # "prefix" | "slash"
    cog: str
    subsystem: str | None
    classification: str
    classification_declared: bool
    visibility_tier: str | None
    aliases: tuple[str, ...]
    discord_hidden: bool
    # Came from the live runtime ledger walk (vs an AST guess).
    runtime_verified: bool = True
    # --- Deferred to later slices (shape pinned now, populated later) ---
    # PR3 — joined from the AST scanner (file/line provenance).
    source: dict[str, Any] | None = None
    # PR2 — populated from the panel registry.
    panels: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()
    # Later — joined from SettingSpec / capability bindings.
    related_settings: tuple[str, ...] = ()
    capability_required: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "qualified_name": self.qualified_name,
            "kind": self.kind,
            "cog": self.cog,
            "subsystem": self.subsystem,
            "classification": self.classification,
            "classification_declared": self.classification_declared,
            "visibility_tier": self.visibility_tier,
            "aliases": list(self.aliases),
            "discord_hidden": self.discord_hidden,
            "runtime_verified": self.runtime_verified,
            "source": self.source,
            "panels": list(self.panels),
            "actions": list(self.actions),
            "related_settings": list(self.related_settings),
            "capability_required": self.capability_required,
        }


@dataclass(frozen=True)
class CommandManifest:
    """Typed snapshot of every command entrypoint at a point in time."""

    version: int
    generated_at: str  # ISO-8601 (tz-aware)
    bot_build: str
    commands: tuple[CommandManifestEntry, ...]

    def findings(self) -> list[dict[str, Any]]:
        """Cross-manifest reconciliation findings (drift) for this manifest.

        Computed lazily (no stored state) by the spine's reconciliation seam —
        e.g. a ``panel_action`` command whose subsystem owns no registered panel.
        Empty when the manifest is clean. Imported function-locally to keep this
        module's top-level imports to its sibling ledger only (cycle discipline).
        """
        from core.runtime import manifest_reconciliation

        return manifest_reconciliation.reconcile_to_dicts(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "bot_build": self.bot_build,
            "commands": [c.to_dict() for c in self.commands],
            # Cross-manifest reconciliation drift (manifest spine PR3) — the
            # live read carries its own trust signal (empty == clean).
            "findings": self.findings(),
        }


# ---------------------------------------------------------------------------
# Projection
# ---------------------------------------------------------------------------


def _qualified_name(entry: CommandSurfaceEntry) -> str:
    """``"group sub"`` for a child of a group, else the bare command name."""
    if entry.parent_group:
        return f"{entry.parent_group} {entry.name}"
    return entry.name


def _entry_from_ledger(
    entry: CommandSurfaceEntry,
    *,
    panels: tuple[str, ...] = (),
) -> CommandManifestEntry:
    return CommandManifestEntry(
        qualified_name=_qualified_name(entry),
        kind=entry.kind,
        cog=entry.cog_name,
        subsystem=entry.subsystem,
        classification=entry.classification,
        classification_declared=entry.classification_declared,
        visibility_tier=entry.visibility_tier,
        aliases=entry.aliases,
        discord_hidden=entry.discord_hidden,
        runtime_verified=True,
        panels=panels,
    )


def build_command_manifest(
    ledger: CommandSurfaceLedger,
    *,
    bot_build: str = "",
    now: datetime.datetime | None = None,
    panels_by_subsystem: dict[str, tuple[str, ...]] | None = None,
) -> CommandManifest:
    """Project a ``CommandSurfaceLedger`` into a typed ``CommandManifest``.

    Pure and side-effect-free (does not touch the cache). Both prefix
    (``ledger.entries``) and slash (``ledger.slash_entries``) routes are
    projected, in that order. ``bot_build`` defaults to empty — a later
    slice will source it from the deploy SHA.

    ``panels_by_subsystem`` (manifest spine PR2) is the
    ``subsystem -> (panel_id, ...)`` map from the panel manifest: when given, a
    command's ``panels`` is the panel ids registered under its subsystem (a
    real, verifiable subsystem-level association). Per-button ``actions`` stay
    deferred — there is no declared button→command binding yet.
    """
    generated_at = (now or datetime.datetime.now(datetime.timezone.utc)).isoformat()
    pmap = panels_by_subsystem or {}
    commands = tuple(
        _entry_from_ledger(e, panels=pmap.get(e.subsystem or "", ()))
        for e in (*ledger.entries, *ledger.slash_entries)
    )
    return CommandManifest(
        version=MANIFEST_VERSION,
        generated_at=generated_at,
        bot_build=bot_build,
        commands=commands,
    )


# ---------------------------------------------------------------------------
# Module state — cached last-built manifest
# ---------------------------------------------------------------------------


_CACHED: CommandManifest | None = None


def build_and_cache(
    ledger: CommandSurfaceLedger,
    *,
    bot_build: str = "",
    panels_by_subsystem: dict[str, tuple[str, ...]] | None = None,
) -> CommandManifest:
    """Project ``ledger`` and cache the result for diagnostics access."""
    global _CACHED
    manifest = build_command_manifest(
        ledger,
        bot_build=bot_build,
        panels_by_subsystem=panels_by_subsystem,
    )
    _CACHED = manifest
    return manifest


def build_and_cache_from_bot(bot: object, *, bot_build: str = "") -> CommandManifest:
    """Build (or reuse) the command ledger, then project + cache the manifest.

    Prefers the already-cached ledger (the startup path builds it just
    before this) and falls back to building it, so the manifest never
    forces a second surface walk. When the panel manifest has been built
    (startup builds it first), its ``subsystem -> panel_ids`` map is joined
    in so each command carries its subsystem's ``panels``.
    """
    from core.runtime import command_surface_ledger, panel_manifest

    ledger = command_surface_ledger.get_cached_ledger()
    if ledger is None:
        ledger = command_surface_ledger.build_ledger(bot)
    pmf = panel_manifest.get_cached_manifest()
    pmap = panel_manifest.panels_by_subsystem(pmf) if pmf is not None else None
    return build_and_cache(ledger, bot_build=bot_build, panels_by_subsystem=pmap)


def get_cached_manifest() -> CommandManifest | None:
    """The last-built manifest, or ``None`` if not built yet."""
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
            "hint": "call command_manifest.build_and_cache_from_bot(bot) after "
            "the ledger build.",
        }
    by_kind: dict[str, int] = {}
    for c in manifest.commands:
        by_kind[c.kind] = by_kind.get(c.kind, 0) + 1
    findings = manifest.findings()
    return {
        "built": True,
        "version": manifest.version,
        "generated_at": manifest.generated_at,
        "bot_build": manifest.bot_build,
        "command_count": len(manifest.commands),
        "by_kind": by_kind,
        # Cross-manifest reconciliation (PR3): 0 == clean.
        "finding_count": len(findings),
        "findings": findings,
    }


def _register_diagnostics() -> None:
    from services import diagnostics_service

    diagnostics_service.register("command_manifest", _snapshot)


_register_diagnostics()


__all__ = [
    "MANIFEST_VERSION",
    "CommandManifest",
    "CommandManifestEntry",
    "build_and_cache",
    "build_and_cache_from_bot",
    "build_command_manifest",
    "get_cached_manifest",
]
