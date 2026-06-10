"""Diagnostic panel data-source fixes (live-audit 2026-06-05).

- "Recent Errors / Recent Logs" reads an in-memory ring buffer instead of the
  legacy ``logs`` DB table (which nothing ever wrote to → always "No logs
  found").
- "Database Schema Check" reports migrations-applied N/N + base tables instead
  of a hard-coded "expected tables" list (which flagged every migration-added
  table as "unexpected").
"""

from __future__ import annotations

import logging

import pytest


def test_log_buffer_captures_and_filters_by_level():
    from cogs.diagnostic import _log_buffer

    _log_buffer._reset_for_tests()
    _log_buffer.install()  # idempotent

    log = logging.getLogger("bot.test_log_buffer")
    log.setLevel(logging.DEBUG)
    log.error("ring-buffer boom")
    log.info("ring-buffer info")

    errors = _log_buffer.recent(level="ERROR", limit=10)
    assert errors and errors[0]["level"] == "ERROR"
    assert any("ring-buffer boom" in r["message"] for r in errors)
    assert all(r["level"] == "ERROR" for r in errors)

    everything = _log_buffer.recent(limit=10)
    assert any("ring-buffer info" in r["message"] for r in everything)


@pytest.mark.asyncio
async def test_query_logs_embed_reads_ring_buffer():
    from cogs.diagnostic import _helpers, _log_buffer

    _log_buffer._reset_for_tests()
    _log_buffer.install()
    logging.getLogger("bot.test_query_logs").error("a query_logs error")

    embed = await _helpers.build_query_logs_embed(event_type="ERROR", limit=10)
    blob = (embed.description or "") + " ".join(
        f"{f.name} {f.value}" for f in embed.fields
    )
    assert "a query_logs error" in blob


@pytest.mark.asyncio
async def test_check_database_embed_uses_migrations_not_expected_list(monkeypatch):
    from cogs.diagnostic import _helpers
    from utils.db.migrations import migration_versions_on_disk

    on_disk = migration_versions_on_disk()
    assert on_disk  # sanity: the migration files exist and parse

    base = {
        "economy",
        "job_progress",
        "inventory",
        "xp",
        "warnings",
        "mod_logs",
        "role_thresholds",
        "guild_settings",
        "logs",
        "reaction_roles",
        "rps_players",
        "mining_inventory",
        "prohibited_words",
        "deathmatch_stats",
        "chain_channels",
        "counting_state",
    }

    import utils.db.migrations as migrations_db

    async def fake_tables():
        # base tables + a migration-added table that used to read "unexpected"
        return base | {"role_automation_exemptions"}

    async def fake_applied():
        return set(on_disk)

    monkeypatch.setattr(migrations_db, "list_public_tables", fake_tables)
    monkeypatch.setattr(migrations_db, "applied_migration_versions", fake_applied)

    embed = await _helpers.build_check_database_embed()
    names = [f.name for f in embed.fields]
    # The stale "Unexpected Tables" field is gone; the check is migration-based.
    assert not any("Unexpected" in n for n in names)
    assert any("Migrations applied" in n for n in names)
    assert any("Base tables" in n for n in names)
    assert "healthy" in (embed.description or "").lower()
