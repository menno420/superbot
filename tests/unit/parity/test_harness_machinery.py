"""Parity-harness machinery tests — DB-free, run in normal CI.

These pin the DETERMINISM layer (normalization, snapshots-diffing, clock)
and the corpus generators. The full boot + capture round-trip needs
Postgres and a dedicated process — that lives behind the
``PARITY_INTEGRATION=1`` gate in ``test_harness_integration.py``; the CLI
(`python3.10 -m parity.run`) is the primary runnable.
"""

from __future__ import annotations

import datetime as dt
import decimal
import sys
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from parity.harness.dbsnap import diff_snapshots, normalize_value  # noqa: E402
from parity.harness.world import Clock  # noqa: E402


class _FakeWorldForNormalizer:
    """Just enough World surface for Normalizer's constructor."""

    guild_id = 700_000_000_000_000_001
    channels = {"general": 1_400_000_000_000_000_001}


def _normalizer():
    from parity.harness.capture import Normalizer

    return Normalizer(_FakeWorldForNormalizer())


# ------------------------------------------------------------------- clock


def test_clock_snowflakes_are_monotonic_and_time_encoded():
    clock = Clock()
    first = clock.snowflake()
    clock.advance()
    second = clock.snowflake()
    assert second > first
    # discord epoch decode: advancing 30s moves the timestamp bits by 30_000ms
    assert (second >> 22) - (first >> 22) == 30_000


def test_clock_is_deterministic_across_instances():
    a, b = Clock(), Clock()
    a.advance()
    b.advance()
    assert a.snowflake() == b.snowflake()


# -------------------------------------------------------------- normalizer


def test_normalizer_maps_known_and_minted_snowflakes():
    n = _normalizer()
    doc = {
        "channel_id": 1_400_000_000_000_000_001,
        "text": "in <#1400000000000000001> for <@900000000000000102>",
        "fresh": 1_456_000_000_000_000_123,
    }
    out = n.normalize(doc)
    assert out["channel_id"] == "<#general>"
    assert out["fresh"] == "<msg:1>"
    # first-appearance ordering is stable
    assert n.normalize(1_456_000_000_000_000_123) == "<msg:1>"
    assert n.normalize(1_456_000_000_000_000_999) == "<msg:2>"


def test_normalizer_scrubs_volatile_values():
    n = _normalizer()
    out = n.normalize(
        {
            "nonce": "12345",
            "msg": "id b726cda6-4e08-4f96-b02c-0bcc43802bcb at 2026-07-02T10:00:00+00:00",
            "cid": "5ad092356ba95b6bcb31c172f8acf40d",
        },
    )
    assert "nonce" not in out
    assert "<uuid>" in out["msg"]
    assert "<ts>" in out["msg"]
    assert out["cid"] == "<cid:1>"


def test_normalizer_auto_cid_refs_are_stable_within_a_case():
    n = _normalizer()
    a = n.normalize("5ad092356ba95b6bcb31c172f8acf40d")
    b = n.normalize("fa2fe554d948af4eddd8da16a0ffdfbf")
    a2 = n.normalize("5ad092356ba95b6bcb31c172f8acf40d")
    assert (a, b, a2) == ("<cid:1>", "<cid:2>", "<cid:1>")


def test_normalizer_static_custom_ids_survive_verbatim():
    n = _normalizer()
    assert n.normalize("nav:help") == "nav:help"
    assert n.normalize("logging_panel.set_mod") == "logging_panel.set_mod"


# ------------------------------------------------------------------ dbsnap


def test_normalize_value_covers_asyncpg_shapes():
    assert normalize_value(dt.datetime(2026, 1, 1)) == "<ts>"
    assert normalize_value(uuid.uuid4()) == "<uuid>"
    assert normalize_value(decimal.Decimal("1.50")) == "1.50"
    assert normalize_value(b"\x00\x01") == "<bytes:2>"
    assert normalize_value('{"a": 1}') == {"a": 1}
    assert normalize_value("plain") == "plain"


def test_diff_snapshots_reports_row_level_delta():
    before = {"t": [{"id": 1}], "gone": [{"id": 9}]}
    after = {"t": [{"id": 1}, {"id": 2}]}
    delta = diff_snapshots(before, after)
    assert delta == {
        "t": {"added": [{"id": 2}]},
        "gone": {"removed": [{"id": 9}]},
    }


def test_diff_snapshots_empty_on_identical():
    snap = {"t": [{"id": 1, "v": "x"}]}
    assert diff_snapshots(snap, snap) == {}


# ----------------------------------------------------------------- goldens


def test_committed_goldens_are_normalized():
    """No committed golden may carry raw volatility — the scrub classes
    (nonce keys, raw uuids/timestamps outside symbolic refs) must be absent.
    Guards against a capture-layer regression silently landing dirty
    fixtures.
    """
    import json
    import re

    goldens = sorted((_REPO_ROOT / "parity" / "goldens").glob("*/*.json"))
    if not goldens:  # corpus not captured in this checkout
        return
    uuid_re = re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    )
    for path in goldens[:50]:  # bounded: shape check, not a full audit
        text = path.read_text()
        assert '"nonce"' not in text, path
        assert not uuid_re.search(text), path
        doc = json.loads(text)
        assert doc["harness_version"] == 1
        assert doc["case_id"]
        assert isinstance(doc["steps"], list)
