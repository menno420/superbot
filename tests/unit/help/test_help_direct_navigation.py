"""Help-menu direct-navigation contract tests.

When the user picks a category in the help dropdown, HelpPanelView._on_select
calls ``cog.build_help_menu_view(interaction)`` and replaces the help embed
with the cog's hub panel directly — no inline command-list fallback, no
secondary click.

The discovery test below AST-scans every cog file: any cog declaring a
``*menu`` command is treated as panel-bearing and must expose an async
``build_help_menu_view``.  When a future cog with a panel lands, the test
fails automatically if the developer forgets the hook — closing the silent
fallback-to-inline regression.

Smoke tests then run the hook against a stubbed interaction for a handful of
representative cogs to assert the returned (embed, view) shape.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

_COGS_DIR = _DISBOT / "cogs"


def _scan_cog_classes() -> dict[str, dict]:
    """AST-scan ``disbot/cogs/*.py`` for ``commands.Cog`` subclasses.

    Returns a mapping ``"<module>:<class>" -> {commands, methods, async_methods}``
    so callers can ask: does this cog declare a command name ending in
    ``menu``, and if so does it also declare an async ``build_help_menu_view``?
    """
    result: dict[str, dict] = {}
    for py in _COGS_DIR.glob("*.py"):
        tree = ast.parse(py.read_text(), filename=str(py))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            is_cog = any(
                isinstance(b, ast.Attribute) and b.attr == "Cog" for b in node.bases
            )
            if not is_cog:
                continue

            commands_set: set[str] = set()
            methods_set: set[str] = set()
            async_methods: set[str] = set()
            for child in node.body:
                if not isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                methods_set.add(child.name)
                if isinstance(child, ast.AsyncFunctionDef):
                    async_methods.add(child.name)
                for dec in child.decorator_list:
                    if not isinstance(dec, ast.Call):
                        continue
                    func = dec.func
                    if not (
                        isinstance(func, ast.Attribute)
                        and func.attr in ("command", "group")
                    ):
                        continue
                    cmd_name: str | None = None
                    for kw in dec.keywords:
                        if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                            cmd_name = kw.value.value
                    if cmd_name is None:
                        cmd_name = child.name
                    commands_set.add(cmd_name)

            module_name = "cogs." + py.stem
            result[f"{module_name}:{node.name}"] = {
                "commands": commands_set,
                "methods": methods_set,
                "async_methods": async_methods,
            }
    return result


def test_every_panel_cog_has_build_help_menu_view():
    """Every cog with a ``*menu`` command must expose ``build_help_menu_view``.

    Regression guard for silent UX drift: if a new panel cog ships without
    the direct-navigation hook, the help dropdown silently falls back to
    the inline command list instead of opening the panel. Without this
    test that omission would only surface as a runtime UX inconsistency.

    Heuristic: any ``@commands.command(name='*menu')`` (or method named
    ``*menu`` with no explicit name) is a panel entry point. The owning
    cog class must define ``async def build_help_menu_view`` so the
    help-menu select can dispatch into the panel directly.
    """
    classes = _scan_cog_classes()

    missing_hook: list[str] = []
    not_async: list[str] = []
    for key, info in classes.items():
        menu_cmds = {c for c in info["commands"] if c.endswith("menu")}
        if not menu_cmds:
            continue
        if "build_help_menu_view" not in info["methods"]:
            missing_hook.append(f"{key} (declares: {sorted(menu_cmds)})")
            continue
        if "build_help_menu_view" not in info["async_methods"]:
            not_async.append(key)

    assert not missing_hook, (
        "These cogs declare a *menu command but do not define "
        "build_help_menu_view — the help dropdown will fall back to the "
        "inline command list instead of opening the panel directly. Add "
        "an async build_help_menu_view(self, interaction) method that "
        "returns (embed, view), mirroring the *menu command body:\n  "
        + "\n  ".join(missing_hook)
    )
    assert not not_async, (
        "build_help_menu_view must be an async method (help_cog awaits "
        "the result):\n  " + "\n  ".join(not_async)
    )


def _stub_interaction(user_id: int = 111, guild_id: int = 222) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = SimpleNamespace(
        id=user_id,
        display_name="tester",
        display_avatar=SimpleNamespace(url="http://x"),
        guild_permissions=SimpleNamespace(administrator=True),
        mention="<@111>",
    )
    interaction.guild = MagicMock()
    interaction.guild.id = guild_id
    interaction.guild_id = guild_id
    interaction.channel = MagicMock()
    interaction.channel.id = 333
    interaction.channel.mention = "#test"
    interaction.client = MagicMock()
    return interaction


@pytest.mark.asyncio
async def test_economy_build_help_menu_view_returns_embed_and_view():
    from unittest.mock import patch

    from cogs.economy_cog import EconomyCog

    cog = EconomyCog(MagicMock())
    interaction = _stub_interaction()

    fake_embed = discord.Embed(title="x")
    with patch(
        "cogs.economy_cog._build_economy_embed",
        new_callable=AsyncMock,
        return_value=fake_embed,
    ):
        embed, view = await cog.build_help_menu_view(interaction)

    assert isinstance(embed, discord.Embed)
    assert isinstance(view, discord.ui.View)


@pytest.mark.asyncio
async def test_mining_build_help_menu_view_returns_embed_and_view():
    from cogs.mining_cog import MiningCog

    cog = MiningCog(MagicMock())
    embed, view = await cog.build_help_menu_view(_stub_interaction())
    assert isinstance(embed, discord.Embed)
    assert isinstance(view, discord.ui.View)


@pytest.mark.asyncio
async def test_role_build_help_menu_view_returns_embed_and_view():
    from cogs.role_cog import RoleCog

    cog = RoleCog(MagicMock())
    embed, view = await cog.build_help_menu_view(_stub_interaction())
    assert isinstance(embed, discord.Embed)
    assert isinstance(view, discord.ui.View)


@pytest.mark.asyncio
async def test_moderation_build_help_menu_view_returns_embed_and_view():
    from cogs.moderation_cog import ModerationCog

    cog = ModerationCog(MagicMock())
    embed, view = await cog.build_help_menu_view(_stub_interaction())
    assert isinstance(embed, discord.Embed)
    assert isinstance(view, discord.ui.View)


@pytest.mark.asyncio
async def test_help_ctx_shim_exposes_required_attrs():
    """The shim must expose author/guild/channel/bot — nothing else needed."""
    from core.runtime.interaction_helpers import help_ctx_shim

    interaction = _stub_interaction()
    ctx = help_ctx_shim(interaction)
    assert ctx.author is interaction.user
    assert ctx.guild is interaction.guild
    assert ctx.channel is interaction.channel
    assert ctx.bot is interaction.client
