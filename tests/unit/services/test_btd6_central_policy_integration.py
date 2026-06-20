"""BTD6 passive replies consume the central AI policy resolver.

Regression coverage for the boundary in
``docs/ownership.md``: AI Platform owns whether AI may reply (guild AI
enabled, channel/category mode, mention-only, role/level/cooldown gates).
BTD6 owns BTD6 knowledge, prompts, strategies, and rendering. The
:mod:`services.btd6_ai_service` module must not duplicate any of the
central policy resolver logic.

These tests:

* Pin that ``btd6_ai_service`` does not import the policy resolver and
  does not contain hand-rolled "is AI enabled here?" checks.
* Run the central stage end-to-end with the BTD6 task and confirm:

    - ``ai_guild_policy.enabled=false`` blocks BTD6 passive replies.
    - The inheritance bug case (``natural_language_enabled=false`` plus
      ``channel mode=always_reply``) allows BTD6 passive replies.
    - Without a channel/category override, ``natural_language_enabled=false``
      blocks BTD6 passive replies with ``AI_NL_DISABLED_FOR_GUILD``.
"""

from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.runtime.ai.contracts import (
    AIRequestContext,
    AIResponse,
    AIScope,
    AITask,
    PolicyDenialReason,
)
from core.runtime.ai.natural_language_stage import AINaturalLanguageStage
from core.runtime.message_pipeline import MessagePipelineContext
from services import ai_natural_language_policy as nlp
from utils.db import ai as ai_db

# ---------------------------------------------------------------------------
# Architectural invariant: btd6_ai_service stays inside its boundary.
# ---------------------------------------------------------------------------


def _btd6_ai_service_source() -> str:
    path = (
        Path(__file__).parents[3]
        / "disbot"
        / "services"
        / "btd6_ai_service.py"
    )
    return path.read_text()


def test_btd6_ai_service_does_not_import_policy_resolver():
    """The BTD6 augmentation service must not import the central policy
    resolver — that lives upstream in the natural-language stage."""
    src = _btd6_ai_service_source()
    # Match real Python import statements, not docstring mentions of the name.
    forbidden_imports = (
        re.compile(r"^\s*from\s+services\.ai_natural_language_policy\b", re.MULTILINE),
        re.compile(r"^\s*from\s+services\s+import\s+[^#\n]*\bai_natural_language_policy\b", re.MULTILINE),
        re.compile(r"^\s*import\s+services\.ai_natural_language_policy\b", re.MULTILINE),
    )
    for pattern in forbidden_imports:
        assert not pattern.search(src), (
            f"btd6_ai_service must not import ai_natural_language_policy "
            f"(matched {pattern.pattern!r}); the policy resolver runs "
            "upstream in the central NL stage."
        )


def test_btd6_ai_service_does_not_read_channel_or_category_policy_tables():
    """No hand-rolled "is this channel/category allowed?" lookups in BTD6."""
    src = _btd6_ai_service_source()
    # Explicit table-name checks: the resolver reads these — BTD6 must not.
    for forbidden in (
        "ai_channel_policy",
        "ai_category_policy",
        "ai_guild_policy",
        "get_channel_policy",
        "get_category_policy",
        "list_channel_policies",
        "list_category_policies",
    ):
        assert forbidden not in src, (
            f"btd6_ai_service must not reference {forbidden!r}; "
            "policy resolution belongs to ai_natural_language_policy."
        )


def test_btd6_ai_service_has_no_handrolled_guild_or_channel_mode_logic():
    """No string-comparison policy code (e.g. ``mode == 'disabled'``) in BTD6."""
    src = _btd6_ai_service_source()
    # Any literal use of the four mode strings outside docstrings would be
    # evidence of duplicated policy logic. The service file is small enough
    # that we can grep the lowered source.
    body = src.lower()
    for forbidden_pattern in (
        r"mode\s*==\s*['\"]disabled['\"]",
        r"mode\s*==\s*['\"]always_reply['\"]",
        r"mode\s*==\s*['\"]mention_only['\"]",
        r"natural_language_enabled",
    ):
        assert not re.search(forbidden_pattern, body), (
            f"btd6_ai_service must not contain {forbidden_pattern!r}; "
            "the central resolver owns this logic."
        )


# ---------------------------------------------------------------------------
# Central stage integration with the BTD6 task route.
# ---------------------------------------------------------------------------


def _btd6_message(*, guild_id: int = 1, channel_id: int = 100):
    msg = MagicMock()
    msg.content = "What's Dart Monkey base cost?"
    msg.id = 777
    msg.guild = MagicMock()
    msg.guild.id = guild_id
    msg.channel = MagicMock()
    msg.channel.id = channel_id
    msg.channel.category_id = 200
    msg.channel.send = AsyncMock()
    msg.author = MagicMock()
    msg.author.id = 42
    msg.author.bot = False
    msg.author.roles = []
    msg.mentions = []
    msg.mention_everyone = False
    return msg


def _btd6_ctx(message):
    bot = MagicMock()
    bot.user = SimpleNamespace(mentioned_in=lambda _msg: False)
    return MessagePipelineContext(bot=bot, message=message)


def _patch_resolver_state(monkeypatch, *, policy, channels=None):
    """Patch the resolver's DB reads so the central stage uses the real
    resolver against an in-memory bundle."""

    async def _get_policy(_gid):
        return policy

    async def _list_channels(_gid):
        return list(channels or [])

    async def _empty(_gid):
        return []

    monkeypatch.setattr(ai_db, "get_guild_policy", _get_policy)
    monkeypatch.setattr(ai_db, "list_channel_policies", _list_channels)
    monkeypatch.setattr(ai_db, "list_category_policies", _empty)
    monkeypatch.setattr(ai_db, "list_role_policies", _empty)
    nlp._reset_for_tests()


def _stub_services_for_btd6(monkeypatch):
    """Stub the stage's collaborators except the resolver and the audit
    capture so the test exercises the real resolver via the stage."""
    from core.runtime.ai import natural_language_stage as mod

    monkeypatch.setattr(
        mod.ai_permission_service,
        "snapshot",
        AsyncMock(
            return_value=SimpleNamespace(level=10, is_fresh_user=False),
        ),
    )
    monkeypatch.setattr(
        mod.ai_permission_service,
        "is_on_cooldown",
        lambda *a, **kw: False,
    )
    monkeypatch.setattr(
        mod.ai_permission_service,
        "mark_reply_sent",
        lambda *a, **kw: None,
    )
    monkeypatch.setattr(
        mod.ai_task_router,
        "classify",
        lambda _text, **_kw: SimpleNamespace(
            task=AITask.BTD6_ANSWER,
            route="btd6.answer",
        ),
    )
    monkeypatch.setattr(
        mod.ai_instruction_service,
        "assemble",
        AsyncMock(
            return_value=SimpleNamespace(
                render_system_prompt=lambda: "btd6 sys",
                render_payload_text=lambda: "btd6 payload",
                instruction_profile_ids=(),
            ),
        ),
    )
    monkeypatch.setattr(
        mod.ai_context_service,
        "build",
        lambda **kw: SimpleNamespace(
            request_context=AIRequestContext(
                task=kw["task"],
                scope=AIScope.USER,
                guild_id=kw["guild_id"],
                actor_id=kw["actor_id"],
                channel_id=kw["channel_id"],
                correlation_id=kw["correlation_id"],
                source="test",
            ),
            correlation_id=kw["correlation_id"],
        ),
    )
    monkeypatch.setattr(
        mod.ai_conversation_service, "append", lambda *a, **kw: None,
    )

    # Replace the feature-fact gather so we don't pull real BTD6 data. The
    # facts must *ground* the benign reply below ("Dart Monkey costs 200.")
    # so these policy-focused tests exercise the reply path and not the BTD6
    # faithfulness floor (which would otherwise refuse an ungrounded reply).
    from core.runtime.ai.feature_facts import FeatureFactsResult

    async def _grounding_facts(_req):
        return FeatureFactsResult(facts=("Dart Monkey costs 200.",))

    monkeypatch.setattr(mod, "_gather_feature_facts", _grounding_facts)

    # Capture gateway call + return a benign reply.
    from services import ai_gateway

    async def _execute(request):
        return AIResponse(
            task=AITask.BTD6_ANSWER,
            provider="deterministic",
            model="btd6",
            text="Dart Monkey costs 200.",
        )

    monkeypatch.setattr(ai_gateway, "execute", _execute)

    from core.runtime.ai import response_renderer_registry
    monkeypatch.setattr(response_renderer_registry, "render", AsyncMock(return_value=None))

    audit: list[dict] = []

    async def _record(**kw):
        audit.append(kw)
        return len(audit)

    monkeypatch.setattr(mod.ai_decision_audit_service, "record", _record)
    return audit


def _enabled_guild_policy(**overrides):
    base = {
        "guild_id": 1,
        "enabled": True,
        "natural_language_enabled": True,
        "default_provider": "deterministic",
        "default_model": "",
        "minimum_level_default": 0,
        "cooldown_seconds": 0,
        "fresh_user_mention_allowance": 0,
        "guild_instruction_profile_id": None,
        "generation": 1,
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_btd6_passive_reply_blocked_when_guild_ai_disabled(monkeypatch):
    audit = _stub_services_for_btd6(monkeypatch)
    _patch_resolver_state(monkeypatch, policy=_enabled_guild_policy(enabled=False))

    stage = AINaturalLanguageStage()
    msg = _btd6_message()
    await stage.process(_btd6_ctx(msg))

    assert len(audit) == 1
    row = audit[0]
    assert row["decision"] == "denied"
    assert row["reason_code"] is PolicyDenialReason.AI_GLOBALLY_DISABLED
    assert row["task"] == "btd6.answer"
    msg.channel.send.assert_not_called()
    nlp._reset_for_tests()


@pytest.mark.asyncio
async def test_btd6_passive_reply_allowed_when_channel_override_beats_guild_nl_disabled(
    monkeypatch,
):
    """The inheritance bug case applied to a BTD6-routed message."""
    audit = _stub_services_for_btd6(monkeypatch)
    _patch_resolver_state(
        monkeypatch,
        policy=_enabled_guild_policy(natural_language_enabled=False),
        channels=[{
            "channel_id": 100,
            "mode": "always_reply",
            "min_level": 0,
            "cooldown_seconds": 0,
            "instruction_profile_id": None,
        }],
    )

    stage = AINaturalLanguageStage()
    msg = _btd6_message()
    await stage.process(_btd6_ctx(msg))

    assert len(audit) == 1
    row = audit[0]
    assert row["decision"] == "replied"
    assert row["reason_code"] is PolicyDenialReason.NONE
    assert row["task"] == "btd6.answer"
    msg.channel.send.assert_awaited_once()
    nlp._reset_for_tests()


@pytest.mark.asyncio
async def test_btd6_passive_reply_blocked_in_non_overridden_channel_when_guild_nl_disabled(
    monkeypatch,
):
    """The inverse: with no channel/category override, the guild baseline
    denies even for a BTD6 message, with ``AI_NL_DISABLED_FOR_GUILD``."""
    audit = _stub_services_for_btd6(monkeypatch)
    _patch_resolver_state(
        monkeypatch,
        policy=_enabled_guild_policy(natural_language_enabled=False),
    )

    stage = AINaturalLanguageStage()
    msg = _btd6_message()
    await stage.process(_btd6_ctx(msg))

    assert len(audit) == 1
    row = audit[0]
    assert row["decision"] == "denied"
    assert row["reason_code"] is PolicyDenialReason.AI_NL_DISABLED_FOR_GUILD
    assert row["task"] == "btd6.answer"
    msg.channel.send.assert_not_called()
    nlp._reset_for_tests()
