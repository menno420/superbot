"""PR-06c: ``_get_visible_commands`` filters by ``extras['classification']``.

The cog's classification metadata flows from
``@commands.command(extras={"classification": "..."})`` through
``cogs.help_cog._classification_hidden`` to the help renderer's
visible-commands list.  Commands tagged ``hidden`` / ``deprecated``
/ ``legacy_duplicate`` are filtered; defaults and other
classifications remain visible.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cogs.help_cog import _classification_hidden, _get_visible_commands


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


class TestClassificationHidden:
    def test_default_extras_visible(self):
        cmd = _make_cmd("daily")
        assert _classification_hidden(cmd) is False

    @pytest.mark.parametrize(
        "cls", ["hidden", "deprecated", "legacy_duplicate"]
    )
    def test_hidden_classifications_filtered(self, cls: str):
        cmd = _make_cmd("anything", extras={"classification": cls})
        assert _classification_hidden(cmd) is True

    @pytest.mark.parametrize(
        "cls", ["primary_entrypoint", "power_user_shortcut", "panel_action", "internal_admin"],
    )
    def test_visible_classifications_kept(self, cls: str):
        cmd = _make_cmd("anything", extras={"classification": cls})
        assert _classification_hidden(cmd) is False

    def test_non_dict_extras_treated_as_visible(self):
        cmd = _make_cmd("daily")
        cmd.extras = "not-a-dict"
        assert _classification_hidden(cmd) is False


class TestGetVisibleCommands:
    def test_excludes_classification_hidden(self):
        visible = _make_cmd("daily")
        hidden = _make_cmd("legacy", extras={"classification": "hidden"})
        deprecated = _make_cmd(
            "old", extras={"classification": "deprecated"},
        )
        cog = _make_cog(visible, hidden, deprecated)
        result = _get_visible_commands(cog)
        names = [c.name for c in result]
        assert "daily" in names
        assert "legacy" not in names
        assert "old" not in names

    def test_still_filters_cmd_hidden_attribute(self):
        """The legacy ``cmd.hidden`` flag still hides commands."""
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
