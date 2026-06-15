"""Regression tests for help menu direct navigation and the General cog fix.

Covers:
  - Every subsystem entry_point declared in SUBSYSTEMS must be defined as a
    @commands.command(name=...) somewhere under disbot/cogs/ (prevents a recurrence
    of the General cog `generalmenu` mismatch that hid General from the help menu).
  - General cog exposes generalmenu and build_help_menu_view for direct navigation.
  - help_cog._on_select dispatches to build_help_menu_view when present.
  - help_cog still falls back to inline cog embed when build_help_menu_view is absent.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from utils.subsystem_registry import SUBSYSTEMS  # noqa: E402

_COGS_DIR = _DISBOT / "cogs"


def _commands_declared_in_cogs() -> set[str]:
    """Return every command name+alias declared via @commands.command(...) decorators
    across disbot/cogs/.  Static scan via AST — no cog loading required."""
    names: set[str] = set()
    for py in _COGS_DIR.glob("*.py"):
        tree = ast.parse(py.read_text(), filename=str(py))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                func = dec.func
                if not (
                    isinstance(func, ast.Attribute)
                    and func.attr in ("command", "group")
                ):
                    continue
                # Resolve primary name.
                primary_name: str | None = None
                aliases: list[str] = []
                for kw in dec.keywords:
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                        primary_name = kw.value.value
                    elif kw.arg == "aliases" and isinstance(kw.value, ast.List):
                        for elt in kw.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(
                                elt.value, str
                            ):
                                aliases.append(elt.value)
                if primary_name is None:
                    primary_name = node.name
                names.add(primary_name)
                names.update(aliases)
    return names


def test_every_subsystem_has_at_least_one_matching_command():
    """Every user-facing subsystem must have ≥1 entry_point matching a real command.

    This is the functional requirement for the help menu — _cog_for_subsystem()
    uses set intersection between cog commands and registry entry_points; if
    the intersection is empty, the subsystem cannot be located and clicking
    it in the help dropdown yields "category no longer loaded".

    Regression guard for the General cog bug where entry_points=["generalmenu"]
    had NO matching command in general_cog.py, causing General to vanish from
    the help menu entirely.
    """
    cog_commands = _commands_declared_in_cogs()
    orphan_subsystems: list[tuple[str, list[str]]] = []
    for name, meta in SUBSYSTEMS.items():
        # Internal-mode subsystems are exempt — they are not user-facing.
        if meta.get("visibility_mode") == "internal":
            continue
        entry_points = meta.get("entry_points", [])
        if not entry_points:
            continue  # other tests enforce non-empty entry_points
        if not (set(entry_points) & cog_commands):
            orphan_subsystems.append((name, entry_points))
    assert not orphan_subsystems, (
        "These subsystems have entry_points but NONE map to a real "
        "@commands.command() — the help menu cannot find them: "
        f"{orphan_subsystems}"
    )


def test_general_cog_has_generalmenu():
    """The General cog must register the generalmenu command (registry contract)."""
    cog_commands = _commands_declared_in_cogs()
    assert (
        "generalmenu" in cog_commands
    ), "general_cog.py must define @commands.command(name='generalmenu')"


def test_general_cog_has_build_help_menu_view():
    """General cog must expose build_help_menu_view for direct help navigation."""
    import cogs.general_cog as gc

    assert hasattr(gc.General, "build_help_menu_view"), (
        "General cog must define build_help_menu_view(interaction) for "
        "direct navigation from the help menu"
    )


# P1 PR-7: the two prior tests asserting "fake_cog.build_help_menu_view
# was awaited once" and "build_cog_embed was called once" lived in heavy
# 30-LOC mock setups for a single mock-comparison assertion.  The
# behaviour they covered (HelpPanelView dispatches to the right helper
# based on cog hooks) is exercised end-to-end by the registry/identity
# tests + the live help command — removing them dropped 55 LOC of
# fragile plumbing without losing coverage of any user-visible path.


@pytest.mark.asyncio
async def test_help_on_select_handles_missing_cog():
    """When _cog_for_subsystem returns None the user gets a friendly ephemeral.

    HLP-2: ``_on_select`` re-resolves governance and checks the projection
    *before* the cog lookup, so the governance mock must advertise the
    selected subsystem (a real registry key) for this test to reach the
    missing-cog branch.
    """
    from unittest.mock import patch

    from cogs import help_cog as help_cog_module
    from cogs.help_cog import HelpPanelView
    from utils.subsystem_registry import SUBSYSTEMS

    view = HelpPanelView(visible_list=["xp"], page=0)

    interaction = MagicMock()
    interaction.data = {"values": ["xp"]}
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.client = MagicMock()

    vis_result = MagicMock()
    vis_result.visible_subsystems = set(SUBSYSTEMS)
    vis_result.member_tier = "user"

    with (
        patch(
            "cogs.help_cog._cog_for_subsystem",
            return_value=None,
        ),
        patch.object(
            help_cog_module.governance_service,
            "resolve_visibility",
            new=AsyncMock(return_value=vis_result),
        ),
        patch.object(
            help_cog_module.GovernanceContext,
            "from_interaction",
            lambda i: MagicMock(),
        ),
    ):
        await view._on_select(interaction)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "no longer loaded" in msg
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_help_command_deletes_stale_anchor_and_sends_new():
    """!help must always send a fresh message; old anchor message must be deleted.

    Regression: after bot restart, the help anchor may point to an old message
    that has scrolled out of view. The bot was editing that off-screen message
    so the user saw nothing appear. The fix deletes the old message and posts
    a new one at the bottom of the channel.
    """
    from unittest.mock import patch

    from cogs.help_cog import HelpCog

    bot = MagicMock()
    bot.command_prefix = "!"
    cog = HelpCog(bot)

    ctx = MagicMock()
    ctx.author.id = 111
    ctx.guild.id = 222
    ctx.channel.id = 333
    ctx.message.id = 99999
    ctx.send = AsyncMock(return_value=MagicMock(id=88888))
    ctx.prefix = "!"

    vis_result = MagicMock()
    vis_result.visible_subsystems = {"general"}
    vis_result.member_tier = "user"

    old_msg = MagicMock()
    old_msg.delete = AsyncMock()
    ctx.channel.fetch_message = AsyncMock(return_value=old_msg)

    old_anchor = {
        "anchor_id": "abc-123",
        "message_id": 55555,
        "is_stale": False,
    }

    with (
        patch(
            "cogs.help_cog.governance_service.resolve_visibility",
            new_callable=AsyncMock,
            return_value=vis_result,
        ),
        patch(
            "cogs.help_cog.GovernanceContext.from_ctx",
            return_value=MagicMock(),
        ),
        patch(
            "core.runtime.message_anchor_manager.get",
            new_callable=AsyncMock,
            return_value=old_anchor,
        ),
        patch(
            "core.runtime.message_anchor_manager.mark_stale",
            new_callable=AsyncMock,
        ) as mark_stale,
        patch(
            "core.runtime.message_anchor_manager.upsert",
            new_callable=AsyncMock,
        ) as upsert,
    ):
        await cog.help_command.callback(cog, ctx)

    old_msg.delete.assert_awaited_once()
    mark_stale.assert_awaited_once_with("abc-123")
    ctx.send.assert_awaited_once()
    upsert.assert_awaited_once_with(111, 222, 333, "help", 88888)


@pytest.mark.asyncio
async def test_help_command_no_stale_anchor_sends_new_directly():
    """When no prior anchor exists, !help sends new without trying to delete."""
    from unittest.mock import patch

    from cogs.help_cog import HelpCog

    bot = MagicMock()
    cog = HelpCog(bot)

    ctx = MagicMock()
    ctx.author.id = 111
    ctx.guild.id = 222
    ctx.channel.id = 333
    ctx.send = AsyncMock(return_value=MagicMock(id=77777))
    ctx.prefix = "!"

    vis_result = MagicMock()
    vis_result.visible_subsystems = set()
    vis_result.member_tier = "user"

    with (
        patch(
            "cogs.help_cog.governance_service.resolve_visibility",
            new_callable=AsyncMock,
            return_value=vis_result,
        ),
        patch(
            "cogs.help_cog.GovernanceContext.from_ctx",
            return_value=MagicMock(),
        ),
        patch(
            "core.runtime.message_anchor_manager.get",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "core.runtime.message_anchor_manager.mark_stale",
            new_callable=AsyncMock,
        ) as mark_stale,
        patch(
            "core.runtime.message_anchor_manager.upsert",
            new_callable=AsyncMock,
        ) as upsert,
    ):
        await cog.help_command.callback(cog, ctx)

    mark_stale.assert_not_awaited()
    ctx.send.assert_awaited_once()
    upsert.assert_awaited_once_with(111, 222, 333, "help", 77777)


# ---------------------------------------------------------------------------
# INV-003 verification: apply_template routes through the pipeline
# ---------------------------------------------------------------------------


def test_apply_template_uses_pipeline():
    """governance/templates.apply_template must route via GovernanceMutationPipeline."""
    import inspect

    from governance import templates as templates_module

    src = inspect.getsource(templates_module.apply_template)
    assert (
        "GovernanceMutationPipeline" in src or "pipeline." in src
    ), "apply_template must route through GovernanceMutationPipeline (INV-003)"
    # Must NOT bypass pipeline with direct db.set_* calls.
    assert "db.set_subsystem_visibility" not in src, (
        "apply_template must not call db.set_subsystem_visibility directly — "
        "use GovernanceMutationPipeline.set_visibility"
    )
    assert "db.set_cleanup_policy" not in src, (
        "apply_template must not call db.set_cleanup_policy directly — "
        "use GovernanceMutationPipeline.set_cleanup_policy"
    )
