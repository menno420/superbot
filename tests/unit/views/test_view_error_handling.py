"""Regression tests for Discord view interaction error handling.

Covers:
  - BaseView.on_error() logs full context and sends ephemeral when not responded
  - PersistentView.on_error() same contract
  - _SubsystemToggleView handles set_subsystem_visibility exceptions gracefully
  - _back_callback handles resolve_visibility exceptions gracefully
  - No exception silently swallowed when interaction already responded

datetime.utcnow() is enforced by ruff DTZ003 (pyproject.toml).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_interaction(*, responded: bool = False) -> MagicMock:
    """Build a minimal discord.Interaction mock."""
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 12345
    interaction.guild_id = 99999
    interaction.channel_id = 11111
    interaction.message = MagicMock()
    interaction.message.id = 22222
    interaction.response = MagicMock()
    interaction.response.is_done = MagicMock(return_value=responded)
    interaction.response.defer = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    interaction.original_response = AsyncMock(return_value=MagicMock())
    return interaction


def _make_item(*, custom_id: str = "test:btn", label: str = "Test") -> MagicMock:
    item = MagicMock()
    item.custom_id = custom_id
    item.label = label
    return item


# ---------------------------------------------------------------------------
# BaseView.on_error()
# ---------------------------------------------------------------------------


class TestBaseViewOnError:
    """BaseView.on_error must log context and send ephemeral if not responded."""

    @pytest.mark.asyncio
    async def test_logs_view_context(self, caplog):
        import logging

        import discord

        from views.base import BaseView

        author = MagicMock(spec=discord.Member)
        view = BaseView(author)
        interaction = _make_interaction()
        item = _make_item(custom_id="test:click", label="Click")
        error = ValueError("boom")

        with caplog.at_level(logging.ERROR, logger="bot.views"):
            await view.on_error(interaction, error, item)

        assert any(
            "BaseView" in r.message for r in caplog.records
        ), "on_error must log the view class name"
        assert any(
            "test:click" in r.message for r in caplog.records
        ), "on_error must log the custom_id"

    @pytest.mark.asyncio
    async def test_log_payload_includes_response_done(self, caplog):
        """Distinguishing "raised before defer" from "raised after defer"
        is important enough to keep in the structured log. Pin that the
        payload includes ``response_done`` for both paths.
        """
        import logging

        import discord

        from views.base import BaseView

        author = MagicMock(spec=discord.Member)
        view = BaseView(author)

        for responded in (False, True):
            caplog.clear()
            interaction = _make_interaction(responded=responded)
            with caplog.at_level(logging.ERROR, logger="bot.views"):
                await view.on_error(interaction, RuntimeError("x"), _make_item())
            assert any(
                f"response_done={responded}" in r.message for r in caplog.records
            ), f"response_done={responded} missing from log payload"

    @pytest.mark.asyncio
    async def test_sends_ephemeral_when_not_responded(self):
        import discord

        from views.base import BaseView

        author = MagicMock(spec=discord.Member)
        view = BaseView(author)
        interaction = _make_interaction(responded=False)

        await view.on_error(interaction, RuntimeError("x"), _make_item())

        interaction.response.send_message.assert_awaited_once()
        call_kwargs = interaction.response.send_message.call_args
        assert call_kwargs.kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_no_double_respond_when_already_responded(self):
        import discord

        from views.base import BaseView

        author = MagicMock(spec=discord.Member)
        view = BaseView(author)
        interaction = _make_interaction(responded=True)

        await view.on_error(interaction, RuntimeError("x"), _make_item())

        interaction.response.send_message.assert_not_awaited()


# ---------------------------------------------------------------------------
# PersistentView.on_error()
# ---------------------------------------------------------------------------


class TestPersistentViewOnError:
    """PersistentView.on_error must have the same contract as BaseView.on_error."""

    @pytest.mark.asyncio
    async def test_sends_ephemeral_when_not_responded(self):
        from core.runtime.persistent_views import PersistentView

        view = PersistentView()
        interaction = _make_interaction(responded=False)

        await view.on_error(interaction, RuntimeError("x"), _make_item())

        interaction.response.send_message.assert_awaited_once()
        assert (
            interaction.response.send_message.call_args.kwargs.get("ephemeral") is True
        )

    @pytest.mark.asyncio
    async def test_logs_view_class_and_item(self, caplog):
        import logging

        from core.runtime.persistent_views import PersistentView

        view = PersistentView()
        interaction = _make_interaction()
        item = _make_item(custom_id="help:select", label="Choose")

        with caplog.at_level(logging.ERROR, logger="bot.runtime.views"):
            await view.on_error(interaction, ValueError("fail"), item)

        assert any("PersistentView" in r.message for r in caplog.records)
        assert any("help:select" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_no_double_respond_when_already_responded(self):
        from core.runtime.persistent_views import PersistentView

        view = PersistentView()
        interaction = _make_interaction(responded=True)

        await view.on_error(interaction, RuntimeError("x"), _make_item())

        interaction.response.send_message.assert_not_awaited()


# ---------------------------------------------------------------------------
# _back_callback error handling (help_cog)
# ---------------------------------------------------------------------------


class TestBackCallbackErrorHandling:
    """_back_callback must send ephemeral on governance failure, never raise."""

    @pytest.mark.asyncio
    async def test_resolve_visibility_failure_sends_ephemeral(self):
        import cogs.help_cog as help_cog

        view = help_cog.HelpPanelView(visible_list=["general"], page=0)
        interaction = _make_interaction(responded=False)
        interaction.client = MagicMock()

        with patch(
            "cogs.help_cog.governance_service.resolve_visibility",
            side_effect=RuntimeError("governance down"),
        ):
            # Attach back button and capture its callback.
            sub_view = MagicMock()
            sub_view.children = []
            sub_view.add_item = MagicMock(side_effect=lambda btn: None)
            help_cog._attach_back_to_help_button(sub_view)

            # The back button was passed to add_item; retrieve it.
            assert sub_view.add_item.called
            back_btn = sub_view.add_item.call_args[0][0]
            await back_btn.callback(interaction)

        # After Phase 3.5 lifecycle hardening the Back callback defers
        # before invoking parent_builder, so a builder failure surfaces
        # via ``followup.send`` rather than ``response.send_message``.
        interaction.followup.send.assert_awaited_once()
        assert interaction.followup.send.call_args.kwargs.get("ephemeral") is True
        interaction.response.send_message.assert_not_awaited()
        interaction.response.edit_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_resolve_visibility_failure_no_raise_when_responded(self):
        import cogs.help_cog as help_cog

        interaction = _make_interaction(responded=True)
        interaction.client = MagicMock()

        with patch(
            "cogs.help_cog.governance_service.resolve_visibility",
            side_effect=RuntimeError("down"),
        ):
            sub_view = MagicMock()
            sub_view.children = []
            sub_view.add_item = MagicMock()
            help_cog._attach_back_to_help_button(sub_view)
            back_btn = sub_view.add_item.call_args[0][0]
            # Must not raise even if interaction is already done.
            await back_btn.callback(interaction)

        interaction.response.send_message.assert_not_awaited()


# ---------------------------------------------------------------------------
# _SubsystemToggleView callback error handling (channel_cog)
# ---------------------------------------------------------------------------


class TestSubsystemToggleViewErrorHandling:
    """Toggle callback must send ephemeral on governance failure."""

    @pytest.mark.asyncio
    async def test_set_visibility_failure_sends_ephemeral(self):
        import discord

        # The view moved from cogs.channel_cog to views.channels.visibility_panel
        # in D2; the cog re-exports it for backwards compatibility.
        from cogs.channel_cog import _SubsystemToggleView
        from services.governance_service import GovernanceContext  # noqa: F401

        ctx = MagicMock()
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 1
        channel = MagicMock(spec=discord.TextChannel)
        channel.id = 777
        channel.name = "test-chan"

        view = _SubsystemToggleView(ctx, channel=channel, manager_message=None)
        view._visibility = {"general": None}

        interaction = _make_interaction(responded=False)
        interaction.guild = MagicMock()

        with patch(
            "views.channels.visibility_panel.governance_service.set_subsystem_visibility",
            side_effect=Exception("authority denied"),
        ):
            callback = view._make_toggle_callback("general")
            await callback(interaction)

        interaction.response.send_message.assert_awaited_once()
        assert (
            interaction.response.send_message.call_args.kwargs.get("ephemeral") is True
        )
        interaction.response.edit_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_set_visibility_success_calls_edit_message(self):
        import discord

        from cogs.channel_cog import _SubsystemToggleView

        ctx = MagicMock()
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 1
        channel = MagicMock(spec=discord.TextChannel)
        channel.id = 777
        channel.name = "test-chan"

        view = _SubsystemToggleView(ctx, channel=channel, manager_message=None)
        view._visibility = {"general": None}

        interaction = _make_interaction(responded=False)
        interaction.guild = MagicMock()

        with (
            patch(
                "views.channels.visibility_panel.governance_service.set_subsystem_visibility",
                new_callable=AsyncMock,
            ) as mock_set,
            patch(
                "views.channels.visibility_panel.GovernanceContext.from_interaction",
                return_value=MagicMock(),
            ),
        ):
            callback = view._make_toggle_callback("general")
            await callback(interaction)

        mock_set.assert_awaited_once()
        interaction.response.edit_message.assert_awaited_once()
        interaction.response.send_message.assert_not_awaited()


# ---------------------------------------------------------------------------
# datetime.utcnow() is now caught by ruff DTZ003 (configured in pyproject.toml).
# The previous AST scan duplicated that lint rule; deleted in P1 PR-5.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# BaseView.on_error exists and has correct signature
# ---------------------------------------------------------------------------


def test_base_view_has_on_error():
    """BaseView must define on_error(interaction, error, item)."""
    import inspect

    from views.base import BaseView

    assert hasattr(BaseView, "on_error"), "BaseView must define on_error()"
    sig = inspect.signature(BaseView.on_error)
    params = list(sig.parameters)
    assert params == [
        "self",
        "interaction",
        "error",
        "item",
    ], f"on_error signature mismatch: {params}"


def test_persistent_view_has_on_error():
    """PersistentView must define on_error(interaction, error, item)."""
    import inspect

    from core.runtime.persistent_views import PersistentView

    assert hasattr(PersistentView, "on_error"), "PersistentView must define on_error()"
    sig = inspect.signature(PersistentView.on_error)
    params = list(sig.parameters)
    assert params == [
        "self",
        "interaction",
        "error",
        "item",
    ], f"on_error signature mismatch: {params}"
