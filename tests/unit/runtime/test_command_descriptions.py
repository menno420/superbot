"""Unit tests for core.runtime.command_descriptions.

The catalog enriches command_surface_ledger entries with description,
signature, and display_name. PR1 verifies:

* Per-command exception isolation (one broken command does not break
  the whole catalog).
* Hidden commands (per the ledger's classification policy) are
  excluded and counted.
* ``find()`` distinguishes prefix and slash forms that share a name.
* Deterministic ordering across builds.
* ``requires_perms`` is empty in PR1 (pinned for deferral).
* Diagnostics summary is compact (counts only — never the full list).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from core.runtime import command_descriptions, command_surface_ledger
from core.runtime.command_descriptions import (
    CommandDescription,
    CommandDescriptionCatalog,
    build_catalog,
    get_cached_catalog,
)


@pytest.fixture(autouse=True)
def _reset_caches():
    command_descriptions._reset_for_tests()
    command_surface_ledger._reset_for_tests()
    yield
    command_descriptions._reset_for_tests()
    command_surface_ledger._reset_for_tests()


# ---------------------------------------------------------------------------
# Helpers — minimal stand-ins for discord.py command objects.
# ---------------------------------------------------------------------------


def _make_prefix_cmd(
    name: str,
    *,
    help_text: str = "",
    signature: str = "",
    cog_name: str = "EconomyCog",
    extras: dict | None = None,
    aliases: tuple[str, ...] = (),
    raises_on_access: str | None = None,
) -> MagicMock:
    cmd = MagicMock(spec=[])
    cmd.name = name
    cmd.qualified_name = name
    cmd.help = help_text
    cmd.signature = signature
    cmd.aliases = list(aliases)
    cmd.parent = None
    cmd.extras = extras or {}
    if cog_name:
        cmd.cog = MagicMock()
        cmd.cog.__class__ = type(cog_name, (), {})
    else:
        cmd.cog = None
    if raises_on_access == "help":
        # Tripwire: accessing ``help`` raises.
        type(cmd).help = property(
            lambda _self: (_ for _ in ()).throw(RuntimeError("boom"))
        )
    return cmd


def _make_slash_param(name: str, *, required: bool = True) -> MagicMock:
    p = MagicMock(spec=[])
    p.name = name
    p.required = required
    return p


def _make_slash_cmd(
    name: str,
    *,
    description: str = "",
    parameters: tuple = (),
    cog_name: str = "EconomyCog",
    extras: dict | None = None,
) -> MagicMock:
    cmd = MagicMock(spec=[])
    cmd.name = name
    cmd.qualified_name = name
    cmd.description = description
    cmd.parameters = list(parameters)
    cmd.parent = None
    cmd.extras = extras or {}
    # Leaf marker — only commands with ``callback`` are described.
    cmd.callback = lambda *a, **kw: None
    binding = MagicMock()
    binding.__class__ = type(cog_name, (), {})
    cmd.binding = binding
    return cmd


def _make_bot(
    *,
    prefix_cmds: tuple = (),
    slash_cmds: tuple = (),
) -> MagicMock:
    bot = MagicMock(spec=[])
    bot.walk_commands = MagicMock(return_value=list(prefix_cmds))
    tree = MagicMock(spec=[])
    tree.walk_commands = MagicMock(return_value=list(slash_cmds))
    bot.tree = tree
    return bot


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_catalog_indexes_prefix_command_with_help() -> None:
    cmd = _make_prefix_cmd("daily", help_text="Claim your daily reward.\nMore info.")
    bot = _make_bot(prefix_cmds=(cmd,))

    catalog = build_catalog(bot)

    assert len(catalog.entries) == 1
    entry = catalog.entries[0]
    assert isinstance(entry, CommandDescription)
    assert entry.kind == "prefix"
    assert entry.qualified_name == "daily"
    assert entry.display_name == "!daily"
    # First non-empty line only.
    assert entry.description == "Claim your daily reward."


def test_catalog_indexes_slash_command_with_description() -> None:
    cmd = _make_slash_cmd(
        "lookup",
        description="Look up a thing.",
        parameters=(_make_slash_param("target"),),
        cog_name="EconomyCog",
    )
    bot = _make_bot(slash_cmds=(cmd,))

    catalog = build_catalog(bot)

    assert len(catalog.entries) == 1
    entry = catalog.entries[0]
    assert entry.kind == "slash"
    assert entry.display_name == "/lookup"
    assert entry.description == "Look up a thing."
    assert entry.signature == "<target>"


def test_slash_signature_marks_optional_params() -> None:
    cmd = _make_slash_cmd(
        "lookup",
        parameters=(
            _make_slash_param("name"),
            _make_slash_param("limit", required=False),
        ),
    )
    bot = _make_bot(slash_cmds=(cmd,))

    catalog = build_catalog(bot)

    assert catalog.entries[0].signature == "<name> <limit?>"


def test_catalog_skips_ledger_hidden_commands() -> None:
    """Commands classified as ``hidden`` via ``cmd.extras`` are dropped
    and counted in ``hidden_skipped`` (the ledger's policy applies
    via :func:`is_command_hidden_from_help`)."""
    visible = _make_prefix_cmd("public", help_text="visible cmd")
    hidden = _make_prefix_cmd(
        "secret",
        help_text="hidden cmd",
        extras={"classification": "hidden"},
    )
    bot = _make_bot(prefix_cmds=(visible, hidden))

    catalog = build_catalog(bot)

    names = [e.qualified_name for e in catalog.entries]
    assert "public" in names
    assert "secret" not in names
    assert catalog.hidden_skipped == 1
    assert catalog.error_skipped == 0


def test_catalog_keeps_building_on_per_command_error() -> None:
    """If introspection of one command raises, the catalog still
    builds with the surviving entries and counts the failure."""
    good = _make_prefix_cmd("good", help_text="OK")
    broken = _make_prefix_cmd("broken", raises_on_access="help")
    bot = _make_bot(prefix_cmds=(good, broken))

    catalog = build_catalog(bot)

    names = [e.qualified_name for e in catalog.entries]
    assert "good" in names
    assert "broken" not in names
    assert catalog.error_skipped == 1


def test_catalog_requires_perms_is_empty_in_pr1() -> None:
    """PR1 defers ``requires_perms`` extraction — every entry ships
    with the empty tuple."""
    cmd = _make_prefix_cmd("daily", help_text="hi")
    bot = _make_bot(prefix_cmds=(cmd,))

    catalog = build_catalog(bot)

    assert all(e.requires_perms == () for e in catalog.entries)


def test_find_returns_tuple_for_prefix_and_slash_with_same_name() -> None:
    """A bot that exposes both ``!foo`` and ``/foo`` must be findable
    in both forms; the prefix-only filter narrows to one."""
    prefix = _make_prefix_cmd("foo", help_text="prefix form")
    slash = _make_slash_cmd("foo", description="slash form")
    bot = _make_bot(prefix_cmds=(prefix,), slash_cmds=(slash,))

    catalog = build_catalog(bot)

    both = catalog.find("foo")
    assert len(both) == 2
    kinds = {e.kind for e in both}
    assert kinds == {"prefix", "slash"}

    slash_only = catalog.find("foo", kind="slash")
    assert len(slash_only) == 1
    assert slash_only[0].kind == "slash"

    assert catalog.find("nonexistent") == ()


def test_catalog_entries_sorted_deterministically() -> None:
    """Two builds against the same stub bot produce identical ordering."""
    cmds = (
        _make_prefix_cmd("zeta", cog_name="EconomyCog"),
        _make_prefix_cmd("alpha", cog_name="EconomyCog"),
        _make_prefix_cmd("beta", cog_name="ModerationCog"),
    )
    bot = _make_bot(prefix_cmds=cmds)

    catalog_a = build_catalog(bot)
    catalog_b = build_catalog(_make_bot(prefix_cmds=cmds))

    assert [e.qualified_name for e in catalog_a.entries] == [
        e.qualified_name for e in catalog_b.entries
    ]


def test_diagnostics_summary_is_compact() -> None:
    """The diagnostics provider must surface counts, not the full list."""
    cmd = _make_prefix_cmd("daily", help_text="hi")
    bot = _make_bot(prefix_cmds=(cmd,))

    catalog = build_catalog(bot)
    snap = catalog.diagnostics_summary()

    assert snap["status"] == "built"
    assert snap["command_count"] == 1
    assert "built_at" in snap
    assert "by_kind" in snap
    assert "entries" not in snap  # never include the full list


def test_get_cached_catalog_returns_last_build() -> None:
    assert get_cached_catalog() is None
    cmd = _make_prefix_cmd("daily", help_text="hi")
    bot = _make_bot(prefix_cmds=(cmd,))
    built = build_catalog(bot)
    assert get_cached_catalog() is built
    assert isinstance(get_cached_catalog(), CommandDescriptionCatalog)


def test_ledger_provides_subsystem_and_tier() -> None:
    """When the ledger has been built first, the catalog's entries
    inherit subsystem + visibility_tier from the matching entry."""
    cmd = _make_prefix_cmd("daily", help_text="hi", cog_name="EconomyCog")
    bot = _make_bot(prefix_cmds=(cmd,))

    command_surface_ledger.build_ledger(bot)
    catalog = build_catalog(bot)

    entry = catalog.entries[0]
    assert entry.subsystem == "economy"
    # economy subsystem is user-tier; see disbot/utils/subsystem_registry.py.
    assert entry.visibility_tier == "user"


def test_ledger_absent_yields_none_subsystem() -> None:
    """If the ledger has not been built, subsystem/tier default to None.

    The downstream service treats None-subsystem entries as hidden so
    the model never sees an unclassified command — matching PR1's
    decision to hide rather than expose unknown surface.
    """
    cmd = _make_prefix_cmd("daily", help_text="hi", cog_name="EconomyCog")
    bot = _make_bot(prefix_cmds=(cmd,))

    catalog = build_catalog(bot)

    entry = catalog.entries[0]
    assert entry.subsystem is None
    assert entry.visibility_tier is None
