"""Unit tests for core.runtime.command_surface_ledger — Phase 2 PR-12."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.runtime import command_surface_ledger as ledger_mod
from core.runtime.command_surface_ledger import (
    CLASSIFICATIONS,
    CommandSurfaceEntry,
    CommandSurfaceLedger,
    LedgerFindings,
    RouterPrefixEntry,
    build_ledger,
    cog_name_to_subsystem,
    get_cached_ledger,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    ledger_mod._reset_for_tests()
    yield
    ledger_mod._reset_for_tests()


# ---------------------------------------------------------------------------
# cog_name_to_subsystem
# ---------------------------------------------------------------------------


def test_cog_name_strips_cog_suffix_and_lowercases():
    assert cog_name_to_subsystem("EconomyCog") == "economy"
    assert cog_name_to_subsystem("ModerationCog") == "moderation"
    assert cog_name_to_subsystem("AdminCog") == "admin"


def test_cog_name_returns_none_when_no_matching_subsystem():
    # "Bogus" → "bogus" — not a SUBSYSTEMS key.
    assert cog_name_to_subsystem("BogusCog") is None


def test_cog_name_returns_none_on_empty_input():
    assert cog_name_to_subsystem("") is None


def test_cog_name_handles_no_cog_suffix():
    # "Economy" → "economy" — still matches SUBSYSTEMS.
    assert cog_name_to_subsystem("Economy") == "economy"


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def _make_cmd(
    name: str,
    cog_name: str = "EconomyCog",
    aliases: tuple[str, ...] = (),
    parent: object | None = None,
) -> MagicMock:
    cmd = MagicMock()
    cmd.name = name
    cmd.qualified_name = f"{parent.qualified_name} {name}" if parent else name
    cmd.aliases = list(aliases)
    cmd.parent = parent
    if cog_name:
        cog = MagicMock()
        cog.__class__.__name__ = cog_name
        # Patch the class name so .__class__.__name__ returns cog_name.
        cmd.cog = MagicMock()
        cmd.cog.__class__ = type(cog_name, (), {})
    else:
        cmd.cog = None
    return cmd


def _make_bot(*commands) -> MagicMock:
    bot = MagicMock()
    bot.walk_commands = MagicMock(return_value=list(commands))
    return bot


def test_build_ledger_captures_basic_command_metadata():
    bot = _make_bot(_make_cmd("daily", cog_name="EconomyCog"))
    ledger = build_ledger(bot)
    assert ledger.version == 1
    assert len(ledger.entries) == 1
    entry = ledger.entries[0]
    assert entry.name == "daily"
    assert entry.cog_name == "EconomyCog"
    assert entry.subsystem == "economy"
    assert entry.kind == "prefix"


def test_build_ledger_records_aliases():
    bot = _make_bot(
        _make_cmd("daily", cog_name="EconomyCog", aliases=("d", "daily_claim")),
    )
    ledger = build_ledger(bot)
    assert ledger.entries[0].aliases == ("d", "daily_claim")


def test_build_ledger_records_subcommand_parent():
    parent_grp = MagicMock()
    parent_grp.qualified_name = "platform"
    sub = _make_cmd("consistency", cog_name="DiagnosticCog", parent=parent_grp)
    bot = _make_bot(sub)
    ledger = build_ledger(bot)
    assert ledger.entries[0].name == "platform consistency"
    assert ledger.entries[0].parent_group == "platform"


def test_build_ledger_marks_subsystem_none_for_orphan_cog():
    bot = _make_bot(_make_cmd("bogus", cog_name="BogusCog"))
    ledger = build_ledger(bot)
    assert ledger.entries[0].subsystem is None
    assert ledger.entries[0].visibility_tier is None
    assert "BogusCog" in ledger.findings.orphan_cog_subsystems


def test_build_ledger_visibility_tier_from_subsystems():
    bot = _make_bot(_make_cmd("ban", cog_name="ModerationCog"))
    ledger = build_ledger(bot)
    # moderation tier is "moderator" per SUBSYSTEMS.
    assert ledger.entries[0].visibility_tier == "moderator"


def test_build_ledger_is_declared_flag_set_for_entry_points():
    # "daily" is a declared entry_point of "economy" per SUBSYSTEMS.
    bot = _make_bot(_make_cmd("daily", cog_name="EconomyCog"))
    ledger = build_ledger(bot)
    assert ledger.entries[0].is_declared is True


def test_build_ledger_is_declared_false_for_undeclared_command():
    # Random command name not in SUBSYSTEMS.entry_points for economy.
    bot = _make_bot(_make_cmd("xyzzy_unknown", cog_name="EconomyCog"))
    ledger = build_ledger(bot)
    assert ledger.entries[0].is_declared is False


def test_build_ledger_is_declared_matches_qualified_subcommand_name():
    """When SUBSYSTEMS.entry_points declares a qualified group
    subcommand like ``"economy stats"``, the ledger must flag the
    matching subcommand as declared even though the bare name
    (``"stats"``) does not appear in entry_points."""
    parent = MagicMock()
    parent.qualified_name = "economy"
    sub = _make_cmd("stats", cog_name="EconomyCog", parent=parent)
    bot = _make_bot(sub)
    with patch(
        "utils.subsystem_registry.SUBSYSTEMS",
        {
            "economy": {
                "entry_points": ["economy stats"],
                "visibility_tier": "user",
            },
        },
    ):
        ledger = build_ledger(bot)
    assert ledger.entries[0].name == "economy stats"
    assert ledger.entries[0].is_declared is True


def test_build_ledger_is_declared_matches_bare_subcommand_name():
    """Conversely, if SUBSYSTEMS lists a bare name like ``"stats"``
    (the legacy convention), a subcommand whose qualified name is
    ``"economy stats"`` is still flagged as declared."""
    parent = MagicMock()
    parent.qualified_name = "economy"
    sub = _make_cmd("stats", cog_name="EconomyCog", parent=parent)
    bot = _make_bot(sub)
    with patch(
        "utils.subsystem_registry.SUBSYSTEMS",
        {
            "economy": {
                "entry_points": ["stats"],
                "visibility_tier": "user",
            },
        },
    ):
        ledger = build_ledger(bot)
    assert ledger.entries[0].is_declared is True


def test_build_ledger_handles_bot_without_walk_commands():
    bot = MagicMock(spec=[])  # no walk_commands attribute
    ledger = build_ledger(bot)
    assert ledger.entries == ()


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


def test_findings_detect_duplicate_command_names():
    # Same qualified_name registered by two different cogs.
    cmd_a = _make_cmd("balance", cog_name="EconomyCog")
    cmd_b = _make_cmd("balance", cog_name="ModerationCog")
    bot = _make_bot(cmd_a, cmd_b)
    ledger = build_ledger(bot)
    assert "balance" in ledger.findings.duplicate_command_names


def test_findings_detect_alias_collision_with_primary_name():
    # 'd' is an alias of 'daily', but also a primary name elsewhere.
    cmd_a = _make_cmd("daily", cog_name="EconomyCog", aliases=("d",))
    cmd_b = _make_cmd("d", cog_name="EconomyCog")
    bot = _make_bot(cmd_a, cmd_b)
    ledger = build_ledger(bot)
    assert "d" in ledger.findings.duplicate_alias_names


def test_findings_detect_alias_collision_between_two_commands():
    cmd_a = _make_cmd("foo", cog_name="EconomyCog", aliases=("xx",))
    cmd_b = _make_cmd("bar", cog_name="EconomyCog", aliases=("xx",))
    bot = _make_bot(cmd_a, cmd_b)
    ledger = build_ledger(bot)
    assert "xx" in ledger.findings.duplicate_alias_names


def test_findings_detect_undeclared_entry_points():
    # No commands registered → every SUBSYSTEMS.entry_points name is undeclared.
    bot = _make_bot()
    ledger = build_ledger(bot)
    # economy.daily is declared in SUBSYSTEMS — should appear in undeclared.
    assert "economy.daily" in ledger.findings.undeclared_entry_points


def test_findings_orphan_cog_subsystems_empty_when_all_match():
    bot = _make_bot(
        _make_cmd("daily", cog_name="EconomyCog"),
        _make_cmd("ban", cog_name="ModerationCog"),
    )
    ledger = build_ledger(bot)
    assert ledger.findings.orphan_cog_subsystems == ()


def test_findings_total_aggregates_all_buckets():
    findings = LedgerFindings(
        orphan_cog_subsystems=("BogusCog",),
        duplicate_command_names=("balance",),
        duplicate_alias_names=("d",),
        undeclared_entry_points=("economy.daily",),
        router_prefix_unknown=("xxx",),
    )
    assert findings.total == 5


def test_router_prefixes_marked_unknown_when_not_in_subsystems():
    fake_handlers = {"unknown_prefix_xyz": lambda: None}
    bot = _make_bot()
    with patch.object(
        ledger_mod,
        "_walk_router_prefixes",
        return_value=[RouterPrefixEntry(prefix="unknown_prefix_xyz", subsystem=None)],
    ):
        ledger = build_ledger(bot)
    assert "unknown_prefix_xyz" in ledger.findings.router_prefix_unknown


def test_router_prefix_known_when_in_subsystems():
    bot = _make_bot()
    with patch.object(
        ledger_mod,
        "_walk_router_prefixes",
        return_value=[RouterPrefixEntry(prefix="economy", subsystem="economy")],
    ):
        ledger = build_ledger(bot)
    assert "economy" not in ledger.findings.router_prefix_unknown


# ---------------------------------------------------------------------------
# Query API
# ---------------------------------------------------------------------------


def test_ledger_by_subsystem_returns_matching_entries():
    bot = _make_bot(
        _make_cmd("daily", cog_name="EconomyCog"),
        _make_cmd("balance", cog_name="EconomyCog"),
        _make_cmd("ban", cog_name="ModerationCog"),
    )
    ledger = build_ledger(bot)
    economy = ledger.by_subsystem("economy")
    assert {e.name for e in economy} == {"daily", "balance"}
    moderation = ledger.by_subsystem("moderation")
    assert {e.name for e in moderation} == {"ban"}


def test_ledger_find_returns_entry_by_name():
    bot = _make_bot(_make_cmd("daily", cog_name="EconomyCog"))
    ledger = build_ledger(bot)
    found = ledger.find("daily")
    assert found is not None
    assert found.name == "daily"
    assert ledger.find("nonexistent") is None


def test_ledger_find_returns_entry_by_alias():
    """find() must resolve a command via its declared aliases so
    callers (PanelRegistry, future help/wizard) don't have to walk
    .aliases themselves."""
    bot = _make_bot(_make_cmd("daily", cog_name="EconomyCog", aliases=("d",)))
    ledger = build_ledger(bot)
    found = ledger.find("d")
    assert found is not None
    assert found.name == "daily"


def test_ledger_find_primary_name_wins_over_alias_collision():
    """When a name is both a primary command and an alias of another,
    the primary entry wins."""
    primary = _make_cmd("d", cog_name="EconomyCog")
    aliased = _make_cmd("daily", cog_name="EconomyCog", aliases=("d",))
    bot = _make_bot(primary, aliased)
    ledger = build_ledger(bot)
    found = ledger.find("d")
    assert found is not None
    assert found.name == "d"  # the primary entry wins, not the aliased one


def test_ledger_subsystem_for_command_returns_owner():
    bot = _make_bot(_make_cmd("daily", cog_name="EconomyCog"))
    ledger = build_ledger(bot)
    assert ledger.subsystem_for_command("daily") == "economy"
    assert ledger.subsystem_for_command("nonexistent") is None


def test_ledger_subsystem_for_command_is_alias_aware():
    """subsystem_for_command must resolve via aliases too — otherwise
    PanelRegistry / help would mis-attribute alias invocations."""
    bot = _make_bot(
        _make_cmd("daily", cog_name="EconomyCog", aliases=("d", "claim")),
    )
    ledger = build_ledger(bot)
    assert ledger.subsystem_for_command("d") == "economy"
    assert ledger.subsystem_for_command("claim") == "economy"


# ---------------------------------------------------------------------------
# Cache + diagnostics
# ---------------------------------------------------------------------------


def test_get_cached_ledger_returns_none_before_first_build():
    assert get_cached_ledger() is None


def test_get_cached_ledger_returns_last_built_snapshot():
    bot = _make_bot(_make_cmd("daily", cog_name="EconomyCog"))
    built = build_ledger(bot)
    cached = get_cached_ledger()
    assert cached is built


def test_diagnostics_snapshot_not_built_state():
    snap = ledger_mod._snapshot()
    assert snap["status"] == "not_built"
    assert "hint" in snap


def test_diagnostics_snapshot_built_state_includes_counts():
    bot = _make_bot(
        _make_cmd("daily", cog_name="EconomyCog"),
        _make_cmd("ban", cog_name="ModerationCog"),
    )
    build_ledger(bot)
    snap = ledger_mod._snapshot()
    assert snap["status"] == "built"
    assert snap["version"] == 1
    assert snap["command_count"] == 2
    assert "router_prefix_count" in snap
    assert "slash_entry_count" in snap
    assert snap["slash_entry_count"] == 0
    assert "findings_total" in snap
    assert isinstance(snap["findings"], dict)
    # Per-bucket finding counts present.
    for key in (
        "orphan_cog_subsystems",
        "duplicate_command_names",
        "duplicate_alias_names",
        "undeclared_entry_points",
        "router_prefix_unknown",
    ):
        assert key in snap["findings"]


def test_diagnostics_service_registers_provider():
    from services import diagnostics_service

    # Module-level _register_diagnostics() ran at import.
    snap = diagnostics_service.snapshot("command_surface_ledger")
    assert "status" in snap


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


def test_ledger_is_frozen():
    bot = _make_bot()
    ledger = build_ledger(bot)
    with pytest.raises(Exception):
        ledger.version = 99  # type: ignore[misc]


def test_entry_is_frozen():
    entry = CommandSurfaceEntry(
        name="daily",
        cog_name="EconomyCog",
        subsystem="economy",
        visibility_tier="user",
    )
    with pytest.raises(Exception):
        entry.name = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Source discipline (no cycle-sensitive top-level imports)
# ---------------------------------------------------------------------------


def test_module_source_keeps_subsystem_registry_function_local():
    """utils.subsystem_registry imports must stay inside functions to
    match the cycle-sensitive discipline used by sibling runtime
    modules (PR-10 / PR-11 pattern)."""
    src = Path(ledger_mod.__file__).read_text()
    head = src.split("\n\nasync def", 1)[0].split("\n\ndef ", 1)[0]
    assert "from utils.subsystem_registry" not in head, (
        "Top-level import of utils.subsystem_registry would force the "
        "core.runtime package to resolve subsystem_registry while it "
        "is still loading; keep the import inside the functions that "
        "need it."
    )


def test_does_not_call_validate_identity_contract():
    """The ledger must NOT call validate_identity_contract — the two
    pieces are deliberately complementary (validator = findings;
    ledger = queryable data).  Calling the validator from the ledger
    builder would duplicate work and risk circular semantics.

    We check at the AST level so docstrings/comments mentioning the
    validator (for context) don't trip the test."""
    import ast

    src = Path(ledger_mod.__file__).read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "validate_identity_contract"
            ):
                pytest.fail("Ledger calls validate_identity_contract (attribute call)")
            if isinstance(func, ast.Name) and func.id == "validate_identity_contract":
                pytest.fail("Ledger calls validate_identity_contract (bare call)")
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "validate_identity_contract":
                    pytest.fail(
                        "Ledger imports validate_identity_contract — "
                        "complementary, not consumer",
                    )


# ---------------------------------------------------------------------------
# PR-06a — Classification contract (additive)
# ---------------------------------------------------------------------------


class TestClassification:
    def test_classifications_tuple_matches_literal_args(self):
        """Canonical tuple must list every value declared in the
        Classification Literal — drift would let cog annotations use a
        value the type checker accepts but no consumer knows about."""
        from typing import get_args

        from core.runtime.command_surface_ledger import Classification

        assert set(CLASSIFICATIONS) == set(get_args(Classification))

    def test_classifications_includes_seven_canonical_values(self):
        assert set(CLASSIFICATIONS) == {
            "primary_entrypoint",
            "power_user_shortcut",
            "panel_action",
            "legacy_duplicate",
            "internal_admin",
            "hidden",
            "deprecated",
        }

    def test_command_surface_entry_default_classification(self):
        entry = CommandSurfaceEntry(
            name="daily",
            cog_name="EconomyCog",
            subsystem="economy",
            visibility_tier="user",
        )
        assert entry.classification == "primary_entrypoint"

    def test_command_surface_entry_classification_explicitly_set(self):
        entry = CommandSurfaceEntry(
            name="legacy_daily",
            cog_name="EconomyCog",
            subsystem="economy",
            visibility_tier="user",
            classification="legacy_duplicate",
        )
        assert entry.classification == "legacy_duplicate"

    def test_findings_unclassified_entry_points_default_empty(self):
        findings = LedgerFindings()
        assert findings.unclassified_entry_points == ()
        assert findings.total == 0

    def test_findings_total_includes_unclassified_count(self):
        findings = LedgerFindings(
            unclassified_entry_points=("economy.daily", "rps.duel"),
        )
        assert findings.total == 2

    def test_diagnostics_snapshot_includes_unclassified_count(self):
        """The diagnostics provider exposes the new bucket so the
        readiness embed and !platform diagnostics show it without
        cog-side knowledge of the field name."""
        from core.runtime.command_surface_ledger import _snapshot

        bot = MagicMock()
        bot.walk_commands = lambda: []
        with patch(
            "core.runtime.command_surface_ledger._walk_router_prefixes",
            return_value=[],
        ):
            build_ledger(bot)
        snap = _snapshot()
        assert "unclassified_entry_points" in snap["findings"]
        assert snap["findings"]["unclassified_entry_points"] == 0


# ---------------------------------------------------------------------------
# PR-06b — Slash command ledger ingestion
# ---------------------------------------------------------------------------


def _make_slash_cmd(
    name: str,
    cog_name: str = "DiagnosticCog",
    parent_name: str | None = None,
) -> MagicMock:
    """Build a discord.py ``app_commands.Command`` look-alike.

    Leaf commands have a ``callback``; groups don't, so the walker
    can filter groups out.  ``binding`` is the cog instance.
    """
    cmd = MagicMock()
    cmd.name = name
    cmd.qualified_name = f"{parent_name} {name}" if parent_name else name
    cmd.callback = MagicMock()  # marks this as a leaf, not a group
    if cog_name:
        cmd.binding = MagicMock()
        cmd.binding.__class__ = type(cog_name, (), {})
    else:
        cmd.binding = None
    if parent_name:
        parent = MagicMock()
        parent.qualified_name = parent_name
        cmd.parent = parent
    else:
        cmd.parent = None
    return cmd


def _make_bot_with_tree(*prefix_cmds, slash_cmds=()) -> MagicMock:
    bot = MagicMock()
    bot.walk_commands = MagicMock(return_value=list(prefix_cmds))
    bot.tree = MagicMock()
    bot.tree.walk_commands = MagicMock(return_value=list(slash_cmds))
    return bot


class TestSlashLedgerIngestion:
    def test_build_ledger_walks_slash_tree(self):
        cmd = _make_slash_cmd("setup-status", cog_name="DiagnosticCog")
        bot = _make_bot_with_tree(slash_cmds=(cmd,))
        ledger = build_ledger(bot)
        assert len(ledger.slash_entries) == 1
        slash = ledger.slash_entries[0]
        assert slash.name == "setup-status"
        assert slash.cog_name == "DiagnosticCog"
        assert slash.subsystem == "diagnostic"
        assert slash.kind == "slash"

    def test_build_ledger_captures_five_setup_slash_commands(self):
        """The 5 live setup slash commands appear in slash_entries when
        the bot tree contains them.  PR-06b's primary regression."""
        names = (
            "setup-status",
            "setup-reset",
            "setup-skip",
            "setup-unskip",
            "setup-depth",
        )
        cmds = [_make_slash_cmd(n, cog_name="DiagnosticCog") for n in names]
        bot = _make_bot_with_tree(slash_cmds=cmds)
        ledger = build_ledger(bot)
        captured = {e.name for e in ledger.slash_entries}
        assert captured == set(names)
        for entry in ledger.slash_entries:
            assert entry.kind == "slash"
            assert entry.classification == "primary_entrypoint"

    def test_slash_groups_filtered_out(self):
        """``app_commands.Group`` instances have no ``callback`` and
        must not appear as slash entries — only leaf commands do."""
        leaf = _make_slash_cmd("setup-status", cog_name="DiagnosticCog")
        group = MagicMock(spec=["name"])
        group.name = "setup"
        bot = _make_bot_with_tree(slash_cmds=(group, leaf))
        ledger = build_ledger(bot)
        names = [e.name for e in ledger.slash_entries]
        assert "setup-status" in names
        assert "setup" not in names

    def test_build_ledger_handles_bot_without_tree(self):
        """Bots without an ``app_commands`` surface (older fixtures)
        still build a ledger; slash_entries is empty."""
        bot = MagicMock(spec=["walk_commands"])
        bot.walk_commands = MagicMock(return_value=[])
        ledger = build_ledger(bot)
        assert ledger.slash_entries == ()

    def test_build_ledger_handles_tree_walk_raise(self):
        """Defensive: if tree.walk_commands raises, slash ingestion
        returns an empty list rather than crashing the builder."""
        bot = MagicMock()
        bot.walk_commands = MagicMock(return_value=[])
        bot.tree = MagicMock()
        bot.tree.walk_commands = MagicMock(side_effect=RuntimeError("boom"))
        ledger = build_ledger(bot)
        assert ledger.slash_entries == ()

    def test_slash_entry_records_parent_group(self):
        sub = _make_slash_cmd(
            "status",
            cog_name="DiagnosticCog",
            parent_name="setup",
        )
        bot = _make_bot_with_tree(slash_cmds=(sub,))
        ledger = build_ledger(bot)
        assert ledger.slash_entries[0].name == "setup status"
        assert ledger.slash_entries[0].parent_group == "setup"

    def test_diagnostics_snapshot_reflects_slash_entry_count(self):
        from core.runtime.command_surface_ledger import _snapshot

        cmds = [
            _make_slash_cmd(n, cog_name="DiagnosticCog")
            for n in ("setup-status", "setup-reset")
        ]
        bot = _make_bot_with_tree(slash_cmds=cmds)
        with patch(
            "core.runtime.command_surface_ledger._walk_router_prefixes",
            return_value=[],
        ):
            build_ledger(bot)
        snap = _snapshot()
        assert snap["slash_entry_count"] == 2


# ---------------------------------------------------------------------------
# PR-06c — Classification ingestion + help-hidden helper
# ---------------------------------------------------------------------------


class TestClassificationIngestion:
    def test_walk_commands_reads_classification_from_extras(self):
        from core.runtime.command_surface_ledger import is_hidden_from_help

        cmd = _make_cmd("legacy_alias", cog_name="EconomyCog")
        cmd.extras = {"classification": "legacy_duplicate"}
        bot = _make_bot(cmd)
        ledger = build_ledger(bot)
        assert ledger.entries[0].classification == "legacy_duplicate"
        assert is_hidden_from_help(ledger.entries[0]) is True

    def test_walk_commands_defaults_classification_when_extras_missing(self):
        cmd = _make_cmd("daily", cog_name="EconomyCog")
        cmd.extras = None  # missing/non-dict
        bot = _make_bot(cmd)
        ledger = build_ledger(bot)
        assert ledger.entries[0].classification == "primary_entrypoint"

    def test_walk_commands_ignores_invalid_classification(self):
        cmd = _make_cmd("daily", cog_name="EconomyCog")
        cmd.extras = {"classification": "garbage"}
        bot = _make_bot(cmd)
        ledger = build_ledger(bot)
        assert ledger.entries[0].classification == "primary_entrypoint"

    def test_walk_slash_commands_reads_classification(self):
        from core.runtime.command_surface_ledger import is_hidden_from_help

        cmd = _make_slash_cmd("legacy-alias", cog_name="DiagnosticCog")
        cmd.extras = {"classification": "deprecated"}
        bot = _make_bot_with_tree(slash_cmds=(cmd,))
        ledger = build_ledger(bot)
        assert ledger.slash_entries[0].classification == "deprecated"
        assert is_hidden_from_help(ledger.slash_entries[0]) is True

    def test_is_hidden_from_help_filters_three_classifications(self):
        from core.runtime.command_surface_ledger import (
            CommandSurfaceEntry,
            is_hidden_from_help,
        )

        common = dict(
            name="x",
            cog_name="EconomyCog",
            subsystem="economy",
            visibility_tier="user",
        )
        for cls in ("hidden", "deprecated", "legacy_duplicate"):
            entry = CommandSurfaceEntry(**common, classification=cls)
            assert is_hidden_from_help(entry) is True, f"{cls!r} must be hidden"

    def test_is_hidden_from_help_keeps_default_visible(self):
        from core.runtime.command_surface_ledger import (
            CommandSurfaceEntry,
            is_hidden_from_help,
        )

        entry = CommandSurfaceEntry(
            name="daily",
            cog_name="EconomyCog",
            subsystem="economy",
            visibility_tier="user",
        )
        assert is_hidden_from_help(entry) is False
