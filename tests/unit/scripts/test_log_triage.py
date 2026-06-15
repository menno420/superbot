"""Tests for ``scripts/hermes/log_triage.py`` — the deterministic, content-free
log-triage analyzer.

Hermetic: pure text in -> report out, nothing touches the network. We exercise
line parsing, error grouping, the content-free **redaction** guarantee (the
whole point — no PII / tokens / log bodies in the output), crash-loop detection,
the JSON shape, and the stdin / empty-window paths.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "hermes" / "log_triage.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("log_triage_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# A representative production-shaped log window (railway_logs text format:
# "<timestamp> [SEVERITY] message"). Contents are synthetic.
_SAMPLE = """\
2026-06-15T12:00:00Z [INFO] Logged in as SuperBot#1234 (id 111122223333444455)
2026-06-15T12:00:01Z [INFO] Connected to gateway
2026-06-15T12:00:05Z [ERROR] asyncpg.exceptions: connection refused to pool
2026-06-15T12:00:06Z [ERROR] Traceback (most recent call last):
2026-06-15T12:00:09Z [WARNING] 429 Too Many Requests on login for user 555566667777888899
2026-06-15T12:00:12Z [ERROR] Ignoring exception in command 'mine': discord.ext error
2026-06-15T12:00:20Z [ERROR] Something unexpected went wrong with widget X
"""


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #


def test_parse_line_splits_ts_severity_message(mod):
    line = mod.parse_line("2026-06-15T12:00:05Z [ERROR] asyncpg pool died")
    assert line.timestamp == "2026-06-15T12:00:05Z"
    assert line.severity == "ERROR"
    assert line.message == "asyncpg pool died"


def test_parse_line_tolerates_missing_ts_and_severity(mod):
    line = mod.parse_line("plain message with no prefix")
    assert line.timestamp == ""
    assert line.severity == ""
    assert line.message == "plain message with no prefix"


def test_parse_lines_drops_blank_lines(mod):
    assert len(mod.parse_lines("a\n\n  \nb\n")) == 2


# --------------------------------------------------------------------------- #
# Grouping / classification
# --------------------------------------------------------------------------- #


def test_triage_groups_errors_by_signature(mod):
    report = mod.triage(_SAMPLE)
    names = {g.name for g in report.groups}
    assert {"database", "traceback", "login/connection", "command/interaction"} <= names
    # The two clean INFO startup lines are not errors.
    assert report.error_count == 5
    assert report.total_lines == 7


def test_unmatched_error_falls_into_generic_bucket(mod):
    report = mod.triage("2026-06-15T12:00:20Z [ERROR] widget exploded unexpectedly\n")
    assert [g.name for g in report.groups] == ["generic error"]


def test_info_lines_are_not_errors(mod):
    report = mod.triage("2026-06-15T12:00:00Z [INFO] all good, nothing to see\n")
    assert report.error_count == 0
    assert report.status == "healthy"


def test_groups_sorted_most_frequent_first(mod):
    text = (
        "[ERROR] asyncpg pool 1\n"
        "[ERROR] asyncpg pool 2\n"
        "[ERROR] Ignoring exception in command 'x'\n"
    )
    report = mod.triage(text)
    assert report.groups[0].name == "database"
    assert report.groups[0].count == 2


# --------------------------------------------------------------------------- #
# Content-free redaction (the core guarantee)
# --------------------------------------------------------------------------- #


def test_redacts_discord_snowflakes(mod):
    out = mod.redact("kicked user 111122223333444455 from guild 999988887777666655")
    assert "111122223333444455" not in out
    assert "<id>" in out


def test_redacts_email_url_ip_and_token(mod):
    # A long opaque token shape (>=24 mixed alnum with digits) — synthetic, not a
    # real provider key format, so it doesn't trip secret scanners.
    fake_token = "OPAQUE" + "abcd1234efgh5678ijkl9012"
    out = mod.redact(
        "user a.b+x@example.com hit https://api.example.com/v1?k=1 "
        f"from 10.0.12.34 with key {fake_token}",
    )
    assert "example.com" not in out
    assert "10.0.12.34" not in out
    assert fake_token not in out
    assert "<email>" in out and "<url>" in out and "<ip>" in out and "<token>" in out


def test_redaction_keeps_plain_words_and_module_paths(mod):
    # Dotted module paths / English words must survive (they are the signal).
    out = mod.redact("asyncpg.exceptions.ConnectionDoesNotExistError on pool")
    assert "asyncpg.exceptions.ConnectionDoesNotExistError" in out
    assert "<token>" not in out


def test_long_example_is_truncated(mod):
    out = mod.redact("word " * 200)
    assert len(out) <= mod._MAX_EXAMPLE_LEN
    assert out.endswith("…")


def test_no_raw_snowflake_or_email_leaks_into_report(mod):
    report = mod.triage(_SAMPLE)
    rendered = mod.render_markdown(report)
    # The raw snowflake from the 429 warning line must never reach the output.
    assert "555566667777888899" not in rendered
    assert "<id>" in rendered


# --------------------------------------------------------------------------- #
# Crash-loop detection
# --------------------------------------------------------------------------- #


def test_detects_crash_loop_from_repeated_startup_banner(mod):
    looping = "\n".join(
        f"2026-06-15T12:0{i}:00Z [INFO] Logged in as SuperBot ready" for i in range(4)
    )
    report = mod.triage(looping + "\n")
    assert report.crash_loop is True
    assert report.status == "crash-looping"
    assert "repeated" in report.crash_loop_detail


def test_single_startup_is_not_a_crash_loop(mod):
    report = mod.triage("2026-06-15T12:00:00Z [INFO] Logged in as SuperBot ready\n")
    assert report.crash_loop is False


# --------------------------------------------------------------------------- #
# JSON + CLI
# --------------------------------------------------------------------------- #


def test_report_to_dict_shape(mod):
    payload = mod.report_to_dict(mod.triage(_SAMPLE))
    assert payload["status"] == "degraded"
    assert payload["error_count"] == 5
    assert isinstance(payload["signatures"], list)
    assert {"name", "count", "last_seen", "example"} <= set(payload["signatures"][0])


def test_empty_window_reports_healthy(mod):
    report = mod.triage("")
    assert report.status == "healthy"
    assert mod.render_markdown(report).count("no errors in window") == 1


def test_main_reads_stdin_and_emits_json(mod, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(_SAMPLE))
    rc = mod.main(["--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "degraded"


def test_main_reads_file_argument(mod, tmp_path, capsys):
    log_file = tmp_path / "window.log"
    log_file.write_text(_SAMPLE, encoding="utf-8")
    rc = mod.main([str(log_file)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "### Production status" in out
    assert "degraded" in out
