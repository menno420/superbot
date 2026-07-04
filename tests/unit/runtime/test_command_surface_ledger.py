"""Unit tests for core.runtime.command_surface_ledger — Phase 2 PR-12."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.runtime import command_surface_ledger as ledger_mod
from core.runtime.command_surface_ledger import (
    ALIAS_DELIBERATION_THRESHOLD,
    CLASSIFICATIONS,
    HIDDEN_ROUTE_CLASSIFICATIONS,
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


def test_multiword_cog_names_convert_to_snake_case():
    """Q-0026: a multi-word cog class resolves to its snake_case key.

    Before the fix these collapsed to ``servermanagement`` /
    ``proofchannel`` / ``fourtwenty``; the latter two silently failed to
    match their already-snake_case registry keys (``proof_channel`` /
    ``four_twenty``), so their commands were orphaned in the ledger.
    """
    assert cog_name_to_subsystem("ServerManagementCog") == "server_management"
    assert cog_name_to_subsystem("ProofChannelCog") == "proof_channel"
    assert cog_name_to_subsystem("FourTwentyCog") == "four_twenty"


def test_acronym_cog_names_stay_collapsed():
    """Acronym runs are a single token — no spurious underscore."""
    assert cog_name_to_subsystem("BTD6Cog") == "btd6"
    assert cog_name_to_subsystem("AICog") == "ai"


def test_snake_case_is_the_output_contract():
    """The conversion output is snake_case regardless of registration.

    A future ``FooBarBazCog`` must register ``foo_bar_baz`` (not the
    collapsed ``foobarbaz``) to resolve.  Pinned against a synthetic
    registry so the contract is documented independently of today's
    keys — this is the regression guard for new multi-word subsystems.
    """
    with patch(
        "utils.subsystem_registry.SUBSYSTEMS",
        {"foo_bar_baz": {"visibility_tier": "user"}},
    ):
        assert cog_name_to_subsystem("FooBarBazCog") == "foo_bar_baz"
    # With only the collapsed key registered, the cog no longer resolves —
    # which is exactly the orphan trap Q-0026 removed.
    with patch(
        "utils.subsystem_registry.SUBSYSTEMS",
        {"foobarbaz": {"visibility_tier": "user"}},
    ):
        assert cog_name_to_subsystem("FooBarBazCog") is None


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


def test_build_ledger_resolves_multiword_subsystem_cog():
    """Q-0026 regression guard (end-to-end): a multi-word cog's command
    is attributed to its snake_case subsystem and is NOT reported as an
    orphan.  ``ServerManagementCog`` previously collapsed to
    ``servermanagement``; the registry key is now ``server_management``.
    """
    bot = _make_bot(
        _make_cmd("servermanagement", cog_name="ServerManagementCog"),
    )
    ledger = build_ledger(bot)
    assert ledger.entries[0].subsystem == "server_management"
    assert "ServerManagementCog" not in ledger.findings.orphan_cog_subsystems


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
        """A slash command's classification flows through to the entry.

        Note: PR-06c review fix — ``deprecated`` is **visible** by
        policy (rendered with a deprecation badge); we use ``hidden``
        here to assert the filter path.
        """
        from core.runtime.command_surface_ledger import is_hidden_from_help

        cmd = _make_slash_cmd("admin-only", cog_name="DiagnosticCog")
        cmd.extras = {"classification": "hidden"}
        bot = _make_bot_with_tree(slash_cmds=(cmd,))
        ledger = build_ledger(bot)
        assert ledger.slash_entries[0].classification == "hidden"
        assert is_hidden_from_help(ledger.slash_entries[0]) is True

    def test_deprecated_remains_visible_per_classification_contract(self):
        """The Classification docstring promises deprecated commands are
        "surfaced with a deprecation warning" — they must NOT be
        filtered out of help.  Policy lives in the canonical
        _HELP_HIDDEN_CLASSIFICATIONS set in command_surface_ledger.
        """
        from core.runtime.command_surface_ledger import (
            CommandSurfaceEntry,
            is_hidden_from_help,
        )

        entry = CommandSurfaceEntry(
            name="old_cmd",
            cog_name="EconomyCog",
            subsystem="economy",
            visibility_tier="user",
            classification="deprecated",
        )
        assert is_hidden_from_help(entry) is False

    def test_is_hidden_from_help_filters_hidden_and_legacy_duplicate(self):
        """PR-06c review fix: only ``hidden`` and ``legacy_duplicate``
        are filtered from help.  Deprecated is rendered with a badge
        (see ``test_deprecated_remains_visible_per_classification_contract``)."""
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
        for cls in ("hidden", "legacy_duplicate"):
            entry = CommandSurfaceEntry(**common, classification=cls)
            assert is_hidden_from_help(entry) is True, f"{cls!r} must be hidden"

    def test_is_command_hidden_from_help_consumes_canonical_policy(self):
        """The cmd-extras helper (used by help_cog) and the entry-based
        helper (used by ledger consumers) must apply the SAME policy.
        Drift here would let help and the ledger disagree about which
        commands are public."""
        from unittest.mock import MagicMock

        from core.runtime.command_surface_ledger import (
            is_command_hidden_from_help,
        )

        cmd_hidden = MagicMock()
        cmd_hidden.extras = {"classification": "hidden"}
        assert is_command_hidden_from_help(cmd_hidden) is True

        cmd_legacy = MagicMock()
        cmd_legacy.extras = {"classification": "legacy_duplicate"}
        assert is_command_hidden_from_help(cmd_legacy) is True

        cmd_deprecated = MagicMock()
        cmd_deprecated.extras = {"classification": "deprecated"}
        # Deprecated stays visible per contract.
        assert is_command_hidden_from_help(cmd_deprecated) is False

        cmd_primary = MagicMock()
        cmd_primary.extras = {"classification": "primary_entrypoint"}
        assert is_command_hidden_from_help(cmd_primary) is False

        cmd_no_extras = MagicMock()
        cmd_no_extras.extras = None  # unannotated → default primary
        assert is_command_hidden_from_help(cmd_no_extras) is False

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


# ---------------------------------------------------------------------------
# DT04 — deliberateness rules at build time (runtime half of the invariant)
# ---------------------------------------------------------------------------


class TestDeliberatenessFindings:
    """``findings.unclassified_entry_points`` reports surface/classification
    contradictions: Discord-hidden routes without a valid hidden-route
    classification, and alias piles without a declared disposition."""

    def test_hidden_without_declaration_is_unclassified_finding(self):
        cmd = _make_cmd("warn", cog_name="ModerationCog")
        cmd.hidden = True
        cmd.extras = None
        ledger = build_ledger(_make_bot(cmd))
        assert "hidden:warn" in ledger.findings.unclassified_entry_points
        assert ledger.entries[0].discord_hidden is True
        assert ledger.entries[0].classification_declared is False

    def test_hidden_with_hidden_route_classification_is_clean(self):
        for cls in sorted(HIDDEN_ROUTE_CLASSIFICATIONS):
            cmd = _make_cmd("warn", cog_name="ModerationCog")
            cmd.hidden = True
            cmd.extras = {"classification": cls}
            ledger = build_ledger(_make_bot(cmd))
            assert ledger.findings.unclassified_entry_points == (), cls
            assert ledger.entries[0].classification == cls
            assert ledger.entries[0].classification_declared is True

    def test_hidden_with_visible_only_classification_is_a_contradiction(self):
        """``primary_entrypoint`` / ``power_user_shortcut`` are by contract
        *visible* surface classifications — declaring one on a Discord-hidden
        command is the exact drift class FIND-B04 found, so it stays a
        finding even though it is an explicit declaration."""
        for cls in sorted(set(CLASSIFICATIONS) - HIDDEN_ROUTE_CLASSIFICATIONS):
            cmd = _make_cmd("warn", cog_name="ModerationCog")
            cmd.hidden = True
            cmd.extras = {"classification": cls}
            ledger = build_ledger(_make_bot(cmd))
            assert "hidden:warn" in ledger.findings.unclassified_entry_points, cls

    def test_mock_hidden_attribute_does_not_read_as_hidden(self):
        """``discord_hidden`` requires the literal ``True`` — an arbitrary
        truthy attribute (a test double, a future non-bool) must not flip
        a command hidden."""
        cmd = _make_cmd("daily", cog_name="EconomyCog")  # cmd.hidden = MagicMock
        ledger = build_ledger(_make_bot(cmd))
        assert ledger.entries[0].discord_hidden is False
        assert ledger.findings.unclassified_entry_points == ()

    def test_alias_pile_without_disposition_is_unclassified_finding(self):
        aliases = tuple(f"a{i}" for i in range(ALIAS_DELIBERATION_THRESHOLD))
        cmd = _make_cmd("leaderboard", cog_name="LeaderboardCog", aliases=aliases)
        cmd.extras = None
        ledger = build_ledger(_make_bot(cmd))
        assert "aliases:leaderboard" in ledger.findings.unclassified_entry_points
        assert ledger.entries[0].alias_classification is None

    def test_alias_pile_with_disposition_is_clean(self):
        aliases = tuple(f"a{i}" for i in range(ALIAS_DELIBERATION_THRESHOLD + 2))
        cmd = _make_cmd("leaderboard", cog_name="LeaderboardCog", aliases=aliases)
        cmd.extras = {"alias_classification": "legacy_duplicate"}
        ledger = build_ledger(_make_bot(cmd))
        assert ledger.findings.unclassified_entry_points == ()
        assert ledger.entries[0].alias_classification == "legacy_duplicate"
        # The command's own classification is untouched by the alias
        # disposition — `!leaderboard` itself stays primary.
        assert ledger.entries[0].classification == "primary_entrypoint"

    def test_below_threshold_aliases_need_no_disposition(self):
        aliases = tuple(
            f"a{i}" for i in range(ALIAS_DELIBERATION_THRESHOLD - 1)
        )
        cmd = _make_cmd("balance", cog_name="EconomyCog", aliases=aliases)
        cmd.extras = None
        ledger = build_ledger(_make_bot(cmd))
        assert ledger.findings.unclassified_entry_points == ()

    def test_invalid_alias_classification_is_not_a_declaration(self):
        aliases = tuple(f"a{i}" for i in range(ALIAS_DELIBERATION_THRESHOLD))
        cmd = _make_cmd("leaderboard", cog_name="LeaderboardCog", aliases=aliases)
        cmd.extras = {"alias_classification": "garbage"}
        ledger = build_ledger(_make_bot(cmd))
        assert ledger.entries[0].alias_classification is None
        assert "aliases:leaderboard" in ledger.findings.unclassified_entry_points

    def test_slash_entries_carry_declared_flag_and_never_hidden(self):
        cmd = _make_slash_cmd("setup-hub", cog_name="DiagnosticCog")
        cmd.extras = {"classification": "legacy_duplicate"}
        bot = _make_bot_with_tree(slash_cmds=(cmd,))
        ledger = build_ledger(bot)
        slash = ledger.slash_entries[0]
        assert slash.classification == "legacy_duplicate"
        assert slash.classification_declared is True
        assert slash.discord_hidden is False
        assert slash.alias_classification is None

    def test_findings_are_sorted_and_prefixed(self):
        hidden_cmd = _make_cmd("zzz", cog_name="EconomyCog")
        hidden_cmd.hidden = True
        hidden_cmd.extras = None
        pile_cmd = _make_cmd(
            "aaa",
            cog_name="EconomyCog",
            aliases=tuple(f"a{i}" for i in range(ALIAS_DELIBERATION_THRESHOLD)),
        )
        pile_cmd.extras = None
        ledger = build_ledger(_make_bot(hidden_cmd, pile_cmd))
        assert ledger.findings.unclassified_entry_points == (
            "aliases:aaa",
            "hidden:zzz",
        )
        # The diagnostics provider surfaces the bucket count.
        snap = ledger_mod._snapshot()
        assert snap["findings"]["unclassified_entry_points"] == 2


# ---------------------------------------------------------------------------
# DT04 — surface-classification completeness invariant (static CI mirror)
# ---------------------------------------------------------------------------
#
# ``build_ledger`` reports contradictions on whatever bot is *running*;
# CI never boots the bot, so this section enforces the same rules over
# the cog sources by AST.  The population is generated from the
# decorator declarations themselves — never from a prose inventory —
# so adding a command automatically enrolls it.
#
# Rules (mirrors of the runtime rules in ``_compute_findings``):
#   V — every ``extras`` classification literal is canonical (a typo
#       silently falls back to the default at runtime; CI fails loud).
#   H — every ``hidden=True`` route declares WHY it is hidden with a
#       classification from HIDDEN_ROUTE_CLASSIFICATIONS.
#   A — every alias pile (>= ALIAS_DELIBERATION_THRESHOLD) declares an
#       ``alias_classification`` disposition.
#   S — the top-level slash surface (``@app_commands.command`` +
#       ``app_commands.Group`` namespaces) matches the reviewed pin
#       below, so a new slash route is a deliberate decision.
#
# Escape hatch: a route that must deviate goes in the explicit
# exception sets below ("<file>:<command>"), with a reviewed reason —
# never by weakening a rule.
#
# Convention enforced by construction: declare ``extras`` as an inline
# dict literal on the decorator.  An extras value built dynamically is
# invisible to this mirror and reads as "no declaration".

_DISBOT_ROOT = Path(ledger_mod.__file__).resolve().parents[2]

# Explicit, reviewed exceptions to rules H and A.  Keys are
# "<file basename>:<command name>".  Empty by design — prefer a real
# classification; an entry here must say why one cannot exist.
HIDDEN_ROUTE_EXCEPTIONS: frozenset[str] = frozenset()
ALIAS_PILE_EXCEPTIONS: frozenset[str] = frozenset()

# Rule S pin — every top-level slash namespace, mapped to its declared
# extras classification (None = deliberately ledger-default, i.e. a
# primary entrypoint).  Compared exactly in both directions: adding,
# removing, renaming, or reclassifying a top-level slash route updates
# this map in the same PR.
EXPECTED_SLASH_SURFACE: dict[str, str | None] = {
    # @app_commands.command
    "admin": None,
    "aimenu": None,
    "btd6menu": None,
    "bugreport": None,
    "community": None,
    "counters": None,
    "dispatch": None,
    "economy": None,
    "games": None,
    "help": None,
    "karma": None,
    "moderation": None,
    "myprofile": None,
    "platform": None,
    "pm": None,  # Project Moon (Limbus) browse panel — read-only knowledge surface
    "server-management": None,
    "settings": None,
    "setup": None,  # Essential Setup front door (plain-language spine; was /quicksetup)
    "setup-advanced": None,  # advanced section-list / draft wizard (was /setup)
    "setup-delegate": None,
    "setup-depth": None,
    "setup-describe": None,  # natural-language setup wedge
    "setup-hub": "legacy_duplicate",  # FIND-B07: explicit compat UI
    "setup-reset": None,
    "setup-skip": None,
    "setup-status": None,
    "setup-undelegate": None,
    "setup-unskip": None,
    "utility": None,
    "uxlab": None,
    # app_commands.Group namespaces (their subcommands ride the
    # group's surface decision; extend the pin per-subcommand only if
    # a group ever needs one classified individually)
    "ai": None,
    # BTD6 unified its five command groups into one `/btd6` (owner request,
    # 2026-06-24): the old btd6ref/btd6ops/btd6events/btd6strat slash groups
    # were removed; their actions are now nested subgroups under `/btd6`
    # (strat/ops/events) which ride this namespace's decision, and the old
    # prefix groups stay only as hidden `legacy_duplicate` aliases.
    "btd6": None,
}


@dataclass(frozen=True)
class _DeclaredRoute:
    """One command/group declaration as written in source."""

    file: str  # basename, e.g. "mining_cog.py"
    line: int
    name: str
    kind: str  # "prefix" | "slash" | "slash-group" | "slash-sub"
    hidden: bool
    alias_count: int
    # Raw literals as written (NOT validated/defaulted) — ``None``
    # means the key is absent or its value is not an inline string
    # literal, both of which count as "no declaration".
    classification: str | None
    alias_classification: str | None

    @property
    def key(self) -> str:
        return f"{self.file}:{self.name}"


def _const(node: object) -> object:
    return node.value if isinstance(node, ast.Constant) else None


def _extract_route(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
    dec: ast.Call,
    kind: str,
    file: str,
) -> _DeclaredRoute:
    name = node.name
    hidden = False
    alias_count = 0
    classification: str | None = None
    alias_classification: str | None = None
    for kw in dec.keywords:
        if kw.arg == "name" and isinstance(_const(kw.value), str):
            name = _const(kw.value)  # type: ignore[assignment]
        elif kw.arg == "hidden":
            hidden = _const(kw.value) is True
        elif kw.arg == "aliases" and isinstance(kw.value, (ast.List, ast.Tuple)):
            alias_count = len(kw.value.elts)
        elif kw.arg == "extras" and isinstance(kw.value, ast.Dict):
            for k, v in zip(kw.value.keys, kw.value.values):
                if _const(k) == "classification":
                    raw = _const(v)
                    classification = raw if isinstance(raw, str) else None
                elif _const(k) == "alias_classification":
                    raw = _const(v)
                    alias_classification = raw if isinstance(raw, str) else None
    return _DeclaredRoute(
        file=file,
        line=dec.lineno,
        name=name,
        kind=kind,
        hidden=hidden,
        alias_count=alias_count,
        classification=classification,
        alias_classification=alias_classification,
    )


def _enumerate_declared_routes() -> list[_DeclaredRoute]:
    """AST-walk every command-bearing source for command declarations.

    Scope: ``disbot/cogs/**/*.py`` plus ``disbot/bot1.py`` (the one
    bot-level command, ``!force``).  Handles ``@commands.command`` /
    ``@commands.group``, prefix-group subcommands (``@<grp>.command``),
    top-level ``@app_commands.command``, ``app_commands.Group``
    assignments, and app-group subcommands (``@<app_grp>.command``).
    """
    sources = sorted((_DISBOT_ROOT / "cogs").rglob("*.py"))
    sources.append(_DISBOT_ROOT / "bot1.py")
    routes: list[_DeclaredRoute] = []
    for path in sources:
        tree = ast.parse(path.read_text())
        file = path.name

        # Pass 1 — app-command group assignments in this module
        # (``x = app_commands.Group(name=...)``): each is a top-level
        # slash namespace, and its variable name marks ``@x.command``
        # decorators as slash subcommands.
        app_group_vars: set[str] = set()
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)):
                continue
            f = node.value.func
            if not (
                isinstance(f, ast.Attribute)
                and f.attr == "Group"
                and isinstance(f.value, ast.Name)
                and f.value.id == "app_commands"
            ):
                continue
            group_name = None
            has_parent = False
            for kw in node.value.keywords:
                if kw.arg == "name" and isinstance(_const(kw.value), str):
                    group_name = _const(kw.value)
                elif kw.arg == "parent":
                    has_parent = True
            for target in node.targets:
                if isinstance(target, ast.Name):
                    app_group_vars.add(target.id)
            # A nested subgroup (``parent=…``, e.g. the unified ``/btd6 strat``)
            # rides its parent's top-level surface decision — its var still marks
            # ``@<var>.command`` as slash-sub, but it is NOT itself a top-level
            # slash namespace, so it does not enter the Rule-S pin.
            if group_name is not None and not has_parent:
                routes.append(
                    _DeclaredRoute(
                        file=file,
                        line=node.lineno,
                        name=group_name,  # type: ignore[arg-type]
                        kind="slash-group",
                        hidden=False,
                        alias_count=0,
                        classification=None,
                        alias_classification=None,
                    ),
                )

        # Pass 2 — decorated command callbacks.
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                f = dec.func
                if not (
                    isinstance(f, ast.Attribute) and f.attr in ("command", "group")
                ):
                    continue
                base = f.value.id if isinstance(f.value, ast.Name) else ""
                if base == "app_commands":
                    kind = "slash"
                elif base in app_group_vars:
                    kind = "slash-sub"
                else:
                    # ``commands`` itself, a prefix-group object
                    # (``platform_grp`` …), or the bot instance.
                    kind = "prefix"
                routes.append(_extract_route(node, dec, kind, file))
    return routes


class TestSurfaceClassificationCompleteness:
    @pytest.fixture(scope="class")
    def routes(self) -> list[_DeclaredRoute]:
        return _enumerate_declared_routes()

    def test_enumeration_sees_known_sentinels(self, routes):
        """Self-check: a broken walker must fail HERE, not silently pass
        the rules over an empty population.  Sentinels, not counts —
        counts rot, declarations don't."""
        by_key = {r.key: r for r in routes}
        chop = by_key["mining_cog.py:chop"]
        assert chop.hidden is True
        assert chop.classification == "panel_action"
        hub = by_key["setup_cog.py:setup-hub"]
        assert hub.kind == "slash"
        assert hub.classification == "legacy_duplicate"
        lb = by_key["leaderboard_cog.py:leaderboard"]
        assert lb.alias_count >= ALIAS_DELIBERATION_THRESHOLD
        assert lb.alias_classification == "legacy_duplicate"
        force = by_key["bot1.py:force"]
        assert force.kind == "prefix"
        # ai_cog declares BOTH a prefix group `!ai` and a slash group
        # `/ai` — disambiguate by kind (by_key keeps only one).
        assert any(
            r.key == "ai_cog.py:ai" and r.kind == "slash-group" for r in routes
        )
        # Generous sanity floor — NOT an inventory pin (the real
        # surface is ~3× this); guards against a walk that silently
        # enumerates one directory level.
        assert len(routes) > 100

    def test_every_extras_classification_literal_is_canonical(self, routes):
        """Rule V — at runtime an unknown literal silently falls back to
        the default; in CI it fails loud, so a typo cannot demote a
        deliberate declaration to an accidental default."""
        offenders = [
            f"{r.file}:{r.line} {r.name} classification={r.classification!r}"
            for r in routes
            if r.classification is not None and r.classification not in CLASSIFICATIONS
        ] + [
            f"{r.file}:{r.line} {r.name} "
            f"alias_classification={r.alias_classification!r}"
            for r in routes
            if r.alias_classification is not None
            and r.alias_classification not in CLASSIFICATIONS
        ]
        assert not offenders, (
            "Non-canonical classification literal(s) — fix the typo or add "
            f"the value to Classification first:\n  " + "\n  ".join(offenders)
        )

    def test_every_discord_hidden_route_declares_why(self, routes):
        """Rule H — FIND-A01/A05/B04: a ``hidden=True`` command without a
        deliberate hidden-route classification is unclassifiable drift."""
        offenders = [
            f"{r.file}:{r.line} {r.name} (classification={r.classification!r})"
            for r in routes
            if r.hidden
            and r.classification not in HIDDEN_ROUTE_CLASSIFICATIONS
            and r.key not in HIDDEN_ROUTE_EXCEPTIONS
        ]
        assert not offenders, (
            "Discord-hidden command(s) without a hidden-route classification."
            "\nDeclare WHY each is hidden, e.g. "
            'extras={"classification": "panel_action"} '
            f"(valid: {sorted(HIDDEN_ROUTE_CLASSIFICATIONS)}), or add a "
            "reviewed entry to HIDDEN_ROUTE_EXCEPTIONS:\n  "
            + "\n  ".join(offenders)
        )

    def test_every_alias_pile_declares_a_disposition(self, routes):
        """Rule A — FIND-A04/Q-A03: a command carrying
        ALIAS_DELIBERATION_THRESHOLD or more aliases is a compatibility
        surface and must say what its aliases are."""
        offenders = [
            f"{r.file}:{r.line} {r.name} ({r.alias_count} aliases)"
            for r in routes
            if r.alias_count >= ALIAS_DELIBERATION_THRESHOLD
            and r.alias_classification not in CLASSIFICATIONS
            and r.key not in ALIAS_PILE_EXCEPTIONS
        ]
        assert not offenders, (
            "Alias pile(s) without a declared disposition.\nDeclare e.g. "
            'extras={"alias_classification": "legacy_duplicate"} (compat '
            'routes) or "power_user_shortcut" (advertised fluency), or add '
            "a reviewed entry to ALIAS_PILE_EXCEPTIONS:\n  "
            + "\n  ".join(offenders)
        )

    def test_top_level_slash_surface_is_pinned(self, routes):
        """Rule S — FIND-B07: the top-level slash surface is small and
        every route on it is a deliberate decision.  Exact two-way
        comparison: a stale pin fails just like a missing one."""
        actual = {
            r.name: r.classification
            for r in routes
            if r.kind in ("slash", "slash-group")
        }
        assert actual == EXPECTED_SLASH_SURFACE, (
            "Top-level slash surface drifted from the pin.\n"
            f"Unexpected/changed: "
            f"{ {k: v for k, v in actual.items() if EXPECTED_SLASH_SURFACE.get(k, '∅') != v} }\n"
            f"Missing: {sorted(set(EXPECTED_SLASH_SURFACE) - set(actual))}\n"
            "Update EXPECTED_SLASH_SURFACE in the same PR that changes "
            "the slash surface."
        )

    def test_static_rules_match_runtime_constants(self):
        """The mirror cannot drift from the module: both rules read their
        thresholds/sets from command_surface_ledger itself."""
        assert ALIAS_DELIBERATION_THRESHOLD >= 2
        assert HIDDEN_ROUTE_CLASSIFICATIONS < set(CLASSIFICATIONS)
        # The two visible-surface classifications are exactly the ones a
        # hidden route may NOT declare.
        assert set(CLASSIFICATIONS) - HIDDEN_ROUTE_CLASSIFICATIONS == {
            "primary_entrypoint",
            "power_user_shortcut",
        }
