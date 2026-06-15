"""Operator explainers IL-1 / IL-2 / IL-3 (read-only diagnostics, wave PR2).

Pins the PURE renderers + the metric reader + the context helper.  All inputs
are constructed directly (no DB, no Discord gateway): the cog methods resolve
via existing read models (`build_governance_snapshot`, `resolve_cleanup_policy`,
`task_outcome_total`) and hand the results to these builders.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import discord

from cogs.diagnostic._platform_embeds import (
    build_access_explainer_embed,
    build_cleanup_preview_embed,
    build_counting_health_embed,
    read_counting_save_outcomes,
)
from governance.models import CleanupPolicy, GovernanceSnapshot, PolicySource


def _snapshot(*, visible, denied):
    return GovernanceSnapshot(
        visible_subsystems=set(visible),
        denied_subsystems=set(denied),
        dependency_blocks={"games": ["economy"]},
        cleanup_policy=CleanupPolicy(
            delete_message=True,
            delete_after_seconds=10,
            send_feedback=False,
            resolved_from=PolicySource.GUILD_OVERRIDE,
        ),
        member_tier="admin",
        scope_provenance={"games": PolicySource.CHANNEL_OVERRIDE},
        capability_map={"games.play": True},
        registry_version=3,
        registry_schema_version=1,
    )


# ---- IL-1 -----------------------------------------------------------------


def test_access_explainer_lists_visible_and_denied():
    embed = build_access_explainer_embed(
        "#general",
        _snapshot(visible=["games", "economy"], denied=["moderation"]),
    )
    assert isinstance(embed, discord.Embed)
    joined = "\n".join(f"{f.name}\n{f.value}" for f in embed.fields)
    assert "Visible (2)" in joined
    assert "Denied (1)" in joined
    assert "`games`" in joined and "`moderation`" in joined
    assert "Resolved from" in joined
    assert "Dependency blocks" in joined
    assert "Cleanup here" in joined


def test_access_explainer_handles_empty_sets():
    embed = build_access_explainer_embed(
        "#empty",
        GovernanceSnapshot(
            visible_subsystems=set(),
            denied_subsystems=set(),
            dependency_blocks={},
            cleanup_policy=CleanupPolicy(
                False,
                0,
                False,
                PolicySource.REGISTRY_DEFAULT,
            ),
            member_tier="member",
            scope_provenance={},
            capability_map={},
            registry_version=1,
            registry_schema_version=1,
        ),
    )
    joined = "\n".join(f.value for f in embed.fields)
    assert "*(none)*" in joined


# ---- IL-2 -----------------------------------------------------------------


def _policy():
    return CleanupPolicy(
        delete_message=True,
        delete_after_seconds=30,
        send_feedback=True,
        resolved_from=PolicySource.CHANNEL_OVERRIDE,
    )


def test_cleanup_preview_channel_lists_scopes_no_thread_note():
    embed = build_cleanup_preview_embed(
        "#general",
        _policy(),
        is_thread=False,
        valid_cleanup_scopes=frozenset({"channel", "category", "guild"}),
    )
    joined = "\n".join(f"{f.name}\n{f.value}" for f in embed.fields)
    assert "`channel`" in joined and "`guild`" in joined
    assert "not** a cleanup scope (RC-5)" in joined
    assert "Thread note" not in joined
    assert "dry run" in (embed.footer.text or "").lower()


def test_cleanup_preview_thread_adds_note():
    embed = build_cleanup_preview_embed(
        "#thread",
        _policy(),
        is_thread=True,
        valid_cleanup_scopes=frozenset({"channel", "category", "guild"}),
    )
    assert any("Thread note" in f.name for f in embed.fields)


# ---- IL-3 -----------------------------------------------------------------


class _Sample:
    def __init__(self, name, labels, value):
        self.name = name
        self.labels = labels
        self.value = value


class _Family:
    def __init__(self, samples):
        self.samples = samples


class _FakeCounter:
    def __init__(self, samples):
        self._samples = samples

    def collect(self):
        return [_Family(self._samples)]


_FAKE_SAMPLES = [
    _Sample(
        "task_outcome_total_total", {"name": "counting:save:1", "outcome": "error"}, 2
    ),
    _Sample(
        "task_outcome_total_total", {"name": "counting:save:1", "outcome": "ok"}, 5
    ),
    _Sample(
        "task_outcome_total_total", {"name": "counting:save:2", "outcome": "error"}, 1
    ),
    # _created samples carry a float timestamp and MUST be ignored:
    _Sample(
        "task_outcome_total_created",
        {"name": "counting:save:1", "outcome": "error"},
        1.7e9,
    ),
    # a non-counting task MUST be ignored:
    _Sample(
        "task_outcome_total_total", {"name": "session_gc:loop", "outcome": "error"}, 9
    ),
]


def test_read_counting_outcomes_per_guild_and_global(monkeypatch):
    from services import metrics

    monkeypatch.setattr(metrics, "PROMETHEUS_AVAILABLE", True)
    monkeypatch.setattr(metrics, "task_outcome_total", _FakeCounter(_FAKE_SAMPLES))

    assert read_counting_save_outcomes(1) == {"ok": 5, "error": 2, "cancelled": 0}
    # global sums counting:save:1 + counting:save:2, excludes session_gc + _created
    assert read_counting_save_outcomes() == {"ok": 5, "error": 3, "cancelled": 0}


def test_read_counting_outcomes_none_when_prometheus_unavailable(monkeypatch):
    from services import metrics

    monkeypatch.setattr(metrics, "PROMETHEUS_AVAILABLE", False)
    assert read_counting_save_outcomes(1) is None


def test_counting_health_embed_unavailable():
    embed = build_counting_health_embed(123, None, None)
    assert "not installed" in (embed.description or "")


def test_counting_health_embed_flags_errors():
    embed = build_counting_health_embed(
        123,
        {"ok": 4, "error": 1, "cancelled": 0},
        {"ok": 10, "error": 1, "cancelled": 0},
    )
    joined = "\n".join(f"{f.name}\n{f.value}" for f in embed.fields)
    assert "⚠️" in joined and "Verdict" in joined
    assert embed.color == discord.Color.orange()


def test_counting_health_embed_healthy():
    embed = build_counting_health_embed(
        123,
        {"ok": 4, "error": 0, "cancelled": 0},
        {"ok": 10, "error": 0, "cancelled": 0},
    )
    joined = "\n".join(f.value for f in embed.fields)
    assert "no save errors" in joined


# ---- IL-1/IL-2 context helper ---------------------------------------------


def test_governance_context_for_thread_vs_channel():
    from cogs.diagnostic._platform_embeds import governance_context_for

    author = MagicMock()
    author.roles = []
    ctx = MagicMock()
    ctx.guild.id = 99
    ctx.author = author

    channel = MagicMock(spec=discord.TextChannel)
    channel.id = 5
    channel.category_id = 7
    cc = governance_context_for(ctx, channel)
    assert cc.guild_id == 99
    assert cc.channel_id == 5
    assert cc.category_id == 7
    assert cc.thread_id is None

    thread = MagicMock(spec=discord.Thread)
    thread.id = 50
    thread.parent_id = 5
    thread.parent = MagicMock()
    thread.parent.category_id = 7
    tc = governance_context_for(ctx, thread)
    assert tc.thread_id == 50
    assert tc.channel_id == 5
    assert tc.category_id == 7
