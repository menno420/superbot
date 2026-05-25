"""PR4A — Policy chooser view dispatches the four scope buttons."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from views.ai.policy.chooser import (  # noqa: E402
    PolicyChooserView,
    build_chooser_embed,
)


def _admin_interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = True
    interaction.response.send_message = AsyncMock()
    return interaction


def _non_admin_interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = False
    interaction.response.send_message = AsyncMock()
    return interaction


def test_chooser_embed_describes_all_four_scopes():
    embed = build_chooser_embed()
    text = "\n".join(
        [embed.title or "", embed.description or ""]
        + [f"{f.name}: {f.value}" for f in embed.fields]
    )
    assert "Channel" in text
    assert "Category" in text
    assert "Role" in text
    assert "List" in text
    # The body must explain the write path so reviewers / admins know
    # mutations are funneled through the mutation service.
    assert "ai_policy_mutation" in text


def test_chooser_embed_mentions_ai_policy_events():
    embed = build_chooser_embed()
    blob = " ".join([embed.description or ""])
    assert "ai.policy" in blob


async def test_interaction_check_rejects_non_admin():
    view = PolicyChooserView()
    interaction = _non_admin_interaction()
    allowed = await view.interaction_check(interaction)
    assert allowed is False
    interaction.response.send_message.assert_awaited_once()
    args, kwargs = interaction.response.send_message.call_args
    assert "Administrator" in args[0]
    assert kwargs.get("ephemeral") is True


async def test_interaction_check_admits_admin():
    view = PolicyChooserView()
    interaction = _admin_interaction()
    allowed = await view.interaction_check(interaction)
    assert allowed is True
    interaction.response.send_message.assert_not_awaited()


async def test_channel_button_opens_channel_select_view():
    view = PolicyChooserView()
    interaction = _admin_interaction()
    await view.channel_btn.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    _, kwargs = interaction.response.send_message.call_args
    # The follow-up is ephemeral and carries a view (the
    # ChannelPolicySelectView created lazily inside the callback).
    assert kwargs.get("ephemeral") is True
    assert kwargs.get("view") is not None
    # Imported here so the test does not force the module to load
    # at collection time.
    from views.ai.policy.channel_view import ChannelPolicySelectView

    assert isinstance(kwargs["view"], ChannelPolicySelectView)


async def test_all_scope_buttons_have_real_implementations():
    """After PR4A commit 4, every chooser sub-button opens a real
    follow-up view. The placeholder phase is done."""
    view = PolicyChooserView()
    for attr in ("channel_btn", "category_btn", "role_btn", "list_btn"):
        handler = getattr(view, attr)
        assert handler is not None, attr


def test_chooser_view_has_one_button_per_scope():
    """Smoke check: five buttons (Channel / Category / Role on row 0,
    Effective policy / List overrides on row 1) sit on the chooser.
    The Preview button was renamed to Effective policy in PR-2; the
    underlying ``preview_btn`` handler (and its custom_id contract)
    is unchanged.
    """
    view = PolicyChooserView()
    labels = sorted(
        item.label
        for item in view.children
        if hasattr(item, "label") and item.label
    )
    assert labels == [
        "Category",
        "Channel",
        "Effective policy",
        "List overrides",
        "Role",
    ]
