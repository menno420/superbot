"""Unit tests for core.runtime.command_manifest — manifest spine slice 1.

The manifest is a pure projection of the CommandSurfaceLedger, so these
tests construct a ledger fixture directly (the ledger is a frozen
aggregate) and pin: faithful projection (count parity, qualified_name
composition, field mapping), the to_dict() export shape, the cache
round-trip, and the diagnostics provider — the first "reconciliation
test that makes the metadata trustworthy."
"""

from __future__ import annotations

import datetime

import pytest

from core.runtime import command_manifest as cm
from core.runtime.command_surface_ledger import (
    CommandSurfaceEntry,
    CommandSurfaceLedger,
    LedgerFindings,
)


def _e(name: str, cog: str, subsystem: str | None, **kw) -> CommandSurfaceEntry:
    """CommandSurfaceEntry with visibility_tier defaulted (it's positional)."""
    kw.setdefault("visibility_tier", None)
    return CommandSurfaceEntry(name=name, cog_name=cog, subsystem=subsystem, **kw)


def _ledger(
    entries: tuple[CommandSurfaceEntry, ...],
    slash: tuple[CommandSurfaceEntry, ...] = (),
) -> CommandSurfaceLedger:
    return CommandSurfaceLedger(
        version=1,
        built_at=datetime.datetime(2026, 6, 17, tzinfo=datetime.timezone.utc),
        entries=entries,
        router_prefixes=(),
        findings=LedgerFindings(),
        slash_entries=slash,
    )


@pytest.fixture(autouse=True)
def _reset():
    cm._reset_for_tests()
    yield
    cm._reset_for_tests()


# ---------------------------------------------------------------------------
# Faithful projection of the ledger
# ---------------------------------------------------------------------------


def test_projects_every_ledger_entry_exactly_once():
    ledger = _ledger(
        entries=(
            _e("warn", "ModCog", "moderation"),
            _e("xp", "XPCog", "xp"),
        ),
        slash=(_e("ping", "CoreCog", None, kind="slash"),),
    )
    manifest = cm.build_command_manifest(ledger)
    # Count parity: prefix entries + slash entries, no more, no fewer.
    assert len(manifest.commands) == 3
    names = [c.qualified_name for c in manifest.commands]
    assert names == ["warn", "xp", "ping"]  # prefix first, then slash


def test_qualified_name_composes_parent_group():
    ledger = _ledger(
        entries=(
            _e("set", "SettingsCog", "settings", parent_group="settings"),
            _e("standalone", "XPCog", "xp"),
        ),
    )
    manifest = cm.build_command_manifest(ledger)
    quals = {c.qualified_name for c in manifest.commands}
    assert quals == {"settings set", "standalone"}


def test_field_mapping_from_ledger_entry():
    entry = CommandSurfaceEntry(
        name="warn",
        cog_name="ModCog",
        subsystem="moderation",
        visibility_tier="moderator",
        aliases=("w", "warning"),
        kind="prefix",
        classification="primary_entrypoint",
        classification_declared=True,
        discord_hidden=False,
    )
    manifest = cm.build_command_manifest(_ledger((entry,)))
    c = manifest.commands[0]
    assert c.qualified_name == "warn"
    assert c.kind == "prefix"
    assert c.cog == "ModCog"
    assert c.subsystem == "moderation"
    assert c.visibility_tier == "moderator"
    assert c.aliases == ("w", "warning")
    assert c.classification == "primary_entrypoint"
    assert c.classification_declared is True
    assert c.discord_hidden is False
    assert c.runtime_verified is True
    # Deferred fields stay at their empty defaults until later slices.
    assert c.source is None
    assert c.panels == ()
    assert c.actions == ()
    assert c.related_settings == ()
    assert c.capability_required is None


# ---------------------------------------------------------------------------
# Panel join (manifest spine PR2)
# ---------------------------------------------------------------------------


def test_panels_joined_by_subsystem():
    ledger = _ledger(
        entries=(
            _e("warn", "ModCog", "moderation"),
            _e("ask", "AICog", "ai"),
            _e("orphan", "MiscCog", "no_panels"),
        ),
    )
    pmap = {"moderation": ("moderation",), "ai": ("ai",)}
    manifest = cm.build_command_manifest(ledger, panels_by_subsystem=pmap)
    by_name = {c.qualified_name: c for c in manifest.commands}
    assert by_name["warn"].panels == ("moderation",)
    assert by_name["ask"].panels == ("ai",)
    # A subsystem with no panel — or no subsystem at all — joins to nothing.
    assert by_name["orphan"].panels == ()
    # actions stays deferred (no declared button→command binding yet).
    assert by_name["warn"].actions == ()


def test_panels_default_empty_without_join():
    ledger = _ledger((_e("warn", "ModCog", "moderation"),))
    manifest = cm.build_command_manifest(ledger)
    assert manifest.commands[0].panels == ()


# ---------------------------------------------------------------------------
# Envelope + to_dict export shape
# ---------------------------------------------------------------------------


def test_envelope_fields():
    fixed = datetime.datetime(2026, 6, 17, 12, 0, tzinfo=datetime.timezone.utc)
    manifest = cm.build_command_manifest(
        _ledger((_e("x", "C", None),)),
        bot_build="abc123",
        now=fixed,
    )
    assert manifest.version == cm.MANIFEST_VERSION
    assert manifest.bot_build == "abc123"
    assert manifest.generated_at == fixed.isoformat()


def test_to_dict_schema_shape():
    manifest = cm.build_command_manifest(_ledger((_e("warn", "ModCog", "moderation"),)))
    d = manifest.to_dict()
    assert set(d) == {"version", "generated_at", "bot_build", "commands", "findings"}
    assert d["findings"] == []
    assert isinstance(d["commands"], list) and len(d["commands"]) == 1
    cmd = d["commands"][0]
    assert set(cmd) == {
        "qualified_name",
        "kind",
        "cog",
        "subsystem",
        "classification",
        "classification_declared",
        "visibility_tier",
        "aliases",
        "discord_hidden",
        "runtime_verified",
        "source",
        "panels",
        "actions",
        "related_settings",
        "capability_required",
    }
    assert cmd["aliases"] == []  # tuple → list for JSON


# ---------------------------------------------------------------------------
# Reconciliation findings in the envelope (manifest spine PR3)
# ---------------------------------------------------------------------------


def test_to_dict_findings_empty_when_clean():
    # A panel_action command WITH its subsystem's panel joined is clean.
    ledger = _ledger((_e("warn", "ModCog", "moderation", classification="panel_action"),))
    manifest = cm.build_command_manifest(
        ledger,
        panels_by_subsystem={"moderation": ("moderation",)},
    )
    assert manifest.findings() == []
    assert manifest.to_dict()["findings"] == []


def test_to_dict_findings_report_dangling_panel_action():
    # A panel_action command whose subsystem has no panel is flagged.
    ledger = _ledger((_e("orphan", "MiscCog", "ghost", classification="panel_action"),))
    manifest = cm.build_command_manifest(ledger)  # no panel join
    findings = manifest.to_dict()["findings"]
    assert len(findings) == 1
    assert findings[0]["kind"] == "dangling_panel_action"
    assert findings[0]["command"] == "orphan"


# ---------------------------------------------------------------------------
# Cache round-trip + diagnostics
# ---------------------------------------------------------------------------


def test_build_and_cache_round_trip():
    assert cm.get_cached_manifest() is None
    ledger = _ledger((_e("x", "C", None),))
    built = cm.build_and_cache(ledger)
    assert cm.get_cached_manifest() is built
    assert len(built.commands) == 1


def test_diagnostics_snapshot_not_built():
    from services import diagnostics_service

    assert "command_manifest" in diagnostics_service.registered_names()
    snap = diagnostics_service.snapshot("command_manifest")
    assert snap["built"] is False


def test_diagnostics_snapshot_built():
    from services import diagnostics_service

    cm.build_and_cache(
        _ledger(
            entries=(_e("warn", "ModCog", "mod"),),
            slash=(_e("ping", "C", None, kind="slash"),),
        )
    )
    snap = diagnostics_service.snapshot("command_manifest")
    assert snap["built"] is True
    assert snap["command_count"] == 2
    assert snap["by_kind"] == {"prefix": 1, "slash": 1}
    assert snap["version"] == cm.MANIFEST_VERSION
    # Reconciliation surfaced (PR3): no panel_action commands → clean.
    assert snap["finding_count"] == 0
    assert snap["findings"] == []
