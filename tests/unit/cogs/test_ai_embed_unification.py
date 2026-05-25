"""PR-4B — providers / routing / settings embeds source from the snapshot.

Pins:

* ``build_providers_embed(snapshot)`` reads from ``snapshot.provider``
  when supplied; falls back to ``ai_diagnostics_service.snapshot_for_cog``
  when ``snapshot=None``.
* ``build_providers_embed`` adds a "Guild override" field when the
  typed policy row has provider/model set.
* ``build_routing_embed(task, snapshot)`` keeps the existing
  per-task routing rows (process-wide, env-driven) and adds a
  guild-override field when the snapshot's policy has overrides.
* The AI settings panel renderer appends an AI-specific
  purpose-grouping field. Schema order in ``cogs/ai/schemas.py``
  is unchanged.

Read-source replacement only — no behavior change, no new mutation
paths.
"""

from __future__ import annotations

import pytest

from cogs.ai_cog import (
    _attach_settings_grouping_field,
    build_providers_embed,
    build_routing_embed,
)
from services import ai_config_projection_service, ai_diagnostics_service


def _snapshot(
    *,
    default_provider: str | None = "openai",
    default_model: str | None = "gpt-4o-mini",
    provider_active: str | None = "openai",
    channel_overrides: int = 0,
    category_overrides: int = 0,
    role_overrides: int = 0,
):
    return ai_config_projection_service.AIConfigSnapshot(
        guild_id=1,
        policy=ai_config_projection_service.PolicySnapshot(
            guild_id=1,
            enabled=True,
            natural_language_enabled=True,
            default_provider=default_provider,
            default_model=default_model,
            channel_override_count=channel_overrides,
            category_override_count=category_overrides,
            role_override_count=role_overrides,
        ),
        memory=ai_config_projection_service.MemorySnapshot(
            window_minutes=0,
            scan_enabled=False,
            cached_channel_count=0,
            cached_total_turns=0,
            per_channel_cap=200,
            channel_lru_cap=50,
            min_floor_turns=3,
        ),
        provider=ai_config_projection_service.ProviderSnapshot(
            enabled=True,
            default_provider=default_provider,
            setup_advisor_provider=default_provider,
            provider_active=provider_active,
            degraded=False,
            last_error_type=None,
            last_fallback_reason=None,
            requests_observed=0,
            failures_observed=0,
            redaction_enabled=True,
        ),
        projection=ai_config_projection_service.ProjectionSnapshot(),
        instruction=ai_config_projection_service.InstructionSnapshot(),
        audit=ai_config_projection_service.AuditSnapshot(),
    )


# ---------------------------------------------------------------------------
# build_providers_embed
# ---------------------------------------------------------------------------


def test_providers_embed_with_snapshot_sources_provider_fields():
    snap = _snapshot(default_provider="openai", provider_active="openai")
    embed = build_providers_embed(snap)
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Default"] == "openai"
    assert fields["Active (last call)"] == "openai"


def test_providers_embed_without_snapshot_uses_diagnostics(monkeypatch):
    monkeypatch.setattr(
        ai_diagnostics_service,
        "snapshot_for_cog",
        lambda: {
            "enabled": True,
            "default_provider": "deterministic",
            "setup_advisor_provider": "deterministic",
            "provider_active": "deterministic",
            "requests_observed": 0,
            "failures_observed": 0,
        },
    )
    embed = build_providers_embed(None)
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Default"] == "deterministic"


def test_providers_embed_shows_guild_override_when_present():
    snap = _snapshot(default_provider="openai", default_model="gpt-4o-mini")
    embed = build_providers_embed(snap)
    override = next(f for f in embed.fields if f.name == "Guild override")
    assert "openai" in override.value
    assert "gpt-4o-mini" in override.value


def test_providers_embed_no_guild_override_field_when_policy_empty(monkeypatch):
    """When the typed policy row has no provider/model set, the
    Guild override field is omitted."""
    monkeypatch.setattr(
        ai_diagnostics_service,
        "snapshot_for_cog",
        lambda: {
            "enabled": True,
            "default_provider": "deterministic",
            "setup_advisor_provider": "deterministic",
            "provider_active": "deterministic",
            "requests_observed": 0,
            "failures_observed": 0,
        },
    )
    snap = _snapshot(default_provider=None, default_model=None)
    embed = build_providers_embed(snap)
    field_names = {f.name for f in embed.fields}
    assert "Guild override" not in field_names


# ---------------------------------------------------------------------------
# build_routing_embed
# ---------------------------------------------------------------------------


def test_routing_embed_renders_task_rows_without_snapshot():
    """No snapshot → backwards-compatible per-task rows only."""
    embed = build_routing_embed()
    # Some task rows are present.
    assert len(embed.fields) > 0
    field_names = {f.name for f in embed.fields}
    assert "Guild override (preempts the env-default at gateway time)" not in field_names


def test_routing_embed_shows_guild_override_when_policy_overrides():
    snap = _snapshot(default_provider="openai", default_model="gpt-4o-mini")
    embed = build_routing_embed(snapshot=snap)
    override = next(
        f
        for f in embed.fields
        if "Guild override" in f.name
    )
    assert "openai" in override.value
    assert "gpt-4o-mini" in override.value


def test_routing_embed_task_filter_still_works(monkeypatch):
    """Pass-through of the task filter is unchanged by PR-4B."""
    snap = _snapshot()
    # Unknown task → "No matching task" field with the known-tasks list.
    embed = build_routing_embed("totally.bogus.task", snapshot=snap)
    field_names = [f.name for f in embed.fields]
    assert "No matching task" in field_names


# ---------------------------------------------------------------------------
# Settings grouping field
# ---------------------------------------------------------------------------


def test_settings_grouping_field_lists_all_groups():
    import discord

    embed = discord.Embed()
    _attach_settings_grouping_field(embed, _snapshot())
    grouping = next(
        f for f in embed.fields if f.name == "Quick reference (by purpose)"
    )
    # Every group label is present in the rendered field.
    for label in (
        "Global baseline",
        "Provider config",
        "Memory config",
        "Access gates",
        "Advanced policy",
    ):
        assert label in grouping.value


def test_settings_grouping_field_renders_override_summary():
    import discord

    embed = discord.Embed()
    _attach_settings_grouping_field(
        embed,
        _snapshot(
            channel_overrides=2,
            category_overrides=1,
            role_overrides=3,
        ),
    )
    grouping = next(
        f for f in embed.fields if f.name == "Quick reference (by purpose)"
    )
    assert "channels: 2" in grouping.value
    assert "categories: 1" in grouping.value
    assert "roles: 3" in grouping.value


def test_settings_grouping_field_tolerates_none_snapshot():
    """When ``snapshot=None``, the grouping field still renders the
    purpose labels — only the scoped-override summary is omitted."""
    import discord

    embed = discord.Embed()
    _attach_settings_grouping_field(embed, None)
    grouping = next(
        f for f in embed.fields if f.name == "Quick reference (by purpose)"
    )
    assert "Global baseline" in grouping.value
    # Scoped-override summary requires the policy slice — omitted on None.
    assert "channels:" not in grouping.value


def test_settings_grouping_schema_order_unchanged():
    """The presentation grouping does not mutate the schema declaration
    order in cogs/ai/schemas.py — pinned by reading the schema directly.
    """
    from cogs.ai.schemas import AI_CONFIG_SCHEMA

    names = [s.name for s in AI_CONFIG_SCHEMA.settings]
    # The first declared setting is `ai_enabled` (the master switch);
    # the presentation grouping puts `ai_enabled` in "Global baseline"
    # but the schema's declaration order is independent.
    assert names[0] == "ai_enabled"
