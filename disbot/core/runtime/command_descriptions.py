"""Bot self-knowledge — command catalog with descriptions.

Sibling of :mod:`core.runtime.command_surface_ledger`. The ledger
owns command identity, classification, subsystem mapping, and the
hidden-from-help policy. This module *enriches* live commands with
description / signature / display-name and freezes the result so the
AI cog can answer "what does !btd6 ask do?" without re-walking the
command surface on every mention.

The catalog is built once at startup (see ``disbot/bot1.py``) and
cached via :func:`get_cached_catalog`. Per-command exception
isolation keeps a single malformed command from breaking the whole
catalog — every described command must survive a TypeError /
AttributeError during introspection without crashing the build.

Diagnostics: registers under name ``"command_descriptions"`` and
returns a compact summary (counts + timestamp) — not the full
entries list.
"""

from __future__ import annotations

import datetime as _datetime
import logging
from dataclasses import dataclass
from typing import Any

from core.runtime import command_surface_ledger

logger = logging.getLogger("bot.runtime.command_descriptions")


@dataclass(frozen=True)
class CommandDescription:
    """Enriched per-command metadata, suitable for inclusion in a prompt."""

    qualified_name: str
    display_name: str
    kind: str  # "prefix" | "slash"
    description: str
    signature: str
    subsystem: str | None
    visibility_tier: str | None
    requires_perms: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommandDescriptionCatalog:
    """Frozen catalog of every described command in the bot.

    ``entries`` is sorted by ``(subsystem or "", kind, qualified_name)``
    so two builds against the same bot produce identical output.
    """

    entries: tuple[CommandDescription, ...]
    built_at: _datetime.datetime
    skipped_count: int
    hidden_skipped: int
    error_skipped: int

    def find(
        self,
        qualified_name: str,
        *,
        kind: str | None = None,
    ) -> tuple[CommandDescription, ...]:
        """Return every entry matching ``qualified_name``.

        Both a prefix and a slash command may share the same name; the
        return is a tuple so callers see both. ``kind`` filters down to
        one form when callers know which they want.
        """
        return tuple(
            e
            for e in self.entries
            if e.qualified_name == qualified_name and (kind is None or e.kind == kind)
        )

    def by_subsystem(self, subsystem: str) -> tuple[CommandDescription, ...]:
        return tuple(e for e in self.entries if e.subsystem == subsystem)

    def diagnostics_summary(self) -> dict[str, Any]:
        """Compact diagnostics payload — counts + timestamp, no full list."""
        by_kind: dict[str, int] = {}
        by_subsystem: dict[str, int] = {}
        for e in self.entries:
            by_kind[e.kind] = by_kind.get(e.kind, 0) + 1
            sub = e.subsystem or "(none)"
            by_subsystem[sub] = by_subsystem.get(sub, 0) + 1
        return {
            "status": "built",
            "built_at": self.built_at.isoformat(),
            "command_count": len(self.entries),
            "by_kind": by_kind,
            "by_subsystem": by_subsystem,
            "skipped_count": self.skipped_count,
            "hidden_skipped": self.hidden_skipped,
            "error_skipped": self.error_skipped,
        }


_CACHED: CommandDescriptionCatalog | None = None


def _reset_for_tests() -> None:
    global _CACHED
    _CACHED = None


def _first_nonempty_line(text: str | None) -> str:
    if not text:
        return ""
    for line in str(text).splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _slash_signature(cmd: object) -> str:
    params = getattr(cmd, "parameters", None) or ()
    parts: list[str] = []
    for p in params:
        name = getattr(p, "name", None) or getattr(p, "display_name", "?")
        required = bool(getattr(p, "required", True))
        parts.append(f"<{name}>" if required else f"<{name}?>")
    return " ".join(parts)


def _build_ledger_index(
    ledger: command_surface_ledger.CommandSurfaceLedger | None,
) -> dict[tuple[str, str], command_surface_ledger.CommandSurfaceEntry]:
    if ledger is None:
        return {}
    index: dict[tuple[str, str], command_surface_ledger.CommandSurfaceEntry] = {}
    for entry in ledger.entries:
        index[(entry.name, "prefix")] = entry
    for entry in ledger.slash_entries:
        index[(entry.name, "slash")] = entry
    return index


def _describe_prefix(
    cmd: object,
    ledger_entry: command_surface_ledger.CommandSurfaceEntry | None,
) -> CommandDescription:
    qualified_name = str(getattr(cmd, "qualified_name", "") or "")
    description = _first_nonempty_line(getattr(cmd, "help", None))
    signature = str(getattr(cmd, "signature", "") or "")
    return CommandDescription(
        qualified_name=qualified_name,
        display_name=f"!{qualified_name}" if qualified_name else "",
        kind="prefix",
        description=description,
        signature=signature,
        subsystem=ledger_entry.subsystem if ledger_entry is not None else None,
        visibility_tier=(
            ledger_entry.visibility_tier if ledger_entry is not None else None
        ),
        requires_perms=(),
    )


def _describe_slash(
    cmd: object,
    ledger_entry: command_surface_ledger.CommandSurfaceEntry | None,
) -> CommandDescription:
    qualified_name = str(getattr(cmd, "qualified_name", "") or "")
    description = _first_nonempty_line(getattr(cmd, "description", None))
    signature = _slash_signature(cmd)
    return CommandDescription(
        qualified_name=qualified_name,
        display_name=f"/{qualified_name}" if qualified_name else "",
        kind="slash",
        description=description,
        signature=signature,
        subsystem=ledger_entry.subsystem if ledger_entry is not None else None,
        visibility_tier=(
            ledger_entry.visibility_tier if ledger_entry is not None else None
        ),
        requires_perms=(),
    )


def build_catalog(bot: object) -> CommandDescriptionCatalog:
    """Walk the live command surface and return a frozen catalog.

    Per-command failures are isolated: any exception during
    description of a single command increments ``error_skipped`` but
    does not stop the build. Hidden commands (per the ledger's
    classification policy) are dropped and counted in
    ``hidden_skipped``.
    """
    ledger = command_surface_ledger.get_cached_ledger()
    ledger_index = _build_ledger_index(ledger)

    entries: list[CommandDescription] = []
    skipped_hidden = 0
    skipped_error = 0

    walk = getattr(bot, "walk_commands", None)
    if walk is not None:
        try:
            prefix_cmds = list(walk())
        except Exception:  # noqa: BLE001 — defensive
            logger.exception("command_descriptions: prefix walk failed")
            prefix_cmds = []
        for cmd in prefix_cmds:
            try:
                if command_surface_ledger.is_command_hidden_from_help(cmd):
                    skipped_hidden += 1
                    continue
                qname = str(getattr(cmd, "qualified_name", "") or "")
                ledger_entry = ledger_index.get((qname, "prefix"))
                entries.append(_describe_prefix(cmd, ledger_entry))
            except Exception:  # noqa: BLE001 — isolate per-command errors
                logger.debug(
                    "command_descriptions: skipping prefix %r",
                    getattr(cmd, "qualified_name", "?"),
                    exc_info=True,
                )
                skipped_error += 1

    tree = getattr(bot, "tree", None)
    slash_walk = getattr(tree, "walk_commands", None) if tree is not None else None
    if slash_walk is not None:
        try:
            slash_cmds = list(slash_walk())
        except Exception:  # noqa: BLE001 — defensive
            logger.exception("command_descriptions: slash walk failed")
            slash_cmds = []
        for cmd in slash_cmds:
            try:
                # Skip groups; only leaf commands carry a callable binding.
                if not hasattr(cmd, "callback"):
                    continue
                if command_surface_ledger.is_command_hidden_from_help(cmd):
                    skipped_hidden += 1
                    continue
                qname = str(getattr(cmd, "qualified_name", "") or "")
                ledger_entry = ledger_index.get((qname, "slash"))
                entries.append(_describe_slash(cmd, ledger_entry))
            except Exception:  # noqa: BLE001 — isolate per-command errors
                logger.debug(
                    "command_descriptions: skipping slash %r",
                    getattr(cmd, "qualified_name", "?"),
                    exc_info=True,
                )
                skipped_error += 1

    entries.sort(key=lambda e: (e.subsystem or "", e.kind, e.qualified_name))

    catalog = CommandDescriptionCatalog(
        entries=tuple(entries),
        built_at=_datetime.datetime.now(tz=_datetime.timezone.utc),
        skipped_count=skipped_hidden + skipped_error,
        hidden_skipped=skipped_hidden,
        error_skipped=skipped_error,
    )
    global _CACHED
    _CACHED = catalog
    logger.info(
        "command_descriptions: built — %d entries (%d hidden, %d errored)",
        len(catalog.entries),
        catalog.hidden_skipped,
        catalog.error_skipped,
    )
    return catalog


def get_cached_catalog() -> CommandDescriptionCatalog | None:
    """Return the last-built catalog, or ``None`` if it has not been built."""
    return _CACHED


def _snapshot() -> dict[str, Any]:
    catalog = _CACHED
    if catalog is None:
        return {
            "status": "not_built",
            "hint": (
                "call command_descriptions.build_catalog(bot) after the"
                " command-surface ledger is built."
            ),
        }
    return catalog.diagnostics_summary()


def _register_diagnostics() -> None:
    from services import diagnostics_service

    diagnostics_service.register("command_descriptions", _snapshot)


_register_diagnostics()


__all__ = [
    "CommandDescription",
    "CommandDescriptionCatalog",
    "build_catalog",
    "get_cached_catalog",
]
