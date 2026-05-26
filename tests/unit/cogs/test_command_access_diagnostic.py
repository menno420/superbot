"""PR-8 — ``!platform command-access`` diagnostic + decision metric.

Pins:

* :func:`build_command_access_diagnostic_embed` produces a structured
  embed naming the configured mode, the resolver decision, the
  bootstrap probe, and any recovery banner — without emitting an
  audit row (the probe is synthetic).
* :func:`resolve_command_access` increments
  :data:`services.metrics.command_access_decisions_total` exactly
  once per call, with the correct label values.

Both surfaces rely on the resolver behaviour pinned by
``tests/unit/runtime/test_command_access_resolver.py``; this module
covers only the new diagnostic + observability wiring layered on top.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogs.diagnostic._platform_embeds import (
    build_command_access_diagnostic_embed,
)
from utils.guild_config_accessors import CommandAccessPolicySnapshot


def _snapshot(mode: str | None, *channel_ids: int) -> CommandAccessPolicySnapshot:
    return CommandAccessPolicySnapshot(
        mode=mode,
        allowed_channels=frozenset(channel_ids),
    )


def _ctx(
    *,
    guild_id: int | None = 10,
    channel_id: int = 100,
    user_id: int = 42,
    owner_id: int = 42,
    administrator: bool = False,
    is_bot_owner: bool = False,
):
    guild = (
        SimpleNamespace(id=guild_id, owner_id=owner_id)
        if guild_id is not None
        else None
    )
    author = SimpleNamespace(
        id=user_id,
        guild_permissions=SimpleNamespace(
            administrator=administrator,
            manage_guild=False,
        ),
    )
    return SimpleNamespace(
        guild=guild,
        channel=SimpleNamespace(id=channel_id),
        author=author,
        bot=SimpleNamespace(is_owner=AsyncMock(return_value=is_bot_owner)),
    )


def _channel(channel_id: int = 100) -> SimpleNamespace:
    return SimpleNamespace(id=channel_id, mention=f"<#{channel_id}>")


# ---------------------------------------------------------------------------
# Diagnostic embed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embed_marks_admitted_channel_as_allowed():
    """The fresh-guild happy path: no DB row, default mode admits the
    channel, embed says **Yes — admitted**.
    """
    ctx = _ctx()
    target = _channel(100)
    snap = _snapshot(None)
    with (
        patch(
            "services.command_access_service.get_policy_snapshot",
            new=AsyncMock(return_value=snap),
        ),
        patch(
            "utils.guild_config_accessors.get_command_access_policy",
            new=AsyncMock(return_value=snap),
        ),
    ):
        embed = await build_command_access_diagnostic_embed(
            ctx=ctx,
            target_channel=target,
        )
    text = "\n".join(f.value for f in embed.fields)
    assert "**Yes**" in text
    assert "all_channels" in text  # default-unconfigured label


@pytest.mark.asyncio
async def test_embed_marks_denied_channel_with_reason_and_feedback():
    """``selected_channels`` mode + non-allowed channel: embed shows
    the denial, the resolver's reason code, and the operator-facing
    feedback message the user would have seen on a real invocation.
    """
    ctx = _ctx(administrator=True)
    target = _channel(999)
    snap = _snapshot("selected_channels", 100)
    with (
        patch(
            "services.command_access_service.get_policy_snapshot",
            new=AsyncMock(return_value=snap),
        ),
        patch(
            "utils.guild_config_accessors.get_command_access_policy",
            new=AsyncMock(return_value=snap),
        ),
    ):
        embed = await build_command_access_diagnostic_embed(
            ctx=ctx,
            target_channel=target,
        )
    text = "\n".join(f.value for f in embed.fields)
    assert "**No**" in text
    assert "channel_not_allowed" in text
    # Operator-facing feedback is surfaced alongside the technical reason.
    assert "Commands aren't enabled in this channel" in text


@pytest.mark.asyncio
async def test_embed_disabled_mode_shows_recovery_field():
    """``disabled_except_bootstrap`` is the most-confusing failure
    mode; the embed must include the explicit recovery banner so
    operators know to flip the mode via the settings panel.
    """
    ctx = _ctx(administrator=True)
    target = _channel(100)
    snap = _snapshot("disabled_except_bootstrap")
    with (
        patch(
            "services.command_access_service.get_policy_snapshot",
            new=AsyncMock(return_value=snap),
        ),
        patch(
            "utils.guild_config_accessors.get_command_access_policy",
            new=AsyncMock(return_value=snap),
        ),
    ):
        embed = await build_command_access_diagnostic_embed(
            ctx=ctx,
            target_channel=target,
        )
    recovery = [f for f in embed.fields if f.name == "Recovery"]
    assert len(recovery) == 1
    assert "!settings" in recovery[0].value
    assert "Command access" in recovery[0].value


@pytest.mark.asyncio
async def test_embed_includes_bootstrap_probe_for_operator():
    """The operator running ``!platform command-access`` should also
    see whether ``!setup`` would still admit them via the bootstrap
    bypass — this is the "I'm not locked out" guarantee for the
    panel.
    """
    ctx = _ctx(administrator=True)
    target = _channel(999)
    snap = _snapshot("disabled_except_bootstrap")
    with (
        patch(
            "services.command_access_service.get_policy_snapshot",
            new=AsyncMock(return_value=snap),
        ),
        patch(
            "utils.guild_config_accessors.get_command_access_policy",
            new=AsyncMock(return_value=snap),
        ),
    ):
        embed = await build_command_access_diagnostic_embed(
            ctx=ctx,
            target_channel=target,
        )
    bootstrap_fields = [f for f in embed.fields if f.name.startswith("Bootstrap probe")]
    assert len(bootstrap_fields) == 1
    # Admin invoker → bootstrap probe must say allowed via bypass.
    assert "bootstrap_bypass" in bootstrap_fields[0].value


@pytest.mark.asyncio
async def test_embed_emits_no_audit_row():
    """The probe is synthetic — running it must NOT call any
    mutation pipeline (otherwise it would pollute the audit log
    every time an operator opened the diagnostic).
    """
    ctx = _ctx()
    target = _channel(100)
    snap = _snapshot(None)
    with (
        patch(
            "services.command_access_service.get_policy_snapshot",
            new=AsyncMock(return_value=snap),
        ),
        patch(
            "utils.guild_config_accessors.get_command_access_policy",
            new=AsyncMock(return_value=snap),
        ),
        patch(
            "services.command_access_service.set_mode",
            new=AsyncMock(),
        ) as mock_set_mode,
        patch(
            "services.command_access_service.replace_allowed_channels",
            new=AsyncMock(),
        ) as mock_replace,
    ):
        await build_command_access_diagnostic_embed(
            ctx=ctx,
            target_channel=target,
        )
    mock_set_mode.assert_not_awaited()
    mock_replace.assert_not_awaited()


# ---------------------------------------------------------------------------
# Decision metric
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolver_emits_decision_metric_with_correct_labels():
    """Allow path under default-unconfigured: metric labels should be
    ``invocation=prefix``, ``decision=allow``, ``reason=allowed``,
    ``mode=all_channels``, ``source=default_unconfigured``.
    """
    from core.runtime.command_access import (
        CommandAccessContext,
        resolve_command_access,
    )

    ctx = CommandAccessContext(
        guild_id=10,
        channel_id=100,
        user_id=42,
        command_name="blackjack",
        invocation_type="prefix",
        is_guild_operator=False,
        is_bot_owner=False,
        is_dm=False,
    )

    counter_proxy = MagicMock()
    labels_proxy = MagicMock()
    counter_proxy.labels = MagicMock(return_value=labels_proxy)

    with (
        patch(
            "utils.guild_config_accessors.get_command_access_policy",
            new=AsyncMock(return_value=_snapshot(None)),
        ),
        patch(
            "services.metrics.command_access_decisions_total",
            new=counter_proxy,
        ),
    ):
        decision = await resolve_command_access(ctx)

    assert decision.allowed is True
    counter_proxy.labels.assert_called_once_with(
        invocation="prefix",
        decision="allow",
        reason="allowed",
        mode="all_channels",
        source="default_unconfigured",
    )
    labels_proxy.inc.assert_called_once()


@pytest.mark.asyncio
async def test_resolver_metric_emit_failure_is_swallowed():
    """An exception inside the metric emit must NOT propagate into
    the admission decision — observability never blocks the gate.
    """
    from core.runtime.command_access import (
        CommandAccessContext,
        resolve_command_access,
    )

    ctx = CommandAccessContext(
        guild_id=10,
        channel_id=100,
        user_id=42,
        command_name="blackjack",
        invocation_type="prefix",
        is_guild_operator=False,
        is_bot_owner=False,
        is_dm=False,
    )

    blown_counter = MagicMock()
    blown_counter.labels = MagicMock(side_effect=RuntimeError("prom broke"))

    with (
        patch(
            "utils.guild_config_accessors.get_command_access_policy",
            new=AsyncMock(return_value=_snapshot(None)),
        ),
        patch(
            "services.metrics.command_access_decisions_total",
            new=blown_counter,
        ),
    ):
        # Must not raise.
        decision = await resolve_command_access(ctx)
    assert decision.allowed is True


@pytest.mark.asyncio
async def test_resolver_metric_uses_none_label_for_lifecycle_drain():
    """Lifecycle-drain denial carries ``mode=None`` in the decision;
    the metric label must surface the string ``"none"`` (Prometheus
    label values cannot be Python ``None``).
    """
    from core.runtime import lifecycle
    from core.runtime.command_access import (
        CommandAccessContext,
        resolve_command_access,
    )

    ctx = CommandAccessContext(
        guild_id=10,
        channel_id=100,
        user_id=42,
        command_name="blackjack",
        invocation_type="slash",
        is_guild_operator=False,
        is_bot_owner=False,
        is_dm=False,
    )

    counter_proxy = MagicMock()
    counter_proxy.labels = MagicMock(return_value=MagicMock())

    lifecycle.reset_for_tests()
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("test")
    try:
        with patch(
            "services.metrics.command_access_decisions_total",
            new=counter_proxy,
        ):
            await resolve_command_access(ctx)
    finally:
        lifecycle.reset_for_tests()

    counter_proxy.labels.assert_called_once_with(
        invocation="slash",
        decision="deny",
        reason="lifecycle_draining",
        mode="none",
        source="lifecycle_deny",
    )
