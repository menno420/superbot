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
'''


def _write_sample(tmp_path: Path) -> Path:
    cogs_dir = tmp_path / "disbot" / "cogs"
    cogs_dir.mkdir(parents=True)
    (cogs_dir / "sample_cog.py").write_text(SAMPLE_COG, encoding="utf-8")
    return tmp_path


def test_scan_commands_types_aliases_and_buttons(mod, tmp_path):
    cogs = mod.scan_commands(_write_sample(tmp_path))
    assert len(cogs) == 1
    cog = cogs[0]
    assert cog["cog"] == "SampleCog"
    assert cog["subsystem"] == "sample"
    by_name = {c["name"]: c for c in cog["commands"]}

    assert by_name["ping"]["type"] == "prefix"
    assert by_name["ping"]["aliases"] == ["p"]
    assert by_name["slashping"]["type"] == "slash"
    # panel_action classification -> button-backed
    assert by_name["panelcmd"]["classification"] == "panel_action"
    assert by_name["panelcmd"]["button_backed"] is True
    # opening a view is also button-backed (heuristic)
    assert by_name["opensview"]["button_backed"] is True
    # a plain prefix command is not button-backed
    assert by_name["ping"]["button_backed"] is False
    # group subcommand is attributed to its parent
    assert by_name["sub"]["parent"] == "grp"


def test_scan_commands_real_repo(mod):
    cogs = mod.scan_commands()
    assert len(cogs) >= 20
    names = {c["cog"] for c in cogs}
    assert "EconomyCog" in names
    total = sum(len(c["commands"]) for c in cogs)
    assert total >= 100
    for cog in cogs:
        for cmd in cog["commands"]:
            assert cmd["type"] in {"prefix", "slash", "both"}
            assert isinstance(cmd["button_backed"], bool)


def test_summarise_shape(mod):
    summary = mod.summarise(mod.scan_commands())
    assert summary["cogs"] >= 20
    assert summary["commands"] >= 100
    assert set(summary["by_type"]) <= {"prefix", "slash", "both"}
    assert summary["button_backed"] >= 0
