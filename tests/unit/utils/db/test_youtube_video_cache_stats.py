"""Unit test pinning the content-free contract of get_cache_stats.

P0-2 / Q-0099 follow-up: the cache-health aggregate query must never *return*
provider content.  ``transcript_text`` may appear only inside a
``... IS NOT NULL`` count predicate (a null-check that returns an integer, not
content); ``metadata_json`` / ``video_id`` / content fields must not appear at
all.  This guards against a future edit accidentally selecting a content column
into the operator diagnostic.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from utils.db import youtube_video_cache as cache  # noqa: E402


async def test_get_cache_stats_query_is_content_free(monkeypatch):
    captured: dict[str, str] = {}

    async def _fetchrow(sql, *args):
        captured["sql"] = sql
        return {}

    fake_conn = MagicMock()
    fake_conn.fetchrow = AsyncMock(side_effect=_fetchrow)
    monkeypatch.setattr(cache.pool, "get", lambda: fake_conn)

    await cache.get_cache_stats()

    sql = captured["sql"]
    # Raw metadata is never referenced at all.
    assert "metadata_json" not in sql
    # video_id (an identifier, not aggregate) is never selected.
    assert "video_id" not in sql
    # transcript_text appears only in the IS NOT NULL count predicate, once.
    assert sql.count("transcript_text") == 1
    assert "transcript_text IS NOT NULL" in sql


async def test_get_cache_stats_returns_dict(monkeypatch):
    fake_conn = MagicMock()
    fake_conn.fetchrow = AsyncMock(return_value={"total_rows": 0})
    monkeypatch.setattr(cache.pool, "get", lambda: fake_conn)

    result = await cache.get_cache_stats()
    assert result == {"total_rows": 0}
