"""Module-1 invariant: the setup advisor consumes the AI gateway.

Two checks:

* AST scan — ``setup_ai_advisor`` must not import the ``openai`` SDK
  directly anymore. The provider chokepoint owns that import.
* Behavioural — when ``OpenAISetupAdvisor.suggest`` runs, the
  gateway's ``execute`` path is invoked (proven by an injected
  duck-typed client appearing as the provider override).
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.guild_snapshot import GuildSnapshot
from services.setup_ai_advisor import OpenAISetupAdvisor


def test_setup_ai_advisor_does_not_import_openai_sdk():
    """Module 1 moves the OpenAI SDK import into the provider package."""
    path = (
        Path(__file__).resolve().parents[3]
        / "disbot"
        / "services"
        / "setup_ai_advisor.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "openai":
            pytest.fail(
                f"services/setup_ai_advisor.py imports openai at line "
                f"{node.lineno}; it must consume the gateway instead.",
            )
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "openai":
                    pytest.fail(
                        f"services/setup_ai_advisor.py imports openai at line "
                        f"{node.lineno}; it must consume the gateway instead.",
                    )


@pytest.mark.asyncio
async def test_setup_advisor_routes_through_gateway():
    """The injected client must end up driving the OpenAIProvider call."""
    fake_client = MagicMock()
    fake_client.chat = MagicMock()
    fake_client.chat.completions = MagicMock()
    fake_response = MagicMock()
    fake_message = MagicMock()
    fake_message.content = '{"recommendations": []}'
    fake_choice = MagicMock()
    fake_choice.message = fake_message
    fake_response.choices = [fake_choice]
    fake_client.chat.completions.create = AsyncMock(return_value=fake_response)

    advisor = OpenAISetupAdvisor(client=fake_client, api_key="sk-test")
    snap = GuildSnapshot(guild_id=1, guild_name="X", owner_id=9)

    draft = await advisor.suggest(snap)

    # The fake client's chat.completions.create was awaited exactly once —
    # proving the gateway → OpenAIProvider → client.chat.completions
    # chain runs end-to-end.
    fake_client.chat.completions.create.assert_awaited_once()
    assert draft.source == "openai"
