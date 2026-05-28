"""Regression: admin refresh summary surfaces parser exception detail.

Operators clicking "Fetch All" need to know WHY ``parse_exception``
fired without grepping the DB. The summary embed renders both
``error_code`` and ``error_message`` (truncated) for each failed run.
"""

from __future__ import annotations

from cogs.btd6._builders import build_admin_refresh_summary_embed
from services.btd6_ingestion_service import IngestionResult


def _result(
    *,
    status: str,
    error_code: str | None = None,
    error_message: str | None = None,
    source_key: str = "nk_btd6_bosses_metadata",
) -> IngestionResult:
    return IngestionResult(
        source_key=source_key,
        status=status,  # type: ignore[arg-type]
        fact_count=0,
        duration_ms=12,
        error_code=error_code,
        run_id=99,
        error_message=error_message,
    )


def test_error_message_renders_in_chain_errors() -> None:
    """parse_exception with detail surfaces the EnvelopeError message."""
    parent = _result(status="ok", source_key="nk_btd6_bosses")
    child_fail = _result(
        status="parse_error",
        error_code="parse_exception",
        error_message="NK envelope rejected for 'nk_btd6_bosses_metadata': success_not_true",
    )
    embed = build_admin_refresh_summary_embed(
        [("nk_btd6_bosses", [parent, child_fail])],
    )
    chains_field = next(f for f in embed.fields if f.name == "Chains")
    value = chains_field.value or ""
    # Both code AND message appear, so a future operator sees what failed.
    assert "parse_exception" in value
    assert "success_not_true" in value


def test_error_message_truncated_to_120_chars() -> None:
    """Long error messages stay within Discord's field-value cap."""
    long_msg = "x" * 500
    result = _result(
        status="parse_error",
        error_code="parse_exception",
        error_message=long_msg,
    )
    embed = build_admin_refresh_summary_embed(
        [("nk_btd6_bosses", [result])],
    )
    chains_field = next(f for f in embed.fields if f.name == "Chains")
    # The 500-char message is truncated; the full string is not present
    # but the truncated prefix is.
    assert long_msg not in (chains_field.value or "")
    assert "x" * 120 in (chains_field.value or "")


def test_no_error_message_just_code() -> None:
    """When error_message is None the line falls back to the error code only."""
    result = _result(status="parse_error", error_code="invalid_json")
    embed = build_admin_refresh_summary_embed(
        [("nk_btd6_bosses", [result])],
    )
    chains_field = next(f for f in embed.fields if f.name == "Chains")
    value = chains_field.value or ""
    assert "invalid_json" in value


def test_ingestion_result_carries_error_message() -> None:
    """The dataclass field exists with a None default for back-compat."""
    r = IngestionResult(
        source_key="x", status="ok", fact_count=0, duration_ms=0,
        error_code=None, run_id=None,
    )
    assert r.error_message is None
