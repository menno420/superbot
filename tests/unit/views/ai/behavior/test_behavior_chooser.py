"""PR-C tests for the Behavior chooser entry view.

Pin:

* The intro embed lists scope / preview / advanced affordances.
* Admin-only gate is enforced on the View.
* The Preview button reuses ``views.ai.policy.preview_view.PreviewChannelSelectView``
  (we never re-implement the dry-run flow).
* The Advanced button reuses ``views.ai.policy.chooser.PolicyChooserView``.
* No view in the package imports ``utils.db.ai`` directly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from views.ai.behavior import BehaviorChooserView, build_behavior_embed

_BEHAVIOR_DIR = (
    Path(__file__).resolve().parents[4] / "disbot" / "views" / "ai" / "behavior"
)


def test_behavior_embed_lists_workflow_affordances():
    embed = build_behavior_embed()
    names = {f.name for f in embed.fields}
    assert {"Channel", "Category"} <= names
    assert any("Preview" in n for n in names)
    assert any("Advanced" in n for n in names)


def test_chooser_view_has_expected_buttons():
    view = BehaviorChooserView()
    labels = {c.label for c in view.children if hasattr(c, "label")}
    assert {"Channel", "Category"} <= labels
    assert any(label and "Preview" in label for label in labels)
    assert "Advanced" in labels


@pytest.mark.asyncio
async def test_admin_gate_rejects_non_admin():
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, MagicMock

    view = BehaviorChooserView()
    interaction = MagicMock()
    interaction.user = SimpleNamespace(
        guild_permissions=SimpleNamespace(administrator=False),
    )
    interaction.response.send_message = AsyncMock()
    ok = await view.interaction_check(interaction)
    assert ok is False
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_preview_button_reuses_preview_channel_select_view(monkeypatch):
    """The Preview button must reuse the PR4B view, never reimplement
    the dry-run flow.
    """
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, MagicMock

    captured: dict = {}

    interaction = MagicMock()
    interaction.user = SimpleNamespace(
        guild_permissions=SimpleNamespace(administrator=True),
    )

    async def _send_message(*args, **kwargs):
        captured.update(kwargs)
        if args:
            captured["content"] = args[0]

    interaction.response.send_message = AsyncMock(side_effect=_send_message)

    view = BehaviorChooserView()
    # Find the preview button by label.
    preview = next(
        c
        for c in view.children
        if hasattr(c, "label") and c.label and "Preview" in c.label
    )
    await preview.callback(interaction)

    from views.ai.policy.preview_view import PreviewChannelSelectView

    assert isinstance(captured["view"], PreviewChannelSelectView)


@pytest.mark.asyncio
async def test_advanced_button_reuses_policy_chooser(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, MagicMock

    captured: dict = {}

    interaction = MagicMock()
    interaction.user = SimpleNamespace(
        guild_permissions=SimpleNamespace(administrator=True),
    )

    async def _send_message(*args, **kwargs):
        captured.update(kwargs)
        if args:
            captured["content"] = args[0]

    interaction.response.send_message = AsyncMock(side_effect=_send_message)

    view = BehaviorChooserView()
    advanced = next(
        c for c in view.children if hasattr(c, "label") and c.label == "Advanced"
    )
    await advanced.callback(interaction)

    from views.ai.policy.chooser import PolicyChooserView

    assert isinstance(captured["view"], PolicyChooserView)


def test_no_behavior_view_imports_ai_db_directly():
    """Behavior UI must route every mutation through the chokepoints —
    no direct calls to utils.db.ai write helpers.
    """
    forbidden = (
        "ai_db.upsert_channel_policy",
        "ai_db.upsert_category_policy",
        "ai_db.upsert_role_policy",
        "ai_db.upsert_instruction_profile",
    )
    for path in _BEHAVIOR_DIR.rglob("*.py"):
        src = path.read_text()
        for sym in forbidden:
            assert sym not in src, f"{path.name} must not call {sym} directly"
        # Also catch ``from utils.db import ai`` followed by a write.
        if "from utils.db" in src or "import utils.db" in src:
            for sym in (
                "upsert_channel_policy",
                "upsert_category_policy",
                "upsert_role_policy",
                "upsert_instruction_profile",
            ):
                assert (
                    sym not in src
                ), f"{path.name} imports utils.db and references {sym}"
