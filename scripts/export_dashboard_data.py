#!/usr/bin/env python3.10
"""Export the developer dashboard's read-only data to JSON (stdlib only).

The developer dashboard (``docs/planning/developer-dashboard-plan.md``) is a
decoupled web app under ``dashboard/`` that must **not** import ``disbot/``. This
script is the seam between the two: it reads the repo's existing structured
sources and serialises them to ``dashboard/data/dashboard.json``, which the
FastAPI app renders.

Sources (all read-only, never imported):

* Bot-function catalogue  <- ``disbot/utils/subsystem_registry.py`` (AST-parsed)
* Ideas                   <- ``docs/ideas/*.md`` (title + Status badge + date)
* Bugs                    <- ``docs/health/bug-book.md`` (``## BUG-NNNN ...``)
* Updates feed            <- ``.sessions/*.md`` (date + title + Status badge)
* Env-var usage map       <- ``disbot/**/*.py`` via ``scripts/scan_env_usage.py``
                             (names + code locations only — never a value)

Pure stdlib so it runs in CI with no extra dependencies and the dashboard's web
dependencies (fastapi, uvicorn, ...) never enter the bot's ``requirements.txt``.
Re-run after the sources change::

    python3.10 scripts/export_dashboard_data.py

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
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO_ROOT / "dashboard" / "data" / "dashboard.json"


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
            },
        )
    updates.sort(key=lambda e: (e["date"], e["file"]), reverse=True)
    return updates[:limit]


def build_data(repo_root: Path = REPO_ROOT) -> dict:
    """Read every source and assemble the dashboard data payload."""
    registry = repo_root / "disbot" / "utils" / "subsystem_registry.py"
    ideas_dir = repo_root / "docs" / "ideas"
    bug_book = repo_root / "docs" / "health" / "bug-book.md"
    sessions_dir = repo_root / ".sessions"

    catalogue = (
        parse_catalogue(registry.read_text(encoding="utf-8"))
        if registry.exists()
        else []
    )
    ideas = parse_ideas(ideas_dir) if ideas_dir.is_dir() else []
    bugs = parse_bugs(bug_book.read_text(encoding="utf-8")) if bug_book.exists() else []
    updates = parse_updates(sessions_dir) if sessions_dir.is_dir() else []

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
            "counts": {
                "functions": len(catalogue),
                "ideas": len(ideas),
                "bugs": len(bugs),
                "updates": len(updates),
                "env_vars": len(env_usage),
                "cogs": sum(1 for c in cogs if c.get("is_cog")),
                "commands": sum(len(c["commands"]) for c in cogs),
                "setting_keys": sum(len(d["keys"]) for d in settings),
                "setting_domains": len(settings),
                "typed_settings": len(specs),
                "visible_subsystems": access.get("total_visible", 0),
                "synonyms": sum(len(s["synonyms"]) for s in synonyms),
            },
        },
        "catalogue": catalogue,
        "ideas": ideas,
        "bugs": bugs,
        "updates": updates,
        "env_usage": env_usage,
        "cogs": cogs,
        "settings": settings,
        "access": access,
        "synonyms": synonyms,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: write the JSON payload (or print its summary)."""
    parser = argparse.ArgumentParser(description="Export dashboard data to JSON.")
    parser.add_argument("--output", default=str(OUTPUT_FILE), help="output JSON path")
    parser.add_argument(
        "--check",
        action="store_true",
        help="print the meta summary without writing the file",
    )
    args = parser.parse_args(argv)

    data = build_data()
    if args.check:
        print(json.dumps(data["meta"], indent=2))
        return 0

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    rel = out.relative_to(REPO_ROOT) if out.is_relative_to(REPO_ROOT) else out
    print(f"wrote {rel} — {data['meta']['counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
