"""BTD6 Cog smoke + INV-B alignment — Module 4 of the AI/BTD6 plan.

Pins:

* SUBSYSTEMS["btd6"] is consistent with the cog's entry_points
  (``btd6`` and ``btd6menu``).
* The cog loads without API keys (deterministic-only).
* ``!btd6 ask`` returns a deterministic answer and does NOT call
  ``services.ai_gateway`` (Module 4 must not exercise the AI path
  — that belongs to Module 5).
* Embed builders are pure: no provider, no DB.
* The persistent view registers under ``SUBSYSTEM = "btd6"``.
* The BTD6 setup section appears in the registry.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

# Force the setup-sections package to import every section module so the
# REGISTRY contains the production set during the test run.
import views.setup.sections  # noqa: F401 — import side-effect
from cogs.btd6._embeds import (
    build_diagnostics_embed,
    build_modes_embed,
    build_status_embed,
    build_test_intent_embed,
    build_towers_embed,
)
from cogs.btd6_cog import BTD6Cog
from core.runtime.persistent_views import _REGISTRY as _PERSISTENT_VIEW_REGISTRY
from services.setup_sections import REGISTRY as SETUP_REGISTRY
from utils.subsystem_registry import SUBSYSTEMS
from views.btd6.panel import BTD6PanelView, build_btd6_panel_embed


def test_subsystem_registry_has_btd6_entry():
    """M1 of the BTD6-top-level + AI-central-policy initiative
    promoted BTD6 from a Games child to its own top-level hub.
    The registry entry must therefore NOT declare a parent_hub
    or hub_group. The matching HubEntry is pinned by
    ``tests/unit/utils/test_hub_registry.py::test_btd6_is_top_level_hub``.
    """
    meta = SUBSYSTEMS["btd6"]
    assert meta["visibility_tier"] == "user"
    assert meta.get("parent_hub") is None
    assert meta.get("hub_group") is None
    assert set(meta["entry_points"]) == {"btd6", "btd6menu"}
    assert "btd6.query.ask" in meta["capabilities"]


def test_btd6_cog_declares_entry_point_commands():
    class _FakeBot:
        pass

    cog = BTD6Cog(_FakeBot())
    names = {cmd.name for cmd in cog.walk_commands()}
    assert "btd6" in names
    assert "btd6menu" in names


@pytest.mark.asyncio
async def test_status_embed_builder_returns_embed(monkeypatch):
    from services import btd6_knowledge_service

    async def _empty_summary():
        return ()

    monkeypatch.setattr(
        btd6_knowledge_service,
        "fact_summary_by_kind",
        _empty_summary,
    )
    embed = await build_status_embed()
    assert isinstance(embed, discord.Embed)
    assert "Status" in (embed.title or "")


def test_diagnostics_embed_lists_entities():
    embed = build_diagnostics_embed()
    assert isinstance(embed, discord.Embed)
    names = {field.name for field in embed.fields}
    assert {"Towers", "Heroes", "Maps", "Modes", "Rounds tracked"} <= names


def test_towers_embed_has_entries():
    embed = build_towers_embed()
    assert isinstance(embed, discord.Embed)
    assert len(embed.fields) >= 4  # at least the fixture's 4 towers


def test_modes_embed_has_entries():
    embed = build_modes_embed()
    assert isinstance(embed, discord.Embed)
    assert len(embed.fields) >= 2


def test_test_intent_embed_renders_resolver_state():
    embed = build_test_intent_embed("Dart Monkey on round 63")
    assert isinstance(embed, discord.Embed)
    field_names = {field.name for field in embed.fields}
    assert "Towers" in field_names
    assert "Rounds" in field_names


@pytest.mark.asyncio
async def test_panel_embed_includes_reference_and_active_blocks(monkeypatch):
    """Panel embed: seed reference block + 'Currently active' block."""
    from unittest.mock import AsyncMock

    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(
        btd6_db, "latest_fact_per_entity_kind", AsyncMock(return_value={}),
    )
    # Hub VM now also calls get_active_events → search_facts.
    monkeypatch.setattr(btd6_db, "search_facts", AsyncMock(return_value=[]))
    embed = await build_btd6_panel_embed()
    assert isinstance(embed, discord.Embed)
    field_names = {field.name for field in embed.fields}
    assert any("Reference" in n for n in field_names)
    assert any("Currently active" in n for n in field_names)


def test_persistent_view_registered_under_btd6_subsystem():
    assert "btd6" in _PERSISTENT_VIEW_REGISTRY
    assert _PERSISTENT_VIEW_REGISTRY["btd6"] is BTD6PanelView


def test_btd6_setup_section_registered():
    assert "btd6" in SETUP_REGISTRY
    section = SETUP_REGISTRY.get("btd6")
    assert section is not None
    assert section.label == "BTD6 Assistant"
    # Module 4 declares no SetupOperation kinds — Module 6 fills these in.
    assert section.op_kinds == frozenset()


@pytest.mark.asyncio
async def test_btd6_ask_runs_deterministically_without_ai_gateway(monkeypatch):
    """`!btd6 ask` must not exercise services.ai_gateway in Module 4."""
    import services.ai_gateway as ai_gateway

    called = False

    async def _fail_if_called(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("Module 4 must not call the AI gateway")

    monkeypatch.setattr(ai_gateway, "execute", _fail_if_called)

    cog = BTD6Cog(MagicMock())
    fake_ctx = MagicMock()
    fake_ctx.send = AsyncMock()

    callback = cog.btd6_ask.callback
    await callback(cog, fake_ctx, question="Dart Monkey")

    assert called is False
    fake_ctx.send.assert_awaited_once()
    sent_embed = fake_ctx.send.await_args.kwargs.get("embed")
    assert sent_embed is not None
    assert "Dart Monkey" in (sent_embed.title or "")


@pytest.mark.asyncio
async def test_setup_adds_cog_to_bot():
    added: list = []

    class _FakeBot:
        async def add_cog(self, cog):
            added.append(cog)

    from cogs.btd6_cog import setup

    await setup(_FakeBot())
    assert len(added) == 1
    assert isinstance(added[0], BTD6Cog)


# ---------------------------------------------------------------------------
# Blocker PR-1: every BTD6 slash command that touches DB must defer
# BEFORE invoking the builder so the 3-second token window doesn't
# expire under load.
# ---------------------------------------------------------------------------


def _slash_interaction():
    """Interaction mock for slash commands. Guild present (for /mine
    and /pending), defer flips response.is_done so safe_followup
    routes through followup.send."""
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = 555
    interaction.user = MagicMock()
    interaction.user.id = 7777

    deferred = {"done": False}
    interaction.response.is_done = lambda: deferred["done"]

    async def _defer(**_kw):
        deferred["done"] = True

    interaction.response.defer = AsyncMock(side_effect=_defer)
    interaction.response.send_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.original_response = AsyncMock()
    return interaction


@pytest.mark.parametrize(
    ("command_attr", "builder_module", "builder_name", "kwargs", "return_kind"),
    [
        (
            "btd6_pending_slash",
            "cogs.btd6._builders",
            "build_pending_review_payload",
            {"limit": 5},
            "pending_list",
        ),
        (
            "btd6_source_health_slash",
            "cogs.btd6._builders",
            "build_source_health_embed",
            {"limit": 25},
            "embed",
        ),
        (
            "btd6_browse_slash",
            "views.btd6.strategy_browse",
            "build_browse_embed",
            {"limit": 10},
            "embed",
        ),
        (
            "btd6_mine_slash",
            "views.btd6.strategy_browse",
            "build_mine_embed",
            {"limit": 10},
            "embed",
        ),
        (
            "btd6_strategy_slash",
            "views.btd6.strategy_browse",
            "build_detail_embed",
            {"strategy_id": 1},
            "embed",
        ),
    ],
)
@pytest.mark.asyncio
async def test_slash_command_defers_before_db_work(
    monkeypatch,
    command_attr,
    builder_module,
    builder_name,
    kwargs,
    return_kind,
):
    """Every named BTD6 slash command must call ``safe_defer`` before
    invoking its builder so DB latency doesn't trip the interaction
    token. Patch targets are the source modules because the cog uses
    function-body lazy imports — ``from cogs.btd6._builders import
    build_…`` re-resolves at call time.
    """
    import importlib

    builder_mod = importlib.import_module(builder_module)

    call_order: list[str] = []

    async def _build_capture(*_a, **_kw):
        call_order.append("build")
        # Match the real return shape per builder so the cog's
        # downstream branching (e.g. ``isinstance(payload, str)``,
        # ``for embed, view in payload``) doesn't TypeError.
        if return_kind == "pending_list":
            return [(MagicMock(spec=discord.Embed), MagicMock())]
        return MagicMock(spec=discord.Embed)

    monkeypatch.setattr(builder_mod, builder_name, _build_capture)

    # Patch safe_defer / safe_followup at the cog's import site.
    from cogs import btd6_cog as cog_mod

    async def _defer_capture(interaction, **_kw):
        call_order.append("defer")
        # Mirror the real helper: flip is_done so any subsequent
        # safe_followup routes through followup.send.
        interaction.response.is_done = lambda: True
        return True

    async def _followup_capture(*_a, **_kw):
        return None

    monkeypatch.setattr(cog_mod, "safe_defer", _defer_capture)
    monkeypatch.setattr(cog_mod, "safe_followup", _followup_capture)

    cog = BTD6Cog(MagicMock())
    interaction = _slash_interaction()
    callback = getattr(cog, command_attr).callback
    await callback(cog, interaction, **kwargs)

    assert call_order[:2] == ["defer", "build"], call_order
