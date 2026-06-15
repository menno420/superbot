"""PR-06c / HLP-2: the command display filter follows classification policy.

The cog's classification metadata flows from
``@commands.command(extras={"classification": "..."})`` through
``services.help_projection.command_display_state`` → the canonical
``core.runtime.command_surface_ledger.is_command_hidden_from_help`` →
every command-rendering help surface (``_get_visible_commands`` for the
command-list embed **and** the typed single-command route — one filter
since the Batch 6 projection seam).

Policy (single source of truth in
``command_surface_ledger._HELP_HIDDEN_CLASSIFICATIONS``):

* ``hidden`` / ``legacy_duplicate`` — filtered from help.
* ``deprecated`` — **kept** in help (rendered with a deprecation
  warning per the Classification contract).
* Everything else (primary_entrypoint, power_user_shortcut,
  panel_action, internal_admin, unannotated default) — kept.

The tests here pin both that the help surfaces defer to the canonical
helper (no second hidden-set declaration outside the ledger) and that
the unknown / unclassified fallback keeps the command visible.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cogs.help_cog import _get_visible_commands
from services.help_projection import HelpEntryState, command_display_state


def _make_cmd(
    name: str,
    *,
    hidden: bool = False,
    enabled: bool = True,
    extras: dict | None = None,
) -> MagicMock:
    cmd = MagicMock()
    cmd.name = name
    cmd.hidden = hidden
    cmd.enabled = enabled
    cmd.extras = extras if extras is not None else {}
    return cmd


def _make_cog(*cmds: MagicMock) -> MagicMock:
    cog = MagicMock()
    cog.get_commands = MagicMock(return_value=list(cmds))
    return cog


def _classification_hides(cmd) -> bool:
    """``True`` when the display decision is the classification hide."""
    decision = command_display_state(cmd)
    return (
        decision.state is HelpEntryState.DISPLAY_HIDDEN
        and decision.reason_code == "classification_hidden"
    )


class TestClassificationHidden:
    def test_default_extras_visible(self):
        cmd = _make_cmd("daily")
        assert _classification_hides(cmd) is False

    @pytest.mark.parametrize("cls", ["hidden", "legacy_duplicate"])
    def test_hidden_classifications_filtered(self, cls: str):
        cmd = _make_cmd("anything", extras={"classification": cls})
        assert _classification_hides(cmd) is True

    def test_deprecated_stays_visible(self):
        """The classification contract says deprecated commands are
        "surfaced with a deprecation warning" — they must NOT be
        filtered from help.  Centralising this in
        ``_HELP_HIDDEN_CLASSIFICATIONS`` (in command_surface_ledger)
        means help and any future panel surface share the policy."""
        cmd = _make_cmd("old", extras={"classification": "deprecated"})
        assert _classification_hides(cmd) is False

    @pytest.mark.parametrize(
        "cls",
        [
            "primary_entrypoint",
            "power_user_shortcut",
            "panel_action",
            "internal_admin",
        ],
    )
    def test_visible_classifications_kept(self, cls: str):
        cmd = _make_cmd("anything", extras={"classification": cls})
        assert _classification_hides(cmd) is False

    def test_non_dict_extras_treated_as_visible(self):
        """Unknown/malformed extras fall through to the canonical
        helper's primary_entrypoint default."""
        cmd = _make_cmd("daily")
        cmd.extras = "not-a-dict"
        assert _classification_hides(cmd) is False

    def test_unknown_classification_treated_as_visible(self):
        """If a cog declares a value not in the Classification Literal,
        the canonical helper defaults to primary_entrypoint so the
        command stays visible — better than silently disappearing."""
        cmd = _make_cmd("anything", extras={"classification": "made_up"})
        assert _classification_hides(cmd) is False


class TestGetVisibleCommands:
    def test_excludes_hidden_and_legacy_duplicate(self):
        visible = _make_cmd("daily")
        hidden = _make_cmd("admin_only", extras={"classification": "hidden"})
        legacy = _make_cmd(
            "old_alias",
            extras={"classification": "legacy_duplicate"},
        )
        cog = _make_cog(visible, hidden, legacy)
        result = _get_visible_commands(cog)
        names = [c.name for c in result]
        assert "daily" in names
        assert "admin_only" not in names
        assert "old_alias" not in names

    def test_keeps_deprecated_in_listing(self):
        """Deprecated commands must remain in the cog's command list
        so the renderer can show the deprecation badge.  Hiding them
        would silently break the documented contract."""
        visible = _make_cmd("daily")
        deprecated = _make_cmd(
            "old", extras={"classification": "deprecated"},
        )
        cog = _make_cog(visible, deprecated)
        names = [c.name for c in _get_visible_commands(cog)]
        assert "daily" in names
        assert "old" in names

    def test_still_filters_cmd_hidden_attribute(self):
        """The legacy ``cmd.hidden`` flag still hides commands —
        classification policy is an *additional* filter, not a
        replacement for the discord.py flag."""
        a = _make_cmd("a", hidden=True)
        b = _make_cmd("b")
        cog = _make_cog(a, b)
        names = [c.name for c in _get_visible_commands(cog)]
        assert names == ["b"]

    def test_still_filters_cmd_enabled_false(self):
        a = _make_cmd("a", enabled=False)
        b = _make_cmd("b")
        cog = _make_cog(a, b)
        names = [c.name for c in _get_visible_commands(cog)]
        assert names == ["b"]


class TestHelpConsumesCanonicalPolicy:
    """Pin that neither help_cog nor the projection carries a parallel
    hidden-set declaration.  A second copy would let help and the ledger
    drift, which is the bug PR-06c review caught."""

    @pytest.mark.parametrize(
        "module_name",
        ["cogs.help_cog", "services.help_projection"],
    )
    def test_no_redeclared_hidden_classifications(self, module_name: str):
        """Source-level check: ``_HELP_HIDDEN_CLASSIFICATIONS`` must
        live only in ``core.runtime.command_surface_ledger`` so the
        policy is single-sourced."""
        import importlib
        import inspect

        module = importlib.import_module(module_name)
        src = inspect.getsource(module)
        assert "_HELP_HIDDEN_CLASSIFICATIONS" not in src, (
            f"{module_name} must consume the canonical policy from "
            "core.runtime.command_surface_ledger; do not redeclare the "
            "_HELP_HIDDEN_CLASSIFICATIONS frozenset locally."
        )

    def test_display_state_delegates_to_canonical_helper(self):
        """End-to-end: the projection's command decision delegates to
        ``is_command_hidden_from_help`` so policy changes in one place
        flow to every help surface automatically."""
        from unittest.mock import patch

        cmd = _make_cmd("x", extras={"classification": "hidden"})
        with patch(
            "core.runtime.command_surface_ledger.is_command_hidden_from_help",
        ) as mock_helper:
            mock_helper.return_value = True
            assert _classification_hides(cmd) is True
            mock_helper.assert_called_once_with(cmd)
