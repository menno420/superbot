#!/usr/bin/env python3.10
"""Export the read-only web data to JSON (stdlib only) — both sites' producer.

The developer dashboard (``docs/planning/developer-dashboard-plan.md``) is a
decoupled web app under ``dashboard/`` that must **not** import ``disbot/``. This
script is the seam between the two: it reads the repo's existing structured
sources and serialises them. It is the **single producer** for both web tiers
(``docs/planning/website-two-site-split-plan-2026-06-19.md`` §2.2 — one producer,
two artifacts, no shared package):

* ``dashboard/data/dashboard.json`` — the **full** payload (developer dashboard).
* ``botsite/data/site.json`` — a **minimized public subset** (the marketing bot
  site). It is an explicit *whitelist* of user-safe families only (see
  :data:`SITE_TOPLEVEL_KEYS` / :func:`build_site_subset`); it physically cannot
  contain a dev-only family (``env_usage`` / ``settings`` / ``access`` / ``reviews``
  / ``ideas`` / raw ``bugs``) or any per-guild value — *redaction by construction*,
  the strongest guarantee for the split's non-negotiable #1.

Sources (all read-only, never imported):

* Bot-function catalogue  <- ``disbot/utils/subsystem_registry.py`` (AST-parsed)
* Ideas                   <- ``docs/ideas/*.md`` (title + Status badge + date)
* Bugs                    <- ``docs/health/bug-book.md`` (``## BUG-NNNN ...``)
* Reviews                 <- ``docs/owner/review-inbox.md`` (``## REV-NNNN — area — STATUS``)
* Updates feed            <- ``.sessions/*.md`` (date + title + Status badge)
* Bot changelog           <- ``docs/bot-changelog.md`` (``## YYYY-MM-DD — title``,
                             curated user-facing changes — plan §7.5)
* Env-var usage map       <- ``disbot/**/*.py`` via ``scripts/scan_env_usage.py``
                             (names + code locations only — never a value)

Pure stdlib so it runs in CI with no extra dependencies and the web tiers' deps
(fastapi, uvicorn, ...) never enter the bot's ``requirements.txt``.
Re-run after the sources change (writes BOTH artifacts by default)::

    python3.10 scripts/export_dashboard_data.py                 # both artifacts
    python3.10 scripts/export_dashboard_data.py --targets site  # only site.json

Reliability (Q-0105): **unverified** — confirm the JSON against the live sources
a few times across sessions before trusting it, and delete this seam if it proves
unreliable. It is a convenience generator, not load-bearing runtime code.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import importlib.util
import json
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO_ROOT / "dashboard" / "data" / "dashboard.json"
SITE_OUTPUT_FILE = REPO_ROOT / "botsite" / "data" / "site.json"
# The SPA data layer regenerated alongside site.json. Exposed as a CLI arg
# (``--data-js-output``) so a test driving ``main()`` with tmp paths cannot clobber
# the tracked repo file (BUG-0022): the live-HEAD build sha would desync it from the
# committed site.json and redden botsite-tests for an unrelated `git add -A`.
DATA_JS_OUTPUT_FILE = REPO_ROOT / "botsite" / "site" / "data.js"

# The ONLY top-level keys the public ``site.json`` subset is allowed to carry
# (plan §5 / §2.2). This is the redaction guarantee for the marketing bot site:
# :func:`build_site_subset` constructs exactly these and nothing else, and the
# freshness/whitelist guard (``check_generated_artifacts_fresh`` /
# ``check_dashboard_data``) asserts the committed file's keys are a SUBSET of this
# set — so a new key in the producer fails closed instead of silently leaking a
# private family onto the public site. Deliberately OMITS ``env_usage``,
# ``settings``, ``access``, ``reviews``, ``ideas``, raw ``bugs``, and ``cogs``
# (the dashboard-only families).
SITE_TOPLEVEL_KEYS: frozenset[str] = frozenset(
    {"meta", "counts", "catalogue", "commands", "bot_changelog"},
)

# The program-console feed (``botsite/data/console.json`` — served at
# ``/console/data.json`` on the public bot-site service). Same
# whitelist-by-construction posture as ``site.json``: only repo-development
# families that are ALREADY public in this repository (session run reports from
# ``.sessions/``, ideas/bugs as counters + titles, the curated changelog).
# The dev-only value families (``env_usage`` / ``settings`` / ``access`` /
# ``reviews``) are excluded, and per-guild/user values never enter the producer.
CONSOLE_OUTPUT_FILE = REPO_ROOT / "botsite" / "data" / "console.json"
CONSOLE_TOPLEVEL_KEYS: frozenset[str] = frozenset(
    {"meta", "sessions", "ideas", "bugs", "bot_changelog", "telemetry"},
)
# The console feed's CROSS-REPO shape contract. ``console.json`` has two consumers —
# superbot's own botsite console (``botsite/console/console.js``) AND the websites
# repo's dashboard ``/console`` page (menno420/websites, fetching the committed file
# over raw GitHub) — so the shape is pinned in the committed, versioned
# ``botsite/data/console_data_contract.json`` (the ``site_data_contract.json``
# pattern applied to this feed; PR #1883's session idea). These producer constants
# must MATCH that file — ``check_dashboard_data.check_console_subset`` enforces the
# parity (CI via tests/unit/scripts/) — and every emitted ``console.json`` carries
# the contract version as ``meta.schema_version`` so consumers can cheaply verify
# the shape they were built against. Changing the shape = edit the contract file
# and these constants in the same commit and bump the version — the explicit,
# reviewable act a consumer repo pins against.
CONSOLE_CONTRACT_FILE = REPO_ROOT / "botsite" / "data" / "console_data_contract.json"
CONSOLE_SCHEMA_VERSION = 1
# Per-entry field whitelist for the console's session feed (run reports).
CONSOLE_SESSION_FIELDS: tuple[str, ...] = (
    "file",
    "date",
    "title",
    "status",
    "run_type",
    "self_initiated",
)
# The program's model-allocation telemetry feed (kit-lab founding plan §5.2 /
# PL-004, Q-0248) — the console's declared "Model & spend telemetry" lane.
# Superbot's rows are HAND-AUTHORED against the kit's canonical schema until it
# truly adopts the kit (plan §4.2); the feed is a per-repo append-only JSONL and
# the exporter renders it as the JSON array the lane contract declares (the
# D-10 refinement: the lane binds to the record shape, not the file encoding).
# Same field-whitelist-by-construction posture as the session feed; no value in
# a row is per-guild/user data (session slug, date, model tier, effort, task
# class, token count, PR outcome — all repo-development metadata).
TELEMETRY_FILE = REPO_ROOT / "telemetry" / "model-usage.jsonl"
CONSOLE_TELEMETRY_FIELDS: tuple[str, ...] = (
    "session",
    "date",
    "model",
    "effort",
    "task_class",
    "tokens_out",
    "outcome",
)
# The structured ``outcome`` object's own whitelist (Q-0248's objective gates).
TELEMETRY_OUTCOME_FIELDS: tuple[str, ...] = (
    "ci_green_first_push",
    "checker_findings",
    "merged_pr",
    "reverted_within_window",
)
# The exported array is capped to the newest rows so the console feed stays
# bounded as the JSONL grows; the file itself remains the full record.
TELEMETRY_ROW_CAP = 200
# Per-command fields the public ``commands`` reference exposes (no per-guild value
# ever appears — these are repo-level command metadata). The interactive command
# browser (plan unit S1.1 / P2) renders these in a clickable detail view:
#
# * ``usage`` — the one-line description (the AST scanner's ``brief``).
# * ``description`` — the command's full first docstring *paragraph* (richer than the
#   one-line ``usage``), Sphinx noise stripped; ``null`` when the command has no
#   docstring. Never invented prose.
# * ``use_cases`` — reserved/``null``: there is no reliable *structured* per-command
#   use-case source in the repo today, so it is emitted as ``null`` rather than
#   fabricated (a curated source is a fast-follow — plan S1.1).
# * ``examples`` — real ``!command …`` invocation snippets lifted verbatim from the
#   docstring (backtick-wrapped); ``[]`` when none. Genuinely user-safe + real.
# * ``status`` — ``finished`` | ``in-progress`` (an honest maturity signal): the
#   command is ``in-progress`` iff its cog/subsystem has a linked OPEN idea or OPEN
#   bug, else ``finished`` (the recommended default — plan S1.1).
# * ``linked_ideas`` — ideas mapped to the command's cog/subsystem, **title + status
#   only** (redaction — never the raw internal idea text). Surfaced as user-facing
#   "what's planned" teasers. ``[]`` when none.
# * ``notes`` — curated per-command note. The plan's v1 candidate (the help-overlay
#   re-describe text) is **per-guild DB data** — unavailable statically AND unsafe to
#   surface publicly — so v1 emits ``null`` (no curated *static* source exists yet; a
#   dedicated community-notes source is a fast-follow, never invented).
#
# ``category`` + ``permissions`` are joined from the command's subsystem catalogue
# entry; ``cooldown`` is reserved (the AST scanner does not statically resolve runtime
# cooldown decorators today, so it is emitted as ``null`` rather than fabricated).
SITE_COMMAND_FIELDS: tuple[str, ...] = (
    "name",
    "aliases",
    "category",
    "cooldown",
    "permissions",
    "usage",
    "description",
    "use_cases",
    "examples",
    "status",
    "linked_ideas",
    "notes",
)

# Public field contracts for the OTHER ``site.json`` families — the *within-family*
# leak guard (keys → leaves). :data:`SITE_TOPLEVEL_KEYS` pins which *families* may
# appear; these pin the exact *leaf fields* each family may carry, so a producer change
# that adds a new field to an already-allowed family (a per-guild value, an internal
# id, a future ``owner_only_note``) fails closed in
# :func:`check_dashboard_data.check_site_subset` instead of leaking silently. Nested
# dicts are pinned per level (``meta`` and ``meta.build``). :data:`SITE_COMMAND_FIELDS`
# (above) is the ``commands`` family's contract; these cover the rest.
SITE_META_FIELDS: tuple[str, ...] = ("generated_at", "build")
SITE_META_BUILD_FIELDS: tuple[str, ...] = (
    "commit",
    "committed_at",
    "subject",
)
SITE_COUNTS_FIELDS: tuple[str, ...] = ("commands", "features", "games")
SITE_CHANGELOG_FIELDS: tuple[str, ...] = ("date", "kind", "summary", "title")
# Public catalogue record contract: the entry-sourced fields the projector keeps
# (:data:`SITE_CATALOGUE_ENTRY_FIELDS`, used by :func:`_site_catalogue` below) plus the
# two derived output fields the projector always adds (``badges``, ``is_game``).
SITE_CATALOGUE_ENTRY_FIELDS: tuple[str, ...] = (
    "key",
    "display_name",
    "description",
    "emoji",
    "category",
    "tags",
)
SITE_CATALOGUE_FIELDS: tuple[str, ...] = SITE_CATALOGUE_ENTRY_FIELDS + (
    "badges",
    "is_game",
)

# The complete public leaf-field contract: family path → allowed leaf fields. Drives
# :func:`check_dashboard_data.check_site_subset`'s within-family whitelist (the sibling
# of the :data:`SITE_TOPLEVEL_KEYS` family whitelist). A dotted path (``meta.build``)
# pins a nested dict; a plain key pins either a dict family (``meta`` / ``counts``) or
# the records of a list family (``catalogue`` / ``commands`` / ``bot_changelog``).
SITE_FIELD_CONTRACT: dict[str, tuple[str, ...]] = {
    "meta": SITE_META_FIELDS,
    "meta.build": SITE_META_BUILD_FIELDS,
    "counts": SITE_COUNTS_FIELDS,
    "catalogue": SITE_CATALOGUE_FIELDS,
    "commands": SITE_COMMAND_FIELDS,
    "bot_changelog": SITE_CHANGELOG_FIELDS,
}

# A command's maturity badge (plan S1.1). ``finished`` is the recommended default;
# ``in-progress`` is set only when the owning subsystem has linked open work.
COMMAND_STATUS_FINISHED = "finished"
COMMAND_STATUS_IN_PROGRESS = "in-progress"

# Idea statuses that count as "open / planned" for the in-progress signal + the
# linked-ideas teasers. Lower-cased ``parse_ideas`` status badges: a captured idea is
# ``ideas`` (the default); ``historical`` / ``reference`` are archived/closed and must
# NOT mark a command in-progress or surface as a "what's planned" teaser.
_OPEN_IDEA_STATUSES: frozenset[str] = frozenset({"ideas", "planned", "in-progress"})
# Bug statuses (upper-cased) that count as "open" for the in-progress signal. A bug
# that is FIXED / RESOLVED / CLOSED no longer makes its subsystem in-progress.
_OPEN_BUG_STATUSES: frozenset[str] = frozenset(
    {"OPEN", "PARTIALLY FIXED", "IN PROGRESS"},
)

# Docstring example extraction: a backtick-wrapped ``!command …`` invocation. The
# bot's prefix is ``!`` (see disbot); only backtick-delimited snippets are taken so a
# stray ``!`` in prose is never mistaken for an example.
_DOC_EXAMPLE_RE = re.compile(r"`+\s*(![A-Za-z][\w-]*(?:[^`\n]*?))\s*`+")
# Sphinx/Python cross-reference noise to strip from a public ``description``
# (``:class:`X``` / ``:meth:`Y``` / ``:func:`Z```), leaving the human label.
_SPHINX_ROLE_RE = re.compile(r":[a-z]+:`~?([^`]+)`")


def _load_scan_env_usage() -> Callable[..., list[dict]]:
    """Load ``scan_env_usage`` from its sibling script (scripts/ isn't a package)."""
    script = Path(__file__).resolve().parent / "scan_env_usage.py"
    spec = importlib.util.spec_from_file_location("_scan_env_usage_seam", script)
    if spec is None or spec.loader is None:  # pragma: no cover - import wiring
        raise ImportError("cannot load scan_env_usage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.scan_env_usage


def _load_scan_commands() -> Callable[..., list[dict]]:
    """Load ``scan_commands`` from its sibling script (scripts/ isn't a package)."""
    script = Path(__file__).resolve().parent / "scan_commands.py"
    spec = importlib.util.spec_from_file_location("_scan_commands_seam", script)
    if spec is None or spec.loader is None:  # pragma: no cover - import wiring
        raise ImportError("cannot load scan_commands.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.scan_commands


def _load_sibling(script_name: str, attr: str) -> Callable[..., object]:
    """Load one callable from a sibling ``scripts/`` module (not a package)."""
    script = Path(__file__).resolve().parent / script_name
    spec = importlib.util.spec_from_file_location(f"_{attr}_seam", script)
    if spec is None or spec.loader is None:  # pragma: no cover - import wiring
        raise ImportError(f"cannot load {script_name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, attr)


# Catalogue fields surfaced from the registry (all str/list literals — the
# non-literal ``color`` field is intentionally skipped).
_CATALOGUE_FIELDS = (
    "display_name",
    "description",
    "emoji",
    "category",
    "visibility_tier",
    # ``visibility_mode`` ("normal" / "internal") drives cog-routing operator
    # visibility: only non-internal subsystems are operator-routable (see
    # views/setup/sections/cog_routing.py), so the dashboard reads it to mark a
    # cog's routing state accurately.
    "visibility_mode",
    "tags",
    "entry_points",
    "capabilities",
    "related_subsystems",
)

_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
# Mirrors scripts/check_session_gate.py: terminator is em/en-dash, pipe, or EOL.
_STATUS_RE = re.compile(
    r"\*\*Status:\*\*\s*`?\s*([A-Za-z0-9 _-]+?)\s*`?\s*(?:[—–|]|$)",
)
# Bug headings use em/en-dash separators: ``## BUG-0014 — title — STATUS``.
_BUG_HEAD_RE = re.compile(r"^##\s+(BUG-\d+)\s*[—–]\s*(.+?)\s*$")
_BUG_STATUS_RE = re.compile(r"[—–]\s*([A-Za-z][A-Za-z ]*)\s*$")
# Review-inbox headings: ``## REV-0001 — <area> — STATUS`` (area in the middle,
# status last). The bracketed body is split on the *last* dash for the status,
# leaving everything before it as the area (so a hyphenated area survives).
_REVIEW_HEAD_RE = re.compile(r"^##\s+(REV-\d+)\s*[—–]\s*(.+?)\s*$")
_REVIEW_STATUS_RE = re.compile(r"[—–]\s*([A-Za-z][A-Za-z ]*?)(?:\s*\([^)]*\))?\s*$")


def _truncate(text: str, limit: int) -> str:
    """Collapse whitespace and ellipsise ``text`` to at most ``limit`` chars."""
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _strip_md(text: str) -> str:
    """Strip the markdown noise (backticks, bold, leading bullet) from a line."""
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = text.replace("**", "")
    return text.lstrip("-* ").strip()


def _first_heading(text: str) -> str | None:
    """Return the first level-1 ``# `` heading text, or None."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def _status_badge(text: str) -> str | None:
    """Return the lowercased ``> **Status:** `<token>``` badge token, or None."""
    for line in text.splitlines():
        if "**Status:**" in line:
            match = _STATUS_RE.search(line)
            if match:
                return match.group(1).strip().lower()
    return None


# Optional authoritative idea->subsystem link (idea-subsystem-tag-on-ideas-2026-06-19):
# ``> **Subsystem:** key1, key2`` (or ``**Area:**``). When present it overrides the
# filename-slug heuristic in :func:`_subsystem_open_work`, killing the generic-word
# cross-matches the heuristic is prone to (e.g. a workflow "executor-chain" idea matching
# the Word-Chain game's ``chain`` subsystem).
_SUBSYSTEM_TAG_RE = re.compile(
    r"\*\*(?:Subsystem|Area)s?:\*\*\s*`?\s*([A-Za-z0-9 ,_-]+?)\s*`?\s*(?:[—–|]|$)",
)
# Sentinels meaning "explicitly tagged, but touches NO bot subsystem" -> links to nothing
# (for agent-workflow / meta ideas that the slug heuristic would otherwise cross-match).
_SUBSYSTEM_TAG_NONE: frozenset[str] = frozenset({"none", "-", "n/a", "na"})


def _subsystem_tags(text: str) -> list[str] | None:
    """Return the explicit subsystem keys an idea declares, or ``None`` when untagged.

    Reads an optional ``> **Subsystem:** key1, key2`` (or ``**Area:**``) line — the
    authoritative idea->subsystem link. Keys are lower-cased + comma-split. A ``none`` /
    ``-`` sentinel returns ``[]`` ("tagged, links to nothing"). An **absent** line returns
    ``None`` so the caller falls back to the filename-slug heuristic. Keys are not
    validated here (unknown keys simply never match a real subsystem — fail-safe).

    Only the **front-matter header** is scanned — the leading block above the first
    ``## `` section heading or code fence — so a ``**Subsystem:**`` *example* deeper in an
    idea's prose (e.g. the proposal that documents this very tag) is never mistaken for a
    real tag.
    """
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("## ") or stripped.startswith("```"):
            break  # left the front-matter header — body examples are not tags
        if "**Subsystem:" not in line and "**Area:" not in line:
            continue
        match = _SUBSYSTEM_TAG_RE.search(line)
        if not match:
            continue
        keys = [
            k.strip() for k in match.group(1).strip().lower().split(",") if k.strip()
        ]
        # [] when only the none/- sentinel was given ("tagged, links to nothing").
        return [k for k in keys if k not in _SUBSYSTEM_TAG_NONE]
    return None


# Run-report ``**Run type:**`` marker (Q-0165): ``routine · dispatch`` -> "routine",
# ``manual`` -> "manual". Lets the updates feed distinguish autonomous routine runs from
# the owner's own sessions.
_RUN_TYPE_RE = re.compile(r"\*\*Run type:\*\*\s*`?\s*([A-Za-z]+)")


def _run_type(text: str) -> str:
    """Return "routine" / "manual" from the run-report ``**Run type:**`` line, or "".

    Classifies on the first word after the marker; "" when the log has no Run type line
    (older logs, before Q-0165).
    """
    for line in text.splitlines():
        if "**Run type:**" in line:
            match = _RUN_TYPE_RE.search(line)
            if match:
                token = match.group(1).strip().lower()
                if "routine" in token:
                    return "routine"
                if "manual" in token:
                    return "manual"
    return ""


# Run-report ``⚑ Self-initiated:`` marker (Q-0172): a non-``none`` value means the run
# promoted an idea to a plan/build with no dispatch or owner ask. Lets the updates feed
# badge + filter unprompted self-initiated work for owner review.
_SELF_INITIATED_RE = re.compile(r"Self-initiated:\*\*\s*(.*)")


def _self_initiated(text: str) -> bool:
    """Return True when the run-report ``⚑ Self-initiated:`` line names real work.

    The line lists any idea promoted to a plan/build without a dispatched order or owner
    request (Q-0172). ``none`` / empty / absent -> False. The ⚑ glyph sits inside the bold
    marker (``**⚑ Self-initiated:**``), so match on the ``Self-initiated:`` substring.
    """
    for line in text.splitlines():
        if "Self-initiated:" in line:
            match = _SELF_INITIATED_RE.search(line)
            if match:
                rest = match.group(1).strip()
                # Drop a trailing provenance tag like "(Q-0172)" and markdown emphasis.
                rest = re.sub(r"\(Q-\d{4}\)", "", rest).strip().strip("`*_ ").lower()
                if rest and not rest.startswith("none"):
                    return True
    return False


def _first_paragraph(text: str) -> str:
    """Return the first body paragraph (skips headings, quotes, list markers)."""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped[0] in "#>-*":
            continue
        return stripped
    return ""


def _date_from_name(name: str) -> str:
    """Extract a ``YYYY-MM-DD`` date from a filename, or empty string."""
    match = _DATE_RE.search(name)
    return match.group(1) if match else ""


def _literal(node: ast.AST) -> object:
    """Best-effort literal value of an AST node, or None for non-literals."""
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


def _find_subsystems_dict(tree: ast.AST) -> ast.Dict | None:
    """Locate the ``SUBSYSTEMS = {...}`` dict node in a parsed module."""
    for node in ast.walk(tree):
        target = None
        if isinstance(node, ast.Assign):
            target = next(
                (t for t in node.targets if isinstance(t, ast.Name)),
                None,
            )
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target
        if target is not None and target.id == "SUBSYSTEMS":
            value = node.value
            if isinstance(value, ast.Dict):
                return value
    return None


def _catalogue_entry(key: str, value: ast.Dict) -> dict:
    """Build one catalogue entry from a subsystem's AST dict node."""
    entry: dict = {"key": key}
    for field_node, val_node in zip(value.keys, value.values, strict=True):
        field = _literal(field_node) if field_node is not None else None
        if isinstance(field, str) and field in _CATALOGUE_FIELDS:
            entry[field] = _literal(val_node)
    return entry


def parse_catalogue(source: str) -> list[dict]:
    """Parse the subsystem registry source into a list of catalogue entries."""
    subsystems = _find_subsystems_dict(ast.parse(source))
    if subsystems is None:
        return []
    entries: list[dict] = []
    for key_node, val_node in zip(subsystems.keys, subsystems.values, strict=True):
        key = _literal(key_node) if key_node is not None else None
        if isinstance(key, str) and isinstance(val_node, ast.Dict):
            entries.append(_catalogue_entry(key, val_node))
    entries.sort(
        key=lambda e: (e.get("category") or "", e.get("display_name") or e["key"]),
    )
    return entries


def parse_ideas(ideas_dir: Path) -> list[dict]:
    """Parse ``docs/ideas/*.md`` into title/status/date/summary records."""
    ideas: list[dict] = []
    for path in sorted(ideas_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        ideas.append(
            {
                "file": path.name,
                "title": _first_heading(text) or path.stem,
                "status": _status_badge(text) or "ideas",
                "date": _date_from_name(path.name),
                "summary": _truncate(_first_paragraph(text), 280),
                "subsystems": _subsystem_tags(text),
            },
        )
    ideas.sort(key=lambda e: e["date"], reverse=True)
    return ideas


def parse_bugs(text: str) -> list[dict]:
    """Parse the bug book markdown into id/title/status/summary records."""
    bugs: list[dict] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        head = _BUG_HEAD_RE.match(line)
        if not head:
            continue
        bug_id, rest = head.group(1), head.group(2)
        status = "unknown"
        status_match = _BUG_STATUS_RE.search(rest)
        if status_match and len(status_match.group(1).strip()) <= 24:
            status = status_match.group(1).strip()
            rest = rest[: status_match.start()].rstrip()
        bugs.append(
            {
                "id": bug_id,
                "title": _strip_md(rest),
                "status": status,
                "summary": _bug_summary(lines, index),
            },
        )
    return bugs


def _bug_summary(lines: list[str], start: int) -> str:
    """Return the 'Symptom' bullet beneath a bug heading, joined and truncated."""
    collected: list[str] = []
    capturing = False
    for line in lines[start + 1 : start + 60]:
        if line.startswith("## "):
            break
        stripped = line.strip()
        if not capturing:
            if stripped.lower().startswith("- **symptom"):
                cleaned = re.sub(r"^- \*\*symptom[^:]*:\*\*", "", stripped, flags=re.I)
                collected.append(cleaned)
                capturing = True
            continue
        if not stripped or stripped.startswith("- **"):
            break
        collected.append(stripped)
    return _truncate(_strip_md(" ".join(collected)), 280)


def parse_reviews(text: str) -> list[dict]:
    """Parse the review-inbox markdown into id/area/status/summary records.

    Mirrors :func:`parse_bugs` but for the owner-review-inbox shape
    ``## REV-NNNN — <area> — STATUS`` (decision Q-0169): the bracketed body is
    split on the *last* dash so a hyphenated area survives, the status is
    normalised to ``OPEN`` / ``RESOLVED`` (everything else passes through
    verbatim), and the summary is the ``- **Review (owner):**`` bullet beneath
    the heading. The page groups by area and shows open vs. resolved.
    """
    reviews: list[dict] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        head = _REVIEW_HEAD_RE.match(line)
        if not head:
            continue
        review_id, rest = head.group(1), head.group(2)
        status = "unknown"
        status_match = _REVIEW_STATUS_RE.search(rest)
        if status_match and len(status_match.group(1).strip()) <= 24:
            status = status_match.group(1).strip()
            rest = rest[: status_match.start()].rstrip()
        reviews.append(
            {
                "id": review_id,
                "area": _strip_md(rest) or "general",
                "status": status,
                "summary": _review_summary(lines, index),
            },
        )
    return reviews


def _review_summary(lines: list[str], start: int) -> str:
    """Return the 'Review (owner)' bullet beneath a review heading, truncated."""
    collected: list[str] = []
    capturing = False
    for line in lines[start + 1 : start + 60]:
        if line.startswith("## "):
            break
        stripped = line.strip()
        if not capturing:
            if stripped.lower().startswith("- **review"):
                cleaned = re.sub(r"^- \*\*review[^:]*:\*\*", "", stripped, flags=re.I)
                collected.append(cleaned)
                capturing = True
            continue
        if not stripped or stripped.startswith("- **"):
            break
        collected.append(stripped)
    return _truncate(_strip_md(" ".join(collected)), 280)


def parse_updates(sessions_dir: Path, limit: int = 60) -> list[dict]:
    """Parse ``.sessions/*.md`` logs into a newest-first updates feed."""
    updates: list[dict] = []
    for path in sessions_dir.glob("*.md"):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        updates.append(
            {
                "file": path.name,
                "date": _date_from_name(path.name),
                "title": _first_heading(text) or path.stem,
                "status": _status_badge(text) or "",
                "run_type": _run_type(text),
                "self_initiated": _self_initiated(text),
            },
        )
    updates.sort(key=lambda e: (e["date"], e["file"]), reverse=True)
    return updates[:limit]


# Bot-changelog headings: ``## YYYY-MM-DD — <title>``, with an optional trailing
# ``(feature)`` / ``(fix)`` / ``(improvement)`` kind tag inside the title (plan §7.5).
# The user-facing curated source — NOT the .sessions/ dev feed.
_CHANGELOG_HEAD_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*[—–-]\s*(.+?)\s*$")
_CHANGELOG_KIND_RE = re.compile(
    r"\((feature|fix|improvement)\)\s*$",
    re.IGNORECASE,
)
_VALID_CHANGELOG_KINDS = frozenset({"feature", "fix", "improvement"})


def parse_telemetry(path: Path) -> list[dict]:
    """Parse ``telemetry/model-usage.jsonl`` into whitelisted records (file order).

    One JSON object per line — the PL-004/Q-0248 per-session record. Tolerant by
    contract: a malformed line, a non-object row, or a missing field is skipped or
    nulled, never fatal (the JSONL is appended by many parallel sessions and one
    bad row must not blank the console lane). Every record is rebuilt from the
    :data:`CONSOLE_TELEMETRY_FIELDS` whitelist (nested ``outcome`` object from
    :data:`TELEMETRY_OUTCOME_FIELDS`) — unknown extra fields are dropped by
    construction. Returns at most :data:`TELEMETRY_ROW_CAP` newest rows.
    """
    if not path.is_file():
        return []
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(raw, dict):
            continue
        record = {field: raw.get(field) for field in CONSOLE_TELEMETRY_FIELDS}
        outcome = raw.get("outcome")
        record["outcome"] = (
            {field: outcome.get(field) for field in TELEMETRY_OUTCOME_FIELDS}
            if isinstance(outcome, dict)
            else None
        )
        records.append(record)
    return records[-TELEMETRY_ROW_CAP:]


def parse_bot_changelog(text: str) -> list[dict]:
    """Parse ``docs/bot-changelog.md`` into date/title/kind/summary records.

    The **curated, user-facing** changelog (plan §7.5 / Q-0179): one record per
    ``## YYYY-MM-DD — <title>`` heading, newest-first. An optional trailing
    ``(feature)`` / ``(fix)`` / ``(improvement)`` tag in the title sets ``kind``
    (default ``""``); the summary is the first body paragraph beneath the heading.
    Deliberately separate from :func:`parse_updates` — that feeds the dev site's
    ``/updates`` from ``.sessions/`` logs (how a session ran), while this is the
    hand-curated "what's new for users" source the public ``/changelog`` renders.
    """
    entries: list[dict] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        head = _CHANGELOG_HEAD_RE.match(line)
        if not head:
            continue
        date, title = head.group(1), head.group(2).strip()
        kind = ""
        kind_match = _CHANGELOG_KIND_RE.search(title)
        if kind_match:
            kind = kind_match.group(1).lower()
            title = title[: kind_match.start()].rstrip()
        entries.append(
            {
                "date": date,
                "title": _strip_md(title),
                "kind": kind if kind in _VALID_CHANGELOG_KINDS else "",
                "summary": _truncate(_changelog_summary(lines, index), 280),
            },
        )
    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries


def _changelog_summary(lines: list[str], start: int) -> str:
    """Return the first body paragraph beneath a changelog heading."""
    for line in lines[start + 1 : start + 30]:
        if line.startswith("## "):
            break
        stripped = line.strip()
        if not stripped or stripped[0] in "#>-*":
            continue
        return _strip_md(stripped)
    return ""


def _git_meta(repo_root: Path) -> dict[str, str]:
    """Return the build commit context the data was generated from, or ``{}``.

    Powers the ``/status`` "deployed build" banner: the dashboard auto-redeploys
    on every merge to ``main`` and serves the committed ``dashboard.json``, so the
    commit recorded here (HEAD when the data was last regenerated) is the deployed
    snapshot's version. Guarded — git may be absent in a build image, and a
    missing build block must degrade to "unavailable", never crash the export.
    """

    def _git(*args: str) -> str:
        return subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()

    # NOTE: the working `branch` is deliberately NOT recorded. It is transient, generator-host
    # junk (a checkout records "claude/<x>" or detached "HEAD"), carries no value in a deployed
    # snapshot, and — like the old wall-clock generated_at — is a needless drift/conflict source
    # whenever two branches regenerate the file. The /status template already guards on its absence
    # (`{% if build.branch %}`). Removed 2026-06-21 (the #1261 conflict root cause).
    try:
        return {
            "commit": _git("rev-parse", "--short", "HEAD"),
            "subject": _git("log", "-1", "--format=%s"),
            "committed_at": _git(
                "log",
                "-1",
                "--format=%cd",
                "--date=format:%Y-%m-%dT%H:%M:%SZ",
            ),
        }
    except (OSError, subprocess.SubprocessError):
        return {}


def build_data(repo_root: Path = REPO_ROOT) -> dict:
    """Read every source and assemble the dashboard data payload."""
    registry = repo_root / "disbot" / "utils" / "subsystem_registry.py"
    ideas_dir = repo_root / "docs" / "ideas"
    bug_book = repo_root / "docs" / "health" / "bug-book.md"
    review_inbox = repo_root / "docs" / "owner" / "review-inbox.md"
    sessions_dir = repo_root / ".sessions"
    bot_changelog_file = repo_root / "docs" / "bot-changelog.md"

    catalogue = (
        parse_catalogue(registry.read_text(encoding="utf-8"))
        if registry.exists()
        else []
    )
    ideas = parse_ideas(ideas_dir) if ideas_dir.is_dir() else []
    bugs = parse_bugs(bug_book.read_text(encoding="utf-8")) if bug_book.exists() else []
    reviews = (
        parse_reviews(review_inbox.read_text(encoding="utf-8"))
        if review_inbox.exists()
        else []
    )
    updates = parse_updates(sessions_dir) if sessions_dir.is_dir() else []
    bot_changelog = (
        parse_bot_changelog(bot_changelog_file.read_text(encoding="utf-8"))
        if bot_changelog_file.exists()
        else []
    )
    telemetry = parse_telemetry(repo_root / "telemetry" / "model-usage.jsonl")

    scan_root = repo_root / "disbot"
    env_usage = (
        _load_scan_env_usage()(scan_root=scan_root, repo_root=repo_root)
        if scan_root.is_dir()
        else []
    )
    cogs = (
        _load_scan_commands()(repo_root=repo_root)
        if (repo_root / "disbot" / "cogs").is_dir()
        else []
    )

    keys_dir = repo_root / "disbot" / "utils" / "settings_keys"
    settings = (
        _load_sibling("scan_settings.py", "scan_settings")(keys_dir=keys_dir)
        if keys_dir.is_dir()
        else []
    )
    cogs_dir = repo_root / "disbot" / "cogs"
    specs = (
        _load_sibling("scan_setting_specs.py", "scan_setting_specs")(
            cogs_dir=cogs_dir,
            keys_dir=keys_dir,
        )
        if cogs_dir.is_dir()
        else []
    )
    # Enrich each settings key with its typed SettingSpec metadata (type,
    # default, hint, enum choices) where the bot declares one.
    spec_by_key = {s["settings_key"]: s for s in specs if s["settings_key"]}
    for domain in settings:
        for entry in domain["keys"]:
            spec = spec_by_key.get(entry["key"])
            if spec is not None:
                entry["type"] = spec["value_type"]
                entry["hint"] = spec["hint"]
                entry["allowed_values"] = spec["allowed_values"]
                if spec["default_known"]:
                    entry["default"] = spec["default"]
    registry_path = repo_root / "disbot" / "utils" / "subsystem_registry.py"
    access = (
        _load_sibling("scan_access.py", "scan_access")(registry=registry_path)
        if registry_path.exists()
        else {"tiers": [], "total_visible": 0, "internal_count": 0}
    )
    synonyms_path = repo_root / "disbot" / "utils" / "synonyms.py"
    synonyms = (
        _load_sibling("scan_synonyms.py", "scan_synonyms")(path=synonyms_path)
        if synonyms_path.exists()
        else []
    )

    # `generated_at` is DETERMINISTIC: the latest commit's time, NOT wall-clock. The committed
    # dashboard.json is a pure function of committed source — so two regenerations at the same
    # commit are byte-identical. A wall-clock timestamp here (the pre-2026-06-21 behavior) changed
    # on every run, which (a) made the refresh workflow churn a PR every cadence even with no real
    # change and (b) GUARANTEED a merge conflict whenever two branches both regenerated the file
    # (each wrote a different second into the same line) — the #1261 root cause. Commit time is the
    # honest "data as of" signal for a committed snapshot and never conflicts at the same commit.
    # Falls back to wall-clock only if git is unavailable (no commit context to anchor to).
    build = _git_meta(repo_root)
    generated_at = build.get("committed_at") or dt.datetime.now(
        dt.timezone.utc,
    ).strftime(
        "%Y-%m-%dT%H:%M:%SZ",
    )
    return {
        "meta": {
            "generated_at": generated_at,
            "build": build,
            "counts": {
                "functions": len(catalogue),
                "ideas": len(ideas),
                "bugs": len(bugs),
                "reviews": len(reviews),
                "reviews_open": sum(
                    1 for r in reviews if r["status"].upper() == "OPEN"
                ),
                "updates": len(updates),
                "env_vars": len(env_usage),
                "cogs": sum(1 for c in cogs if c.get("is_cog")),
                "commands": sum(len(c["commands"]) for c in cogs),
                "setting_keys": sum(len(d["keys"]) for d in settings),
                "setting_domains": len(settings),
                "typed_settings": len(specs),
                "visible_subsystems": access.get("total_visible", 0),
                "synonyms": sum(len(s["synonyms"]) for s in synonyms),
                "bot_changelog": len(bot_changelog),
            },
        },
        "catalogue": catalogue,
        "ideas": ideas,
        "bugs": bugs,
        "reviews": reviews,
        "updates": updates,
        "bot_changelog": bot_changelog,
        "telemetry": telemetry,
        "env_usage": env_usage,
        "cogs": cogs,
        "settings": settings,
        "access": access,
        "synonyms": synonyms,
    }


# ---------------------------------------------------------------------------
# Public subset (botsite/data/site.json) — plan §5 / §2.2
# ---------------------------------------------------------------------------
# Game categories the marketing "features showcase" treats as games (the
# `/features` page merges the function catalogue + games; the public counts
# expose only catalogue counts, never server/user totals — plan layout note).
_GAME_CATEGORIES: frozenset[str] = frozenset({"games"})
# Public catalogue fields — declared metadata only (name/description/category/
# badges). Omits internal-only fields like ``capabilities`` and ``entry_points``
# (operator wiring, not user marketing) and ``visibility_mode`` (an internal flag).
# The entry-projection source is :data:`SITE_CATALOGUE_ENTRY_FIELDS` (declared up top
# with the other public field contracts); the full output contract (these + the derived
# ``badges`` / ``is_game``) is :data:`SITE_CATALOGUE_FIELDS`.


def _site_catalogue(catalogue: list[dict]) -> list[dict]:
    """Project the full catalogue to the public, user-safe metadata subset.

    ``badges`` is a small derived, user-facing list (currently the category), kept
    deliberately generic so the showcase can render a chip without leaking the
    internal ``visibility_tier`` / ``capabilities``.
    """
    out: list[dict] = []
    for entry in catalogue:
        projected = {f: entry.get(f) for f in SITE_CATALOGUE_ENTRY_FIELDS if f in entry}
        category = entry.get("category")
        projected["badges"] = [category] if category else []
        projected["is_game"] = category in _GAME_CATEGORIES
        out.append(projected)
    return out


def _command_description(doc: str) -> str | None:
    """The command's full first docstring *paragraph*, or ``None`` if no docstring.

    Richer than the one-line ``brief``/``usage``: collects the leading run of
    non-blank lines (stopping at the first blank line), strips Sphinx cross-reference
    roles (``:class:`X``` → ``X``) and markdown noise, and collapses whitespace. A
    docstring-less command returns ``None`` (never invented prose — plan S1.1).
    """
    if not doc:
        return None
    lines = doc.splitlines()
    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    paragraph: list[str] = []
    while index < len(lines) and lines[index].strip():
        paragraph.append(lines[index].strip())
        index += 1
    if not paragraph:
        return None
    text = _SPHINX_ROLE_RE.sub(r"\1", " ".join(paragraph))
    cleaned = _strip_md(text)
    return cleaned or None


def _command_examples(doc: str) -> list[str]:
    """Real ``!command …`` invocation snippets lifted verbatim from the docstring.

    Only backtick-wrapped invocations are taken (a bare ``!`` in prose is never an
    example), de-duplicated in first-seen order, whitespace-collapsed, and length-
    capped. ``[]`` when the docstring has none — never fabricated.
    """
    out: list[str] = []
    for match in _DOC_EXAMPLE_RE.finditer(doc or ""):
        example = " ".join(match.group(1).split())
        if example and example not in out:
            out.append(_truncate(example, 120))
    return out


def _command_docstrings(repo_root: Path) -> dict[tuple[str, str], str]:
    """Map ``(rel_file, command_name)`` -> the command method's full docstring.

    Re-parses the same files :func:`scripts.scan_commands.scan_commands` reads (the
    cogs tree + ``bot1.py``) so S1.1 can derive the richer ``description`` /
    ``examples`` fields **without editing the scanner** (its exclusive owner is the
    merged S1 unit). The command *name* uses the same resolution the scanner does —
    the decorator's ``name=`` kwarg when present, else the method name — so the join
    in :func:`_site_commands` lines up with the scanner's ``name`` field. A file that
    fails to parse is skipped (mirrors the scanner's tolerance).
    """
    cogs_dir = repo_root / "disbot" / "cogs"
    files = sorted(cogs_dir.rglob("*.py")) if cogs_dir.is_dir() else []
    bot1 = repo_root / "disbot" / "bot1.py"
    if bot1.exists():
        files.append(bot1)
    out: dict[tuple[str, str], str] = {}
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        rel = str(path.relative_to(repo_root))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            call = _command_decorator_call(node)
            if call is _NOT_A_COMMAND:
                continue
            name = call  # the resolved command name (str)
            doc = ast.get_docstring(node) or ""
            # First writer wins for a duplicated (file, name) — deterministic with the
            # sorted walk; the docstring map is best-effort enrichment either way.
            out.setdefault((rel, name), doc)
    return out


# Sentinel: the function carries no command/group decorator (distinct from a command
# whose resolved name is the falsy-but-valid method name).
_NOT_A_COMMAND = object()


def _command_decorator_call(node: ast.FunctionDef | ast.AsyncFunctionDef) -> object:
    """Resolve a command method's *name* from its decorator, or ``_NOT_A_COMMAND``.

    Recognises the same decorator vocabulary as the scanner (``commands.command`` /
    ``group`` / ``hybrid_*`` / ``app_commands.*`` and ``<group>.command`` /
    ``.group`` subcommand leaves). Returns the ``name=`` kwarg when the decorator
    sets one, else the method name — matching ``scan_commands`` so the docstring map
    keys join cleanly to the scanned command records.
    """
    command_leaves = {"command", "group", "hybrid_command", "hybrid_group"}
    for dec in node.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        leaf: str | None = None
        if isinstance(target, ast.Attribute):
            leaf = target.attr
        elif isinstance(target, ast.Name):
            leaf = target.id
        if leaf not in command_leaves:
            continue
        if isinstance(dec, ast.Call):
            for kw in dec.keywords:
                if kw.arg == "name":
                    try:
                        value = ast.literal_eval(kw.value)
                    except (ValueError, TypeError, SyntaxError):
                        value = None
                    if isinstance(value, str):
                        return value
        return node.name
    return _NOT_A_COMMAND


def _subsystem_open_work(
    ideas: list[dict],
    bugs: list[dict],
    catalogue: list[dict],
) -> dict[str, dict]:
    """Map each subsystem key -> its linked open ideas + whether it has open work.

    The linking prefers an idea's **explicit** ``Subsystem:`` tag
    (:func:`_subsystem_tags`) when present, and falls back to a **heuristic name-match**
    for un-tagged ideas, tuned to keep false positives low: a subsystem matches an
    un-tagged idea when every token of its key (``rps_tournament`` -> ``rps`` +
    ``tournament``) appears as a whole token in the idea's **filename slug** — the
    curated, topical part — rather than the free-text title (which drags in generic-word
    false matches). Bugs match on their (short, topical) title.
    Returns, per subsystem key::

        {"in_progress": bool, "ideas": [{"title", "status"}, ...]}

    ``in_progress`` is True iff the subsystem has at least one OPEN idea or OPEN bug.
    ``ideas`` carries only **open** ideas as **title + status** (redaction — never the
    raw idea body). Subsystems with no linked open work are absent from the map (the
    caller defaults them to ``finished`` / ``[]``).

    The explicit tag is the durable fix for the heuristic's one weakness — a single-word
    subsystem key that is also a common slug word cross-matching an unrelated idea (e.g.
    ``chain`` ~ an agent "self-chaining" workflow idea). Tag such an idea ``Subsystem:
    none`` and it links to nothing; tag a real one ``Subsystem: <key>`` and the link
    becomes authoritative. Un-tagged ideas keep the (safe, title+status-only) heuristic.
    """

    def _tokens(text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    keys = [e.get("key") for e in catalogue if isinstance(e.get("key"), str)]
    open_ideas = [
        i for i in ideas if (i.get("status") or "").lower() in _OPEN_IDEA_STATUSES
    ]
    open_bugs = [
        b for b in bugs if (b.get("status") or "").upper() in _OPEN_BUG_STATUSES
    ]

    def _idea_matches(idea: dict, key: str, key_parts: list[str]) -> bool:
        """Explicit ``Subsystem:`` tag wins; un-tagged ideas use the slug heuristic."""
        tags = idea.get("subsystems")
        if tags is not None:  # explicitly tagged ([] means "links to nothing")
            return key in tags
        slug = _tokens(idea.get("file", ""))
        return all(part in slug for part in key_parts)

    result: dict[str, dict] = {}
    for key in keys:
        key_parts = key.split("_")
        linked_ideas: list[dict] = []
        for idea in open_ideas:
            if _idea_matches(idea, key, key_parts):
                linked_ideas.append(
                    {
                        "title": idea.get("title") or "",
                        "status": idea.get("status") or "",
                    },
                )
        has_open_bug = any(
            all(part in _tokens(bug.get("title", "")) for part in key_parts)
            for bug in open_bugs
        )
        if linked_ideas or has_open_bug:
            result[key] = {
                "in_progress": True,
                "ideas": linked_ideas,
            }
    return result


def _site_commands(
    cogs: list[dict],
    catalogue: list[dict],
    *,
    docstrings: dict[tuple[str, str], str] | None = None,
    subsystem_work: dict[str, dict] | None = None,
) -> list[dict]:
    """Build the public command reference (no per-guild value, ever).

    Each command exposes exactly :data:`SITE_COMMAND_FIELDS` — repo-level metadata
    only. ``category`` and ``permissions`` are joined from the command's owning
    subsystem catalogue entry (``category`` = the subsystem category; ``permissions``
    = its declared ``visibility_tier`` — the honest static "who can see this" signal,
    NOT a per-guild grant). ``usage`` is the one-line ``brief``; ``description`` /
    ``examples`` come from the command's full docstring (``docstrings`` map, keyed by
    ``(file, name)``); ``status`` / ``linked_ideas`` come from the subsystem's open
    work (``subsystem_work`` map). ``use_cases`` / ``notes`` / ``cooldown`` are
    reserved ``None`` (no honest static source — never fabricated). Subcommands are
    listed too (they are real commands; the browser can group by name).
    """
    docstrings = docstrings or {}
    subsystem_work = subsystem_work or {}
    sysmap = {c.get("key"): c for c in catalogue}
    out: list[dict] = []
    for cog in cogs:
        subsystem = cog.get("subsystem") or ""
        sys_entry = sysmap.get(subsystem, {})
        cog_file = cog.get("file") or ""
        work = subsystem_work.get(subsystem, {})
        for cmd in cog.get("commands", []):
            name = cmd.get("name")
            doc = docstrings.get((cog_file, name), "")
            out.append(
                {
                    "name": name,
                    "aliases": list(cmd.get("aliases") or []),
                    "category": sys_entry.get("category") or "other",
                    "cooldown": None,
                    "permissions": sys_entry.get("visibility_tier") or "",
                    "usage": cmd.get("brief") or "",
                    "description": _command_description(doc),
                    "use_cases": None,
                    "examples": _command_examples(doc),
                    "status": (
                        COMMAND_STATUS_IN_PROGRESS
                        if work.get("in_progress")
                        else COMMAND_STATUS_FINISHED
                    ),
                    "linked_ideas": list(work.get("ideas") or []),
                    "notes": None,
                },
            )
    out.sort(key=lambda c: ((c.get("category") or ""), (c.get("name") or "")))
    return out


def build_site_subset(data: dict, *, repo_root: Path = REPO_ROOT) -> dict:
    """Derive the public ``site.json`` subset from the full dashboard payload.

    Returns a dict whose top-level keys are **exactly** :data:`SITE_TOPLEVEL_KEYS`
    — redaction by construction (plan §2.2). It carries only user-safe families:
    a slim ``meta`` (build provenance only), public catalogue ``counts``
    (commands/features/games — never server/user totals), a metadata-only
    ``catalogue``, a value-free ``commands`` reference (enriched per S1.1 with
    description/examples/status/linked-ideas for the interactive browser, all
    repo-level metadata only), and the curated ``bot_changelog``. Everything
    dev-only (``env_usage`` / ``settings`` / ``access`` / ``reviews`` / ``ideas`` /
    raw ``bugs`` / ``cogs``) is dropped.

    ``repo_root`` is used only to re-read command docstrings for the S1.1
    enrichment (the scanner, S1's exclusive file, doesn't expose full docstrings);
    it degrades gracefully (no docstrings → ``description``/``examples`` empty) so a
    payload built elsewhere still produces a valid subset.
    """
    meta = data.get("meta", {})
    catalogue = data.get("catalogue", [])
    cogs = data.get("cogs", [])
    ideas = data.get("ideas", [])
    bugs = data.get("bugs", [])

    site_catalogue = _site_catalogue(catalogue)
    docstrings = _command_docstrings(repo_root)
    subsystem_work = _subsystem_open_work(ideas, bugs, catalogue)
    site_commands = _site_commands(
        cogs,
        catalogue,
        docstrings=docstrings,
        subsystem_work=subsystem_work,
    )
    games = sum(1 for e in site_catalogue if e.get("is_game"))

    subset = {
        # meta: build provenance only (sha/subject/date) + generation stamp. NO
        # private counts here — the public counts live in the separate ``counts``
        # family below, scoped to catalogue totals only.
        "meta": {
            "generated_at": meta.get("generated_at", ""),
            "build": meta.get("build", {}),
        },
        # counts: catalogue totals ONLY (plan §5). Never server/user totals — those
        # would require the deferred live source (plan §3, post-security-review).
        "counts": {
            "commands": len(site_commands),
            "features": len(site_catalogue),
            "games": games,
        },
        "catalogue": site_catalogue,
        "commands": site_commands,
        "bot_changelog": data.get("bot_changelog", []),
    }
    # Defensive: guarantee the contract the CI whitelist asserts. If a future edit
    # adds a key here, this raises in the producer/tests before it can ship.
    extra = set(subset) - SITE_TOPLEVEL_KEYS
    if extra:
        raise ValueError(
            f"site.json subset produced disallowed top-level keys: {sorted(extra)} "
            f"(allowed: {sorted(SITE_TOPLEVEL_KEYS)})",
        )
    return subset


def build_console_subset(data: dict) -> dict:
    """Derive the program-console feed from the full dashboard payload.

    Returns a dict whose top-level keys are **exactly**
    :data:`CONSOLE_TOPLEVEL_KEYS` — redaction by construction, mirroring
    :func:`build_site_subset`. The console (the owner's one-glance page at
    ``/console``) gets: build provenance, the session run-report feed (with the
    ``self_initiated`` ⚑ flag, Q-0172 accountability), ideas/bugs as **counters
    plus open-bug titles** (never full bodies), and the curated changelog.
    """
    meta = data.get("meta", {}) or {}
    ideas = data.get("ideas", []) or []
    bugs = data.get("bugs", []) or []
    updates = data.get("updates", []) or []

    def _by_status(items: list[dict]) -> dict[str, int]:
        return _count_states(
            [str(item.get("status") or "unknown").lower() for item in items],
        )

    def _count_states(states_list: list[str]) -> dict[str, int]:
        out: dict[str, int] = {}
        for key in states_list:
            out[key] = out.get(key, 0) + 1
        return dict(sorted(out.items()))

    def _bug_state(bug: dict) -> str:
        """Effective bug state: the parsed status, else the title-tail verdict.

        The bug book records outcomes in the title suffix ("… — FIXED (root)")
        and the scanner's ``status`` field is often ``unknown`` — deriving from
        the tail keeps the console's open-bug count honest instead of listing
        long-fixed bugs as open.
        """
        parsed = str(bug.get("status") or "").lower()
        if parsed and parsed != "unknown":
            return parsed
        title = str(bug.get("title") or "").upper()
        if "PARTIALLY FIXED" in title:
            return "partial"
        # em-dash only: the bug book's verdict convention is "… — FIXED (root)";
        # a plain hyphen would false-match mid-title words like "quick-fixed".
        if re.search(r"—\s*FIXED\b", title):
            return "fixed"
        if re.search(r"—\s*EXPECTED\b", title):
            return "expected"
        if re.search(r"—\s*OPEN\b", title):
            return "open"
        return "unknown"

    closed = {"fixed", "closed", "resolved", "wontfix", "done", "expected"}
    states = [(b, _bug_state(b)) for b in bugs]
    all_open = [
        {"id": b.get("id"), "title": b.get("title"), "status": state}
        for b, state in states
        if state not in closed
    ]
    open_bugs = all_open[:10]  # the list is capped; open_count carries the truth

    sessions = [
        {field: entry.get(field) for field in CONSOLE_SESSION_FIELDS}
        for entry in updates
    ]

    subset = {
        "meta": {
            "generated_at": meta.get("generated_at"),
            "build": meta.get("build", {}),
            # The cross-repo shape-contract version (console_data_contract.json):
            # consumers (websites' dashboard /console) pin the version they were
            # built against and verify it here at render time.
            "schema_version": CONSOLE_SCHEMA_VERSION,
        },
        "sessions": sessions,
        "ideas": {"total": len(ideas), "by_status": _by_status(ideas)},
        "bugs": {
            "total": len(bugs),
            "by_status": _count_states([state for _, state in states]),
            "open_count": len(all_open),
            "open": open_bugs,
        },
        "bot_changelog": data.get("bot_changelog", []),
        # The declared "Model & spend telemetry" lane's feed (kit-lab plan §7.3):
        # already field-whitelisted by parse_telemetry — repo-development metadata
        # only, never per-guild/user values.
        "telemetry": data.get("telemetry", []) or [],
    }
    extra = set(subset) - CONSOLE_TOPLEVEL_KEYS
    if extra:
        raise ValueError(
            f"console.json subset produced disallowed top-level keys: {sorted(extra)} "
            f"(allowed: {sorted(CONSOLE_TOPLEVEL_KEYS)})",
        )
    return subset


def _write_json(out: Path, payload: dict) -> str:
    """Write ``payload`` as pretty JSON to ``out`` and return its repo-relative path."""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return str(out.relative_to(REPO_ROOT) if out.is_relative_to(REPO_ROOT) else out)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: write the JSON artifact(s) (or print the summary).

    By default writes **both** ``dashboard.json`` (full) and ``site.json`` (public
    subset) from one in-memory build (plan §2.2 — single producer). ``--targets``
    selects which to emit; ``--check`` prints the full payload's meta and writes
    nothing.
    """
    parser = argparse.ArgumentParser(
        description="Export the web data to JSON (dashboard full payload + bot-site public subset).",
    )
    parser.add_argument(
        "--targets",
        choices=("both", "dashboard", "site", "console"),
        default="both",
        help="which artifact(s) to write (default: both = dashboard + site + console)",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_FILE),
        help="dashboard.json output path",
    )
    parser.add_argument(
        "--site-output",
        default=str(SITE_OUTPUT_FILE),
        help="site.json (public subset) output path",
    )
    parser.add_argument(
        "--data-js-output",
        default=str(DATA_JS_OUTPUT_FILE),
        help="botsite/site/data.js (SPA data layer) output path; redirect in tests "
        "so they never clobber the tracked repo file",
    )
    parser.add_argument(
        "--console-output",
        default=str(CONSOLE_OUTPUT_FILE),
        help="console.json (program-console feed) output path",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="print the meta summary without writing any file",
    )
    args = parser.parse_args(argv)

    data = build_data()
    if args.check:
        print(json.dumps(data["meta"], indent=2))
        return 0

    if args.targets in ("both", "dashboard"):
        rel = _write_json(Path(args.output), data)
        print(f"wrote {rel} — {data['meta']['counts']}")
    if args.targets in ("both", "site"):
        subset = build_site_subset(data)
        rel = _write_json(Path(args.site_output), subset)
        print(f"wrote {rel} — {subset['counts']}")
        # Regenerate the SPA data layer (botsite/site/data.js) from the same subset,
        # so the design site stays in lock-step with site.json (one pipeline). The
        # builder lives inside botsite/ (stdlib-only, no disbot); load it by file
        # path (the script may run with scripts/ — not the repo root — on sys.path).
        import importlib.util

        sd_path = REPO_ROOT / "botsite" / "site_data.py"
        spec = importlib.util.spec_from_file_location("botsite_site_data", sd_path)
        if spec is None or spec.loader is None:  # pragma: no cover - defensive
            raise RuntimeError(f"cannot load {sd_path}")
        site_data = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(site_data)

        data_js = Path(args.data_js_output)
        data_js.parent.mkdir(parents=True, exist_ok=True)
        data_js.write_text(site_data.render_from_site(subset), encoding="utf-8")
        print(f"wrote {data_js} (SPA data layer)")
    if args.targets in ("both", "console"):
        console = build_console_subset(data)
        rel = _write_json(Path(args.console_output), console)
        print(f"wrote {rel} — console feed ({len(console['sessions'])} sessions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
