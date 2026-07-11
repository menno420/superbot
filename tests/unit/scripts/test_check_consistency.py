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


def test_real_tree_produces_no_graduated_rule_errors(mod):
    """The live tree must parse and surface zero error-severity findings.

    All four consistency rules are now GRADUATED — edit_in_place joined
    back_button / panel_base_class / select_option_truncation via the ultracode
    consolidation fleet (#1375), so every rule carries ``severity="error"`` and any
    live finding is an error that `--mode strict` (wired into CI) would fail on.
    This test mirrors that CI gate locally: it must stay clean, or a regression
    reintroduced an ephemeral-instead-of-in-place panel / front-truncated select /
    direct-`discord.ui.View` panel / back-affordance-less hub.
    """
    findings = mod.run_checks(mod._all_files(), mod._load_exceptions())
    errors = [f for f in findings if f.severity == "error"]
    assert (
        errors == []
    ), "graduated consistency rule(s) flagged the live tree: " + "; ".join(
        f.display(mod.REPO_ROOT) for f in errors
    )


def test_graduated_rules_carry_error_severity(mod):
    """All four consistency rules are now CI-enforced (severity='error') — the
    ultracode consolidation fleet (#1375) cleared the edit_in_place backlog and
    graduated the last warn-only rule."""
    by_name = {r.name: r for r in mod.RULES}
    for name in (
        "edit_in_place",
        "back_button",
        "panel_base_class",
        "select_option_truncation",
    ):
        assert by_name[name].severity == "error", f"{name} should be graduated"
        # A graduated rule carries no leftover blocker note.
        assert by_name[name].graduation_blocker == ""


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

# A registry-driven hub: controls added dynamically via add_item (no decorated
# @ui.button), no back affordance — the gap the Explore world hub exploited.
_HUB_ADDS_ITEMS_NO_BACK = """\
import discord


class WorldHub(HubView):
    def __init__(self, author):
        super().__init__(author)
        self.add_item(discord.ui.Button(label="Mine", custom_id="explore:open:mine"))
"""

# Same dynamic hub, but its module defines a custom back-button SUBCLASS wired
# through super().__init__ (the _BackToHubButton pattern) — not a Button(...)
# call, so the naive check misses it; the keyword-scan must catch it.
_HUB_CUSTOM_BACK_SUBCLASS = """\
import discord


class _BackToHubButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Back to Hub", custom_id="hub.back", emoji="↩")


class SettingsHub(HubView):
    def __init__(self, author):
        super().__init__(author)
        self.add_item(_BackToHubButton())
        self.add_item(discord.ui.Button(label="Roles"))
"""

# A dynamic hub whose Home button navigates via the shared transition_to helper.
_HUB_TRANSITION_TO = """\
import discord

from views.navigation import transition_to


class CompareView(HubView):
    def __init__(self, author, home_builder):
        super().__init__(author)
        self._home_builder = home_builder
        btn = discord.ui.Button(label="Home")

        async def _home(interaction):
            await transition_to(interaction, builder=self._home_builder)

        btn.callback = _home
        self.add_item(btn)
"""


# A dynamic hub that declares SUBSYSTEM — attach_standard_nav auto-attaches its
# 📚 Help / ↩ <hub> control in __init__, so it is NOT a back gap even though the
# module references no attach_back_button (the never-stranded mechanism).
_HUB_SUBSYSTEM_AUTO_NAV = """\
import discord


class FishingDone(HubView):
    SUBSYSTEM = "fishing"

    def __init__(self, author):
        super().__init__(author)
        self.add_item(discord.ui.Button(label="Cast again", custom_id="x:again"))
"""

# Same, but opts out of auto-nav (STANDARD_NAV = False) — it genuinely has no
# nav, so the rule must still flag it.
_HUB_SUBSYSTEM_NAV_OPT_OUT = """\
import discord


class DemoHub(HubView):
    SUBSYSTEM = "ux_lab"
    STANDARD_NAV = False

    def __init__(self, author):
        super().__init__(author)
        self.add_item(discord.ui.Button(label="Ping", custom_id="x:ping"))
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


def test_back_flags_dynamic_add_item_hub_without_affordance(mod, tmp_path, monkeypatch):
    """Registry-driven hubs build controls via add_item, not @ui.button — the
    rule must still flag one with no back (the Explore world-hub dead-end class).
    """
    findings = _back_findings(mod, tmp_path, monkeypatch, _HUB_ADDS_ITEMS_NO_BACK)
    assert len(findings) == 1
    assert findings[0].qualname == "WorldHub"


def test_back_custom_back_button_subclass_is_clean(mod, tmp_path, monkeypatch):
    """A custom back-button subclass (super().__init__(label='Back...', ...))
    added via add_item is a real back affordance and must not be flagged.
    """
    assert _back_findings(mod, tmp_path, monkeypatch, _HUB_CUSTOM_BACK_SUBCLASS) == []


def test_back_transition_to_helper_is_clean(mod, tmp_path, monkeypatch):
    """A Home/Back button navigating via the shared transition_to helper counts
    as a nav affordance (the UX-lab compare/probes/wing pattern).
    """
    assert _back_findings(mod, tmp_path, monkeypatch, _HUB_TRANSITION_TO) == []


def test_back_subsystem_panel_with_auto_nav_is_clean(mod, tmp_path, monkeypatch):
    """A SUBSYSTEM-declaring panel auto-attaches standard nav (📚 Help / ↩ hub)
    in its constructor — the affordance is present at runtime, so the static
    rule must not flag it even with no attach_back_button in the module.
    """
    assert _back_findings(mod, tmp_path, monkeypatch, _HUB_SUBSYSTEM_AUTO_NAV) == []


def test_back_flags_subsystem_panel_that_opts_out_of_auto_nav(
    mod, tmp_path, monkeypatch
):
    """STANDARD_NAV = False opts out of auto-nav, so such a panel genuinely has
    no back affordance and must still be flagged.
    """
    findings = _back_findings(mod, tmp_path, monkeypatch, _HUB_SUBSYSTEM_NAV_OPT_OUT)
    assert len(findings) == 1
    assert findings[0].qualname == "DemoHub"


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
        assert _base_findings(mod, tmp_path, monkeypatch, _DIRECT_VIEW, rel=rel) == []


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


# ---------------------------------------------------------------------------
# Graduation tracker (the #1060 session idea)
# ---------------------------------------------------------------------------


def _rule(mod, **kw):
    """A throwaway Rule whose check fn returns *n* synthetic findings."""
    n = kw.pop("count", 0)

    def fn(files, exceptions):
        return [
            mod.Finding(file=Path("x.py"), line=i + 1, rule=kw["name"], message="m")
            for i in range(n)
        ]

    return mod.Rule(fn=fn, **kw)


def test_graduation_eligible_when_zero_findings_and_no_blocker(mod):
    rule = _rule(mod, name="r", count=0)
    state, detail = mod.graduation_status(rule, 0)
    assert state == "ELIGIBLE"
    assert "error" in detail


def test_graduation_not_ready_with_open_findings(mod):
    rule = _rule(mod, name="r", count=3)
    state, detail = mod.graduation_status(rule, 3)
    assert state == "NOT READY"
    assert "3" in detail


def test_graduation_blocked_reports_the_specific_blocker(mod):
    rule = _rule(mod, name="r", graduation_blocker="needs the FOO redesign")
    # A hard blocker wins even at zero findings (the count alone is not enough).
    state, detail = mod.graduation_status(rule, 0)
    assert state == "BLOCKED"
    assert detail == "needs the FOO redesign"


def test_graduation_graduated_when_severity_is_error(mod):
    rule = _rule(mod, name="r", severity="error")
    state, _ = mod.graduation_status(rule, 0)
    assert state == "GRADUATED"


def test_run_checks_stamps_findings_with_rule_severity(mod, tmp_path, monkeypatch):
    """A rule flipped to ``error`` produces error-severity findings (graduation)."""
    _write(mod, tmp_path, monkeypatch, "views/score.py", _BAD)
    # Temporarily graduate edit_in_place to error and confirm the finding inherits it.
    target = next(r for r in mod.RULES if r.name == "edit_in_place")
    monkeypatch.setattr(target, "severity", "error")
    findings = mod.run_checks([tmp_path / "views/score.py"], {})
    edit_findings = [f for f in findings if f.rule == "edit_in_place"]
    assert edit_findings and all(f.severity == "error" for f in edit_findings)


def test_live_edit_in_place_rule_is_graduated(mod):
    """The real edit_in_place rule graduated to error (ultracode fleet #1375): the
    AI-nav redesign shipped (U1 #1376) and the remaining genuine cases are
    allowlisted, so it enforces a clean tree and carries no leftover blocker."""
    rule = next(r for r in mod.RULES if r.name == "edit_in_place")
    assert rule.severity == "error"
    assert rule.graduation_blocker == ""


def test_graduation_mode_ignores_file_filter(mod, monkeypatch, capsys):
    """--graduation always scans the full tree, never a filtered subset (Codex P2).

    Pointing ``--file`` at a single file must not change the graduation verdict —
    the decision is whole-tree. With every rule now graduated (#1375), the tracker
    reports them GRADUATED regardless of the filter; the report still renders the
    full rule set rather than a filtered subset.
    """
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_consistency.py", "--graduation", "--file", "disbot/views/base.py"],
    )
    rc = mod.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "graduation tracker" in out
    # The full rule set is reported (not filtered to base.py), all GRADUATED.
    assert "edit_in_place" in out and "GRADUATED" in out


# ---------------------------------------------------------------------------
# Per-rule scope — rules 3+4 also scan cogs/ (BUG-0017 was a cog-layer blind spot)
# ---------------------------------------------------------------------------


def test_panel_base_class_default_scope_skips_cogs(mod, tmp_path, monkeypatch):
    """With the default ``views/`` scope, a cog-layer direct-View is NOT flagged.

    This is exactly the BUG-0017 blind spot: before the scope widened, a
    ``discord.ui.View`` subclass in ``cogs/`` slipped past the rule entirely.
    """
    _write(mod, tmp_path, monkeypatch, "cogs/widget_cog.py", _DIRECT_VIEW)
    assert mod.rule_panel_base_class([tmp_path / "cogs/widget_cog.py"], {}) == []


def test_panel_base_class_cog_scope_flags_direct_view(mod, tmp_path, monkeypatch):
    """With ``cogs/`` in the rule's roots, a cog-layer direct-View IS flagged."""
    _write(mod, tmp_path, monkeypatch, "cogs/widget_cog.py", _DIRECT_VIEW)
    findings = mod.rule_panel_base_class(
        [tmp_path / "cogs/widget_cog.py"], {}, ("views/", "cogs/")
    )
    assert len(findings) == 1
    assert findings[0].rule == "panel_base_class"
    assert findings[0].qualname == "PickerView"


def test_select_option_truncation_cog_scope_flags_truncation(
    mod, tmp_path, monkeypatch
):
    """With ``cogs/`` in scope, a cog-layer ``[:25]`` select truncation IS flagged
    (the BUG-0017 / #1040 class living in the cog layer)."""
    _write(mod, tmp_path, monkeypatch, "cogs/widget_cog.py", _TRUNCATES)
    findings = mod.rule_select_option_truncation(
        [tmp_path / "cogs/widget_cog.py"], {}, ("views/", "cogs/")
    )
    assert len(findings) == 1
    assert findings[0].rule == "select_option_truncation"


def test_select_option_truncation_default_scope_skips_cogs(mod, tmp_path, monkeypatch):
    """The default ``views/`` scope leaves a cog-layer truncation unflagged."""
    _write(mod, tmp_path, monkeypatch, "cogs/widget_cog.py", _TRUNCATES)
    assert (
        mod.rule_select_option_truncation([tmp_path / "cogs/widget_cog.py"], {}) == []
    )


def test_registry_scopes_rules_3_and_4_to_cogs(mod):
    """The registry opts rules 3+4 into the cog layer and keeps rules 1+2 views-only.

    Rules 1 (edit_in_place) + 2 (back_button) target panel / HubView nav that lives
    in ``views/``; rules 3+4 are the patterns that also occur in the cog layer
    (BUG-0017).
    """
    by_name = {r.name: r for r in mod.RULES}
    assert by_name["edit_in_place"].roots == ("views/",)
    assert by_name["back_button"].roots == ("views/",)
    assert by_name["panel_base_class"].roots == ("views/", "cogs/")
    assert by_name["select_option_truncation"].roots == ("views/", "cogs/")


def test_all_files_includes_the_cog_layer(mod):
    """``_all_files`` collects the union of all rules' roots, so cog files are in
    the scan set (rules 3+4 re-filter to their own roots via ``_iter_parsed``)."""
    files = mod._all_files()
    rels = {str(f.relative_to(mod.DISBOT_ROOT)) for f in files}
    assert any(r.startswith("cogs/") for r in rels)
    assert any(r.startswith("views/") for r in rels)


# ---------------------------------------------------------------------------
# Rule 5 — card-engine helper duplication
# ---------------------------------------------------------------------------

# An image-render module (imports Pillow, lazy) that re-declares the engine's
# private `_fonts` helper — the pre-#1396 triplication class the rule guards.
_RENDER_DUP = """\
from __future__ import annotations


def _fonts(size_big, size_small):
    from PIL import ImageFont

    return ImageFont.load_default(), ImageFont.load_default()


def render_thing():
    return _fonts(40, 20)
"""

# Same renderer, migrated: imports the engine, no private helper (clean).
_RENDER_CLEAN = """\
from __future__ import annotations

from utils.card_render import get_theme, new_canvas


def render_thing():
    canvas = new_canvas(100, 50, get_theme("midnight"))
    return canvas.to_png() if canvas else None
"""

# A non-render utils module that happens to define `_fit` but imports neither
# Pillow nor the engine — out of scope (not the duplication class).
_NON_RENDER = """\
from __future__ import annotations


def _fit(model, data):
    return model
"""


def _card_findings(mod, tmp_path, monkeypatch, src, *, rel="utils/thing_render.py"):
    f = _write(mod, tmp_path, monkeypatch, rel, src)
    return mod.rule_card_engine_helper_duplication([f], {}, ("utils/",))


def test_flags_renderer_redeclaring_an_engine_helper(mod, tmp_path, monkeypatch):
    findings = _card_findings(mod, tmp_path, monkeypatch, _RENDER_DUP)
    assert len(findings) == 1
    assert findings[0].rule == "card_engine_helper_duplication"
    assert findings[0].qualname == "_fonts"
    assert findings[0].severity == "warning"


def test_migrated_renderer_using_the_engine_is_clean(mod, tmp_path, monkeypatch):
    assert _card_findings(mod, tmp_path, monkeypatch, _RENDER_CLEAN) == []


def test_non_render_utils_helper_is_out_of_scope(mod, tmp_path, monkeypatch):
    # `_fit` in a module importing neither Pillow nor the engine is not the
    # card-engine-duplication class — no false positive.
    assert _card_findings(mod, tmp_path, monkeypatch, _NON_RENDER) == []


def test_card_render_engine_itself_is_exempt(mod, tmp_path, monkeypatch):
    # The engine is the one legitimate home; a private helper there is never flagged.
    findings = _card_findings(
        mod, tmp_path, monkeypatch, _RENDER_DUP, rel="utils/card_render.py"
    )
    assert findings == []


def test_allowlist_suppresses_a_genuine_independent_helper(mod, tmp_path, monkeypatch):
    f = _write(mod, tmp_path, monkeypatch, "utils/thing_render.py", _RENDER_DUP)
    cfg = {
        "card_engine_helper_duplication": {
            "exceptions": [
                {"pattern": "utils/thing_render.py::_fonts", "reason": "bespoke"},
            ],
        },
    }
    assert mod.rule_card_engine_helper_duplication([f], cfg, ("utils/",)) == []


def test_rule_5_is_registered_and_scoped_to_utils(mod):
    by_name = {r.name: r for r in mod.RULES}
    assert "card_engine_helper_duplication" in by_name
    rule = by_name["card_engine_helper_duplication"]
    assert rule.roots == ("utils/",)
    assert rule.severity == "warning"  # warn-first (Q-0105)


# ---------------------------------------------------------------------------
# Rule 6 — settle-once adoption (money-safety)
# ---------------------------------------------------------------------------

# A wager-settling view with NO settle-once guard (the double-settlement bug):
# it pays out the escrow pot but takes no atomic claim, so a second trigger
# (a finishing button + on_timeout) double-settles.
_SETTLE_NO_GUARD = """\
import discord

from services import game_wager_workflow


class _PvpView(discord.ui.View):
    async def _resolve(self):
        await game_wager_workflow.settle_pvp(self.match_id, winner=self.winner)

    async def on_timeout(self):
        await self._resolve()
"""

# The RPS PvP shape: the view mixes in SettleOnceMixin and claims in a sibling
# method before settling — clean.
_SETTLE_CLASS_MIXIN = """\
import discord

from services import game_wager_workflow
from utils.terminal_guard import SettleOnceMixin


class _PvpView(SettleOnceMixin, discord.ui.View):
    async def _resolve(self):
        if not self.claim_settlement():
            return
        await game_wager_workflow.settle_pvp(self.match_id, winner=self.winner)

    async def on_timeout(self):
        await self._resolve()
"""

# A class that does not inherit the mixin but calls self.claim_settlement() in a
# sibling method — the guard is present in the class body, so it is clean.
_SETTLE_CLASS_CLAIM = """\
import discord

from services import game_wager_workflow


class _PvpView(discord.ui.View):
    def _guard(self):
        return self.claim_settlement()

    async def _resolve(self):
        if not self._guard():
            return
        await game_wager_workflow.refund_pvp(self.match_id)
"""

# The blackjack shape: a module-level settle function guarded by
# state.claim_settlement() before the settle call (no enclosing class) — clean.
_SETTLE_MODULE_FN = """\
from services import game_wager_workflow


async def _settle(state):
    if not state.claim_settlement():
        return
    await game_wager_workflow.settle_pvp(state.match_id, winner=state.winner)
"""

# The workflow module itself only DEFINES settle_pvp/refund_pvp; it never calls
# them, so the rule must not match a def (out of scope, not a double-settle site).
_SETTLE_DEFINITION_ONLY = """\
async def settle_pvp(match_id, winner):
    return None


async def refund_pvp(match_id):
    return None
"""


def _settle_findings(mod, tmp_path, monkeypatch, src, *, rel="views/pvp.py"):
    _write(mod, tmp_path, monkeypatch, rel, src)
    return mod.rule_settle_once_adoption([tmp_path / rel], {})


# The deathmatch human-duel shape the 2026-07-07 widening exists to catch: a
# cog-layer view whose W/L write (update_leaderboard) is reachable from a
# button resolve AND on_timeout with no claim — the Gate-V Arm-D live
# double-write (FINAL-REVIEW §6.3 #1).
_SETTLE_COG_DUEL_NO_GUARD = """\
import discord


class _DuelView(discord.ui.View):
    async def _resolve(self, interaction):
        await self.cog.update_leaderboard(winner_id=1, loser_id=2, guild_id=3)

    async def on_timeout(self):
        await self.cog.update_leaderboard(winner_id=2, loser_id=1, guild_id=3)
"""

# An unguarded tournament payout in a cog — the FREE-reward leg has no escrow
# rows to consume, so the caller-side claim is its only double-pay guard.
_SETTLE_COG_TOURNAMENT_NO_GUARD = """\
from services import game_wager_workflow


class _Tourn:
    async def check_progress(self, guild):
        await game_wager_workflow.payout_tournament(
            guild_id=guild.id, subsystem="x", winner_id=1, reason="win",
            free_reward=100, free_reason="free",
        )
"""


def test_settle_flags_unguarded_cog_duel_view(mod, tmp_path, monkeypatch):
    # cogs/ joined the scan roots in the 2026-07-07 widening.
    findings = _settle_findings(
        mod, tmp_path, monkeypatch, _SETTLE_COG_DUEL_NO_GUARD, rel="cogs/dm.py"
    )
    assert len(findings) == 2
    assert {f.qualname for f in findings} == {
        "_DuelView._resolve",
        "_DuelView.on_timeout",
    }


def test_settle_cog_duel_view_with_mixin_is_clean(mod, tmp_path, monkeypatch):
    src = _SETTLE_COG_DUEL_NO_GUARD.replace(
        "class _DuelView(discord.ui.View):",
        "class _DuelView(SettleOnceMixin, discord.ui.View):",
    )
    assert (
        _settle_findings(mod, tmp_path, monkeypatch, src, rel="cogs/dm.py") == []
    )


def test_settle_flags_unguarded_tournament_payout(mod, tmp_path, monkeypatch):
    findings = _settle_findings(
        mod,
        tmp_path,
        monkeypatch,
        _SETTLE_COG_TOURNAMENT_NO_GUARD,
        rel="cogs/tourn.py",
    )
    assert len(findings) == 1
    assert "payout_tournament" in findings[0].message


def test_settle_guarded_tournament_payout_is_clean(mod, tmp_path, monkeypatch):
    src = _SETTLE_COG_TOURNAMENT_NO_GUARD.replace(
        "        await game_wager_workflow.payout_tournament(",
        "        if not self.claim_settlement():\n"
        "            return\n"
        "        await game_wager_workflow.payout_tournament(",
    )
    assert (
        _settle_findings(mod, tmp_path, monkeypatch, src, rel="cogs/tourn.py")
        == []
    )


def test_settle_flags_unguarded_wager_settle(mod, tmp_path, monkeypatch):
    findings = _settle_findings(mod, tmp_path, monkeypatch, _SETTLE_NO_GUARD)
    assert len(findings) == 1
    assert findings[0].rule == "settle_once_adoption"
    assert findings[0].qualname == "_PvpView._resolve"
    assert findings[0].severity == "warning"


def test_settle_class_mixin_is_clean(mod, tmp_path, monkeypatch):
    assert _settle_findings(mod, tmp_path, monkeypatch, _SETTLE_CLASS_MIXIN) == []


def test_settle_class_claim_in_sibling_method_is_clean(mod, tmp_path, monkeypatch):
    # The claim lives in a sibling method, not the settling one — the rule checks
    # the whole enclosing class, so this is clean (the RPS resolve/settle split).
    assert _settle_findings(mod, tmp_path, monkeypatch, _SETTLE_CLASS_CLAIM) == []


def test_settle_module_level_function_with_claim_is_clean(mod, tmp_path, monkeypatch):
    # The blackjack shape: a free function guarded by state.claim_settlement().
    findings = _settle_findings(
        mod, tmp_path, monkeypatch, _SETTLE_MODULE_FN, rel="services/bj_settle.py"
    )
    assert findings == []


def test_settle_refund_pvp_is_also_a_settle_site(mod, tmp_path, monkeypatch):
    # refund_pvp moves the pot too — an unguarded refund is the same class.
    src = _SETTLE_NO_GUARD.replace("settle_pvp(self.match_id, winner=self.winner)",
                                   "refund_pvp(self.match_id)")
    findings = _settle_findings(mod, tmp_path, monkeypatch, src)
    assert len(findings) == 1
    assert "refund_pvp" in findings[0].message


def test_settle_definition_only_module_is_out_of_scope(mod, tmp_path, monkeypatch):
    # `def settle_pvp` is a definition, not a call — the workflow that owns the
    # helpers must never be flagged.
    findings = _settle_findings(
        mod, tmp_path, monkeypatch, _SETTLE_DEFINITION_ONLY,
        rel="services/game_wager_workflow.py",
    )
    assert findings == []


def test_settle_rule_scans_services_layer(mod, tmp_path, monkeypatch):
    # A state object in services/ that settles without a guard IS flagged (the
    # rule scopes views/ + services/, so a service-layer state object is covered).
    src = """\
from services import game_wager_workflow


class _PvPState:
    async def resolve(self):
        await game_wager_workflow.settle_pvp(self.match_id, winner=self.w)
"""
    findings = _settle_findings(
        mod, tmp_path, monkeypatch, src, rel="services/bj_state.py"
    )
    assert len(findings) == 1
    assert findings[0].qualname == "_PvPState.resolve"


def test_settle_rule_scans_cogs_layer(mod, tmp_path, monkeypatch):
    # The 2026-07-07 cogs/ widening (the live-confirmed deathmatch W/L write): an
    # unguarded settle site in the COG layer IS flagged. Regression pin for the
    # 2026-07-11 fix — the widening had been inert because the registry entry passed
    # only ("views/","services/"), so a new unguarded cog-layer settle would ship
    # unscanned even though the function default + docstring include cogs/.
    src = """\
from services import game_wager_workflow


class _DuelView:
    async def _resolve(self):
        await game_wager_workflow.payout_tournament(self.match_id)
"""
    findings = _settle_findings(
        mod, tmp_path, monkeypatch, src, rel="cogs/deathmatch_cog.py"
    )
    assert len(findings) == 1
    assert findings[0].qualname == "_DuelView._resolve"
    assert "payout_tournament" in findings[0].message


def test_settle_allowlist_suppresses_by_qualname(mod, tmp_path, monkeypatch):
    _write(mod, tmp_path, monkeypatch, "views/pvp.py", _SETTLE_NO_GUARD)
    cfg = {
        "settle_once_adoption": {
            "exceptions": [
                {
                    "pattern": "views/pvp.py::_PvpView._resolve",
                    "reason": "verified single-trigger settle",
                },
            ],
        },
    }
    assert mod.rule_settle_once_adoption([tmp_path / "views/pvp.py"], cfg) == []


def test_rule_6_is_registered_and_scoped(mod):
    by_name = {r.name: r for r in mod.RULES}
    assert "settle_once_adoption" in by_name
    rule = by_name["settle_once_adoption"]
    # cogs/ MUST be in the registry scope: the 2026-07-07 widening (the
    # live-confirmed deathmatch W/L write) was inert while this entry passed only
    # ("views/","services/"), so a new unguarded cog-layer settle would ship
    # unscanned. Fixed + graduated to error 2026-07-11 (clean across all 3 layers).
    assert rule.roots == ("views/", "services/", "cogs/")
    assert rule.severity == "error"


def test_settle_once_rule_runs_clean_on_the_live_tree(mod):
    """The live tree's wager-settle callers all adopt the guard across views/ +
    services/ + cogs/ — the 0-findings graduation prerequisite (now enforced)."""
    findings = mod.rule_settle_once_adoption(
        mod._all_files(), mod._load_exceptions(), ("views/", "services/", "cogs/")
    )
    assert findings == [], "settle_once_adoption flagged the live tree: " + "; ".join(
        f.display(mod.REPO_ROOT) for f in findings
    )
