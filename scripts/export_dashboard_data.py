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
# Per-command fields the public ``commands`` reference exposes (no per-guild value
# ever appears — these are repo-level command metadata). ``usage`` is the one-line
# description (the AST scanner's ``brief``); ``category`` + ``permissions`` are
# joined from the command's subsystem catalogue entry; ``cooldown`` is reserved
# (the AST scanner does not statically resolve runtime cooldown decorators today,
# so it is emitted as ``null`` rather than fabricated — see :func:`build_site_subset`).
SITE_COMMAND_FIELDS: tuple[str, ...] = (
    "name",
    "aliases",
    "category",
    "cooldown",
    "permissions",
    "usage",
)


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
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
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

    return {
        "meta": {
            "generated_at": dt.datetime.now(dt.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ",
            ),
            "build": _git_meta(repo_root),
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
_SITE_CATALOGUE_FIELDS: tuple[str, ...] = (
    "key",
    "display_name",
    "description",
    "emoji",
    "category",
    "tags",
)


def _site_catalogue(catalogue: list[dict]) -> list[dict]:
    """Project the full catalogue to the public, user-safe metadata subset.

    ``badges`` is a small derived, user-facing list (currently the category), kept
    deliberately generic so the showcase can render a chip without leaking the
    internal ``visibility_tier`` / ``capabilities``.
    """
    out: list[dict] = []
    for entry in catalogue:
        projected = {f: entry.get(f) for f in _SITE_CATALOGUE_FIELDS if f in entry}
        category = entry.get("category")
        projected["badges"] = [category] if category else []
        projected["is_game"] = category in _GAME_CATEGORIES
        out.append(projected)
    return out


def _site_commands(cogs: list[dict], catalogue: list[dict]) -> list[dict]:
    """Build the public command reference (no per-guild value, ever).

    Each command exposes exactly :data:`SITE_COMMAND_FIELDS`. ``category`` and
    ``permissions`` are joined from the command's owning subsystem catalogue entry
    (``category`` = the subsystem category; ``permissions`` = its declared
    ``visibility_tier`` — the honest static "who can see this" signal, NOT a
    per-guild grant). ``usage`` is the command's one-line description (the AST
    scanner's ``brief``). ``cooldown`` is reserved/``None`` — runtime cooldown
    decorators are not statically resolved by the scanner today, so it is left
    unset rather than fabricated. Subcommands are skipped (the reference lists
    top-level commands; a later page can expand groups).
    """
    sysmap = {c.get("key"): c for c in catalogue}
    out: list[dict] = []
    for cog in cogs:
        subsystem = cog.get("subsystem") or ""
        sys_entry = sysmap.get(subsystem, {})
        for cmd in cog.get("commands", []):
            out.append(
                {
                    "name": cmd.get("name"),
                    "aliases": list(cmd.get("aliases") or []),
                    "category": sys_entry.get("category") or "other",
                    "cooldown": None,
                    "permissions": sys_entry.get("visibility_tier") or "",
                    "usage": cmd.get("brief") or "",
                },
            )
    out.sort(key=lambda c: ((c.get("category") or ""), (c.get("name") or "")))
    return out


def build_site_subset(data: dict) -> dict:
    """Derive the public ``site.json`` subset from the full dashboard payload.

    Returns a dict whose top-level keys are **exactly** :data:`SITE_TOPLEVEL_KEYS`
    — redaction by construction (plan §2.2). It carries only user-safe families:
    a slim ``meta`` (build provenance only), public catalogue ``counts``
    (commands/features/games — never server/user totals), a metadata-only
    ``catalogue``, a value-free ``commands`` reference, and the curated
    ``bot_changelog``. Everything dev-only (``env_usage`` / ``settings`` /
    ``access`` / ``reviews`` / ``ideas`` / raw ``bugs`` / ``cogs``) is dropped.
    """
    meta = data.get("meta", {})
    catalogue = data.get("catalogue", [])
    cogs = data.get("cogs", [])

    site_catalogue = _site_catalogue(catalogue)
    site_commands = _site_commands(cogs, catalogue)
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
        choices=("both", "dashboard", "site"),
        default="both",
        help="which artifact(s) to write (default: both)",
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
