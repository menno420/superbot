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
from cogs.btd6_cog import (
    BTD6Cog,
    build_diagnostics_embed,
    build_modes_embed,
    build_status_embed,
    build_test_intent_embed,
    build_towers_embed,
)
from core.runtime.persistent_views import _REGISTRY as _PERSISTENT_VIEW_REGISTRY
from services.setup_sections import REGISTRY as SETUP_REGISTRY
from utils.subsystem_registry import SUBSYSTEMS
from views.btd6.panel import BTD6PanelView, build_btd6_panel_embed


def test_subsystem_registry_has_btd6_entry():
    meta = SUBSYSTEMS["btd6"]
    assert meta["visibility_tier"] == "user"
    assert meta["parent_hub"] == "games"
    assert set(meta["entry_points"]) == {"btd6", "btd6menu"}
    assert "btd6.query.ask" in meta["capabilities"]


def test_btd6_cog_declares_entry_point_commands():
    class _FakeBot:
        pass

    cog = BTD6Cog(_FakeBot())
    names = {cmd.name for cmd in cog.walk_commands()}
    assert "btd6" in names
    assert "btd6menu" in names


def test_status_embed_builder_returns_embed():
    embed = build_status_embed()
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


def test_panel_embed_uses_dataset_versions():
    embed = build_btd6_panel_embed()
    assert isinstance(embed, discord.Embed)
    field_names = {field.name for field in embed.fields}
    assert {"Data version", "Game version", "Entities"} <= field_names


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
