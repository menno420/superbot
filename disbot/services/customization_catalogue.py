"""Customization catalogue — S2 of the Global Settings & Customization Manager.

A read-only, frozen catalogue that composes existing platform primitives
into one queryable inventory of every subsystem's customization surface.

Sources combined (all read-only):

* :mod:`core.runtime.command_surface_ledger` — live commands per subsystem.
* :mod:`core.runtime.settings_registry` — declared :class:`SettingSpec`s.
* :mod:`core.runtime.subsystem_schema` — :class:`BindingSpec` and
  :class:`ResourceRequirement` declarations per subsystem.
* :data:`utils.subsystem_registry.SUBSYSTEMS` — display metadata,
  ``entry_points``, ``visibility_tier``, ``related_subsystems``.
* :mod:`services.diagnostics_service` — registered diagnostics provider
  names (cross-discoverability signal).
* live ``bot.cogs`` — cogs implementing ``build_help_menu_view`` (the
  canonical help direct-navigation hook).
* live ``bot.walk_commands()`` — commands carrying ``extras["panel"] is
  True`` (the **deprecated** :func:`panel_command` decorator; zero
  adopters in production — see the decorator's docstring).

Panel-detection priority (authoritative first; regex is last-resort):

1. ``ledger_extras`` — command tagged ``extras["panel"] = True`` via the
   :func:`panel_command` decorator. **Deprecated with zero adopters**:
   no production command carries the tag, so this source is currently
   always empty. Detection stays wired for compatibility, but do not
   add new adopters.
2. ``help_hook`` — cog implements ``build_help_menu_view``. A synthetic
   panel record with ``command="<build_help_menu_view>"`` is created.
3. ``known_list`` — entries in :data:`KNOWN_PANEL_COMMANDS`. **The
   canonical panel-declaration mechanism today** — the
   ``scripts/new_subsystem.py`` scaffold registers new panels here.
4. ``regex_fallback`` — command name matches ``r".+menu$"``. Always
   surfaced as a ``regex_inferred_panels`` finding so operators can
   migrate it to an explicit declaration.

Per-source dependence is observable: the ``customization_catalogue``
diagnostics snapshot reports ``panels_by_source`` counts, so an
operator can see how much of the inventory rests on the curated list
vs. the regex fallback. Settings Phase 2 (declaration coverage —
consolidated plan Batch 4) replaces curated declaration with real
per-domain registrations; that lane, not decorator adoption, is the
successor to this scheme.

Diagnostics provider name: ``"customization_catalogue"``.

Cycle discipline (mirrors :mod:`services.platform_consistency`): all
cross-package imports are function-local. Top-level imports are
stdlib only. Verified by
``tests/unit/services/test_customization_catalogue_import_cycle.py``.
"""

from __future__ import annotations

import datetime
import logging
import re
from collections.abc import Collection
from dataclasses import dataclass
from typing import Any, TypeVar

logger = logging.getLogger("bot.services.customization_catalogue")


_CATALOGUE_VERSION = 1


# A panel command's command name (bare or qualified). Applied to the
# last whitespace-separated segment so subcommands like
# ``platform schemas`` are evaluated against ``schemas`` rather than
# the whole qualified name.
_PANEL_REGEX = re.compile(r".+menu$")


# Curated allowlist of (subsystem, command_name) pairs — the canonical
# panel-declaration mechanism today. New panels register HERE (the
# ``scripts/new_subsystem.py`` scaffold prints the snippet); the
# ``@panel_command`` decorator that was meant to supersede this list is
# deprecated with zero adopters.
#
# An entry here only counts as a panel when the command is actually
# present in the live command surface ledger (i.e. the cog loaded
# successfully). Stale entries are silently ignored.
KNOWN_PANEL_COMMANDS: tuple[tuple[str, str], ...] = (
    ("admin", "adminmenu"),
    ("chain", "chainmenu"),
    ("channel", "channelmenu"),
    ("cleanup", "cleanup"),
    ("cleanup", "wordmenu"),
    ("community_spotlight", "spotlight"),
    ("counting", "countingmenu"),
    ("economy", "economymenu"),
    ("fishing", "fish"),
    ("games", "games"),
    ("general", "generalmenu"),
    ("logging", "logging"),
    ("mining", "minemenu"),
    ("moderation", "modmenu"),
    ("project_moon", "pm"),
    ("proof_channel", "prizemenu"),
    ("role", "rolemenu"),
    ("server_management", "servermanagement"),
    ("ticket", "ticket"),
    ("utility", "utilitymenu"),
    ("ux_lab", "uxlab"),
    ("xp", "xpmenu"),
)


_C = TypeVar("_C")


def panel_command(cmd: _C) -> _C:
    """Decorator marking a command as a subsystem panel entry point.

    .. deprecated:: 2026-06-10
        **Zero adopters; do not add new ones.** This decorator shipped
        with S2 expecting S5/S10 to tag existing panels — that
        migration never happened. The canonical declaration mechanism
        is :data:`KNOWN_PANEL_COMMANDS` (maintained by the
        ``scripts/new_subsystem.py`` scaffold), and Settings Phase 2's
        per-domain registrations (consolidated plan Batch 4) are the
        planned successor. The decorator and its ``ledger_extras``
        detection stay functional so nothing breaks if a tag appears,
        but they are no longer the recommended path.

    Sets ``cmd.extras["panel"] = True`` on the underlying command so
    :func:`build_catalogue` can detect it via the ``ledger_extras``
    source.

    Usage — apply ABOVE ``@commands.command(...)`` so the decorator
    receives the :class:`~discord.ext.commands.Command` instance::

        @panel_command
        @commands.command(name="mymenu")
        async def mymenu(self, ctx):
            ...

    A best-effort attempt is made when applied below ``@commands.command``
    (i.e. to a bare coroutine) — the panel flag is set on the function
    but discord.py won't propagate it onto the resulting Command. Prefer
    the documented order.
    """
    extras = getattr(cmd, "extras", None)
    if extras is None:
        try:
            cmd.extras = {"panel": True}  # type: ignore[attr-defined]
        except (AttributeError, TypeError):  # pragma: no cover - defensive
            pass
    else:
        try:
            extras["panel"] = True
        except (AttributeError, TypeError):  # pragma: no cover - defensive
            pass
    return cmd


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PanelDeclaration:
    """A single detected panel for a subsystem.

    ``source`` is one of ``"ledger_extras" | "help_hook" | "known_list" |
    "regex_fallback"`` and records the highest-priority detection source
    that flagged the panel.
    """

    command: str
    source: str


@dataclass(frozen=True)
class CustomizationEntry:
    """A single subsystem's aggregated customization snapshot."""

    subsystem: str
    display_name: str
    visibility_tier: str | None
    has_schema: bool
    has_help_hook: bool
    has_diagnostics_provider: bool
    panels: tuple[PanelDeclaration, ...]
    setting_names: tuple[str, ...]
    binding_names: tuple[str, ...]
    resource_intents: tuple[str, ...]
    command_count: int
    related_subsystems: tuple[str, ...]


@dataclass(frozen=True)
class CustomizationFindings:
    """Cross-cutting findings computed at build time."""

    subsystems_missing_panel: tuple[str, ...] = ()
    subsystems_missing_help_hook: tuple[str, ...] = ()
    subsystems_missing_schema: tuple[str, ...] = ()
    panels_without_settings: tuple[str, ...] = ()
    settings_without_panel: tuple[str, ...] = ()
    regex_inferred_panels: tuple[str, ...] = ()
    undiscoverable_surfaces: tuple[str, ...] = ()

    @property
    def total(self) -> int:
        return (
            len(self.subsystems_missing_panel)
            + len(self.subsystems_missing_help_hook)
            + len(self.subsystems_missing_schema)
            + len(self.panels_without_settings)
            + len(self.settings_without_panel)
            + len(self.regex_inferred_panels)
            + len(self.undiscoverable_surfaces)
        )


@dataclass(frozen=True)
class CustomizationCatalogue:
    """An immutable snapshot of the customization surface at build time."""

    version: int
    built_at: datetime.datetime
    entries: tuple[CustomizationEntry, ...]
    findings: CustomizationFindings

    def get(self, subsystem: str) -> CustomizationEntry | None:
        for entry in self.entries:
            if entry.subsystem == subsystem:
                return entry
        return None

    def panels(self) -> tuple[PanelDeclaration, ...]:
        out: list[PanelDeclaration] = []
        for entry in self.entries:
            out.extend(entry.panels)
        return tuple(out)

    def by_panel_count(self) -> dict[str, int]:
        return {entry.subsystem: len(entry.panels) for entry in self.entries}


# ---------------------------------------------------------------------------
# Module state — cached last-built catalogue
# ---------------------------------------------------------------------------


_CACHED: CustomizationCatalogue | None = None


def _reset_for_tests() -> None:
    global _CACHED
    _CACHED = None


# ---------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------


_KEYWORDS_UNDISCOVERABLE = ("settings", "config", "policy")


def _walk_help_hooks(bot: object) -> set[str]:
    """Return the set of subsystems whose cog implements
    ``build_help_menu_view``.
    """
    from core.runtime.command_surface_ledger import cog_name_to_subsystem

    out: set[str] = set()
    cogs = getattr(bot, "cogs", None) or {}
    for cog in cogs.values():
        if not callable(getattr(cog, "build_help_menu_view", None)):
            continue
        sub = cog_name_to_subsystem(cog.__class__.__name__)
        if sub:
            out.add(sub)
    return out


def _walk_extras_panels(bot: object) -> set[tuple[str, str]]:
    """Return ``{(subsystem, qualified_name)}`` for every command marked
    ``extras["panel"] is True`` (i.e. tagged by :func:`panel_command`).
    """
    from core.runtime.command_surface_ledger import cog_name_to_subsystem

    walk = getattr(bot, "walk_commands", None)
    if walk is None:
        return set()
    out: set[tuple[str, str]] = set()
    for cmd in walk():
        extras = getattr(cmd, "extras", None) or {}
        if extras.get("panel") is not True:
            continue
        cog = getattr(cmd, "cog", None)
        cog_name = cog.__class__.__name__ if cog is not None else ""
        sub = cog_name_to_subsystem(cog_name) if cog_name else None
        if sub:
            qualified = getattr(cmd, "qualified_name", None) or cmd.name
            out.add((sub, qualified))
    return out


def _ledger_commands_by_subsystem(ledger: Any) -> dict[str, list[str]]:
    """Group ledger entries by subsystem. ``ledger`` may be ``None``."""
    if ledger is None:
        return {}
    out: dict[str, list[str]] = {}
    for entry in getattr(ledger, "entries", ()):
        sub = getattr(entry, "subsystem", None)
        if sub is None:
            continue
        out.setdefault(sub, []).append(entry.name)
    return out


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_catalogue(bot: object | None = None) -> CustomizationCatalogue:
    """Walk every authoritative source and return a frozen snapshot.

    ``bot`` is optional. When provided, the builder additionally walks
    ``bot.cogs`` for ``build_help_menu_view`` hooks and
    ``bot.walk_commands()`` for ``@panel_command`` ``extras["panel"]``
    declarations. When ``bot is None`` those two signals are skipped
    and ``subsystems_missing_help_hook`` stays empty (we have no
    information rather than a false negative).

    Caches the result for diagnostics access; call again to refresh
    after a hot-reload. Sync — no I/O.
    """
    from core.runtime import command_surface_ledger as _cls
    from core.runtime import settings_registry as _sr
    from core.runtime import subsystem_schema as _ss
    from services import diagnostics_service as _ds
    from utils.subsystem_registry import SUBSYSTEMS

    ledger = _cls.get_cached_ledger()
    registry = _sr.get_cached_registry()
    schemas = _ss.all_schemas()
    diag_provider_names = set(_ds.registered_names())
    ledger_cmds_by_sub = _ledger_commands_by_subsystem(ledger)

    help_hook_subsystems = _walk_help_hooks(bot) if bot is not None else set()
    extras_panel_pairs = _walk_extras_panels(bot) if bot is not None else set()

    known_by_sub: dict[str, set[str]] = {}
    for sub, cmd in KNOWN_PANEL_COMMANDS:
        known_by_sub.setdefault(sub, set()).add(cmd)

    entries: list[CustomizationEntry] = []
    regex_inferred: list[str] = []
    panels_without_settings: list[str] = []
    settings_without_panel: list[str] = []
    missing_panel: list[str] = []
    missing_help_hook: list[str] = []
    missing_schema: list[str] = []

    for sub_name in sorted(SUBSYSTEMS):
        meta = SUBSYSTEMS[sub_name]
        schema = schemas.get(sub_name)

        if registry is not None:
            setting_names = tuple(e.name for e in registry.by_subsystem(sub_name))
        else:
            setting_names = tuple(s.name for s in (schema.settings if schema else ()))
        binding_names = tuple(b.name for b in (schema.bindings if schema else ()))
        resource_intents = tuple(
            r.intent for r in (schema.resource_requirements if schema else ())
        )

        ledger_cmds = ledger_cmds_by_sub.get(sub_name, [])
        command_count = len(ledger_cmds)
        ledger_cmd_set = set(ledger_cmds)

        # Panel detection — priority: ledger_extras > help_hook > known_list > regex.
        panels: list[PanelDeclaration] = []
        seen_commands: set[str] = set()

        # (1) ledger_extras — @panel_command tagged commands
        for s, cmd in sorted(extras_panel_pairs):
            if s != sub_name or cmd in seen_commands:
                continue
            panels.append(PanelDeclaration(command=cmd, source="ledger_extras"))
            seen_commands.add(cmd)

        # (2) help_hook — synthetic panel for cogs implementing the hook
        if sub_name in help_hook_subsystems:
            panels.append(
                PanelDeclaration(
                    command="<build_help_menu_view>",
                    source="help_hook",
                ),
            )

        # (3) known_list — curated panel commands. Only count when the
        # command actually appears in the live ledger; absence means the
        # cog failed to load (or hasn't loaded yet at REPL/test time).
        for cmd in sorted(known_by_sub.get(sub_name, ())):
            if cmd in seen_commands:
                continue
            if ledger is not None and cmd in ledger_cmd_set:
                panels.append(PanelDeclaration(command=cmd, source="known_list"))
                seen_commands.add(cmd)

        # (4) regex_fallback — commands ending in "menu" not already
        # detected by a higher-priority source.
        for cmd in sorted(ledger_cmds):
            bare = cmd.split()[-1] if cmd else ""
            if not _PANEL_REGEX.match(bare):
                continue
            if cmd in seen_commands:
                continue
            panels.append(PanelDeclaration(command=cmd, source="regex_fallback"))
            seen_commands.add(cmd)
            regex_inferred.append(f"{sub_name}.{cmd}")

        if not panels:
            missing_panel.append(sub_name)
        if bot is not None and sub_name not in help_hook_subsystems:
            missing_help_hook.append(sub_name)
        if schema is None:
            missing_schema.append(sub_name)
        if panels and not setting_names and not binding_names and not resource_intents:
            for p in panels:
                panels_without_settings.append(f"{sub_name}.{p.command}")
        if setting_names and not panels:
            for s in setting_names:
                settings_without_panel.append(f"{sub_name}.{s}")

        entries.append(
            CustomizationEntry(
                subsystem=sub_name,
                display_name=str(meta.get("display_name", sub_name)),
                visibility_tier=meta.get("visibility_tier"),
                has_schema=schema is not None,
                has_help_hook=sub_name in help_hook_subsystems,
                has_diagnostics_provider=sub_name in diag_provider_names,
                panels=tuple(panels),
                setting_names=setting_names,
                binding_names=binding_names,
                resource_intents=resource_intents,
                command_count=command_count,
                related_subsystems=tuple(meta.get("related_subsystems", ())),
            ),
        )

    # Undiscoverable surfaces: settings/config/policy commands whose
    # owning subsystem has neither a panel nor a help-hook AND whose
    # name is not already an explicit entry_point. Identifies admin
    # commands that ship without a route through help/admin/platform.
    undiscoverable: list[str] = []
    entries_by_sub = {e.subsystem: e for e in entries}
    if ledger is not None:
        for entry in getattr(ledger, "entries", ()):
            sub = getattr(entry, "subsystem", None)
            if sub is None:
                continue
            cat_entry = entries_by_sub.get(sub)
            if cat_entry is None:
                continue
            name_lower = entry.name.lower()
            if not any(tok in name_lower for tok in _KEYWORDS_UNDISCOVERABLE):
                continue
            if cat_entry.panels or cat_entry.has_help_hook:
                continue
            meta = SUBSYSTEMS.get(sub, {})
            if entry.name in (meta.get("entry_points") or ()):
                continue
            undiscoverable.append(f"{sub}.{entry.name}")

    findings = CustomizationFindings(
        subsystems_missing_panel=tuple(sorted(missing_panel)),
        subsystems_missing_help_hook=tuple(sorted(missing_help_hook)),
        subsystems_missing_schema=tuple(sorted(missing_schema)),
        panels_without_settings=tuple(sorted(panels_without_settings)),
        settings_without_panel=tuple(sorted(settings_without_panel)),
        regex_inferred_panels=tuple(sorted(regex_inferred)),
        undiscoverable_surfaces=tuple(sorted(undiscoverable)),
    )

    cat = CustomizationCatalogue(
        version=_CATALOGUE_VERSION,
        built_at=datetime.datetime.now(tz=datetime.timezone.utc),
        entries=tuple(entries),
        findings=findings,
    )
    global _CACHED
    _CACHED = cat
    logger.info(
        "customization_catalogue: built v%d — %d subsystems, %d panels, %d findings",
        cat.version,
        len(cat.entries),
        sum(len(e.panels) for e in cat.entries),
        findings.total,
    )
    return cat


def get_cached_catalogue() -> CustomizationCatalogue | None:
    """Return the last-built catalogue, or ``None`` if not yet built."""
    return _CACHED


# ---------------------------------------------------------------------------
# Actionable settings groups — the Settings hub's discovery rule
# (settings audit §6 inclusion rule + §11 Phase 1, scoreboard Lane 7)
# ---------------------------------------------------------------------------


# Settings Phase 2 (consolidated plan Batch 4): domain-config inclusion is
# DECLARED per subsystem — a ``DomainPanelSpec`` on the subsystem's own
# ``SubsystemSchema`` (registered in its cog_load, e.g.
# ``cogs/cleanup/schemas.py``) — not curated here. The Phase 1
# ``DOMAIN_CONFIG_SUBSYSTEMS`` frozenset this replaced is gone; the
# declaration set is pinned by
# ``tests/unit/invariants/test_domain_panel_declarations.py`` so adding or
# dropping a domain group is a deliberate, test-visible act. Declaring one
# only affects *discovery*; the domain's panel/services stay the mutation
# owner.


@dataclass(frozen=True)
class ActionableGroup:
    """One subsystem the Settings hub should list, and why.

    A group is *actionable* when an operator who opens it can actually do
    something: edit a declared scalar (``editable_setting_count``), edit a
    binding, run a provisionable resource flow, or open a registered
    domain-config panel. Router-only / read-only / internal / empty
    subsystems never become groups (audit §6 — the "28 listed, 3 truncated,
    many empty" defect class).
    """

    subsystem: str
    display_name: str
    description: str
    emoji: str | None
    ui_priority: int
    editable_setting_count: int = 0
    binding_count: int = 0
    resource_count: int = 0
    has_domain_panel: bool = False

    @property
    def surfaces(self) -> tuple[str, ...]:
        """The actionable surface kinds this group declares (stable order)."""
        out: list[str] = []
        if self.editable_setting_count:
            out.append("settings")
        if self.binding_count:
            out.append("bindings")
        if self.resource_count:
            out.append("resources")
        if self.has_domain_panel:
            out.append("panel")
        return tuple(out)


# Settings-dropdown ordering (tools/sim/settings_order_sim.py, 2026-07-01).
# `!settings` is an admin-only surface: the operator opens it to *configure the
# server*, so the server-operations groups (moderation / management / admin +
# admin-tier community like welcome / counters) sort to the TOP — ahead of the
# games / economy / progression groups that lead the *global* ``ui_priority``
# discovery order. This is settings-surface-only: Help and the hubs still sort
# by the global ``ui_priority``, untouched. The sim measured this cut the mean
# config-group find-cost from ~28 to ~8 rows of scrolling.
_SETTINGS_CONFIG_CATEGORIES = frozenset({"moderation", "management", "admin"})
_SETTINGS_ADMIN_TIERS = frozenset({"staff", "moderator", "administrator", "owner"})


def _settings_config_tier(meta: dict[str, object]) -> int:
    """0 for server-config groups (sorted first in ``!settings``), else 1."""
    category = meta.get("category")
    if category in _SETTINGS_CONFIG_CATEGORIES:
        return 0
    if category == "community" and meta.get("visibility_tier") in _SETTINGS_ADMIN_TIERS:
        return 0
    return 1


def actionable_settings_groups() -> tuple[ActionableGroup, ...]:
    """Every subsystem the Settings hub should offer, sorted for display.

    Live composition (no snapshot staleness): reads the identity manifest
    (``utils.subsystem_registry.SUBSYSTEMS``), the live schema declarations
    (``core.runtime.subsystem_schema.all_schemas``), and the declared
    per-schema ``domain_panels`` declarations (Settings Phase 2 — see the
    note above). Inclusion rule (audit §6):

    * ``visibility_mode='internal'`` never appears;
    * otherwise the subsystem needs at least one actionable surface —
      an *editable* scalar (a ``SettingSpec`` with a ``settings_key``),
      a declared binding, a declared resource requirement, or a
      registered domain-config panel.

    Deterministic and side-effect-free; sorted **server-config groups first**
    (see :func:`_settings_config_tier`), then by ``ui_priority`` then display
    name within each tier — so an admin opening ``!settings`` reaches the
    moderation / logging / welcome / roles groups without scrolling past the
    games and economy groups. Discovery only — mutation stays with each
    surface's canonical owner (scalar pipeline / binding / provisioning /
    domain services).
    """
    # Function-local imports: keep this module import-light and let tests
    # monkeypatch the manifest/schema sources.
    from core.runtime.subsystem_schema import all_schemas
    from utils.subsystem_registry import SUBSYSTEMS

    schemas = all_schemas()
    groups: list[ActionableGroup] = []
    tier_by_sub: dict[str, int] = {}
    for name, meta in SUBSYSTEMS.items():
        if meta.get("visibility_mode", "normal") == "internal":
            continue
        schema = schemas.get(name)
        editable = (
            sum(1 for spec in schema.settings if spec.settings_key)
            if schema is not None
            else 0
        )
        bindings = len(schema.bindings) if schema is not None else 0
        resources = len(schema.resource_requirements) if schema is not None else 0
        domain_panel = bool(schema.domain_panels) if schema is not None else False
        if not (editable or bindings or resources or domain_panel):
            continue
        tier_by_sub[name] = _settings_config_tier(meta)
        groups.append(
            ActionableGroup(
                subsystem=name,
                display_name=str(meta.get("display_name", name)),
                description=str(meta.get("description", "")),
                emoji=meta.get("emoji") or None,
                ui_priority=int(meta.get("ui_priority", 99)),
                editable_setting_count=editable,
                binding_count=bindings,
                resource_count=resources,
                has_domain_panel=domain_panel,
            ),
        )
    groups.sort(
        key=lambda g: (
            tier_by_sub[g.subsystem],
            g.ui_priority,
            g.display_name.lower(),
            g.subsystem,
        ),
    )
    return tuple(groups)


async def group_availability(
    guild_id: int,
    subsystems: Collection[str],
) -> dict[str, str]:
    """Actor-facing availability labels for ``subsystems`` in ``guild_id``.

    One deterministic axis today: per-guild **cog routing** (the canonical
    "is this feature active here" owner, ``services.command_routing``). A
    subsystem with a guild-scope ``enabled=false`` routing row maps to a
    ``"routed off"`` label; everything else is absent from the dict. The hub
    renders the label on the group's option — the group stays *reachable*
    (an admin may configure a routed-off feature before enabling it), and
    every edit/reset callback still re-checks authority at execution time.

    Supplementary by contract: a routing read failure returns ``{}`` rather
    than sinking the hub. Channel/category-scope rows are deliberately not
    surfaced — a partial restriction is not a group-level state.
    """
    from core.runtime.command_surface_ledger import cog_name_to_subsystem
    from services import command_routing

    wanted = set(subsystems)
    labels: dict[str, str] = {}
    try:
        rows = await command_routing.list_for_guild(guild_id)
    except Exception:  # noqa: BLE001 — availability is supplementary
        logger.warning(
            "customization_catalogue: routing availability read failed; "
            "rendering hub without availability labels",
            exc_info=True,
        )
        return {}
    for row in rows:
        if row.get("scope_type") != "guild" or row.get("enabled"):
            continue
        raw = str(row.get("cog_name") or "")
        # Routing rows store the subsystem key (the setup section's option
        # values); normalise class-name rows defensively.
        key = raw if raw in wanted else cog_name_to_subsystem(raw)
        if key in wanted:
            labels[str(key)] = "routed off"
    return labels


# ---------------------------------------------------------------------------
# Diagnostics provider — registers at import time
# ---------------------------------------------------------------------------


def _snapshot() -> dict[str, Any]:
    """Stable diagnostics snapshot for ``!platform customization``.

    Returns counts + findings counts only. Operators wanting the full
    entries list call :func:`get_cached_catalogue` from a REPL or a
    future admin command.
    """
    cat = _CACHED
    if cat is None:
        return {
            "status": "not_built",
            "hint": "call customization_catalogue.build_catalogue(bot) after cogs load.",
        }
    panel_count = sum(len(e.panels) for e in cat.entries)
    panels_by_source: dict[str, int] = {}
    for entry in cat.entries:
        for p in entry.panels:
            panels_by_source[p.source] = panels_by_source.get(p.source, 0) + 1
    return {
        "status": "built",
        "version": cat.version,
        "built_at": cat.built_at.isoformat(),
        "subsystem_count": len(cat.entries),
        "panel_count": panel_count,
        "panels_by_source": panels_by_source,
        "subsystems_with_schema": sum(1 for e in cat.entries if e.has_schema),
        "subsystems_with_help_hook": sum(1 for e in cat.entries if e.has_help_hook),
        "findings_total": cat.findings.total,
        "findings": {
            "subsystems_missing_panel": len(cat.findings.subsystems_missing_panel),
            "subsystems_missing_help_hook": len(
                cat.findings.subsystems_missing_help_hook,
            ),
            "subsystems_missing_schema": len(cat.findings.subsystems_missing_schema),
            "panels_without_settings": len(cat.findings.panels_without_settings),
            "settings_without_panel": len(cat.findings.settings_without_panel),
            "regex_inferred_panels": len(cat.findings.regex_inferred_panels),
            "undiscoverable_surfaces": len(cat.findings.undiscoverable_surfaces),
        },
    }


def _register_diagnostics() -> None:
    from services import diagnostics_service

    diagnostics_service.register("customization_catalogue", _snapshot)


_register_diagnostics()


__all__: list[str] = [
    "ActionableGroup",
    "CustomizationCatalogue",
    "CustomizationEntry",
    "CustomizationFindings",
    "KNOWN_PANEL_COMMANDS",
    "PanelDeclaration",
    "actionable_settings_groups",
    "build_catalogue",
    "get_cached_catalogue",
    "group_availability",
    "panel_command",
]
