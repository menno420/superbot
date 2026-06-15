#!/usr/bin/env python3
"""Deterministic, content-free triage of SuperBot's production logs.

This owns the *mechanical* half of the ``superbot-log-triage`` Hermes skill —
the "error scan" and "crash-loop check" the skill prompt used to ask the model
to do by eyeballing raw log text. Eyeballing is the fragile "the model assembles
the answer" class the BTD6 fixes (BUG-0002/0004) closed; the reliable shape is
**the deterministic layer owns the answer**. Hermes pipes the read-only reader
into this tool and reports its output verbatim:

    python3 scripts/hermes/railway_logs.py -n 400 2>&1 | python3 scripts/hermes/log_triage.py

**Read-only + content-free by construction.** It never connects to anything
(pure text in -> report out) and it never echoes a full log message: every
example line is **redacted** (Discord snowflakes, bearer/long tokens, emails,
URLs, IP addresses, long hex/base64 runs -> placeholders) and truncated, so the
report surfaces *signal* (which signatures, how many, when last) without leaking
log bodies or PII. This is the "content-free surfacing of prod log signal"
the caretaker routine wanted (router Q-0130).

Input is the ``<timestamp> [SEVERITY] message`` line format
``railway_logs.format_logs`` emits, but parsing is tolerant: a bare line with no
timestamp/severity is still scanned by its message text.

Stdlib-only (no third-party deps) so the unit tests run in CI without installing
anything. Invoke with **``python3``** (version-agnostic) like the rest of
``scripts/hermes/`` — the Hermes VPS has Python 3.11, not the repo's CI-pinned
3.10, and this is a stdlib text tool, NOT one of the CI-parity tools. Do not
"correct" the usage lines to ``python3.10``.

Usage:
    python3 scripts/hermes/log_triage.py [FILE]      # or read stdin
    python3 scripts/hermes/log_triage.py --json
    cat logs.txt | python3 scripts/hermes/log_triage.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Line parsing — tolerant of the ``<ts> [SEV] message`` reader format
# ---------------------------------------------------------------------------

#: ``railway_logs.format_logs`` emits ``<timestamp> [SEVERITY] message`` (either
#: the timestamp or the ``[SEV]`` tag may be absent). Capture all three loosely.
_LINE_RE = re.compile(
    r"^\s*(?P<ts>\S+T\S+)?\s*(?:\[(?P<sev>[A-Z]+)\]\s*)?(?P<msg>.*?)\s*$",
)


@dataclass(frozen=True)
class LogLine:
    """One parsed log line. ``raw`` is kept only for crash-loop fingerprinting,
    never emitted (the report shows redacted examples only).
    """

    timestamp: str
    severity: str
    message: str
    raw: str


def parse_line(line: str) -> LogLine:
    """Parse one ``<ts> [SEV] message`` line; tolerant of missing fields."""
    m = _LINE_RE.match(line)
    if m is None:  # pragma: no cover - the regex matches anything
        return LogLine("", "", line.strip(), line.rstrip("\n"))
    return LogLine(
        timestamp=m.group("ts") or "",
        severity=(m.group("sev") or "").upper(),
        message=m.group("msg") or "",
        raw=line.rstrip("\n"),
    )


def parse_lines(text: str) -> list[LogLine]:
    """Parse a log blob into lines, dropping blank lines."""
    return [parse_line(ln) for ln in text.splitlines() if ln.strip()]


# ---------------------------------------------------------------------------
# Redaction — keep examples content-free (no PII, no tokens, no log bodies)
# ---------------------------------------------------------------------------

# Order matters: scrub the most specific / most sensitive shapes first so a
# token inside a URL is masked before the URL rule generalises it.
_REDACTORS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "<email>"),
    (re.compile(r"https?://\S+"), "<url>"),
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"), "<ip>"),
    # Discord snowflakes: 17-20 digit ids (users/guilds/channels/messages).
    (re.compile(r"\b\d{17,20}\b"), "<id>"),
    # Long opaque tokens / hashes / base64 (>=24 mixed alnum, must contain a
    # digit so plain English words and dotted module paths are never masked).
    (re.compile(r"\b(?=[\w.-]*\d)[A-Za-z0-9_.-]{24,}\b"), "<token>"),
    # Any remaining long bare number run (e.g. an 8+ digit counter).
    (re.compile(r"\b\d{8,}\b"), "<num>"),
)

_MAX_EXAMPLE_LEN = 120


def redact(message: str) -> str:
    """Return a content-free, truncated version of *message* for a report cell.

    Masks emails, URLs, IPs, Discord snowflakes, long tokens/hashes, and long
    number runs, then squeezes whitespace and truncates. The goal is a stable
    *signature* of the line, never its contents.
    """
    out = message
    for pattern, repl in _REDACTORS:
        out = pattern.sub(repl, out)
    out = " ".join(out.split())
    if len(out) > _MAX_EXAMPLE_LEN:
        out = out[: _MAX_EXAMPLE_LEN - 1].rstrip() + "…"
    return out


# ---------------------------------------------------------------------------
# Error signatures — group an error line by the kind of failure it is
# ---------------------------------------------------------------------------

#: Ordered (name, matcher) — first match wins, so put the specific buckets
#: before the catch-all "generic error". Matchers are case-insensitive
#: substring/regex predicates over the raw line text.
_SIGNATURES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("traceback", re.compile(r"Traceback \(most recent call last\)", re.I)),
    (
        "login/connection",
        re.compile(
            r"\b429\b|cannot connect|websocket|privileged.*intent"
            r"|improper token|rate limit|gateway|disconnect",
            re.I,
        ),
    ),
    (
        "database",
        re.compile(
            r"asyncpg|\bpool\b|connection refused|too many connections"
            r"|deadlock|relation .* does not exist|migration",
            re.I,
        ),
    ),
    (
        "command/interaction",
        re.compile(
            r"Ignoring exception|discord\.ext|app command|interaction"
            r"|command .* raised",
            re.I,
        ),
    ),
)

#: A line counts as an error worth grouping if it carries an error-ish severity
#: or one of these tokens (so an ERROR with no severity tag still registers).
_ERROR_SEVERITIES = {"ERROR", "CRITICAL", "FATAL", "WARN", "WARNING"}
_ERROR_TOKENS = re.compile(
    r"\berror\b|\bexception\b|\bfailed\b|\bfailure\b|traceback|\bcritical\b",
    re.I,
)

#: Startup-banner fingerprints — repeated occurrences mean a restart loop.
_STARTUP_RE = re.compile(
    r"logged in as|connected to gateway|bot is ready|starting bot"
    r"|messaging platforms|cog.*loaded|on_ready",
    re.I,
)


def is_error(line: LogLine) -> bool:
    """Whether *line* is an error/warning worth triaging."""
    if line.severity in _ERROR_SEVERITIES:
        return True
    return bool(_ERROR_TOKENS.search(line.raw))


def classify(line: LogLine) -> str:
    """The signature bucket for an error *line* (catch-all: ``generic error``)."""
    for name, matcher in _SIGNATURES:
        if matcher.search(line.raw):
            return name
    return "generic error"


# ---------------------------------------------------------------------------
# Triage report
# ---------------------------------------------------------------------------


@dataclass
class SignatureGroup:
    """An aggregated error signature — counts + last-seen + a redacted example."""

    name: str
    count: int = 0
    last_seen: str = ""
    example: str = ""


@dataclass
class TriageReport:
    """The deterministic triage outcome, ready to render markdown or JSON."""

    total_lines: int = 0
    error_count: int = 0
    groups: list[SignatureGroup] = field(default_factory=list)
    crash_loop: bool = False
    crash_loop_detail: str = ""

    @property
    def status(self) -> str:
        """One-word production status for the report header."""
        if self.crash_loop:
            return "crash-looping"
        if self.error_count:
            return "degraded"
        return "healthy"


#: A startup banner repeating at least this many times in the window is a loop.
_CRASH_LOOP_MIN_REPEATS = 3


def _detect_crash_loop(lines: list[LogLine]) -> tuple[bool, str]:
    """Detect a restart loop: a startup banner (or identical fatal signature)
    repeating ``>= _CRASH_LOOP_MIN_REPEATS`` times in the window.
    """
    startups = [ln for ln in lines if _STARTUP_RE.search(ln.raw)]
    # Group repeated startup banners by their redacted signature.
    banners: dict[str, list[LogLine]] = {}
    for ln in startups:
        banners.setdefault(redact(ln.message), []).append(ln)
    for sig, hits in banners.items():
        if len(hits) >= _CRASH_LOOP_MIN_REPEATS:
            first, last = hits[0].timestamp, hits[-1].timestamp
            span = f" between {first} and {last}" if first and last else ""
            return True, f"startup banner repeated {len(hits)}×{span} ({sig})"
    return False, ""


def triage(text: str) -> TriageReport:
    """Analyse a log blob into a deterministic, content-free triage report."""
    lines = parse_lines(text)
    report = TriageReport(total_lines=len(lines))

    groups: dict[str, SignatureGroup] = {}
    for ln in lines:
        if not is_error(ln):
            continue
        report.error_count += 1
        name = classify(ln)
        grp = groups.get(name)
        if grp is None:
            grp = SignatureGroup(name=name)
            groups[name] = grp
        grp.count += 1
        # Keep the *most recent* example (last line wins — logs are chronological).
        grp.last_seen = ln.timestamp or grp.last_seen
        grp.example = redact(ln.message)

    # Stable order: most frequent first, then alphabetical for ties.
    report.groups = sorted(
        groups.values(),
        key=lambda g: (-g.count, g.name),
    )
    report.crash_loop, report.crash_loop_detail = _detect_crash_loop(lines)
    return report


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_markdown(report: TriageReport) -> str:
    """Render the report as the markdown block the skill pastes into its output."""
    out: list[str] = []
    out.append("### Production status")
    out.append(
        f"{report.status} — {report.error_count} error/warning line(s) "
        f"across {report.total_lines} log line(s) in window",
    )
    out.append("")
    out.append("### Error signatures")
    if report.groups:
        out.append("| Signature | Count | Last seen | Example (redacted) |")
        out.append("|-----------|-------|-----------|--------------------|")
        for g in report.groups:
            last = g.last_seen or "—"
            example = g.example or "—"
            out.append(f"| {g.name} | {g.count} | {last} | {example} |")
    else:
        out.append("no errors in window")
    out.append("")
    out.append("### Crash-loop")
    out.append(report.crash_loop_detail if report.crash_loop else "none detected")
    return "\n".join(out)


def report_to_dict(report: TriageReport) -> dict:
    """JSON-serialisable view of the report (``--json``)."""
    return {
        "status": report.status,
        "total_lines": report.total_lines,
        "error_count": report.error_count,
        "crash_loop": report.crash_loop,
        "crash_loop_detail": report.crash_loop_detail,
        "signatures": [
            {
                "name": g.name,
                "count": g.count,
                "last_seen": g.last_seen,
                "example": g.example,
            }
            for g in report.groups
        ],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _read_input(path: str | None) -> str:
    if path and path != "-":
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    return sys.stdin.read()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic, content-free triage of SuperBot logs "
        "(reads the railway_logs.py text format from a FILE or stdin).",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="log file to read (default: stdin; '-' is also stdin)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the report as JSON instead of markdown",
    )
    args = parser.parse_args(argv)

    text = _read_input(args.file)
    report = triage(text)
    if args.json:
        print(json.dumps(report_to_dict(report), indent=2))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
