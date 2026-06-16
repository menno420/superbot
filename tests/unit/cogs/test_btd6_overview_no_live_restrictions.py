"""Tower / hero *overview* embeds must not dump live event restrictions.

Live-tested bug: ``!btd6 tower <name>`` and ``!btd6 hero <name>`` rendered a
"Live data" field stuffed with every active race / odyssey / challenge ban for
that tower (dozens of lines). That belongs in the dedicated ⚠️ Event-status
drill-down, not the overview — the tower *browser* detail already documents
this ("keep it uncluttered"); the prefix/slash builders and the hero browser
detail were the stragglers. These guards pin the decision: the overview
builders never consult the event-restriction service, so no "Live data" field
appears regardless of what events are live.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from cogs.btd6._builders import build_hero_embed, build_tower_embed


def _field_names(embed) -> list[str]:
    return [f.name for f in embed.fields]


@pytest.mark.asyncio
async def test_tower_overview_has_no_live_data_field() -> None:
    with patch(
        "services.btd6_live_query_service.get_active_event_restrictions_for_tower",
        new=AsyncMock(return_value=()),
    ) as scan:
        embed = await build_tower_embed("dart monkey")
    assert "Live data" not in _field_names(embed)
    scan.assert_not_awaited()


@pytest.mark.asyncio
async def test_hero_overview_has_no_live_data_field() -> None:
    with patch(
        "services.btd6_live_query_service.get_active_event_restrictions_for_hero",
        new=AsyncMock(return_value=()),
    ) as scan:
        embed = await build_hero_embed("quincy")
    assert "Live data" not in _field_names(embed)
    scan.assert_not_awaited()
