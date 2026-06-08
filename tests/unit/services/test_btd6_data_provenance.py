"""DataProvenance, FactRow, and extract_provenance — unit tests.

Covers the provenance contract defined in
``docs/btd6/btd6-provenance-schema.md`` (RC-10 gate PR).
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services.btd6_fact_store import DataProvenance  # noqa: E402
from services.btd6_fact_store import FactRow  # noqa: E402
from services.btd6_fact_store import extract_provenance  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _ts(hours_ago: float = 0) -> datetime:
    return datetime.now(tz=timezone.utc) - timedelta(hours=hours_ago)


def _row(
    *,
    source_id: int = 1,
    source_key: str = "nk_btd6_races",
    source_name: str = "data.ninjakiwi.com",
    source_kind: str = "official_api",
    trust_tier: int = 1,
    fetched_at: datetime | None = None,
    game_version: str | None = "43.0",
    fact_type: str = "btd6.race_metadata",
    entity_kind: str = "btd6_race",
    entity_key: str = "test_race",
    body_json: dict | None = None,
    confidence: float = 1.0,
    version: int = 1,
) -> dict:
    return {
        "id": 42,
        "source_id": source_id,
        "source_key": source_key,
        "source_name": source_name,
        "source_kind": source_kind,
        "trust_tier": trust_tier,
        "fetched_at": fetched_at or _ts(1),
        "game_version": game_version,
        "fact_type": fact_type,
        "entity_kind": entity_kind,
        "entity_key": entity_key,
        "body_json": body_json or {"name": entity_key},
        "confidence": confidence,
        "version": version,
        "validated_at": None,
    }


# ---------------------------------------------------------------------------
# DataProvenance
# ---------------------------------------------------------------------------


def test_extract_provenance_populates_all_fields():
    ts = _ts(12)  # 12 h ago → aging (fresh < 6 h, aging < 48 h)
    p = extract_provenance(_row(
        source_id=7,
        source_key="nk_btd6_races",
        source_name="data.ninjakiwi.com",
        source_kind="official_api",
        trust_tier=1,
        fetched_at=ts,
        game_version="43.0",
    ))
    assert p.source_id == 7
    assert p.source_key == "nk_btd6_races"
    assert p.source_name == "data.ninjakiwi.com"
    assert p.source_kind == "official_api"
    assert p.trust_tier == 1
    assert p.fetched_at == ts
    assert p.game_version == "43.0"
    assert p.freshness == "aging"


def test_freshness_bucket_fresh():
    p = extract_provenance(_row(fetched_at=_ts(0.1)))
    assert p.freshness == "fresh"


def test_freshness_bucket_stale():
    p = extract_provenance(_row(fetched_at=_ts(72)))
    assert p.freshness == "stale"


def test_freshness_bucket_never_when_missing():
    row = _row()
    row["fetched_at"] = None
    with pytest.raises((KeyError, TypeError)):
        extract_provenance(row)


def test_is_official_true_for_tier1():
    p = extract_provenance(_row(trust_tier=1))
    assert p.is_official is True


def test_is_official_false_for_tier2():
    p = extract_provenance(_row(trust_tier=2, source_kind="webpage"))
    assert p.is_official is False


def test_label_format():
    p = extract_provenance(_row(
        source_name="bloonswiki.com", trust_tier=2, fetched_at=_ts(0.5)
    ))
    assert "bloonswiki.com" in p.label
    assert "tier 2" in p.label
    assert "fresh" in p.label


def test_data_provenance_is_frozen():
    p = extract_provenance(_row())
    with pytest.raises(Exception):
        p.trust_tier = 99  # type: ignore[misc]


def test_extract_provenance_accepts_iso_string_fetched_at():
    ts = _ts(1)
    row = _row(fetched_at=ts.isoformat())
    p = extract_provenance(row)
    assert abs((p.fetched_at.replace(tzinfo=timezone.utc) - ts).total_seconds()) < 2


def test_extract_provenance_missing_optional_fields_defaults_safely():
    row = _row()
    for key in ("source_key", "source_name", "source_kind", "game_version"):
        row.pop(key, None)
    p = extract_provenance(row)
    assert p.source_key == ""
    assert p.source_name == ""
    assert p.source_kind == ""
    assert p.game_version is None


# ---------------------------------------------------------------------------
# FactRow
# ---------------------------------------------------------------------------


def test_fact_row_from_row_populates_all_fields():
    ts = _ts(1)
    fr = FactRow.from_row(_row(
        fact_type="btd6.race_metadata",
        entity_kind="btd6_race",
        entity_key="the_race",
        body_json={"name": "Test Race"},
        fetched_at=ts,
        confidence=0.9,
        version=2,
    ))
    assert fr.fact_id == 42
    assert fr.fact_type == "btd6.race_metadata"
    assert fr.entity_kind == "btd6_race"
    assert fr.entity_key == "the_race"
    assert fr.body_json == {"name": "Test Race"}
    assert fr.confidence == pytest.approx(0.9)
    assert fr.version == 2
    assert isinstance(fr.provenance, DataProvenance)


def test_fact_row_provenance_trust_tier_matches_row():
    fr = FactRow.from_row(_row(trust_tier=2, source_kind="webpage"))
    assert fr.provenance.trust_tier == 2
    assert fr.provenance.is_official is False


def test_fact_row_is_frozen():
    fr = FactRow.from_row(_row())
    with pytest.raises(Exception):
        fr.fact_type = "mutated"  # type: ignore[misc]


def test_fact_row_body_json_defaults_to_empty_dict_when_missing():
    row = _row()
    row["body_json"] = None
    fr = FactRow.from_row(row)
    assert fr.body_json == {}
