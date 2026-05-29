"""Fetch BTD6 tower data from bloonswiki.com and write the runtime data.

bloonswiki exposes everything we need as clean JSON (unlike the rendered
tables), and — unlike the Fandom wiki whose costs proved wrong — its numbers
are authoritative:

* **costs / XP** via the Cargo API (``btd6_towers``, ``btd6_upgrades``,
  ``btd6_paragons``) — Medium cost, plus XP per upgrade;
* **stats** via the per-tower data page ``Module:BTD6 stats/<tower>/new``
  (raw JSON), flattened + damage-type-decoded by ``parse_bloonswiki``.

For each tower this:
  1. corrects the Medium cost columns in ``data/btd6/towers.csv`` (the
     existing CSV→JSON import then regenerates ``towers.json``);
  2. writes the rich per-tower file ``disbot/data/btd6/stats/<id>.json``
     (base cost, category, paragon cost, per-upgrade cost+XP, and the full
     per-tier stats).

Only the Medium cost is stored; Easy/Hard/Impoppable are derived by
``utils.btd6.difficulty_costs``. Numbers are facts; the wiki's prose
descriptions are intentionally not copied (CC BY-NC-SA). Run by a maintainer;
the output is committed — the bot never fetches at runtime.

    python3.10 scripts/fetch_bloonswiki.py --tower bomb_shooter --dry-run
    python3.10 scripts/fetch_bloonswiki.py --tower bomb_shooter
    python3.10 scripts/fetch_bloonswiki.py --all
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _REPO_ROOT / "scripts"
for _p in (str(_SCRIPTS), str(_REPO_ROOT / "disbot")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_BASE = "https://www.bloonswiki.com"
_API = _BASE + "/api.php"
_USER_AGENT = (
    "SuperBot-BTD6-DataFetch/1.0 "
    "(https://github.com/menno420/superbot; bot data pipeline)"
)
_DEFAULT_DELAY = 1.0

_DEFAULT_CSV = _REPO_ROOT / "data" / "btd6" / "towers.csv"
_DEFAULT_STATS_DIR = _REPO_ROOT / "disbot" / "data" / "btd6" / "stats"
_DEFAULT_HEROES_JSON = _REPO_ROOT / "disbot" / "data" / "btd6" / "heroes.json"
_DEFAULT_HERO_STATS_DIR = _DEFAULT_STATS_DIR / "heroes"

_PATH_PREFIX = {1: "top", 2: "mid", 3: "bot"}


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as resp:  # noqa: S310 (https only)
        return resp.read().decode("utf-8")


def _cargo_query(
    tables: str,
    fields: str,
    where: str,
    order_by: str = "",
    limit: int = 500,
) -> list[dict]:
    """Run a Cargo query and return the list of result rows."""
    params = urllib.parse.urlencode(
        {
            "action": "cargoquery",
            "format": "json",
            "tables": tables,
            "fields": fields,
            "where": where,
            "order_by": order_by,
            "limit": str(limit),
        },
    )
    data = json.loads(_get(f"{_API}?{params}"))
    return [row.get("title", {}) for row in data.get("cargoquery", [])]


def _fetch_stats_raw(canonical: str) -> str:
    page = urllib.parse.quote(canonical.replace(" ", "_"))
    return _get(f"{_BASE}/Module:BTD6_stats/{page}/new?action=raw")


def _int(value: object) -> int | None:
    try:
        return int(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Fetch + assemble
# ---------------------------------------------------------------------------


@dataclass
class TowerData:
    tower_id: str
    canonical: str
    base_cost: int | None = None
    category: str | None = None
    paragon_cost: int | None = None
    upgrades: list[dict] = field(default_factory=list)
    tiers: dict[str, dict] = field(default_factory=dict)
    game_version: str = ""
    warnings: list[str] = field(default_factory=list)


def fetch_tower(tower_id: str, canonical: str, *, delay: float) -> TowerData:
    """Fetch costs + stats for one tower and assemble :class:`TowerData`."""
    from parse_bloonswiki import parse_stats_json

    td = TowerData(tower_id=tower_id, canonical=canonical)
    safe = canonical.replace("'", "\\'")

    towers = _cargo_query("btd6_towers", "cost,category", f"name='{safe}'")
    if towers:
        td.base_cost = _int(towers[0].get("cost"))
        category = str(towers[0].get("category", "")).strip().lower()
        td.category = category or None
    else:
        td.warnings.append("no btd6_towers row (tower not found on wiki)")
    time.sleep(delay)

    rows = _cargo_query(
        "btd6_upgrades",
        "path,tier,name,cost,xp",
        f"tower='{safe}' AND unused=0",
        order_by="path,tier",
    )
    for row in rows:
        td.upgrades.append(
            {
                "path": _int(row.get("path")),
                "tier": _int(row.get("tier")),
                "name": str(row.get("name", "")).strip(),
                "cost": _int(row.get("cost")),
                "xp": _int(row.get("xp")),
            },
        )
    time.sleep(delay)

    paragons = _cargo_query("btd6_paragons", "cost", f"tower='{safe}'")
    if paragons:
        td.paragon_cost = _int(paragons[0].get("cost"))
    time.sleep(delay)

    try:
        stats = parse_stats_json(_fetch_stats_raw(canonical))
        td.tiers = stats.tiers
        td.game_version = stats.game_version
        td.warnings.extend(f"stats: {w}" for w in stats.warnings)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            # Pure economy/buff towers (Banana Farm, Monkey Village) have no
            # combat-stats page — keep their costs, note the absence.
            td.warnings.append("no stats page (utility tower — costs only)")
        else:
            raise

    _validate(td)
    return td


@dataclass
class HeroData:
    hero_id: str
    canonical: str
    base_cost: int | None = None
    cost_chimps: int | None = None
    levels: dict[str, dict] = field(default_factory=dict)
    game_version: str = ""
    warnings: list[str] = field(default_factory=list)


def fetch_hero(hero_id: str, canonical: str, *, delay: float) -> HeroData:
    """Fetch cost + per-level stats for one hero and assemble :class:`HeroData`.

    Cost comes from Cargo ``btd6_heroes`` (always present). Per-level combat
    stats come from ``Module:BTD6 stats/<Hero>/new`` — but only ~6 heroes have
    such a module; the rest 404 and keep cost only (handled like utility towers).
    """
    from parse_bloonswiki import parse_hero_stats_json

    hd = HeroData(hero_id=hero_id, canonical=canonical)
    safe = canonical.replace("'", "\\'")

    rows = _cargo_query("btd6_heroes", "cost,cost_C", f"name='{safe}'")
    if rows:
        # Cargo output keys use spaces for underscores (``cost_C`` → ``cost C``).
        hd.base_cost = _int(rows[0].get("cost"))
        hd.cost_chimps = _int(rows[0].get("cost C") or rows[0].get("cost_C"))
    else:
        hd.warnings.append("no btd6_heroes row (hero not found on wiki)")
    time.sleep(delay)

    try:
        stats = parse_hero_stats_json(_fetch_stats_raw(canonical))
        hd.levels = stats.levels
        hd.game_version = stats.game_version
        hd.warnings.extend(f"stats: {w}" for w in stats.warnings)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            hd.warnings.append("no stats module (prose-only hero — cost only)")
        else:
            raise

    if hd.base_cost is None:
        hd.warnings.append("missing base cost")
    return hd


def _writable(td: TowerData) -> bool:
    """Costs are sound enough to commit (stats may legitimately be absent)."""
    return td.base_cost is not None and len(td.upgrades) == 15


def _hero_writable(hd: HeroData) -> bool:
    """Only heroes with a real per-level stats module are worth a stats file."""
    return bool(hd.levels)


def _validate(td: TowerData) -> None:
    if td.base_cost is None:
        td.warnings.append("missing base cost")
    by_path: dict[int | None, int] = {}
    for up in td.upgrades:
        by_path[up["path"]] = by_path.get(up["path"], 0) + 1
    for path in (1, 2, 3):
        if by_path.get(path, 0) != 5:
            td.warnings.append(
                f"path {path} has {by_path.get(path, 0)} upgrades, expected 5",
            )
    # Sanity-check Medium costs against the difficulty formula's self-consistency.
    from utils.btd6.difficulty_costs import cost_for_difficulty

    for up in td.upgrades:
        if (
            up["cost"] is not None
            and cost_for_difficulty(up["cost"], "medium") != up["cost"]
        ):
            td.warnings.append(f"cost round-trip failed for {up['name']!r}")


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------


def stats_document(td: TowerData) -> dict:
    return {
        "tower_id": td.tower_id,
        "canonical": td.canonical,
        "game_version": td.game_version,
        "source": "bloonswiki.com (CC BY-NC-SA)",
        "base_cost": td.base_cost,
        "category": td.category,
        "paragon_cost": td.paragon_cost,
        "upgrades": td.upgrades,
        "tiers": td.tiers,
    }


def write_stats_file(td: TowerData, stats_dir: Path) -> Path:
    stats_dir.mkdir(parents=True, exist_ok=True)
    out = stats_dir / f"{td.tower_id}.json"
    out.write_text(
        json.dumps(stats_document(td), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out


def hero_stats_document(hd: HeroData) -> dict:
    return {
        "hero_id": hd.hero_id,
        "canonical": hd.canonical,
        "game_version": hd.game_version,
        "source": "bloonswiki.com (CC BY-NC-SA)",
        "base_cost": hd.base_cost,
        "cost_chimps": hd.cost_chimps,
        "levels": hd.levels,
    }


def write_hero_stats_file(hd: HeroData, heroes_dir: Path) -> Path:
    heroes_dir.mkdir(parents=True, exist_ok=True)
    out = heroes_dir / f"{hd.hero_id}.json"
    out.write_text(
        json.dumps(hero_stats_document(hd), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out


def apply_costs_to_row(row: dict, td: TowerData) -> None:
    """Write fetched base cost, upgrade names, and Medium costs into a CSV row.

    Names are written too so the former placeholder rows (Desperado, Mermonkey,
    Beast Handler) become complete and enter the roster, and so names stay
    consistent with the cost/stats source.
    """
    if td.base_cost is not None:
        row["base_cost"] = str(td.base_cost)
    if td.category:
        row["category"] = td.category
    for up in td.upgrades:
        prefix = _PATH_PREFIX.get(up["path"])
        if prefix is None or up["tier"] is None:
            continue
        if up["name"]:
            row[f"{prefix}_{up['tier']}"] = up["name"]
        if up["cost"] is not None:
            row[f"{prefix}_{up['tier']}_cost"] = str(up["cost"])


def update_csv(csv_path: Path, fetched: dict[str, TowerData]) -> None:
    with csv_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    for row in rows:
        td = fetched.get(row["id"])
        if td is not None:
            apply_costs_to_row(row, td)
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Reporting + CLI
# ---------------------------------------------------------------------------


def _report(td: TowerData) -> str:
    lines = [
        f"{td.canonical} ({td.tower_id})",
        f"  base cost: {td.base_cost}  category: {td.category}  "
        f"paragon: {td.paragon_cost}  version: {td.game_version or '?'}",
        f"  upgrades: {len(td.upgrades)}  stat tiers: {len(td.tiers)}",
    ]
    for up in td.upgrades:
        lines.append(
            (
                f"    P{up['path']}T{up['tier']} {up['name']}: ${up['cost']:,} / {up['xp']:,} XP"
                if up["cost"] is not None and up["xp"] is not None
                else f"    P{up['path']}T{up['tier']} {up['name']}: ?"
            ),
        )
    if td.warnings:
        lines.append(f"  ⚠ {len(td.warnings)} warning(s):")
        lines.extend(f"    - {w}" for w in td.warnings)
    else:
        lines.append("  ✓ no warnings")
    return "\n".join(lines)


def _read_roster(csv_path: Path) -> list[tuple[str, str]]:
    with csv_path.open(encoding="utf-8", newline="") as fh:
        return [(r["id"], r["canonical"]) for r in csv.DictReader(fh)]


def _read_hero_roster(heroes_json: Path) -> list[tuple[str, str]]:
    data = json.loads(heroes_json.read_text(encoding="utf-8"))
    return [(h["id"], h["canonical"]) for h in data.get("heroes", [])]


def _hero_report(hd: HeroData) -> str:
    lines = [
        f"{hd.canonical} ({hd.hero_id})",
        f"  base cost: {hd.base_cost}  chimps: {hd.cost_chimps}  "
        f"levels: {len(hd.levels)}  version: {hd.game_version or '?'}",
    ]
    if hd.warnings:
        lines.append(f"  ⚠ {len(hd.warnings)} warning(s):")
        lines.extend(f"    - {w}" for w in hd.warnings)
    else:
        lines.append("  ✓ no warnings")
    return "\n".join(lines)


def _run_heroes(args: argparse.Namespace) -> int:
    """Fetch heroes (one or all) and write per-level stats files for those that
    have a real stats module. Cost-only heroes are reported but not written.
    """
    roster = _read_hero_roster(args.heroes_json)
    if args.hero:
        key = args.hero.strip().lower()
        roster = [
            (hid, canon) for hid, canon in roster if key in (hid.lower(), canon.lower())
        ]
        if not roster:
            print(f"No hero matching {args.hero!r} in {args.heroes_json}")
            return 1

    written = 0
    any_warn = False
    for hid, canon in roster:
        try:
            hd = fetch_hero(hid, canon, delay=args.delay)
        except Exception as exc:  # noqa: BLE001 - report + continue across roster
            print(f"{canon} ({hid}): FETCH FAILED — {exc}\n")
            any_warn = True
            continue
        print(_hero_report(hd) + "\n")
        any_warn = any_warn or bool(hd.warnings)
        if not args.dry_run and _hero_writable(hd):
            write_hero_stats_file(hd, args.hero_stats_dir)
            written += 1

    if not args.dry_run and written:
        print(f"Wrote {written} hero stats file(s) to {args.hero_stats_dir}")
    return 1 if any_warn else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tower", help="Tower id or canonical name to fetch")
    group.add_argument(
        "--all",
        action="store_true",
        help="Fetch every tower in the CSV",
    )
    group.add_argument("--hero", help="Hero id or canonical name to fetch")
    group.add_argument(
        "--all-heroes",
        action="store_true",
        help="Fetch every hero in heroes.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch + report, write nothing",
    )
    parser.add_argument("--delay", type=float, default=_DEFAULT_DELAY)
    parser.add_argument("--csv", type=Path, default=_DEFAULT_CSV)
    parser.add_argument("--stats-dir", type=Path, default=_DEFAULT_STATS_DIR)
    parser.add_argument("--heroes-json", type=Path, default=_DEFAULT_HEROES_JSON)
    parser.add_argument(
        "--hero-stats-dir",
        type=Path,
        default=_DEFAULT_HERO_STATS_DIR,
    )
    args = parser.parse_args(argv)

    if args.hero or args.all_heroes:
        return _run_heroes(args)

    roster = _read_roster(args.csv)
    if args.tower:
        key = args.tower.strip().lower()
        roster = [
            (tid, canon) for tid, canon in roster if key in (tid.lower(), canon.lower())
        ]
        if not roster:
            print(f"No tower matching {args.tower!r} in {args.csv}")
            return 1

    fetched: dict[str, TowerData] = {}
    any_warn = False
    for tid, canon in roster:
        try:
            td = fetch_tower(tid, canon, delay=args.delay)
        except Exception as exc:  # noqa: BLE001 - report + continue across roster
            print(f"{canon} ({tid}): FETCH FAILED — {exc}\n")
            any_warn = True
            continue
        print(_report(td) + "\n")
        any_warn = any_warn or bool(td.warnings)
        if not args.dry_run and _writable(td):
            write_stats_file(td, args.stats_dir)
            fetched[tid] = td
        elif not args.dry_run:
            print(f"  (skipped writing {tid} — costs unsound)\n")

    if not args.dry_run and fetched:
        update_csv(args.csv, fetched)
        print(f"Updated {len(fetched)} tower(s) in {args.csv} and {args.stats_dir}")

    return 1 if any_warn else 0


if __name__ == "__main__":
    raise SystemExit(main())
