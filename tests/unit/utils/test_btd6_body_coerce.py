"""Coverage for the promoted ``coerce_body`` helper.

Previously duplicated as ``_coerce_body`` in ``cogs/btd6/_builders.py``
and ``services/btd6_live_query_service.py``. Both call sites now import
from ``utils.btd6.body_coerce``.
"""

from __future__ import annotations

from utils.btd6.body_coerce import coerce_body


def test_dict_passes_through() -> None:
    payload = {"a": 1, "b": "two"}
    assert coerce_body(payload) is payload


def test_legacy_double_encoded_string_decodes() -> None:
    assert coerce_body('{"name":"Reversed Loop","end_ms":12345}') == {
        "name": "Reversed Loop",
        "end_ms": 12345,
    }


def test_malformed_json_string_returns_empty_dict() -> None:
    assert coerce_body("not json") == {}


def test_non_mapping_json_returns_empty_dict() -> None:
    # `[1, 2, 3]` is valid JSON but not a mapping; we cannot project
    # it onto a dict so the helper falls back to ``{}``.
    assert coerce_body("[1, 2, 3]") == {}
    assert coerce_body("42") == {}
    assert coerce_body('"a string"') == {}


def test_none_returns_empty_dict() -> None:
    assert coerce_body(None) == {}


def test_int_returns_empty_dict() -> None:
    assert coerce_body(123) == {}
