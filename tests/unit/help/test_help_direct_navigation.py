"""Help-menu direct-navigation contract tests.

When the user picks a category in the help dropdown, HelpCategoryView._on_select
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

    Returns a mapping ``"<module>:<class>" -> info`` where ``info`` contains:
      * ``commands`` — set of command names (from ``name=`` kwarg or function name)
      * ``aliases`` — set of alias strings from ``aliases=[...]`` kwargs
      * ``methods`` — set of all method names on the class
      * ``async_methods`` — subset of ``methods`` that are ``async def``
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
            aliases_set: set[str] = set()
            entrypoint_set: set[str] = set()
            entrypoint_aliases: set[str] = set()
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
                    # Subsystem entry_points are always *top-level* command
                    # names, registered on ``commands`` / ``app_commands``.
                    # ``@<group>.command(...)`` registers a subcommand whose
                    # leaf name must NOT be matched against entry_points —
                    # otherwise ``!btd6strat mine`` would falsely resolve the
                    # ``mining`` subsystem to the BTD6 strategy cog.
                    registrar = (
                        func.value.id if isinstance(func.value, ast.Name) else None
                    )
                    is_top_level = registrar in ("commands", "app_commands")
                    cmd_name: str | None = None
                    dec_aliases: set[str] = set()
                    for kw in dec.keywords:
                        if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                            cmd_name = kw.value.value
                        elif kw.arg == "aliases" and isinstance(kw.value, ast.List):
                            for elt in kw.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(
                                    elt.value, str
                                ):
                                    dec_aliases.add(elt.value)
                    if cmd_name is None:
                        cmd_name = child.name
                    commands_set.add(cmd_name)
                    aliases_set.update(dec_aliases)
                    if is_top_level:
                        entrypoint_set.add(cmd_name)
                        entrypoint_aliases.update(dec_aliases)

            module_name = "cogs." + py.stem
            result[f"{module_name}:{node.name}"] = {
                "commands": commands_set,
                "aliases": aliases_set,
                "entry_point_commands": entrypoint_set,
                "entry_point_aliases": entrypoint_aliases,
                "methods": methods_set,
                "async_methods": async_methods,
            }
    return result


def test_every_visible_subsystem_cog_has_build_help_menu_view():
    """Every cog reachable from the help dropdown must expose ``build_help_menu_view``.

    Walks ``SUBSYSTEMS`` (skipping ``visibility_mode='internal'`` and the
    help cog itself), resolves each subsystem to its owning cog by
    intersecting the registered ``entry_points`` with the cog's command
    names **and aliases**, and asserts the cog declares an async
    ``build_help_menu_view`` method.

    Regression guard: closes the silent UX drift where a new subsystem
    ships without the direct-navigation hook and the help dropdown
    silently falls back to the inline command list. Catches the case
    even for game cogs that have no ``*menu`` command (blackjack, rps,
    deathmatch), which the previous ``*menu``-only heuristic missed.
    """
    from utils.subsystem_registry import SUBSYSTEMS

    classes = _scan_cog_classes()

    missing_hook: list[str] = []
    not_async: list[str] = []
    unresolved: list[str] = []

    for sub_name, meta in SUBSYSTEMS.items():
        if meta.get("visibility_mode") == "internal":
            continue
        if sub_name == "help":  # help can't direct-navigate to itself
            continue
        entry_points = set(meta.get("entry_points", ()))
        if not entry_points:
            continue

        # Find the cog whose *top-level* commands (or aliases) intersect
        # entry_points. Subcommand leaf names (e.g. ``!btd6strat mine``) are
        # excluded so they don't falsely resolve another subsystem.
        owning = [
            key
            for key, info in classes.items()
            if (info["entry_point_commands"] | info["entry_point_aliases"])
            & entry_points
        ]
        if not owning:
            unresolved.append(f"{sub_name} (entry_points={sorted(entry_points)})")
            continue

        for key in owning:
            info = classes[key]
            if "build_help_menu_view" not in info["methods"]:
                missing_hook.append(f"{sub_name} → {key}")
            elif "build_help_menu_view" not in info["async_methods"]:
                not_async.append(f"{sub_name} → {key}")

    assert not unresolved, (
        "Subsystems whose entry_points match no cog (likely registry "
        "drift — entry_points reference a command that doesn't exist):\n  "
        + "\n  ".join(unresolved)
    )
    assert not missing_hook, (
        "Cogs reachable from the help dropdown must define an async "
        "build_help_menu_view(self, interaction) so the dropdown navigates "
        "directly to the panel instead of falling back to the inline "
        "command list:\n  " + "\n  ".join(missing_hook)
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
async def test_blackjack_build_help_menu_view_returns_embed_and_view():
    """Game cogs return a stats_block overview + empty view (back-btn appended later)."""
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog(MagicMock())
    embed, view = await cog.build_help_menu_view(_stub_interaction())
    assert isinstance(embed, discord.Embed)
    assert isinstance(view, discord.ui.View)
    assert embed.title == "🃏 Blackjack"


@pytest.mark.asyncio
async def test_rps_build_help_menu_view_returns_embed_and_view():
    from cogs.rps_tournament_cog import RPSTournamentCog

    cog = RPSTournamentCog(MagicMock())
    embed, view = await cog.build_help_menu_view(_stub_interaction())
    assert isinstance(embed, discord.Embed)
    assert isinstance(view, discord.ui.View)
    assert embed.title == "✂️ Rock Paper Scissors"


@pytest.mark.asyncio
async def test_deathmatch_build_help_menu_view_returns_embed_and_view():
    from cogs.deathmatch_cog import Deathmatch

    cog = Deathmatch(MagicMock())
    embed, view = await cog.build_help_menu_view(_stub_interaction())
    assert isinstance(embed, discord.Embed)
    assert isinstance(view, discord.ui.View)
    assert embed.title == "⚔️ Deathmatch"


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
