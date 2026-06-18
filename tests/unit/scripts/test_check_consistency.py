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
