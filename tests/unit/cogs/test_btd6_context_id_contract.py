"""Regression contract: every VM and stable-content embed surfaces a context_id.

Two assertions:

1. Every VM builder returns a view-model whose ``context.context_id``
   matches the contract regex ``^btd6_[a-z_]+:[A-Za-z0-9_-]+$``.
2. Every embed in the documented allowlist carries a
   ``ctx=<context_id>`` segment in its footer. Embeds in the
   exclusion list (transient operational / debug) intentionally
   omit the footer.

The allowlist + exclusion list are defined in this file. Renaming or
adding an embed without updating one of the lists is an explicit
test failure — surface the contract gap rather than silently drift.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from services.btd6_view_model_service import make_context_handle

CONTEXT_ID_RE = re.compile(r"^btd6_[a-z_]+:[A-Za-z0-9_-]+$")
FOOTER_CTX_RE = re.compile(r"(?: • )?ctx=(btd6_[a-z_]+:[A-Za-z0-9_-]+)")


# ---------------------------------------------------------------------------
# Allowlist — every embed below MUST carry a context_id footer.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_panel_embed_carries_context_id(monkeypatch) -> None:
    from services import btd6_knowledge_service
    from utils.db import btd6_sources as btd6_db
    from views.btd6.panel import build_btd6_panel_embed

    monkeypatch.setattr(
        btd6_db,
        "latest_fact_per_entity_kind",
        AsyncMock(return_value={}),
    )
    # Hub VM now also calls get_active_events → search_facts.
    monkeypatch.setattr(btd6_db, "search_facts", AsyncMock(return_value=[]))
    monkeypatch.setattr(btd6_knowledge_service, "data_version", lambda: "1.0")
    monkeypatch.setattr(btd6_knowledge_service, "game_version", lambda: "42.0")
    monkeypatch.setattr(btd6_knowledge_service, "list_towers", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_heroes", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_maps", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_modes", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_rounds", lambda: [])

    embed = await build_btd6_panel_embed()
    match = FOOTER_CTX_RE.search(embed.footer.text or "")
    assert match, "panel embed footer missing ctx= marker"
    assert match.group(1) == "btd6_hub:main"


@pytest.mark.asyncio
async def test_status_embed_carries_context_id(monkeypatch) -> None:
    from cogs.btd6._embeds import build_status_embed
    from services import btd6_knowledge_service

    monkeypatch.setattr(btd6_knowledge_service, "data_version", lambda: "1.0")
    monkeypatch.setattr(btd6_knowledge_service, "game_version", lambda: "42.0")
    monkeypatch.setattr(btd6_knowledge_service, "list_towers", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_heroes", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_maps", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_modes", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_rounds", lambda: [])
    monkeypatch.setattr(
        btd6_knowledge_service,
        "fact_summary_by_kind",
        AsyncMock(return_value=()),
    )
    embed = await build_status_embed()
    match = FOOTER_CTX_RE.search(embed.footer.text or "")
    assert match, "status embed footer missing ctx= marker"
    assert match.group(1) == "btd6_status:global"


@pytest.mark.asyncio
async def test_source_health_embed_carries_context_id(monkeypatch) -> None:
    from cogs.btd6._builders import build_source_health_embed
    from services import btd6_source_registry

    monkeypatch.setattr(
        btd6_source_registry,
        "list_health",
        AsyncMock(return_value=[]),
    )
    embed = await build_source_health_embed()
    match = FOOTER_CTX_RE.search(embed.footer.text or "")
    assert match, "source health embed footer missing ctx= marker"
    assert match.group(1) == "btd6_diagnostics:sources"


@pytest.mark.asyncio
async def test_latest_data_embed_carries_context_id(monkeypatch) -> None:
    from cogs.btd6._builders import build_latest_data_embed
    from services import btd6_source_registry
    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(btd6_db, "search_facts", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        btd6_source_registry,
        "list_all",
        AsyncMock(return_value=[]),
    )
    embed = await build_latest_data_embed()
    match = FOOTER_CTX_RE.search(embed.footer.text or "")
    assert match, "latest data embed footer missing ctx= marker"
    assert match.group(1) == "btd6_diagnostics:latest_data"


@pytest.mark.asyncio
async def test_live_events_embed_carries_context_id(monkeypatch) -> None:
    from cogs.btd6._builders import build_live_events_embed
    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(btd6_db, "search_facts", AsyncMock(return_value=[]))
    embed = await build_live_events_embed("race")
    match = FOOTER_CTX_RE.search(embed.footer.text or "")
    assert match, "live events embed footer missing ctx= marker"
    assert match.group(1) == "btd6_race:list"


def test_event_detail_embed_carries_context_id() -> None:
    from cogs.btd6._builders import build_event_detail_embed

    now = datetime.now(tz=timezone.utc)
    row = {
        "entity_kind": "btd6_race",
        "entity_key": "R42",
        "body_json": {"name": "Reversed Loop", "start_ms": 1, "end_ms": 2**40},
        "fetched_at": now,
    }
    embed = build_event_detail_embed("btd6_race", "R42", row=row)
    match = FOOTER_CTX_RE.search(embed.footer.text or "")
    assert match, "event detail embed footer missing ctx= marker"
    assert match.group(1) == "btd6_race:R42"


# ---------------------------------------------------------------------------
# VM builders — context_id matches regex
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hub_view_model_context_id(monkeypatch) -> None:
    from services import btd6_knowledge_service
    from services.btd6_view_model_service import build_hub_view_model
    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(
        btd6_db,
        "latest_fact_per_entity_kind",
        AsyncMock(return_value={}),
    )
    monkeypatch.setattr(btd6_db, "search_facts", AsyncMock(return_value=[]))
    monkeypatch.setattr(btd6_knowledge_service, "data_version", lambda: "1.0")
    monkeypatch.setattr(btd6_knowledge_service, "game_version", lambda: "42.0")
    monkeypatch.setattr(btd6_knowledge_service, "list_towers", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_heroes", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_maps", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_modes", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_rounds", lambda: [])

    vm = await build_hub_view_model()
    assert CONTEXT_ID_RE.match(vm.context.context_id)


def test_make_context_handle_round_trips_every_type() -> None:
    """Every BTD6ContextType produces a regex-matching context_id."""
    for ctx_type in (
        "hub",
        "race",
        "boss",
        "ct",
        "ct_relic",
        "odyssey",
        "event",
        "tower",
        "hero",
        "leaderboard",
        "strategy",
        "source",
        "status",
        "diagnostics",
    ):
        handle = make_context_handle(ctx_type, "test_key_42")  # type: ignore[arg-type]
        assert CONTEXT_ID_RE.match(handle.context_id), (
            f"context_id {handle.context_id!r} for type {ctx_type!r} "
            f"does not match the contract regex"
        )


# ---------------------------------------------------------------------------
# Exclusion list — every embed below intentionally OMITS the footer.
# ---------------------------------------------------------------------------


def test_refresh_summary_embed_omits_context_id() -> None:
    """Transient operational embed — no Team Panel attach target."""
    from cogs.btd6._builders import build_admin_refresh_summary_embed

    embed = build_admin_refresh_summary_embed([])
    text = embed.footer.text or ""
    assert "ctx=" not in text, (
        "Refresh summary embed should NOT carry a context_id footer — "
        "it's a transient operation result, not a stable entity."
    )
