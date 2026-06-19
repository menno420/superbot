"""Tests for ``scripts/check_consistency.py`` — the UX-consistency linter.

Rule 1 (**edit-in-place**) flags a panel button/select callback that delivers its
result via a standalone ephemeral message and never edits the panel in place. The
synthetic-file tests monkeypatch ``DISBOT_ROOT`` to a ``tmp_path`` tree and drop
fake ``views/<name>.py`` files under it (the ``check_architecture`` test pattern).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_consistency.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("check_consistency_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(mod, tmp_path, monkeypatch, rel, src):
    monkeypatch.setattr(mod, "DISBOT_ROOT", tmp_path)
    f = tmp_path / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(src, encoding="utf-8")
    return f


# A panel callback whose ONLY action is a new ephemeral message (the bug).
_BAD = """\
import discord


class ScorePanel(discord.ui.View):
    @discord.ui.button(label="Roll")
    async def roll(self, interaction, button):
        await interaction.response.send_message("You rolled a 6!", ephemeral=True)
"""

# Same shape, but the callback edits the panel in place (correct).
_EDITS = """\
import discord


class ScorePanel(discord.ui.View):
    @discord.ui.button(label="Roll")
    async def roll(self, interaction, button):
        await interaction.response.edit_message(content="You rolled a 6!", view=self)
"""

# An early-return validation toast — the correct guard pattern, not the bug.
_GUARD = """\
import discord


class ScorePanel(discord.ui.View):
    @discord.ui.button(label="Roll")
    async def roll(self, interaction, button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Not your panel.", ephemeral=True)
            return
        await interaction.response.edit_message(content="rolled", view=self)
"""

# A non-ephemeral send (e.g. a public broadcast) — out of rule-1 scope.
_PUBLIC = """\
import discord


class ScorePanel(discord.ui.View):
    @discord.ui.button(label="Announce")
    async def announce(self, interaction, button):
        await interaction.followup.send("Winner announced!")
"""

# A plain method (not a ui callback) that sends ephemerally — out of scope.
_NON_CALLBACK = """\
import discord


class ScorePanel(discord.ui.View):
    async def helper(self, interaction):
        await interaction.response.send_message("x", ephemeral=True)
"""

# The codebase's house idiom: the callback re-renders the panel via a same-class
# `self._rerender()` helper (which does `self.message.edit(...)`), then confirms
# out-of-band. This edits in place — it must NOT be flagged.
_RERENDER_HELPER = """\
import discord


class ScorePanel(discord.ui.View):
    async def _rerender(self):
        if self.message:
            await self.message.edit(view=self)

    @discord.ui.button(label="Reset")
    async def reset(self, interaction, button):
        await self._rerender()
        await interaction.followup.send("done", ephemeral=True)
"""


def _findings(mod, tmp_path, monkeypatch, src, *, rel="views/score.py"):
    _write(mod, tmp_path, monkeypatch, rel, src)
    return mod.rule_edit_in_place([tmp_path / rel], {})


def test_flags_ephemeral_only_panel_callback(mod, tmp_path, monkeypatch):
    findings = _findings(mod, tmp_path, monkeypatch, _BAD)
    assert len(findings) == 1
    assert findings[0].rule == "edit_in_place"
    assert findings[0].qualname == "ScorePanel.roll"
    assert findings[0].severity == "warning"


def test_callback_that_edits_in_place_is_clean(mod, tmp_path, monkeypatch):
    assert _findings(mod, tmp_path, monkeypatch, _EDITS) == []


def test_callback_using_inplace_rerender_helper_is_clean(mod, tmp_path, monkeypatch):
    # A callback that re-renders via the house `self._rerender()` idiom edits in
    # place even though the `.edit` lives in the helper, not the callback body.
    assert _findings(mod, tmp_path, monkeypatch, _RERENDER_HELPER) == []


def test_early_return_validation_toast_is_clean(mod, tmp_path, monkeypatch):
    assert _findings(mod, tmp_path, monkeypatch, _GUARD) == []


def test_non_ephemeral_send_is_out_of_scope(mod, tmp_path, monkeypatch):
    assert _findings(mod, tmp_path, monkeypatch, _PUBLIC) == []


def test_non_callback_method_is_out_of_scope(mod, tmp_path, monkeypatch):
    assert _findings(mod, tmp_path, monkeypatch, _NON_CALLBACK) == []


def test_allowlist_suppresses_by_file_and_method(mod, tmp_path, monkeypatch):
    _write(mod, tmp_path, monkeypatch, "views/score.py", _BAD)
    cfg = {
        "edit_in_place": {
            "exceptions": [
                {"pattern": "views/score.py::ScorePanel.roll", "reason": "real toast"},
            ],
        },
    }
    assert mod.rule_edit_in_place([tmp_path / "views/score.py"], cfg) == []


def test_allowlist_suppresses_by_file_prefix(mod, tmp_path, monkeypatch):
    _write(mod, tmp_path, monkeypatch, "views/score.py", _BAD)
    cfg = {
        "edit_in_place": {
            "exceptions": [{"pattern": "views/score.py", "reason": "whole file ok"}],
        },
    }
    assert mod.rule_edit_in_place([tmp_path / "views/score.py"], cfg) == []


def test_only_scans_views(mod, tmp_path, monkeypatch):
    # A cog with the same shape is not in rule-1 scope (views/ only).
    findings = _findings(mod, tmp_path, monkeypatch, _BAD, rel="cogs/score_cog.py")
    assert findings == []


def test_real_tree_runs_clean_or_warns_only(mod):
    """The live tree must parse and produce only warnings (never errors)."""
    findings = mod.run_checks(mod._all_files(), mod._load_exceptions())
    assert all(f.severity == "warning" for f in findings)


# ---------------------------------------------------------------------------
# Rule 2 — back-button presence
# ---------------------------------------------------------------------------

# A HubView panel with its own child button but no back affordance (the bug).
_HUB_NO_BACK = """\
import discord


class SettingsHub(HubView):
    @discord.ui.button(label="Roles")
    async def roles(self, interaction, button):
        await interaction.response.edit_message(view=self)
"""

# Same panel, but the module attaches a back button via the shared helper.
_HUB_WITH_HELPER = """\
import discord

from views.navigation import attach_back_button


class SettingsHub(HubView):
    @discord.ui.button(label="Roles")
    async def roles(self, interaction, button):
        attach_back_button(self, parent_builder=None, custom_id="settings:back")
        await interaction.response.edit_message(view=self)
"""

# Same panel, but one of its own buttons is the back affordance.
_HUB_WITH_BACK_BUTTON = """\
import discord


class SettingsHub(HubView):
    @discord.ui.button(label="◀ Back", custom_id="settings:back")
    async def back(self, interaction, button):
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Roles")
    async def roles(self, interaction, button):
        await interaction.response.edit_message(view=self)
"""

# A HubView with no child controls — not a navigable panel, out of scope.
_HUB_NO_CONTROLS = """\
import discord


class SettingsHub(HubView):
    async def render(self):
        return None
"""


def _back_findings(mod, tmp_path, monkeypatch, src, *, rel="views/settings_hub.py"):
    _write(mod, tmp_path, monkeypatch, rel, src)
    return mod.rule_back_button([tmp_path / rel], {})


def test_back_flags_hub_panel_without_affordance(mod, tmp_path, monkeypatch):
    findings = _back_findings(mod, tmp_path, monkeypatch, _HUB_NO_BACK)
    assert len(findings) == 1
    assert findings[0].rule == "back_button"
    assert findings[0].qualname == "SettingsHub"
    assert findings[0].severity == "warning"


def test_back_helper_call_is_clean(mod, tmp_path, monkeypatch):
    assert _back_findings(mod, tmp_path, monkeypatch, _HUB_WITH_HELPER) == []


def test_back_labelled_button_is_clean(mod, tmp_path, monkeypatch):
    assert _back_findings(mod, tmp_path, monkeypatch, _HUB_WITH_BACK_BUTTON) == []


def test_hub_without_child_controls_is_out_of_scope(mod, tmp_path, monkeypatch):
    assert _back_findings(mod, tmp_path, monkeypatch, _HUB_NO_CONTROLS) == []


def test_back_allowlist_suppresses_by_class(mod, tmp_path, monkeypatch):
    _write(mod, tmp_path, monkeypatch, "views/settings_hub.py", _HUB_NO_BACK)
    cfg = {
        "back_button": {
            "exceptions": [
                {
                    "pattern": "views/settings_hub.py::SettingsHub",
                    "reason": "top of stack",
                },
            ],
        },
    }
    assert mod.rule_back_button([tmp_path / "views/settings_hub.py"], cfg) == []


# ---------------------------------------------------------------------------
# Rule 3 — panel base-class
# ---------------------------------------------------------------------------

# A view extending discord.ui.View directly outside the allowlist (the bug).
_DIRECT_VIEW = """\
import discord


class PickerView(discord.ui.View):
    @discord.ui.button(label="Pick")
    async def pick(self, interaction, button):
        await interaction.response.edit_message(view=self)
"""

# A view that correctly extends the framework base.
_BASE_VIEW = """\
class PickerView(BaseView):
    pass
"""


def _base_findings(mod, tmp_path, monkeypatch, src, *, rel="views/picker.py"):
    _write(mod, tmp_path, monkeypatch, rel, src)
    return mod.rule_panel_base_class([tmp_path / rel], {})


def test_base_flags_direct_view_subclass(mod, tmp_path, monkeypatch):
    findings = _base_findings(mod, tmp_path, monkeypatch, _DIRECT_VIEW)
    assert len(findings) == 1
    assert findings[0].rule == "panel_base_class"
    assert findings[0].qualname == "PickerView"
    assert findings[0].severity == "warning"


def test_base_view_subclass_is_clean(mod, tmp_path, monkeypatch):
    assert _base_findings(mod, tmp_path, monkeypatch, _BASE_VIEW) == []


def test_base_game_state_path_is_allowlisted(mod, tmp_path, monkeypatch):
    # views/rps and views/blackjack are the game-state lifecycle allowlist.
    assert (
        _base_findings(mod, tmp_path, monkeypatch, _DIRECT_VIEW, rel="views/rps/x.py")
        == []
    )
    assert (
        _base_findings(
            mod, tmp_path, monkeypatch, _DIRECT_VIEW, rel="views/blackjack/y.py"
        )
        == []
    )


def test_base_arch_exempted_paths_are_allowlisted(mod, tmp_path, monkeypatch):
    # views/ai and views/games mirror the arch checker's documented
    # specialized-lifecycle path exemptions (canonical_helpers.yaml §
    # base_view.exemptions) — the consistency rule must not re-flag them (Q-0120).
    for rel in ("views/ai/policy/chooser.py", "views/games/deathmatch_panel.py"):
        assert (
            _base_findings(mod, tmp_path, monkeypatch, _DIRECT_VIEW, rel=rel) == []
        )


def test_base_framework_home_is_allowlisted(mod, tmp_path, monkeypatch):
    # views/base.py defines BaseView/HubView, which extend discord.ui.View.
    assert (
        _base_findings(mod, tmp_path, monkeypatch, _DIRECT_VIEW, rel="views/base.py")
        == []
    )


def test_base_allowlist_suppresses_by_class(mod, tmp_path, monkeypatch):
    _write(mod, tmp_path, monkeypatch, "views/picker.py", _DIRECT_VIEW)
    cfg = {
        "panel_base_class": {
            "exceptions": [
                {
                    "pattern": "views/picker.py::PickerView",
                    "reason": "game-state lifecycle",
                },
            ],
        },
    }
    assert mod.rule_panel_base_class([tmp_path / "views/picker.py"], cfg) == []


# ---------------------------------------------------------------------------
# Rule 4 — select-option truncation
# ---------------------------------------------------------------------------

# A select-building view that front-truncates its option source (the #1040 bug).
_TRUNCATES = """\
import discord


class RolePicker(discord.ui.Select):
    def __init__(self, roles):
        options = [discord.SelectOption(label=r.name, value=str(r.id)) for r in roles]
        super().__init__(options=options[:25])
"""

# Same view, but it paginates with a windowed page (the correct fix) — clean.
_WINDOWED = """\
import discord


class RolePicker(discord.ui.Select):
    def __init__(self, roles, start):
        options = [discord.SelectOption(label=r.name, value=str(r.id)) for r in roles]
        super().__init__(options=options[start : start + 25])
"""

# A string-length slice (Discord's 100-char label limit), N > 25 — not a drop.
_STRING_LIMIT = """\
import discord


class RolePicker(discord.ui.Select):
    def __init__(self, role):
        super().__init__(
            options=[discord.SelectOption(label=role.name[:100], value="1")],
        )
"""

# A non-select view that slices a list for a top-N embed — out of scope (no
# SelectOption in the module).
_NON_SELECT = """\
import discord


def build_embed(rows):
    embed = discord.Embed(title="Top")
    for row in rows[:10]:
        embed.add_field(name=row.name, value=str(row.score))
    return embed
"""


def _trunc_findings(mod, tmp_path, monkeypatch, src, *, rel="views/role_picker.py"):
    _write(mod, tmp_path, monkeypatch, rel, src)
    return mod.rule_select_option_truncation([tmp_path / rel], {})


def test_trunc_flags_front_slice_in_select_view(mod, tmp_path, monkeypatch):
    findings = _trunc_findings(mod, tmp_path, monkeypatch, _TRUNCATES)
    assert len(findings) == 1
    assert findings[0].rule == "select_option_truncation"
    assert findings[0].severity == "warning"


def test_trunc_windowed_pagination_is_clean(mod, tmp_path, monkeypatch):
    assert _trunc_findings(mod, tmp_path, monkeypatch, _WINDOWED) == []


def test_trunc_string_length_slice_is_clean(mod, tmp_path, monkeypatch):
    assert _trunc_findings(mod, tmp_path, monkeypatch, _STRING_LIMIT) == []


def test_trunc_non_select_view_is_out_of_scope(mod, tmp_path, monkeypatch):
    assert _trunc_findings(mod, tmp_path, monkeypatch, _NON_SELECT) == []


def test_trunc_only_scans_views(mod, tmp_path, monkeypatch):
    assert (
        _trunc_findings(mod, tmp_path, monkeypatch, _TRUNCATES, rel="cogs/x.py") == []
    )


def test_trunc_allowlist_suppresses_by_file_prefix(mod, tmp_path, monkeypatch):
    _write(mod, tmp_path, monkeypatch, "views/role_picker.py", _TRUNCATES)
    cfg = {
        "select_option_truncation": {
            "exceptions": [
                {
                    "pattern": "views/role_picker.py",
                    "reason": "intentional top-N display",
                },
            ],
        },
    }
    assert (
        mod.rule_select_option_truncation([tmp_path / "views/role_picker.py"], cfg)
        == []
    )


def test_trunc_finding_carries_enclosing_qualname(mod, tmp_path, monkeypatch):
    """The truncation finding names its enclosing class/method so an allowlist
    can scope an exception to one callback (the ``::Class.method`` suffix)."""
    findings = _trunc_findings(mod, tmp_path, monkeypatch, _TRUNCATES)
    assert findings[0].qualname == "RolePicker.__init__"


# Two slices in one file: a genuine select truncation (RolePicker.__init__) and
# a top-N embed display (build_embed) — the ::qualname allowlist must suppress
# only the display, leaving the real select flagged.
_MIXED = """\
import discord


class RolePicker(discord.ui.Select):
    def __init__(self, roles):
        options = [discord.SelectOption(label=r.name, value=str(r.id)) for r in roles]
        super().__init__(options=options[:25])


def build_embed(rows):
    embed = discord.Embed(title="Top")
    for row in rows[:10]:
        embed.add_field(name=row.name, value=str(row.score))
    return embed
"""


def test_trunc_qualname_allowlist_suppresses_only_scoped_callback(
    mod, tmp_path, monkeypatch
):
    _write(mod, tmp_path, monkeypatch, "views/role_picker.py", _MIXED)
    cfg = {
        "select_option_truncation": {
            "exceptions": [
                {
                    "pattern": "views/role_picker.py::build_embed",
                    "reason": "top-N embed display, not a select",
                },
            ],
        },
    }
    findings = mod.rule_select_option_truncation(
        [tmp_path / "views/role_picker.py"], cfg
    )
    # The display slice is suppressed; the genuine select truncation remains.
    quals = {f.qualname for f in findings}
    assert quals == {"RolePicker.__init__"}
