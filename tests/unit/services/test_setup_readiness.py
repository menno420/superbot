"""Unit tests for :mod:`services.setup_readiness` (PR H).

Pins:

* ``collect`` walks every registered subsystem schema; subsystems
  with no bindings/settings get ``score=None`` so they don't drag
  the aggregate.
* Each subsystem's score is ``(bound + configured) / (declared
  bindings + declared settings)``.
* Aggregate score is the unweighted mean of per-subsystem scores
  that are not ``None``.
* A setting counts as configured only when:
  - the stored value is non-empty, AND
  - the stored value differs from the spec's default, AND
  - the spec has a non-empty ``settings_key`` (legacy KV migration).
* A binding counts as bound when ``subsystem_bindings`` has a row
  whose status is anything other than the sentinel "cleared"/"error"
  states.
* The shared embed renderer produces an operator-readable summary
  including the aggregate percentage and per-subsystem lines.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SettingSpec,
    SubsystemSchema,
    _reset_for_tests,
    register,
)
from services import setup_readiness


@pytest.fixture(autouse=True)
def _isolated_schema_registry():
    """Each test owns the schema registry. Reset before + after.

    The real registry is populated by ``cog_load`` hooks across the
    bot; isolated tests need a clean slate so they assert only on
    what they declare.
    """
    _reset_for_tests()
    yield
    _reset_for_tests()


def _register_subsystem(
    name: str,
    *,
    bindings: list[tuple[str, BindingKind]] | None = None,
    settings: list[tuple[str, str, str | int | bool]] | None = None,
) -> None:
    """Register a minimal :class:`SubsystemSchema` for the test.

    ``bindings`` is a list of ``(binding_name, kind)`` tuples;
    ``settings`` is ``(name, settings_key, default)`` tuples.
    """
    binding_specs = tuple(
        BindingSpec(
            name=bn,
            kind=kind,
            required=False,
            hint="",
            capability_required=f"{name}.test.bind",
        )
        for bn, kind in (bindings or [])
    )
    setting_specs = tuple(
        SettingSpec(
            name=sn,
            value_type=type(default),
            default=default,
            settings_key=key,
            capability_required=f"{name}.test.set",
            hint="",
        )
        for sn, key, default in (settings or [])
    )
    register(
        SubsystemSchema(
            subsystem=name,
            bindings=binding_specs,
            settings=setting_specs,
        ),
    )


# ---------------------------------------------------------------------------
# collect — registry walk + per-subsystem scoring
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_collect_empty_registry_returns_none_score():
    """No registered schemas — no scores. Should not divide-by-zero."""
    with patch(
        "services.setup_readiness.db_bindings.list_for_guild",
        new_callable=AsyncMock,
        return_value=[],
    ):
        report = await setup_readiness.collect(guild_id=42)
    assert report.aggregate_score is None
    assert report.per_subsystem == ()
    assert report.percentage == 0


@pytest.mark.asyncio
async def test_subsystem_with_no_config_has_none_score():
    """Subsystems declaring no bindings/settings get ``score=None``."""
    _register_subsystem("empty_sub")
    with patch(
        "services.setup_readiness.db_bindings.list_for_guild",
        new_callable=AsyncMock,
        return_value=[],
    ):
        report = await setup_readiness.collect(guild_id=42)
    assert len(report.per_subsystem) == 1
    entry = report.per_subsystem[0]
    assert entry.subsystem == "empty_sub"
    assert entry.score is None
    assert entry.has_config is False
    # Empty-config subsystem does NOT drag the aggregate down.
    assert report.aggregate_score is None


@pytest.mark.asyncio
async def test_all_bound_all_configured_scores_full():
    """A subsystem with every binding bound and every setting
    configured scores 1.0 (100%).
    """
    _register_subsystem(
        "fully_ready",
        bindings=[("announce_channel", BindingKind.CHANNEL)],
        settings=[("threshold", "fully_ready.threshold", 3)],
    )

    binding_rows = [
        {
            "subsystem": "fully_ready",
            "binding_name": "announce_channel",
            "status": "active",
        },
    ]
    with patch(
        "services.setup_readiness.db_bindings.list_for_guild",
        new_callable=AsyncMock,
        return_value=binding_rows,
    ), patch(
        "services.setup_readiness.db.get_setting",
        new_callable=AsyncMock,
        # Non-default value — stored "10" differs from default 3.
        return_value="10",
    ):
        report = await setup_readiness.collect(guild_id=42)

    entry = report.per_subsystem[0]
    assert entry.bindings_bound == 1
    assert entry.settings_configured == 1
    assert entry.score == 1.0
    assert report.percentage == 100


@pytest.mark.asyncio
async def test_partial_fill_scores_half():
    """Two declared, one filled → 0.5."""
    _register_subsystem(
        "half_ready",
        bindings=[("log_channel", BindingKind.CHANNEL)],
        settings=[("interval", "half_ready.interval", 5)],
    )
    # Binding is bound but the setting is unset (stored "" — default).
    with patch(
        "services.setup_readiness.db_bindings.list_for_guild",
        new_callable=AsyncMock,
        return_value=[
            {
                "subsystem": "half_ready",
                "binding_name": "log_channel",
                "status": "active",
            },
        ],
    ), patch(
        "services.setup_readiness.db.get_setting",
        new_callable=AsyncMock,
        return_value="",
    ):
        report = await setup_readiness.collect(guild_id=42)
    entry = report.per_subsystem[0]
    assert entry.bindings_bound == 1
    assert entry.settings_configured == 0
    assert entry.score == 0.5


@pytest.mark.asyncio
async def test_setting_equal_to_default_does_not_count_as_configured():
    """A stored value that matches the spec's default is treated as
    'not yet customized' so the score reflects operator intent.
    """
    _register_subsystem(
        "default_setting",
        settings=[("ttl", "default_setting.ttl", 60)],
    )
    with patch(
        "services.setup_readiness.db_bindings.list_for_guild",
        new_callable=AsyncMock,
        return_value=[],
    ), patch(
        "services.setup_readiness.db.get_setting",
        new_callable=AsyncMock,
        # Stored value matches the default repr.
        return_value="60",
    ):
        report = await setup_readiness.collect(guild_id=42)
    assert report.per_subsystem[0].settings_configured == 0


@pytest.mark.asyncio
async def test_setting_with_empty_key_never_counts_as_configured():
    """SettingSpec with empty ``settings_key`` cannot be looked up via
    the legacy KV — treat it as un-configured and surface as a known
    migration gap.
    """
    _register_subsystem(
        "unmigrated",
        settings=[("legacy_thing", "", "default")],
    )
    with patch(
        "services.setup_readiness.db_bindings.list_for_guild",
        new_callable=AsyncMock,
        return_value=[],
    ), patch(
        "services.setup_readiness.db.get_setting",
        new_callable=AsyncMock,
        return_value="something",
    ):
        report = await setup_readiness.collect(guild_id=42)
    assert report.per_subsystem[0].settings_configured == 0


@pytest.mark.asyncio
async def test_cleared_binding_status_does_not_count_as_bound():
    """Bindings with cleared/error status are audit residue, not
    satisfied slots. They should NOT count toward the score.
    """
    _register_subsystem(
        "with_cleared_binding",
        bindings=[("ch", BindingKind.CHANNEL)],
    )
    with patch(
        "services.setup_readiness.db_bindings.list_for_guild",
        new_callable=AsyncMock,
        return_value=[
            {
                "subsystem": "with_cleared_binding",
                "binding_name": "ch",
                "status": "cleared",
            },
        ],
    ), patch(
        "services.setup_readiness.db.get_setting",
        new_callable=AsyncMock,
        return_value="",
    ):
        report = await setup_readiness.collect(guild_id=42)
    assert report.per_subsystem[0].bindings_bound == 0


@pytest.mark.asyncio
async def test_aggregate_score_excludes_subsystems_without_config():
    """The aggregate averages only subsystems with declared
    bindings/settings — empty-config subsystems don't drag it down.
    """
    _register_subsystem("empty_sub")
    _register_subsystem(
        "scored_sub",
        bindings=[("ch", BindingKind.CHANNEL)],
        settings=[("x", "scored_sub.x", 1)],
    )
    with patch(
        "services.setup_readiness.db_bindings.list_for_guild",
        new_callable=AsyncMock,
        return_value=[
            {"subsystem": "scored_sub", "binding_name": "ch", "status": "active"},
        ],
    ), patch(
        "services.setup_readiness.db.get_setting",
        new_callable=AsyncMock,
        return_value="42",  # non-default
    ):
        report = await setup_readiness.collect(guild_id=42)
    # scored_sub: 1.0 (1/1 + 1/1). empty_sub: None.
    # Aggregate = mean([1.0]) = 1.0 — empty_sub excluded.
    assert report.aggregate_score == 1.0


@pytest.mark.asyncio
async def test_report_totals_aggregate_across_subsystems():
    """``ReadinessReport`` totals are sums across all subsystems."""
    _register_subsystem(
        "a",
        bindings=[("ch1", BindingKind.CHANNEL), ("ch2", BindingKind.CHANNEL)],
    )
    _register_subsystem(
        "b",
        settings=[
            ("s1", "b.s1", 10),
            ("s2", "b.s2", 20),
            ("s3", "b.s3", 30),
        ],
    )
    with patch(
        "services.setup_readiness.db_bindings.list_for_guild",
        new_callable=AsyncMock,
        return_value=[
            {"subsystem": "a", "binding_name": "ch1", "status": "active"},
        ],
    ), patch(
        "services.setup_readiness.db.get_setting",
        new_callable=AsyncMock,
        return_value="",
    ):
        report = await setup_readiness.collect(guild_id=42)
    assert report.bindings_declared == 2
    assert report.bindings_bound == 1
    assert report.settings_declared == 3
    assert report.settings_configured == 0


# ---------------------------------------------------------------------------
# Embed renderer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_setup_readiness_embed_includes_percentage_in_title():
    from cogs.diagnostic._platform_embeds import build_setup_readiness_embed

    _register_subsystem(
        "scored",
        bindings=[("ch", BindingKind.CHANNEL)],
    )
    with patch(
        "services.setup_readiness.db_bindings.list_for_guild",
        new_callable=AsyncMock,
        return_value=[
            {"subsystem": "scored", "binding_name": "ch", "status": "active"},
        ],
    ), patch(
        "services.setup_readiness.db.get_setting",
        new_callable=AsyncMock,
        return_value="",
    ):
        embed = await build_setup_readiness_embed(guild_id=42)
    assert "100%" in (embed.title or "")


@pytest.mark.asyncio
async def test_build_setup_readiness_embed_handles_empty_registry():
    from cogs.diagnostic._platform_embeds import build_setup_readiness_embed

    with patch(
        "services.setup_readiness.db_bindings.list_for_guild",
        new_callable=AsyncMock,
        return_value=[],
    ):
        embed = await build_setup_readiness_embed(guild_id=42)
    # No score — title shows the em-dash.
    assert "—" in (embed.title or "")
    # And the embed explicitly surfaces the "no schemas" message.
    field_values = "\n".join(f.value or "" for f in embed.fields)
    assert "subsystem_schema.register" in field_values
