"""Tests for ``scripts/scan_commands.py`` — the cog command-surface scanner.

Loaded via ``importlib`` (the repo convention for ``scripts/`` modules). Pure
stdlib, so it runs in CI with no extra dependencies.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "scan_commands.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("scan_commands_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SAMPLE_COG = '''
from discord import app_commands
from discord.ext import commands


class SampleCog(commands.Cog):
    @commands.command(name="ping", aliases=["p"])
    async def ping(self, ctx):
        """Ping the bot."""
        await ctx.send("pong")

    @app_commands.command(name="slashping")
    async def slashping(self, interaction):
        """Slash ping."""

    @commands.command(name="panelcmd", extras={"classification": "panel_action"})
    async def panelcmd(self, ctx):
        """Open via button."""

    @commands.command(name="opensview")
    async def opensview(self, ctx):
        view = SomeView()
        await ctx.send(view=view)

    @commands.group(name="grp")
    async def grp(self, ctx):
        """A group."""

    @grp.command(name="sub")
    async def grp_sub(self, ctx):
        """A subcommand."""


class SampleMixin:
    """A command-bearing mixin — not a real Cog."""

    @commands.command(name="mixincmd")
    async def mixincmd(self, ctx):
        """A command defined on a mixin."""
'''

SAMPLE_BOT1 = '''
from discord.ext import commands


@bot.command(name="rootcmd")
async def rootcmd(ctx):
    """A top-level command defined outside any cog."""
'''


def _write_repo(tmp_path: Path) -> Path:
    cogs_dir = tmp_path / "disbot" / "cogs"
    cogs_dir.mkdir(parents=True)
    (cogs_dir / "sample_cog.py").write_text(SAMPLE_COG, encoding="utf-8")
    (tmp_path / "disbot" / "bot1.py").write_text(SAMPLE_BOT1, encoding="utf-8")
    return tmp_path


def test_scan_commands_types_aliases_and_buttons(mod, tmp_path):
    cogs = mod.scan_commands(_write_repo(tmp_path))
    by_cog = {c["cog"]: c for c in cogs}

    assert "SampleCog" in by_cog
    sample = by_cog["SampleCog"]
    assert sample["is_cog"] is True
    assert sample["subsystem"] == "sample"
    by_name = {c["name"]: c for c in sample["commands"]}
    assert by_name["ping"]["type"] == "prefix"
    assert by_name["ping"]["aliases"] == ["p"]
    assert by_name["ping"]["button_backed"] is False
    assert by_name["slashping"]["type"] == "slash"
    assert by_name["panelcmd"]["classification"] == "panel_action"
    assert by_name["panelcmd"]["button_backed"] is True
    assert by_name["opensview"]["button_backed"] is True
    assert by_name["sub"]["parent"] == "grp"


def test_cog_to_subsystem_is_acronym_aware(mod):
    f = mod._cog_to_subsystem
    # Plain CamelCase splits on word boundaries.
    assert f("EconomyCog") == "economy"
    assert f("CommunitySpotlightCog") == "community_spotlight"
    assert f("RockPaperScissorsCog") == "rock_paper_scissors"
    # Acronym (+digit) runs stay whole -> they match the registry's keys.
    assert f("AICog") == "ai"
    assert f("BTD6Cog") == "btd6"
    assert f("XPCog") == "xp"


def test_mixin_is_not_a_cog_but_keeps_its_commands(mod, tmp_path):
    by_cog = {c["cog"]: c for c in mod.scan_commands(_write_repo(tmp_path))}
    assert "SampleMixin" in by_cog
    assert by_cog["SampleMixin"]["is_cog"] is False
    # the command is still counted — it is real (inherited by a cog)
    assert "mixincmd" in {c["name"] for c in by_cog["SampleMixin"]["commands"]}


def test_module_level_command_from_bot1(mod, tmp_path):
    cogs = mod.scan_commands(_write_repo(tmp_path))
    module = next((c for c in cogs if c["cog"] == "(bot1.py)"), None)
    assert module is not None
    assert module["is_cog"] is False
    cmd = module["commands"][0]
    assert cmd["name"] == "rootcmd"
    assert cmd["type"] == "prefix"
    assert cmd["parent"] is None


def test_scan_commands_real_repo(mod):
    cogs = mod.scan_commands()
    assert len(cogs) >= 20
    assert "EconomyCog" in {c["cog"] for c in cogs}
    total = sum(len(c["commands"]) for c in cogs)
    assert total >= 100
    for cog in cogs:
        for cmd in cog["commands"]:
            assert cmd["type"] in {"prefix", "slash", "both"}
            assert isinstance(cmd["button_backed"], bool)


def test_summarise_breakdown_adds_up(mod):
    summary = mod.summarise(mod.scan_commands())
    assert summary["cogs"] >= 20  # real cogs only (is_cog)
    assert summary["cogs"] <= summary["command_classes"]
    assert summary["commands"] >= 100
    # the breakdown must partition the total exactly
    assert (
        summary["top_level_prefix"] + summary["subcommands"] + summary["slash"]
        == summary["commands"]
    )
    assert set(summary["by_type"]) <= {"prefix", "slash", "both"}
