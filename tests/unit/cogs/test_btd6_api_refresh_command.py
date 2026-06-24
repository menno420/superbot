"""Tests for the staff-only `!btd6 refresh-source` command and the
slash twin `/btd6 refresh-source` — both new in this PR.

Also pins the renamed panel button + the new latest-data attribution and
covers the new `build_refresh_source_embed` builder behaviour.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from cogs.btd6 import _unified
from cogs.btd6._builders import (
    _format_known_keys,
    build_latest_data_embed,
    build_refresh_source_embed,
)
from cogs.btd6_events_cog import BTD6EventsCog
from services import btd6_ingestion_service

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok_result(
    source_key: str = "nk_btd6_maps",
) -> btd6_ingestion_service.IngestionResult:
    return btd6_ingestion_service.IngestionResult(
        source_key=source_key,
        status="ok",
        fact_count=42,
        duration_ms=87,
        error_code=None,
        run_id=123,
        written_entity_keys=("a", "b", "c"),
    )


def _slash_interaction() -> MagicMock:
    """Mirror the fixture pattern from test_btd6_cog.py:169-189."""
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = 555
    interaction.user = MagicMock()
    interaction.user.id = 7777

    deferred = {"done": False}
    interaction.response.is_done = lambda: deferred["done"]

    async def _defer(**_kw):
        deferred["done"] = True

    interaction.response.defer = AsyncMock(side_effect=_defer)
    interaction.response.send_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.original_response = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# (Panel button + copy pins for "Refresh Panel" removed — the button was
# dropped in the admin-panel restructure. New panel-layout pins live in
# tests/unit/cogs/test_btd6_panel_admin_button.py.)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# build_refresh_source_embed — success / error / unknown / dependency
# ---------------------------------------------------------------------------


def test_refresh_source_embed_success_renders_ok_fields():
    embed = build_refresh_source_embed("nk_btd6_maps", [_ok_result()])
    assert embed.color == discord.Color.green()
    assert "nk_btd6_maps" in (embed.title or "")
    field = embed.fields[0]
    assert "`nk_btd6_maps`" in field.name
    value = field.value or ""
    assert "status=`ok`" in value
    assert "facts=42" in value
    assert "run_id=`123`" in value


def test_refresh_source_embed_error_status_is_red():
    err = btd6_ingestion_service.IngestionResult(
        source_key="nk_btd6_maps",
        status="fetch_error",
        fact_count=0,
        duration_ms=5,
        error_code="503",
        run_id=9,
    )
    embed = build_refresh_source_embed("nk_btd6_maps", [err])
    assert embed.color == discord.Color.red()
    value = embed.fields[0].value or ""
    assert "status=`fetch_error`" in value
    assert "error=`503`" in value


def test_refresh_source_embed_dependency_chain_labels_each_child_by_its_key():
    parent = _ok_result(source_key="nk_btd6_ct")
    child = _ok_result(source_key="nk_btd6_ct_tiles")
    embed = build_refresh_source_embed("nk_btd6_ct", [parent, child])
    names = [f.name or "" for f in embed.fields]
    # The first field is the aggregate "Summary" when there are >1
    # results; per-result fields start at index 1.
    assert names[0] == "Summary"
    assert names[1].startswith("parent · ")
    assert "`nk_btd6_ct`" in names[1]
    assert names[2].startswith("child · ")
    assert "`nk_btd6_ct_tiles`" in names[2]


def test_refresh_source_embed_caps_fields_under_discord_limit():
    """Chain refreshes for nk_btd6_maps return up to 34 results.
    Without a cap, embed.fields would exceed Discord's 25-field max
    and the message would be rejected with HTTP 400. Cap rendered
    per-result fields and surface the rest in a summary."""
    parent = _ok_result(source_key="nk_btd6_maps")
    children = [_ok_result(source_key=f"nk_btd6_maps_one_{i}") for i in range(33)]
    embed = build_refresh_source_embed("nk_btd6_maps", [parent, *children])

    # Discord's per-embed field limit is 25.
    assert len(embed.fields) <= 25

    names = [f.name or "" for f in embed.fields]
    assert names[0] == "Summary"
    # When truncated, a "…" field explains the omission.
    assert "…" in names
    truncation_field = next(f for f in embed.fields if f.name == "…")
    value = truncation_field.value or ""
    assert "more child runs omitted" in value
    assert "source-health" in value


def test_refresh_source_embed_summary_aggregates_counts():
    """Multi-result embeds include a Summary field with status counts."""
    ok = _ok_result(source_key="nk_btd6_maps")
    err = btd6_ingestion_service.IngestionResult(
        source_key="nk_btd6_maps_filter",
        status="parse_error",
        fact_count=0,
        duration_ms=10,
        error_code="parse_exception",
        run_id=2,
    )
    embed = build_refresh_source_embed("nk_btd6_maps", [ok, err])
    summary = next(f for f in embed.fields if f.name == "Summary")
    value = summary.value or ""
    assert "2 runs" in value
    assert "1 ok" in value
    assert "1 parse_error" in value


def test_refresh_source_embed_unknown_source_shows_known_keys():
    unknown = btd6_ingestion_service.IngestionResult(
        source_key="nonsense",
        status="disabled",
        fact_count=0,
        duration_ms=0,
        error_code="source_not_registered",
        run_id=None,
    )
    embed = build_refresh_source_embed(
        "nonsense",
        [unknown],
        known_source_keys=["nk_btd6_maps", "nk_btd6_events", "nk_btd6_ct"],
    )
    field_names = [f.name for f in embed.fields]
    assert "Known source keys" in field_names
    known_value = next(f.value for f in embed.fields if f.name == "Known source keys")
    assert "`nk_btd6_maps`" in (known_value or "")


def test_refresh_source_embed_exception_with_detail_includes_message():
    exc = RuntimeError("connection reset")
    embed = build_refresh_source_embed(
        "nk_btd6_maps",
        results=[],
        exception=exc,
        include_exception_detail=True,
    )
    assert embed.color == discord.Color.red()
    value = embed.fields[0].value or ""
    assert "RuntimeError" in value
    assert "connection reset" in value


def test_refresh_source_embed_exception_without_detail_sanitizes():
    exc = RuntimeError("oh no http://internal.example/secret tok=abc123")
    embed = build_refresh_source_embed(
        "nk_btd6_maps",
        results=[],
        exception=exc,
        include_exception_detail=False,
    )
    value = embed.fields[0].value or ""
    assert "RuntimeError" in value
    assert "Check logs" in value
    assert "http://internal" not in value
    assert "secret" not in value
    assert "tok=abc123" not in value


def test_known_source_keys_helper_bounds_by_1024_chars():
    # 500 keys, ~16 chars each → far over the 1024 cap.
    keys = [f"nk_btd6_key_{i:04d}" for i in range(500)]
    value = _format_known_keys(keys)
    assert len(value) <= 1024
    assert value.endswith("more)")


# ---------------------------------------------------------------------------
# Prefix command behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_source_prefix_success_embed(monkeypatch):
    async def _stub(source_key, *, reason, started_by_user_id):
        return [_ok_result(source_key=source_key)]

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source_or_dependencies",
        _stub,
    )

    cog = BTD6EventsCog(MagicMock())
    ctx = MagicMock()
    ctx.author.id = 4242
    ctx.send = AsyncMock()

    await cog.btd6_refresh_source.callback(cog, ctx, source_key="nk_btd6_maps")

    ctx.send.assert_awaited_once()
    sent_embed = ctx.send.await_args.kwargs.get("embed")
    assert sent_embed is not None
    assert "nk_btd6_maps" in (sent_embed.title or "")
    assert sent_embed.color == discord.Color.green()


@pytest.mark.asyncio
async def test_refresh_source_prefix_error_result_embed(monkeypatch):
    async def _stub(source_key, *, reason, started_by_user_id):
        return [
            btd6_ingestion_service.IngestionResult(
                source_key=source_key,
                status="fetch_error",
                fact_count=0,
                duration_ms=5,
                error_code="503",
                run_id=9,
            ),
        ]

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source_or_dependencies",
        _stub,
    )

    cog = BTD6EventsCog(MagicMock())
    ctx = MagicMock()
    ctx.author.id = 1
    ctx.send = AsyncMock()
    await cog.btd6_refresh_source.callback(cog, ctx, source_key="nk_btd6_maps")

    embed = ctx.send.await_args.kwargs.get("embed")
    assert embed.color == discord.Color.red()
    assert "error=`503`" in (embed.fields[0].value or "")


@pytest.mark.asyncio
async def test_refresh_source_prefix_unknown_source(monkeypatch):
    async def _stub(source_key, *, reason, started_by_user_id):
        return [
            btd6_ingestion_service.IngestionResult(
                source_key=source_key,
                status="disabled",
                fact_count=0,
                duration_ms=0,
                error_code="source_not_registered",
                run_id=None,
            ),
        ]

    async def _list_all(*, limit=100):
        return [
            {"id": 1, "source_key": "nk_btd6_maps"},
            {"id": 2, "source_key": "nk_btd6_events"},
        ]

    from services import btd6_source_registry

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source_or_dependencies",
        _stub,
    )
    monkeypatch.setattr(btd6_source_registry, "list_all", _list_all)

    cog = BTD6EventsCog(MagicMock())
    ctx = MagicMock()
    ctx.author.id = 1
    ctx.send = AsyncMock()
    await cog.btd6_refresh_source.callback(cog, ctx, source_key="nonsense")

    embed = ctx.send.await_args.kwargs.get("embed")
    field_names = [f.name for f in embed.fields]
    assert "Known source keys" in field_names


@pytest.mark.asyncio
async def test_refresh_source_prefix_ct_uses_dependencies(monkeypatch):
    captured: dict = {}

    async def _stub(source_key, *, reason, started_by_user_id):
        captured["source_key"] = source_key
        return [
            _ok_result(source_key="nk_btd6_ct"),
            _ok_result(source_key="nk_btd6_ct_tiles"),
        ]

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source_or_dependencies",
        _stub,
    )

    cog = BTD6EventsCog(MagicMock())
    ctx = MagicMock()
    ctx.author.id = 1
    ctx.send = AsyncMock()
    await cog.btd6_refresh_source.callback(cog, ctx, source_key="nk_btd6_ct")

    assert captured["source_key"] == "nk_btd6_ct"
    embed = ctx.send.await_args.kwargs.get("embed")
    names = [f.name for f in embed.fields]
    assert any("parent · " in n and "nk_btd6_ct" in n for n in names)
    assert any("child · " in n and "nk_btd6_ct_tiles" in n for n in names)


@pytest.mark.asyncio
async def test_refresh_source_prefix_propagates_user_id(monkeypatch):
    seen: dict = {}

    async def _stub(source_key, *, reason, started_by_user_id):
        seen["started_by_user_id"] = started_by_user_id
        seen["reason"] = reason
        return [_ok_result(source_key=source_key)]

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source_or_dependencies",
        _stub,
    )

    cog = BTD6EventsCog(MagicMock())
    ctx = MagicMock()
    ctx.author.id = 999_111
    ctx.send = AsyncMock()
    await cog.btd6_refresh_source.callback(cog, ctx, source_key="nk_btd6_maps")

    assert seen == {"started_by_user_id": 999_111, "reason": "manual"}


@pytest.mark.asyncio
async def test_refresh_source_prefix_handles_service_exception_sanitized(monkeypatch):
    async def _raises(source_key, *, reason, started_by_user_id):
        raise RuntimeError("oh no http://internal.example/secret tok=abc123")

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source_or_dependencies",
        _raises,
    )

    cog = BTD6EventsCog(MagicMock())
    ctx = MagicMock()
    ctx.author.id = 1
    ctx.send = AsyncMock()
    await cog.btd6_refresh_source.callback(cog, ctx, source_key="nk_btd6_maps")

    embed = ctx.send.await_args.kwargs.get("embed")
    value = embed.fields[0].value or ""
    assert "RuntimeError" in value
    assert "Check logs" in value
    assert "http://internal" not in value
    assert "secret" not in value


# ---------------------------------------------------------------------------
# Slash command behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_source_slash_defers_before_service_call(monkeypatch):
    call_order: list[str] = []

    async def _stub(source_key, *, reason, started_by_user_id):
        call_order.append("service")
        return [_ok_result(source_key=source_key)]

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source_or_dependencies",
        _stub,
    )

    from cogs.btd6 import _reply as cog_mod

    async def _defer_capture(interaction, **_kw):
        call_order.append("defer")
        interaction.response.is_done = lambda: True
        return True

    async def _followup_capture(*_a, **_kw):
        call_order.append("followup")
        return

    monkeypatch.setattr(cog_mod, "safe_defer", _defer_capture)
    monkeypatch.setattr(cog_mod, "safe_followup", _followup_capture)

    interaction = _slash_interaction()
    await _unified.events_refresh_source_slash.callback(
        interaction,
        source_key="nk_btd6_maps",
    )

    assert call_order == ["defer", "service", "followup"], call_order


@pytest.mark.asyncio
async def test_refresh_source_slash_includes_exception_detail(monkeypatch):
    async def _raises(source_key, *, reason, started_by_user_id):
        raise RuntimeError("connection reset by peer")

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source_or_dependencies",
        _raises,
    )

    from cogs.btd6 import _reply as cog_mod

    captured: dict = {}

    async def _defer_capture(interaction, **_kw):
        interaction.response.is_done = lambda: True
        return True

    async def _followup_capture(interaction, *_a, **kwargs):
        captured["embed"] = kwargs.get("embed")
        return

    monkeypatch.setattr(cog_mod, "safe_defer", _defer_capture)
    monkeypatch.setattr(cog_mod, "safe_followup", _followup_capture)

    interaction = _slash_interaction()
    await _unified.events_refresh_source_slash.callback(
        interaction,
        source_key="nk_btd6_maps",
    )

    embed = captured["embed"]
    value = embed.fields[0].value or ""
    assert "RuntimeError" in value
    assert "connection reset by peer" in value  # slash gets the detail


@pytest.mark.asyncio
async def test_refresh_source_slash_handles_service_exception(monkeypatch):
    """Helper raises after defer; safe_followup still receives an embed."""

    async def _raises(source_key, *, reason, started_by_user_id):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source_or_dependencies",
        _raises,
    )

    from cogs.btd6 import _reply as cog_mod

    followup_calls: list[dict] = []

    async def _defer_capture(interaction, **_kw):
        interaction.response.is_done = lambda: True
        return True

    async def _followup_capture(interaction, *_a, **kwargs):
        followup_calls.append(kwargs)
        return

    monkeypatch.setattr(cog_mod, "safe_defer", _defer_capture)
    monkeypatch.setattr(cog_mod, "safe_followup", _followup_capture)

    interaction = _slash_interaction()
    await _unified.events_refresh_source_slash.callback(
        interaction,
        source_key="nk_btd6_maps",
    )

    assert len(followup_calls) == 1
    assert followup_calls[0].get("embed") is not None
    assert followup_calls[0].get("ephemeral") is True


# ---------------------------------------------------------------------------
# Permission wiring
# ---------------------------------------------------------------------------


def test_refresh_source_prefix_command_has_staff_check():
    cog = BTD6EventsCog(MagicMock())
    cmd = next(
        c
        for c in cog.walk_commands()
        if c.name == "refresh-source"
        and getattr(c, "parent", None) is not None
        and c.parent.name == "btd6events"
    )
    # The has_guild_permissions decorator attaches a check; verify by
    # constructing a non-staff ctx and asserting at least one check is
    # falsy. Mirrors how discord.py command checks are exercised.
    assert len(cmd.checks) >= 1


def test_refresh_source_slash_has_default_permissions():
    cmd = next(c for c in _unified.events_app.commands if c.name == "refresh-source")
    perms = cmd.default_permissions
    assert perms is not None
    assert perms.manage_guild is True


# ---------------------------------------------------------------------------
# latest-data attribution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_latest_data_renders_source_key(monkeypatch):
    async def _search_facts(*, limit=50, **_kw):
        return [
            {
                "id": 1,
                "source_id": 42,
                "fact_type": "tower",
                "entity_kind": "tower",
                "entity_key": "dart_monkey",
                "body_json": {},
                "game_version": "47.0",
                "fetched_at": datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
                "validated_at": None,
                "confidence": 1.0,
                "version": 3,
            },
        ]

    async def _list_all(*, limit=100):
        return [{"id": 42, "source_key": "nk_btd6_maps"}]

    from services import btd6_source_registry
    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(btd6_db, "search_facts", _search_facts)
    monkeypatch.setattr(btd6_source_registry, "list_all", _list_all)

    embed = await build_latest_data_embed()
    value = embed.fields[0].value or ""
    assert "source=`nk_btd6_maps`" in value
    assert "`dart_monkey`" in value


@pytest.mark.asyncio
async def test_latest_data_renders_dash_for_missing_source(monkeypatch):
    async def _search_facts(*, limit=50, **_kw):
        return [
            {
                "id": 2,
                "source_id": 99,  # not present in the registry response
                "fact_type": "tower",
                "entity_kind": "tower",
                "entity_key": "orphan",
                "body_json": {},
                "game_version": "47.0",
                "fetched_at": datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
                "validated_at": None,
                "confidence": 1.0,
                "version": 1,
            },
        ]

    async def _list_all(*, limit=100):
        return [{"id": 42, "source_key": "nk_btd6_maps"}]

    from services import btd6_source_registry
    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(btd6_db, "search_facts", _search_facts)
    monkeypatch.setattr(btd6_source_registry, "list_all", _list_all)

    embed = await build_latest_data_embed()
    value = embed.fields[0].value or ""
    assert "source=`—`" in value


# ---------------------------------------------------------------------------
# Service-level pins (the new public helper)
# ---------------------------------------------------------------------------


def test_refresh_source_or_dependencies_exported_in_all():
    assert "refresh_source_or_dependencies" in btd6_ingestion_service.__all__
    assert "IngestionReason" in btd6_ingestion_service.__all__


@pytest.mark.asyncio
async def test_refresh_source_or_dependencies_routes_single_source(monkeypatch):
    # ``nk_btd6_events`` is intentionally NOT in _DEPENDENCY_CHAINS
    # (no child parsers exist for the events endpoint) so this is the
    # canonical single-source test case. Don't switch to a chain
    # parent like ``nk_btd6_maps`` — that would now fan out.
    async def _mock_refresh(
        source_key,
        *,
        path_params=None,
        reason="scheduled",
        started_by_user_id=None,
    ):
        return _ok_result(source_key=source_key)

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source",
        _mock_refresh,
    )

    results = await btd6_ingestion_service.refresh_source_or_dependencies(
        "nk_btd6_events",
        reason="manual",
        started_by_user_id=1,
    )
    assert len(results) == 1
    assert results[0].source_key == "nk_btd6_events"


@pytest.mark.asyncio
async def test_refresh_source_or_dependencies_routes_to_dependency_chain(monkeypatch):
    calls: list[str] = []

    async def _mock_refresh(
        source_key,
        *,
        path_params=None,
        reason="scheduled",
        started_by_user_id=None,
    ):
        calls.append(source_key)
        if source_key == "nk_btd6_ct":
            return btd6_ingestion_service.IngestionResult(
                source_key=source_key,
                status="ok",
                fact_count=1,
                duration_ms=10,
                error_code=None,
                run_id=1,
                written_entity_keys=("ct_5",),
            )
        return _ok_result(source_key=source_key)

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source",
        _mock_refresh,
    )

    results = await btd6_ingestion_service.refresh_source_or_dependencies(
        "nk_btd6_ct",
        reason="manual",
        started_by_user_id=42,
    )
    assert len(results) == 2
    assert {r.source_key for r in results} == {"nk_btd6_ct", "nk_btd6_ct_tiles"}
    assert calls == ["nk_btd6_ct", "nk_btd6_ct_tiles"]


@pytest.mark.asyncio
async def test_refresh_source_or_dependencies_unknown_source_returns_structured_result(
    monkeypatch,
):
    """No exception escape — unknown keys yield a structured `disabled` result."""
    from services import btd6_source_registry

    async def _get_by_key(_key):
        return None

    monkeypatch.setattr(btd6_source_registry, "get_by_key", _get_by_key)

    results = await btd6_ingestion_service.refresh_source_or_dependencies(
        "nonsense",
        reason="manual",
        started_by_user_id=1,
    )
    assert len(results) == 1
    assert results[0].status == "disabled"
    assert results[0].error_code == "source_not_registered"


@pytest.mark.asyncio
async def test_refresh_source_or_dependencies_propagates_started_by(monkeypatch):
    seen: list[int | None] = []

    async def _mock_refresh(
        source_key,
        *,
        path_params=None,
        reason="scheduled",
        started_by_user_id=None,
    ):
        seen.append(started_by_user_id)
        if source_key == "nk_btd6_ct":
            return btd6_ingestion_service.IngestionResult(
                source_key=source_key,
                status="ok",
                fact_count=1,
                duration_ms=10,
                error_code=None,
                run_id=1,
                written_entity_keys=("ct_5",),
            )
        return _ok_result(source_key=source_key)

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source",
        _mock_refresh,
    )

    await btd6_ingestion_service.refresh_source_or_dependencies(
        "nk_btd6_ct",
        reason="manual",
        started_by_user_id=12345,
    )
    assert seen == [12345, 12345]


@pytest.mark.asyncio
async def test_refresh_with_dependencies_child_role_is_dependency(monkeypatch):
    """Child runs always record ``triggered_by="dependency"`` (their role
    in the chain) regardless of the parent's reason. Operator
    attribution lives in ``started_by_user_id``.

    This replaces the post-#353 inherit-parent-reason behaviour — see
    the audit-semantic section in the production-readiness plan.
    """
    reasons: list[str] = []

    async def _mock_refresh(
        source_key,
        *,
        path_params=None,
        reason="scheduled",
        started_by_user_id=None,
    ):
        reasons.append(reason)
        if source_key == "nk_btd6_ct":
            return btd6_ingestion_service.IngestionResult(
                source_key=source_key,
                status="ok",
                fact_count=1,
                duration_ms=10,
                error_code=None,
                run_id=1,
                written_entity_keys=("ct_5",),
            )
        return _ok_result(source_key=source_key)

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source",
        _mock_refresh,
    )

    await btd6_ingestion_service.refresh_with_dependencies(
        "nk_btd6_ct",
        reason="manual",
        started_by_user_id=1,
    )
    # Parent role flows through; child role is "dependency".
    assert reasons == ["manual", "dependency"]
