"""AI Cog smoke and INV-B alignment — Module 2 of the AI/BTD6 plan.

These tests pin:

* The cog is importable in CI (no API keys required).
* The cog declares the entry-point commands the SUBSYSTEMS registry
  promises (``ai`` group + ``aimenu``), and the registry has the
  matching ``ai`` row.
* Embed builders return :class:`discord.Embed` instances without
  invoking any provider (no env keys, no network).
* The persistent view registers under ``SUBSYSTEM = "ai"``.
* The help-surface-map invariants (pinned in
  ``tests/unit/docs/test_help_surface_map_doc.py``) continue to hold
  with the new ``ai`` row.
"""

from __future__ import annotations

import discord
import pytest

from cogs.ai_cog import (
    AICog,
    build_diagnostics_embed,
    build_providers_embed,
    build_routing_embed,
    build_status_embed,
)
from core.runtime.ai.contracts import AITask
from core.runtime.persistent_views import _REGISTRY as _PERSISTENT_VIEW_REGISTRY
from utils.subsystem_registry import SUBSYSTEMS
from views.ai.panel import AIPanelView, build_ai_panel_embed


def test_subsystem_registry_has_ai_entry():
    meta = SUBSYSTEMS["ai"]
    assert meta["visibility_tier"] == "administrator"
    assert set(meta["entry_points"]) == {"ai", "aimenu"}
    assert "ai.platform.view" in meta["capabilities"]


def test_ai_cog_declares_entry_point_commands():
    """``walk_commands`` over the cog must reveal `ai` and `aimenu`."""

    class _FakeBot:
        pass

    cog = AICog(_FakeBot())
    names = {cmd.name for cmd in cog.walk_commands()}
    # ``walk_commands`` yields the group, the subcommands, and the
    # top-level ``aimenu`` command. The entry-points the registry
    # promises are ``ai`` and ``aimenu``.
    assert "ai" in names
    assert "aimenu" in names


def test_status_embed_builder_returns_embed():
    embed = build_status_embed()
    assert isinstance(embed, discord.Embed)
    assert embed.title == "AI Gateway — Status"


def test_diagnostics_embed_builder_returns_embed():
    embed = build_diagnostics_embed()
    assert isinstance(embed, discord.Embed)
    assert embed.title == "AI Gateway — Diagnostics"


def test_providers_embed_builder_returns_embed():
    embed = build_providers_embed()
    assert isinstance(embed, discord.Embed)
    assert embed.title == "AI Gateway — Providers"


def test_routing_embed_lists_all_tasks_by_default():
    embed = build_routing_embed()
    assert isinstance(embed, discord.Embed)
    # One field per AITask, plus zero overflow when no filter given.
    field_names = {field.name for field in embed.fields}
    for task in AITask:
        assert task.value in field_names


def test_routing_embed_narrows_to_one_task():
    embed = build_routing_embed(AITask.SETUP_SUGGEST.value)
    assert isinstance(embed, discord.Embed)
    field_names = {field.name for field in embed.fields}
    assert field_names == {AITask.SETUP_SUGGEST.value}


def test_routing_embed_handles_unknown_task_gracefully():
    embed = build_routing_embed("does.not.exist")
    assert isinstance(embed, discord.Embed)
    assert any("No matching task" in (field.name or "") for field in embed.fields)


def test_ai_panel_embed_renders_without_provider_call():
    """Building the panel must not trigger a gateway request."""
    embed = build_ai_panel_embed()
    assert isinstance(embed, discord.Embed)
    assert "AI Platform" in (embed.title or "")


def test_persistent_view_registered_under_ai_subsystem():
    """The @register decorator side-effect must populate the view registry."""
    assert "ai" in _PERSISTENT_VIEW_REGISTRY
    assert _PERSISTENT_VIEW_REGISTRY["ai"] is AIPanelView


@pytest.mark.asyncio
async def test_setup_adds_cog_to_bot():
    """``cogs.ai_cog.setup`` must add the cog instance to the bot."""
    added: list = []

    class _FakeBot:
        async def add_cog(self, cog):
            added.append(cog)

    from cogs.ai_cog import setup

    await setup(_FakeBot())
    assert len(added) == 1
    assert isinstance(added[0], AICog)
