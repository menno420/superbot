"""Command surface ledger — Phase 2 PR-12.

An immutable, in-memory catalogue of every command entrypoint the bot
exposes — prefix commands AND slash commands (PR-06b) — together
with their owner subsystem, visibility tier, and any group/alias
relationships.

The ledger is **read-only** and **builder-driven**: ``build_ledger(bot)``
walks the live ``bot.commands`` surface and the interaction router's
prefix registry once, returns a frozen ``CommandSurfaceLedger``, and
caches it for later diagnostics access.  Tests and admin commands
that want to inspect the surface ask the cache directly via
``get_cached_ledger()``.

This module does NOT duplicate
:func:`utils.subsystem_registry.validate_identity_contract`.  The
validator emits *findings* (action-oriented warnings); the ledger
emits *data* (a queryable index).  Both consume the same source data
(SUBSYSTEMS + bot.commands + router prefixes), so a future
PanelRegistry can call ``ledger.by_subsystem("economy")`` without
re-walking ``bot.commands``.

Public surface:

    CommandSurfaceEntry      — frozen dataclass per command
    Classification           — Literal of canonical classification values
    CLASSIFICATIONS          — tuple of all canonical classification values
    RouterPrefixEntry        — frozen dataclass per registered router prefix
    LedgerFindings           — frozen dataclass with orphan/duplicate buckets
    CommandSurfaceLedger     — frozen aggregate snapshot
    build_ledger(bot)        — walks the live surface, caches, returns ledger
    get_cached_ledger()      — last-built ledger, or None if not built
    cog_name_to_subsystem(s) — normalise a cog class name to a SUBSYSTEMS key

Diagnostics provider name: ``"command_surface_ledger"``.
"""

from __future__ import annotations

import datetime
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Literal, get_args

logger = logging.getLogger("bot.runtime.command_surface_ledger")


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


# PR-06a — Classification contract.
#
# Each command entrypoint is classified so help/navigation surfaces and
# the readiness embed can decide whether to render, dim, hide, or warn
# about a command without consulting the help cog directly.  PR-06a
# ships only the type + the default; PR-06b wires slash-command
# ingestion; PR-06c sweeps the cogs to annotate.
#
# Values:
#
# * ``primary_entrypoint`` — the canonical command operators use.
#   Default for unannotated commands so PR-06a is purely additive.
# * ``power_user_shortcut`` — alternative spelling kept for fluency;
#   help may dim it after PR-06c.
# * ``panel_action`` — invoked from a panel button rather than typed;
#   help can omit from the prefix-typed listing.
# * ``legacy_duplicate`` — an alias kept around for backwards-compat;
#   PR-06c may filter from help suggestions.
# * ``internal_admin`` — surfaced only to staff/operators.
# * ``hidden`` — never surfaced in help (still callable).
# * ``deprecated`` — surfaced with a deprecation warning.
Classification = Literal[
    "primary_entrypoint",
    "power_user_shortcut",
    "panel_action",
    "legacy_duplicate",
    "internal_admin",
    "hidden",
    "deprecated",
]

# Canonical tuple of every classification value.  Used by the
# invariant test to assert nothing has drifted between the Literal and
# any classification registry added by PR-06c.
CLASSIFICATIONS: tuple[Classification, ...] = get_args(Classification)


@dataclass(frozen=True)
class CommandSurfaceEntry:
    """A single command entrypoint registered with the bot."""

    name: str
    cog_name: str
    subsystem: str | None
    visibility_tier: str | None
    aliases: tuple[str, ...] = ()
    parent_group: str | None = None
    is_declared: bool = False
    kind: str = "prefix"  # reserved values: "prefix" | "slash"
    # PR-06a: classification defaults to ``primary_entrypoint`` so
    # adding the field is purely additive.  PR-06c populates this from
    # per-cog declarations (decorator or metadata map) and surfaces
    # the unclassified set as a finding.
    classification: Classification = "primary_entrypoint"


@dataclass(frozen=True)
class RouterPrefixEntry:
    """An interaction-router prefix → owner subsystem mapping."""

    prefix: str
    subsystem: str | None


@dataclass(frozen=True)
class LedgerFindings:
    """Cross-cutting checks computed at build time."""

    orphan_cog_subsystems: tuple[str, ...] = ()
    duplicate_command_names: tuple[str, ...] = ()
    duplicate_alias_names: tuple[str, ...] = ()
    undeclared_entry_points: tuple[str, ...] = ()
    router_prefix_unknown: tuple[str, ...] = ()
    # PR-06a: populated by PR-06c once per-cog classification metadata
    # exists.  Empty in PR-06a because the default classification
    # (``primary_entrypoint``) means every command is considered
    # classified out of the box.  Reserved here so the dataclass shape
    # is stable across the PR-06a → PR-06c sequence.
    unclassified_entry_points: tuple[str, ...] = ()

    @property
    def total(self) -> int:
        return (
            len(self.orphan_cog_subsystems)
            + len(self.duplicate_command_names)
            + len(self.duplicate_alias_names)
            + len(self.undeclared_entry_points)
            + len(self.router_prefix_unknown)
            + len(self.unclassified_entry_points)
        )


@dataclass(frozen=True)
class CommandSurfaceLedger:
    """An immutable snapshot of the command surface at a point in time."""

    version: int
    built_at: datetime.datetime
    entries: tuple[CommandSurfaceEntry, ...]
    router_prefixes: tuple[RouterPrefixEntry, ...]
    findings: LedgerFindings
    # Reserved for a future PR that wires app_commands.
    slash_entries: tuple[CommandSurfaceEntry, ...] = field(default_factory=tuple)

    def by_subsystem(self, subsystem: str) -> tuple[CommandSurfaceEntry, ...]:
        return tuple(e for e in self.entries if e.subsystem == subsystem)

    def find(self, name: str) -> CommandSurfaceEntry | None:
        """Return the entry whose primary ``name`` matches, or the first
        entry that declares ``name`` as an alias.  Primary names take
        precedence over aliases so a command's canonical entry always
        wins when both forms collide (the collision itself is reported
        as a ``duplicate_alias_names`` finding).
        """
        for entry in self.entries:
            if entry.name == name:
                return entry
        for entry in self.entries:
            if name in entry.aliases:
                return entry
        return None

    def subsystem_for_command(self, name: str) -> str | None:
        """Return the owning subsystem for *name*; alias-aware via
        :meth:`find`.  Returns ``None`` when neither a primary name
        nor an alias matches.
        """
        entry = self.find(name)
        return entry.subsystem if entry is not None else None


# ---------------------------------------------------------------------------
# Module state — cached last-built ledger
# ---------------------------------------------------------------------------

_CACHED: CommandSurfaceLedger | None = None

_LEDGER_VERSION = 1

# Cog class name normalisation: trim "Cog" suffix + lowercase.
# `EconomyCog` → `economy`; `ProofChannelCog` → `proofchannel`.
_COG_SUFFIX_RE = re.compile(r"cog$", re.IGNORECASE)


def cog_name_to_subsystem(cog_name: str) -> str | None:
    """Normalise a cog class name to a SUBSYSTEMS key, or None on miss."""
    if not cog_name:
        return None
    normalised = _COG_SUFFIX_RE.sub("", cog_name).lower()
    # Function-local: utils.subsystem_registry transitively touches
    # core.runtime, so we keep this import inside the function to
    # match the cycle-sensitive discipline used by other runtime
    # modules.
    from utils.subsystem_registry import SUBSYSTEMS

    return normalised if normalised in SUBSYSTEMS else None


def _reset_for_tests() -> None:
    global _CACHED
    _CACHED = None


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def _classification_from_command(cmd: object) -> Classification:
    """Read ``cmd.extras["classification"]`` if present.

    PR-06c: cogs declare a classification by passing
    ``extras={"classification": "panel_action"}`` to the
    ``@commands.command`` / ``@app_commands.command`` decorator.  An
    unknown or absent value falls back to ``"primary_entrypoint"``
    so PR-06c is purely additive — every existing command keeps its
    default identity unless its cog opts in.
    """
    extras = getattr(cmd, "extras", None)
    if not isinstance(extras, dict):
        return "primary_entrypoint"
    raw = extras.get("classification")
    if raw in CLASSIFICATIONS:
        return raw  # type: ignore[return-value]
    return "primary_entrypoint"


def _walk_commands(bot: object) -> list[CommandSurfaceEntry]:
    """Walk ``bot.commands`` and build one entry per command + alias.

    Subcommands of a group are recorded with ``parent_group`` set to
    the group's qualified name.  Aliases are recorded as separate
    entries with ``is_alias=True`` semantics carried via the
    ``aliases`` field of the primary entry rather than duplicated
    entries — duplicates would confuse "subsystem_for_command" if a
    cog happened to use the same string as an alias to a different
    command (we detect that as ``duplicate_alias_names`` in findings).
    """
    entries: list[CommandSurfaceEntry] = []
    walk = getattr(bot, "walk_commands", None)
    if walk is None:
        return entries
    for cmd in walk():
        cog = getattr(cmd, "cog", None)
        cog_name = cog.__class__.__name__ if cog is not None else ""
        subsystem = cog_name_to_subsystem(cog_name) if cog_name else None
        visibility_tier = _visibility_for(subsystem)
        parent = getattr(cmd, "parent", None)
        parent_name = parent.qualified_name if parent is not None else None
        aliases = tuple(getattr(cmd, "aliases", ()) or ())
        is_declared = _is_declared_entry_point(
            cmd.name,
            cmd.qualified_name,
            subsystem,
        )
        entries.append(
            CommandSurfaceEntry(
                name=cmd.qualified_name,
                cog_name=cog_name,
                subsystem=subsystem,
                visibility_tier=visibility_tier,
                aliases=aliases,
                parent_group=parent_name,
                is_declared=is_declared,
                kind="prefix",
                classification=_classification_from_command(cmd),
            ),
        )
    return entries


def _walk_slash_commands(bot: object) -> list[CommandSurfaceEntry]:
    """Walk ``bot.tree`` and build one entry per registered slash command.

    PR-06b: 5 setup slash commands (``/setup-status``, ``/setup-reset``,
    ``/setup-skip``, ``/setup-unskip``, ``/setup-depth``) are
    registered today but were previously invisible to the ledger
    because the walker only enumerated prefix commands.  This walk
    runs over ``bot.tree.walk_commands()`` (discord.py
    ``CommandTree.walk_commands``) and emits one
    ``CommandSurfaceEntry`` per slash command with ``kind="slash"``.

    Groups (``app_commands.Group``) are flattened — only leaf
    commands are emitted, with ``parent_group`` set to the group's
    qualified name.  ``binding`` (the cog instance) is read via
    ``getattr`` so a missing attribute (e.g. unbound) yields
    ``cog_name=""`` rather than raising.

    The default ``classification`` is left at ``"primary_entrypoint"``;
    PR-06c will annotate the setup slash commands as panel actions
    where appropriate.
    """
    entries: list[CommandSurfaceEntry] = []
    tree = getattr(bot, "tree", None)
    if tree is None:
        return entries
    walk = getattr(tree, "walk_commands", None)
    if walk is None:
        return entries
    try:
        iter_cmds = walk()
    except Exception as exc:  # noqa: BLE001 — best-effort walk
        logger.warning(
            "command_surface_ledger: slash walk_commands raised %s",
            exc,
        )
        return entries
    for cmd in iter_cmds:
        # Skip groups; only leaf commands carry a callable binding.
        # discord.py's ``app_commands.Group`` does not have a
        # ``callback`` attribute — leaf ``Command`` instances do.
        if not hasattr(cmd, "callback"):
            continue
        binding = getattr(cmd, "binding", None)
        cog_name = binding.__class__.__name__ if binding is not None else ""
        subsystem = cog_name_to_subsystem(cog_name) if cog_name else None
        visibility_tier = _visibility_for(subsystem)
        parent = getattr(cmd, "parent", None)
        parent_name = (
            getattr(parent, "qualified_name", None) if parent is not None else None
        )
        qualified_name = getattr(cmd, "qualified_name", None) or getattr(
            cmd,
            "name",
            "",
        )
        is_declared = _is_declared_entry_point(
            getattr(cmd, "name", ""),
            qualified_name,
            subsystem,
        )
        entries.append(
            CommandSurfaceEntry(
                name=qualified_name,
                cog_name=cog_name,
                subsystem=subsystem,
                visibility_tier=visibility_tier,
                aliases=(),
                parent_group=parent_name,
                is_declared=is_declared,
                kind="slash",
                classification=_classification_from_command(cmd),
            ),
        )
    return entries


# PR-06c: classifications that the help renderer must exclude from
# command listings and dropdowns.  ``primary_entrypoint`` and
# ``power_user_shortcut`` always render; ``panel_action`` and
# ``internal_admin`` render only inside their specific surfaces;
# ``hidden`` / ``deprecated`` / ``legacy_duplicate`` are filtered.
_HELP_HIDDEN_CLASSIFICATIONS: frozenset[Classification] = frozenset(
    {"hidden", "deprecated", "legacy_duplicate"},
)


def is_hidden_from_help(entry: CommandSurfaceEntry) -> bool:
    """Return ``True`` if the help renderer should omit ``entry``.

    PR-06c filtering helper consumed by ``cogs.help_cog`` and any
    future panel surface.  ``hidden`` / ``deprecated`` /
    ``legacy_duplicate`` commands are filtered out of the dropdown
    and the per-cog command listing; they remain callable directly.

    Used downstream by ``cogs.help_cog._get_visible_commands`` to
    layer classification-aware filtering on top of the existing
    ``cmd.hidden`` / ``cmd.enabled`` flags.
    """
    return entry.classification in _HELP_HIDDEN_CLASSIFICATIONS


def _visibility_for(subsystem: str | None) -> str | None:
    if subsystem is None:
        return None
    from utils.subsystem_registry import SUBSYSTEMS

    meta = SUBSYSTEMS.get(subsystem)
    if meta is None:
        return None
    tier = meta.get("visibility_tier")
    return str(tier) if tier is not None else None


def _is_declared_entry_point(
    bare_name: str,
    qualified_name: str,
    subsystem: str | None,
) -> bool:
    """A subsystem's ``entry_points`` list may use either bare command
    names (``"daily"``) or qualified group-subcommand pairs
    (``"platform consistency"``).  Match either form so subcommands
    are correctly flagged as declared without forcing SUBSYSTEMS to
    pick one convention.
    """
    if subsystem is None:
        return False
    from utils.subsystem_registry import SUBSYSTEMS

    meta = SUBSYSTEMS.get(subsystem)
    if meta is None:
        return False
    declared = meta.get("entry_points") or ()
    return bare_name in declared or qualified_name in declared


def _walk_router_prefixes() -> list[RouterPrefixEntry]:
    """Snapshot the interaction-router prefix registry."""
    from core.runtime import interaction_router
    from utils.subsystem_registry import SUBSYSTEMS

    prefixes = list(getattr(interaction_router, "_handlers", {}).keys())
    return [
        RouterPrefixEntry(
            prefix=p,
            subsystem=p if p in SUBSYSTEMS else None,
        )
        for p in sorted(prefixes)
    ]


def _compute_findings(
    entries: list[CommandSurfaceEntry],
    router_prefixes: list[RouterPrefixEntry],
) -> LedgerFindings:
    """Cross-cutting checks once the data is in hand."""
    from utils.subsystem_registry import SUBSYSTEMS

    # Orphan: cog name normalised to a key that does not exist in
    # SUBSYSTEMS.  We surface the unique cog names that produced
    # orphan entries so reviewers can rename or register them.
    orphans: set[str] = set()
    for e in entries:
        if not e.cog_name:
            continue
        if e.subsystem is None:
            orphans.add(e.cog_name)

    # Duplicate names: same qualified_name registered by >1 cog.
    name_counts: dict[str, set[str]] = {}
    for e in entries:
        name_counts.setdefault(e.name, set()).add(e.cog_name)
    dup_names = tuple(sorted(n for n, cogs in name_counts.items() if len(cogs) > 1))

    # Duplicate aliases: any alias that collides with a primary
    # command name OR with another command's alias.
    primary_names = {e.name for e in entries}
    alias_to_owners: dict[str, set[str]] = {}
    for e in entries:
        for a in e.aliases:
            alias_to_owners.setdefault(a, set()).add(e.name)
    dup_aliases: set[str] = set()
    for alias, owners in alias_to_owners.items():
        if alias in primary_names:
            dup_aliases.add(alias)
        if len(owners) > 1:
            dup_aliases.add(alias)

    # Undeclared entry points: SUBSYSTEMS lists a command that has
    # no live registration.  Mirrors the validator's
    # entry_point_missing_command finding but as queryable data.
    live_names = primary_names | {a for e in entries for a in e.aliases}
    undeclared: list[str] = []
    for sub, meta in SUBSYSTEMS.items():
        for declared in meta.get("entry_points") or ():
            if declared not in live_names:
                undeclared.append(f"{sub}.{declared}")
    undeclared.sort()

    # Router prefix unknown: an interaction-router prefix that does
    # not correspond to a declared subsystem.
    unknown_prefixes = tuple(
        sorted(p.prefix for p in router_prefixes if p.subsystem is None),
    )

    return LedgerFindings(
        orphan_cog_subsystems=tuple(sorted(orphans)),
        duplicate_command_names=dup_names,
        duplicate_alias_names=tuple(sorted(dup_aliases)),
        undeclared_entry_points=tuple(undeclared),
        router_prefix_unknown=unknown_prefixes,
    )


def build_ledger(bot: object) -> CommandSurfaceLedger:
    """Walk the live command surface and return a frozen ledger snapshot.

    Caches the result for later diagnostics access; call again to
    refresh after a hot-reload.  The function is sync-safe: it does
    not perform I/O.

    PR-06b: in addition to prefix commands (``bot.walk_commands``),
    the builder now walks ``bot.tree.walk_commands`` to populate
    ``slash_entries``.  Missing trees or older bots without an
    ``app_commands`` surface gracefully degrade to an empty
    ``slash_entries`` tuple.
    """
    entries = _walk_commands(bot)
    slash_entries = _walk_slash_commands(bot)
    router_prefixes = _walk_router_prefixes()
    findings = _compute_findings(entries, router_prefixes)
    ledger = CommandSurfaceLedger(
        version=_LEDGER_VERSION,
        built_at=datetime.datetime.now(tz=datetime.timezone.utc),
        entries=tuple(entries),
        router_prefixes=tuple(router_prefixes),
        findings=findings,
        slash_entries=tuple(slash_entries),
    )
    global _CACHED
    _CACHED = ledger
    logger.info(
        "command_surface_ledger: built v%d — %d prefix command(s), "
        "%d slash command(s), %d router prefix(es), %d finding(s)",
        ledger.version,
        len(ledger.entries),
        len(ledger.slash_entries),
        len(ledger.router_prefixes),
        findings.total,
    )
    return ledger


def get_cached_ledger() -> CommandSurfaceLedger | None:
    """Return the last built ledger, or None if :func:`build_ledger`
    has not yet been called this process.
    """
    return _CACHED


# ---------------------------------------------------------------------------
# Diagnostics provider
# ---------------------------------------------------------------------------


def _snapshot() -> dict[str, Any]:
    """Stable diagnostics snapshot — counts + findings counts only.

    Does NOT include the full entries list (which would explode the
    diagnostics payload).  Operators wanting the full list call
    :func:`get_cached_ledger` from a REPL or future admin command.
    """
    ledger = _CACHED
    if ledger is None:
        return {
            "status": "not_built",
            "hint": "call command_surface_ledger.build_ledger(bot) after cogs load.",
        }
    return {
        "status": "built",
        "version": ledger.version,
        "built_at": ledger.built_at.isoformat(),
        "command_count": len(ledger.entries),
        "router_prefix_count": len(ledger.router_prefixes),
        "slash_entry_count": len(ledger.slash_entries),
        "findings_total": ledger.findings.total,
        "findings": {
            "orphan_cog_subsystems": len(ledger.findings.orphan_cog_subsystems),
            "duplicate_command_names": len(ledger.findings.duplicate_command_names),
            "duplicate_alias_names": len(ledger.findings.duplicate_alias_names),
            "undeclared_entry_points": len(ledger.findings.undeclared_entry_points),
            "router_prefix_unknown": len(ledger.findings.router_prefix_unknown),
            "unclassified_entry_points": len(
                ledger.findings.unclassified_entry_points,
            ),
        },
    }


def _register_diagnostics() -> None:
    from services import diagnostics_service

    diagnostics_service.register("command_surface_ledger", _snapshot)


_register_diagnostics()


__all__ = [
    "CLASSIFICATIONS",
    "Classification",
    "CommandSurfaceEntry",
    "CommandSurfaceLedger",
    "LedgerFindings",
    "RouterPrefixEntry",
    "build_ledger",
    "cog_name_to_subsystem",
    "get_cached_ledger",
    "is_hidden_from_help",
]
