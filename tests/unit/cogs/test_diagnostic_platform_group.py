"""The ``!platform`` group lives on the extracted ``PlatformCommandsMixin``.

``diagnostic_cog.py`` hit the 800-LOC cog ceiling, so the whole ``!platform``
runtime-introspection group was moved onto
:class:`cogs.diagnostic.platform_group.PlatformCommandsMixin`, which
``DiagnosticCog`` mixes in.  discord.py's ``CogMeta`` collects commands across
the cog's MRO, so the surface and its single-cog registration must be
unchanged.  These tests pin that the extraction stays faithful: the group still
registers under the one cog, every documented subcommand is present, and the
commands are defined on the mixin (not back inline on the cog), so the cog
cannot silently regrow past the ceiling.
"""

from __future__ import annotations


def _platform_group():
    """The ``platform`` group command as collected onto ``DiagnosticCog``."""
    from cogs.diagnostic_cog import DiagnosticCog

    groups = [c for c in DiagnosticCog.__cog_commands__ if c.name == "platform"]
    assert len(groups) == 1, "exactly one !platform group must register on the cog"
    return groups[0]


def test_platform_group_registers_on_the_cog_via_the_mixin():
    from cogs.diagnostic.platform_group import PlatformCommandsMixin
    from cogs.diagnostic_cog import DiagnosticCog

    # The mixin contributes the group across the MRO.
    assert issubclass(DiagnosticCog, PlatformCommandsMixin)
    grp = _platform_group()
    # ``invoke_without_command`` opens the interactive hub — unchanged behaviour.
    assert grp.invoke_without_command is True


def test_every_documented_platform_subcommand_is_present():
    grp = _platform_group()
    names = {sub.name for sub in grp.commands}
    # The full read-only !platform surface (R1 + the Phase S2.5 / Phase 1 / IL
    # additions) — a representative, load-bearing subset that the extraction
    # must preserve.  Drawn from the group docstring + the shipped subcommands.
    expected = {
        "status",
        "anchors",
        "identity",
        "runtime",
        "health",
        "startup",
        "findings",
        "finding",
        "lifecycle",
        "caches",
        "media",
        "economy",
        "locks",
        "tasks",
        "views",
        "slow",
        "sessions",
        "schemas",
        "settings-registry",
        "setting",
        "customization",
        "provisioning",
        "bindings",
        "resources",
        "flags",
        "flag",
        "migrations",
        "consistency",
        "backfill",
    }
    missing = expected - names
    assert not missing, f"!platform subcommands lost in the extraction: {sorted(missing)}"


def test_platform_commands_are_defined_on_the_mixin_not_the_cog():
    """The weight must stay on the helper module, off the cog file.

    If a future change re-inlines the group onto ``DiagnosticCog`` the LOC
    would creep back toward the ceiling; pin that the group's callback is
    owned by the mixin module.
    """
    grp = _platform_group()
    assert grp.callback.__module__ == "cogs.diagnostic.platform_group"
