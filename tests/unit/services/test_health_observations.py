"""Unit tests for services.health_observations — PR4 (bot awareness).

Pins the pure classification/grouping primitives that turn the unstructured
recent-error stream into bounded, deterministic, ID-free findings:

* ``normalize_text`` strips secrets / IDs / hashes / multi-line traces;
* ``fingerprint`` is deterministic, ID-free, and distinguishes real diffs;
* ``group_log_errors`` collapses repeats into one counted finding and never
  leaks a raw secret/ID into the grouping key.
"""

from __future__ import annotations

from services import health_observations as ho
from services.health_contracts import FindingSeverity

_SECRET = "S3CR3TTOKENvalue"
_SNOWFLAKE = "1234567890123456789"  # 19-digit Discord ID


# --- normalize_text --------------------------------------------------------


def test_normalize_strips_secret_and_id() -> None:
    out = ho.normalize_text(f"RuntimeError: token={_SECRET} role {_SNOWFLAKE}")
    assert _SECRET not in out
    assert _SNOWFLAKE not in out
    assert "<secret>" in out
    assert "<id>" in out


def test_normalize_flattens_multiline_and_bounds() -> None:
    out = ho.normalize_text("Traceback:\n  File x\n  line y\nBoom", limit=20)
    assert "\n" not in out
    assert len(out) <= 20


def test_normalize_empty_is_empty() -> None:
    assert ho.normalize_text(None) == ""
    assert ho.normalize_text("") == ""


# --- fingerprint -----------------------------------------------------------


def test_fingerprint_is_deterministic() -> None:
    a = ho.fingerprint(
        category="runtime.log_error",
        subsystem="errors",
        operation="boom",
        exc_type="KeyError",
    )
    b = ho.fingerprint(
        category="runtime.log_error",
        subsystem="errors",
        operation="boom",
        exc_type="KeyError",
    )
    assert a == b
    assert a == "runtime_log_error:errors:boom:keyerror"


def test_fingerprint_excludes_raw_ids_and_secrets() -> None:
    fp = ho.fingerprint(
        category="runtime.log_error",
        subsystem="errors",
        operation=f"role {_SNOWFLAKE} token={_SECRET} missing",
        exc_type="KeyError",
    )
    assert _SNOWFLAKE not in fp
    assert _SECRET not in fp


def test_fingerprint_distinguishes_real_differences() -> None:
    base = dict(
        category="runtime.log_error",
        subsystem="errors",
        operation="op",
        exc_type="KeyError",
    )
    assert ho.fingerprint(**base) != ho.fingerprint(
        **{**base, "exc_type": "ValueError"}
    )
    assert ho.fingerprint(**base) != ho.fingerprint(**{**base, "operation": "other"})
    # an optional code segment further distinguishes
    assert ho.fingerprint(**base) != ho.fingerprint(**base, code="503")


def test_classify_extracts_exception_type() -> None:
    exc, _ = ho.classify_log_message("Failed to load: ConnectionError: refused")
    assert exc == "ConnectionError"
    exc, _ = ho.classify_log_message("just a plain message")
    assert exc == "LogError"


# --- group_log_errors ------------------------------------------------------


def test_group_collapses_repeats_into_one_counted_finding() -> None:
    entries = [
        {"level": "ERROR", "message": f"KeyError: missing key {i}"} for i in range(5)
    ]
    # Different trailing integers normalize away (they are < 7 digits, so the
    # *stem* differs) — use the SAME message to prove counting.
    entries = [{"level": "ERROR", "message": "KeyError: cache miss"}] * 4
    findings = ho.group_log_errors(entries)
    assert len(findings) == 1
    assert findings[0].occurrence_count == 4
    assert findings[0].severity is FindingSeverity.ERROR
    assert findings[0].source == "log_buffer"
    assert findings[0].related_subsystem == "errors"


def test_group_keeps_distinct_messages_separate_and_sorts_busiest_first() -> None:
    entries = [{"level": "ERROR", "message": "KeyError: cache miss"}] * 3 + [
        {"level": "ERROR", "message": "ValueError: bad input"}
    ] * 1
    findings = ho.group_log_errors(entries)
    assert len(findings) == 2
    assert findings[0].occurrence_count == 3  # busiest first
    assert findings[1].occurrence_count == 1


def test_group_caps_to_max_findings() -> None:
    entries = [
        {"level": "ERROR", "message": f"Error number {chr(65 + i)} happened"}
        for i in range(10)
    ]
    findings = ho.group_log_errors(entries, max_findings=3)
    assert len(findings) == 3


def test_group_never_leaks_secret_or_id_into_fingerprint_or_message() -> None:
    entries = [
        {
            "level": "ERROR",
            "message": f"AuthError: token={_SECRET} for role {_SNOWFLAKE}",
        }
    ]
    findings = ho.group_log_errors(entries)
    assert len(findings) == 1
    f = findings[0]
    assert _SECRET not in f.fingerprint and _SECRET not in f.message
    assert _SNOWFLAKE not in f.fingerprint and _SNOWFLAKE not in f.message


def test_group_ignores_blank_entries() -> None:
    assert ho.group_log_errors([{"level": "ERROR", "message": "   "}]) == []
    assert ho.group_log_errors([]) == []
