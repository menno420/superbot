"""Fetch BTD6 tower and hero data from the Bloons wiki MediaWiki API.

Reads ``data/btd6/towers.csv`` and ``data/btd6/heroes.csv``, fetches
structured gameplay data from the Bloons fandom wiki for each entry, and
writes updated CSVs with the fetched fields filled in.

Fields fetched:
  towers  — base_cost, top_1..top_5, mid_1..mid_5, bot_1..bot_5
  heroes  — base_cost, ability_3_name, ability_3_summary,
             ability_10_name, ability_10_summary

Fields intentionally skipped:
  description — fill these manually; wiki prose is CC-BY-SA and copying
                verbatim creates an attribution obligation.

Usage::

    python3.10 scripts/fetch_btd6_wiki_data.py
    python3.10 scripts/fetch_btd6_wiki_data.py --dry-run
    python3.10 scripts/fetch_btd6_wiki_data.py --delay 1.5
    python3.10 scripts/fetch_btd6_wiki_data.py --towers-csv path/to/towers.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_TOWERS_CSV = _REPO_ROOT / "data" / "btd6" / "towers.csv"
_DEFAULT_HEROES_CSV = _REPO_ROOT / "data" / "btd6" / "heroes.csv"

_API_BASE = "https://bloons.fandom.com/api.php"
_USER_AGENT = (
    "SuperBot-BTD6-DataFetch/1.0 "
    "(https://github.com/menno420/superbot; bot data pipeline)"
)
_DEFAULT_DELAY = 1.0  # seconds between API requests

# ---------------------------------------------------------------------------
# Wiki API
# ---------------------------------------------------------------------------


def _fetch_wikitext_raw(page_title: str) -> str | None:
    """Return raw wikitext for *page_title*, or None if the page is missing."""
    params = urllib.parse.urlencode(
        {
            "action": "parse",
            "page": page_title,
            "prop": "wikitext",
            "format": "json",
        },
    )
    url = f"{_API_BASE}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"    HTTP error: {exc}")
        return None

    if "error" in data:
        # API returns {"error": {"code": "missingtitle", ...}} for missing pages
        return None

    return data.get("parse", {}).get("wikitext", {}).get("*")


def _fetch_wikitext(page_title: str) -> str | None:
    """Return raw wikitext, following #REDIRECT if the page is a redirect."""
    wikitext = _fetch_wikitext_raw(page_title)
    if wikitext is None:
        return None
    redirect_m = re.match(r"#REDIRECT\s*\[\[([^\]]+)\]\]", wikitext, re.IGNORECASE)
    if redirect_m:
        target = redirect_m.group(1).strip()
        wikitext = _fetch_wikitext_raw(target)
    return wikitext


def _btd6_page_title(wiki_url: str) -> str:
    """Derive the BTD6 subpage title from a fandom wiki URL.

    E.g. https://bloons.fandom.com/wiki/Dart_Monkey → Dart_Monkey_(BTD6)
    """
    page = wiki_url.rstrip("/").rsplit("/wiki/", 1)[-1]
    return f"{page}_(BTD6)"


# ---------------------------------------------------------------------------
# Wikitext parsing — shared helpers
# ---------------------------------------------------------------------------


def _extract_medium_cost(wikitext: str) -> int | None:
    """Extract the Medium difficulty base cost from wikitext.

    Handles both infobox forms:
      $315 ([[Medium Difficulty|Medium]])    — towers
      *$540 ([[Medium Difficulty|Medium]])   — heroes (bullet list)
    """
    # Primary: [[Medium Difficulty|Medium]] link style
    m = re.search(r"\$([0-9,]+)\s*\(\[\[Medium", wikitext)
    if m:
        return int(m.group(1).replace(",", ""))
    # Fallback: plain "(Medium)" text
    m = re.search(r"\$([0-9,]+)\s*\(Medium", wikitext)
    if m:
        return int(m.group(1).replace(",", ""))
    return None


def _find_template_blocks(wikitext: str, template_name: str) -> list[str]:
    """Return all ``{{template_name ...}}`` blocks via bracket counting.

    Uses bracket depth tracking so nested templates inside upgrade blocks
    are handled correctly.
    """
    results: list[str] = []
    pattern = re.compile(r"\{\{" + re.escape(template_name) + r"\b", re.IGNORECASE)
    for m in pattern.finditer(wikitext):
        start = m.start()
        depth = 0
        i = start
        limit = len(wikitext) - 1
        while i <= limit:
            two = wikitext[i : i + 2]
            if two == "{{":
                depth += 1
                i += 2
            elif two == "}}":
                depth -= 1
                if depth == 0:
                    results.append(wikitext[start : i + 2])
                    break
                i += 2
            else:
                i += 1
    return results


def _get_template_param(block: str, param: str) -> str | None:
    """Extract the value of a named parameter from a template block.

    Stops at the next pipe ``|``, closing ``}}``, or end of string.
    """
    m = re.search(
        r"\|\s*" + re.escape(param) + r"\s*=\s*(.*?)(?=\n\s*\||\n\s*\}\}|\}\}|$)",
        block,
        re.DOTALL,
    )
    if m:
        return m.group(1).strip()
    return None


# ---------------------------------------------------------------------------
# Tower parsing
# ---------------------------------------------------------------------------


def _extract_tower_data(wikitext: str) -> dict[str, Any]:
    """Parse cost and all 15 upgrade names from a tower's BTD6 wikitext.

    Returns::

        {
            "cost": int | None,
            "upgrades": [[top_1..top_5], [mid_1..mid_5], [bot_1..bot_5]] | None,
            "warnings": [str, ...],
        }
    """
    warnings: list[str] = []
    cost = _extract_medium_cost(wikitext)
    if cost is None:
        warnings.append("could not extract Medium cost")

    # Split wikitext at ===Path N=== section headers (Path 1/2/3)
    header_re = re.compile(r"(===+\s*Path\s*[1-3]\s*===+)", re.IGNORECASE)
    parts = header_re.split(wikitext)

    # Collect section content that follows each header
    path_contents: list[str] = []
    for i, part in enumerate(parts):
        if header_re.fullmatch(part.strip()) and i + 1 < len(parts):
            path_contents.append(parts[i + 1])

    if len(path_contents) < 3:
        warnings.append(
            f"expected 3 Path sections, found {len(path_contents)} — upgrades skipped",
        )
        return {"cost": cost, "upgrades": None, "warnings": warnings}

    paths: list[list[str]] = []
    for path_idx, content in enumerate(path_contents[:3], start=1):
        blocks = _find_template_blocks(content, "Upgrade")
        names: list[str] = []
        for block in blocks:
            name = _get_template_param(block, "name")
            if name:
                # Skip blocks that look like hero level headers (e.g. "Level 3")
                if re.fullmatch(r"Level\s*\d+", name, re.IGNORECASE):
                    continue
                names.append(name)
            if len(names) == 5:
                break
        if len(names) < 5:
            warnings.append(f"Path {path_idx}: expected 5 upgrades, found {len(names)}")
        paths.append(names)

    return {"cost": cost, "upgrades": paths, "warnings": warnings}


# ---------------------------------------------------------------------------
# Hero parsing
# ---------------------------------------------------------------------------


def _extract_hero_data(wikitext: str) -> dict[str, Any]:
    """Parse cost and level-3/10 abilities from a hero's BTD6 wikitext.

    Returns::

        {
            "cost": int | None,
            "abilities": {3: {"name": str, "summary": str},
                          10: {"name": str, "summary": str}},
            "warnings": [str, ...],
        }
    """
    warnings: list[str] = []
    cost = _extract_medium_cost(wikitext)
    if cost is None:
        warnings.append("could not extract Medium cost")

    blocks = _find_template_blocks(wikitext, "Upgrade")
    abilities: dict[int, dict[str, str]] = {}

    for block in blocks:
        name_val = _get_template_param(block, "name") or ""
        lvl_m = re.fullmatch(r"Level\s*(\d+)", name_val.strip(), re.IGNORECASE)
        if not lvl_m:
            continue
        level = int(lvl_m.group(1))
        if level not in (3, 10):
            continue

        desc = _get_template_param(block, "description") or ""
        # Wiki format is "AbilityName: summary" for most heroes.
        # Geraldo uses "New Item! ItemName - summary" (no colon before name).
        if ":" in desc:
            ability_name, _, summary = desc.partition(":")
            abilities[level] = {
                "name": ability_name.strip(),
                "summary": summary.strip(),
            }
        elif " - " in desc:
            # e.g. "New Item! See Invisibility Potion - grants short term camo..."
            # Strip leading "New Item! " prefix if present before splitting.
            cleaned = re.sub(r"^New Item!\s*", "", desc).strip()
            ability_name, _, summary = cleaned.partition(" - ")
            abilities[level] = {
                "name": ability_name.strip(),
                "summary": summary.strip(),
            }
        else:
            # No separator — store the whole description as the name
            abilities[level] = {"name": desc.strip(), "summary": ""}
            if desc:
                warnings.append(
                    f"Level {level} description has no separator: {desc[:60]!r}",
                )

    for required_level in (3, 10):
        if required_level not in abilities:
            warnings.append(f"level {required_level} ability not found in wikitext")

    return {"cost": cost, "abilities": abilities, "warnings": warnings}


# ---------------------------------------------------------------------------
# CSV row update helpers
# ---------------------------------------------------------------------------


def _update_tower_row(
    row: dict[str, str],
    data: dict[str, Any],
) -> dict[str, str]:
    updated = dict(row)
    if data.get("cost"):
        updated["base_cost"] = str(data["cost"])
    upgrades = data.get("upgrades")
    if upgrades and len(upgrades) == 3:
        for prefix, names in (
            ("top_", upgrades[0]),
            ("mid_", upgrades[1]),
            ("bot_", upgrades[2]),
        ):
            for i, name in enumerate(names[:5], start=1):
                updated[f"{prefix}{i}"] = name
    return updated


def _update_hero_row(
    row: dict[str, str],
    data: dict[str, Any],
) -> dict[str, str]:
    updated = dict(row)
    if data.get("cost"):
        updated["base_cost"] = str(data["cost"])
    for level, col_prefix in ((3, "ability_3"), (10, "ability_10")):
        ab = data.get("abilities", {}).get(level)
        if ab:
            updated[f"{col_prefix}_name"] = ab["name"]
            updated[f"{col_prefix}_summary"] = ab["summary"]
    return updated


# ---------------------------------------------------------------------------
# CSV I/O
# ---------------------------------------------------------------------------


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Return (fieldnames, rows) from a CSV file."""
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    return fieldnames, rows


def _write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Main fetch loop
# ---------------------------------------------------------------------------


def _print_tower_result(name: str, data: dict[str, Any]) -> None:
    cost = data.get("cost")
    upgrades = data.get("upgrades")
    print(f"    base_cost={cost}")
    if upgrades:
        labels = ("top", "mid", "bot")
        for label, path in zip(labels, upgrades, strict=False):
            print(f"    {label}: {path}")
    for w in data.get("warnings", []):
        print(f"    WARN: {w}")


def _print_hero_result(name: str, data: dict[str, Any]) -> None:
    print(f"    base_cost={data.get('cost')}")
    for level, ab in sorted(data.get("abilities", {}).items()):
        summary_preview = ab["summary"][:60]
        print(f"    level {level}: {ab['name']!r} — {summary_preview}")
    for w in data.get("warnings", []):
        print(f"    WARN: {w}")


def fetch_all(
    *,
    towers_csv: Path,
    heroes_csv: Path,
    delay: float,
    dry_run: bool,
) -> int:
    tower_fieldnames, tower_rows = _read_csv(towers_csv)
    hero_fieldnames, hero_rows = _read_csv(heroes_csv)

    # --- Towers ---
    print(f"\n=== Towers ({len(tower_rows)}) ===")
    updated_towers: list[dict[str, str]] = []
    for row in tower_rows:
        name = row.get("canonical") or row.get("id") or "?"
        wiki_url = row.get("wiki_url", "").strip()
        if not wiki_url:
            print(f"  SKIP {name}: no wiki_url")
            updated_towers.append(row)
            continue
        page_title = _btd6_page_title(wiki_url)
        print(f"  {name}  ({page_title})")
        wikitext = _fetch_wikitext(page_title)
        if wikitext is None:
            print("    WARN: page not found on wiki — row unchanged")
            updated_towers.append(row)
        else:
            data = _extract_tower_data(wikitext)
            _print_tower_result(name, data)
            updated_towers.append(_update_tower_row(row, data))
        time.sleep(delay)

    # --- Heroes ---
    print(f"\n=== Heroes ({len(hero_rows)}) ===")
    updated_heroes: list[dict[str, str]] = []
    for row in hero_rows:
        name = row.get("canonical") or row.get("id") or "?"
        wiki_url = row.get("wiki_url", "").strip()
        if not wiki_url:
            print(f"  SKIP {name}: no wiki_url")
            updated_heroes.append(row)
            continue
        page_title = _btd6_page_title(wiki_url)
        print(f"  {name}  ({page_title})")
        wikitext = _fetch_wikitext(page_title)
        if wikitext is None:
            print("    WARN: page not found on wiki — row unchanged")
            updated_heroes.append(row)
        else:
            data = _extract_hero_data(wikitext)
            _print_hero_result(name, data)
            updated_heroes.append(_update_hero_row(row, data))
        time.sleep(delay)

    if dry_run:
        print("\n--dry-run: CSVs not written.")
        return 0

    _write_csv(towers_csv, tower_fieldnames, updated_towers)
    _write_csv(heroes_csv, hero_fieldnames, updated_heroes)
    print(f"\nWrote {towers_csv} and {heroes_csv}.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Fetch BTD6 cost and upgrade/ability data from the Bloons fandom wiki "
            "and write the results into data/btd6/towers.csv and heroes.csv. "
            "Descriptions are intentionally skipped — fill those manually."
        ),
    )
    p.add_argument(
        "--towers-csv",
        type=Path,
        default=_DEFAULT_TOWERS_CSV,
        help="Path to towers CSV (default: data/btd6/towers.csv)",
    )
    p.add_argument(
        "--heroes-csv",
        type=Path,
        default=_DEFAULT_HEROES_CSV,
        help="Path to heroes CSV (default: data/btd6/heroes.csv)",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=_DEFAULT_DELAY,
        metavar="SECONDS",
        help="Pause between API requests (default: 1.0s). Increase if you hit rate limits.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and print data without writing any files.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return fetch_all(
        towers_csv=args.towers_csv,
        heroes_csv=args.heroes_csv,
        delay=args.delay,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
