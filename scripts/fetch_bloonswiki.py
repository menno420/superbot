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
_DEFAULT_PARAGON_STATS_DIR = _DEFAULT_STATS_DIR / "paragons"
_DEFAULT_BLOONS_JSON = _REPO_ROOT / "disbot" / "data" / "btd6" / "bloons.json"
_DEFAULT_ROUNDS_JSON = _REPO_ROOT / "disbot" / "data" / "btd6" / "rounds.json"
_CATALOG_GAME_VERSION = "54.0"

# btd6_bloons Cargo fields. Cargo output keys use spaces ("rbe fort", "parent of").
_BLOON_FIELDS = (
    "id,name,rbe,rbe_fort,health,health_fort,speed,layers,immunity,parent_of,is_moab"
)
_BLOON_CATEGORY_ORDER = {"basic": 0, "special": 1, "moab_class": 2, "modifier": 3}

_PATH_PREFIX = {1: "top", 2: "mid", 3: "bot"}


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------


def _get(url: str, *, retries: int = 4) -> str:
    """GET ``url`` with the pinned UA, retrying transient network/TLS errors.

    Real HTTP statuses (404 etc.) are re-raised immediately so callers can act on
    them (e.g. economy towers 404 on the stats module). Transient hiccups — TLS
    handshake blips, rate limits (429), 5xx — back off and retry so a single
    flaky edge node doesn't abort a whole ``--all`` run.
    """
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    delay = 2.0
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:  # noqa: S310 (https)
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except urllib.error.URLError:
            # Wraps transient TLS / connection errors (incl. clock-skew certs).
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError("unreachable")  # pragma: no cover


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


def _float(value: object) -> float | int | None:
    try:
        number = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


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
    paragon_name: str | None = None
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

    paragons = _cargo_query("btd6_paragons", "name,cost", f"tower='{safe}'")
    if paragons:
        td.paragon_cost = _int(paragons[0].get("cost"))
        td.paragon_name = str(paragons[0].get("name", "")).strip() or None
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
        "paragon_name": td.paragon_name,
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


# ---------------------------------------------------------------------------
# Paragons (btd6_paragons Cargo + Module:BTD6 stats/<Paragon>/new)
# ---------------------------------------------------------------------------


@dataclass
class ParagonData:
    tower_id: str
    tower_canonical: str
    paragon_id: str
    paragon_name: str | None = None
    cost: int | None = None
    cost_chimps: int | None = None
    xp: int | None = None
    base: dict = field(default_factory=dict)
    game_version: str = ""
    warnings: list[str] = field(default_factory=list)


def _fetch_paragon_stats_raw(paragon_name: str) -> str:
    page = urllib.parse.quote(paragon_name.replace(" ", "_"))
    return _get(f"{_BASE}/Module:BTD6_stats/{page}/new?action=raw")


def fetch_paragon(
    tower_id: str,
    tower_canonical: str,
    *,
    delay: float,
) -> ParagonData | None:
    """Fetch a tower's paragon cost + degree-independent base stats.

    Returns ``None`` when the tower has no paragon (no ``btd6_paragons`` row).
    The paragon's *degree-dependent* stats are derived at runtime from the base
    node by ``utils.btd6.paragon_degrees`` — nothing per-degree is fetched.

    Like utility towers / prose-only heroes, the two paragons without a stats
    module (Root of all Nature, Herald of Everfrost) 404 on the module page; we
    keep their Cargo cost and note the absence rather than failing the run.
    """
    from parse_bloonswiki import parse_paragon_stats_json

    from utils.btd6 import paragon_math

    safe = tower_canonical.replace("'", "\\'")
    rows = _cargo_query("btd6_paragons", "name,cost,cost_C,xp", f"tower='{safe}'")
    if not rows:
        return None  # this tower has no paragon

    name = str(rows[0].get("name", "")).strip() or None
    resolved = paragon_math.resolve_paragon(tower_canonical)
    paragon_id = resolved.paragon_id if resolved else _slug(name or tower_id)
    pd = ParagonData(
        tower_id=tower_id,
        tower_canonical=tower_canonical,
        paragon_id=paragon_id,
        paragon_name=name,
        cost=_int(rows[0].get("cost")),
        # Cargo flattens ``cost_C`` to a space-separated key in JSON output.
        cost_chimps=_int(rows[0].get("cost C") or rows[0].get("cost_C")),
        xp=_int(rows[0].get("xp")),
    )
    time.sleep(delay)

    if not name:
        pd.warnings.append("no paragon name in btd6_paragons")
        return pd
    try:
        stats = parse_paragon_stats_json(_fetch_paragon_stats_raw(name))
        pd.base = stats.base
        pd.game_version = stats.game_version
        pd.warnings.extend(f"stats: {w}" for w in stats.warnings)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            pd.warnings.append("no stats module (module-less paragon — cost only)")
        else:
            raise
    return pd


def _slug(text: str) -> str:
    return "_".join("".join(c for c in text.lower() if c.isalnum() or c == " ").split())


def _paragon_writable(pd: ParagonData) -> bool:
    """Only paragons with a real stats module are worth a stats file."""
    return bool(pd.base.get("attacks") or pd.base.get("abilities"))


def paragon_stats_document(pd: ParagonData) -> dict:
    return {
        "paragon_id": pd.paragon_id,
        "tower_id": pd.tower_id,
        "canonical": pd.paragon_name,
        "tower_canonical": pd.tower_canonical,
        "game_version": pd.game_version,
        "source": "bloonswiki.com (CC BY-NC-SA)",
        "cost": pd.cost,
        "cost_chimps": pd.cost_chimps,
        "xp": pd.xp,
        "base": pd.base,
    }


def write_paragon_stats_file(pd: ParagonData, paragons_dir: Path) -> Path:
    paragons_dir.mkdir(parents=True, exist_ok=True)
    out = paragons_dir / f"{pd.paragon_id}.json"
    out.write_text(
        json.dumps(paragon_stats_document(pd), indent=2, ensure_ascii=False) + "\n",
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


def _paragon_report(pd: ParagonData) -> str:
    groups = ""
    if pd.base:
        from utils.btd6 import paragon_degrees

        groups = ", ".join(paragon_degrees.degree_stat_groups(pd.base))
    lines = [
        f"{pd.paragon_name or '?'} ({pd.paragon_id}) — {pd.tower_canonical}",
        f"  cost: {pd.cost}  chimps: {pd.cost_chimps}  xp: {pd.xp}  "
        f"version: {pd.game_version or '?'}",
        f"  degree-stat groups: {groups or '(none — module-less)'}",
    ]
    if pd.warnings:
        lines.append(f"  ⚠ {len(pd.warnings)} warning(s):")
        lines.extend(f"    - {w}" for w in pd.warnings)
    else:
        lines.append("  ✓ no warnings")
    return "\n".join(lines)


def _run_paragons(args: argparse.Namespace) -> int:
    """Fetch paragons (one or all) and write a stats file for each that has a
    stats module. Cost-only (module-less) paragons are reported, not written.
    """
    roster = _read_roster(args.csv)
    if args.paragon:
        from utils.btd6 import paragon_math

        key = args.paragon.strip().lower()
        resolved = paragon_math.resolve_paragon(args.paragon)
        roster = [
            (tid, canon)
            for tid, canon in roster
            if key in (tid.lower(), canon.lower())
            or (resolved is not None and canon.lower() == resolved.tower.lower())
        ]
        if not roster:
            print(f"No tower/paragon matching {args.paragon!r}")
            return 1

    written = 0
    any_warn = False
    for tid, canon in roster:
        try:
            pd = fetch_paragon(tid, canon, delay=args.delay)
        except Exception as exc:  # noqa: BLE001 - report + continue across roster
            print(f"{canon} ({tid}) paragon: FETCH FAILED — {exc}\n")
            any_warn = True
            continue
        if pd is None:
            continue  # tower has no paragon — silent skip
        print(_paragon_report(pd) + "\n")
        any_warn = any_warn or bool(pd.warnings)
        if not args.dry_run and _paragon_writable(pd):
            write_paragon_stats_file(pd, args.paragon_stats_dir)
            written += 1

    if not args.dry_run and written:
        print(f"Wrote {written} paragon stats file(s) to {args.paragon_stats_dir}")
    return 1 if any_warn else 0


# ---------------------------------------------------------------------------
# Bloons (btd6_bloons Cargo -> merged bloons.json)
# ---------------------------------------------------------------------------


def _bloon_category(bloon_id: str, is_moab: bool) -> str:
    from utils.btd6 import bloon_ids

    if is_moab:
        return "moab_class"
    if bloon_id in bloon_ids.BASIC_IDS:
        return "basic"
    return "special"


def _bloon_properties(is_moab: bool, status: list[str]) -> list[str]:
    props: list[str] = []
    if is_moab:
        props.append("moab-class")
    if any(s.lower() == "knockback" for s in status):
        props.append("knockback-immune")
    return props


def _children_string(children: list[dict], name_by_id: dict[str, str]) -> str:
    parts: list[str] = []
    for child in children:
        name = name_by_id.get(child["bloon_id"]) or child["bloon_id"].title()
        prefix = " ".join(m.capitalize() for m in child["modifiers"])
        label = f"{prefix} {name}".strip()
        if child["count"] > 1:
            label += "s"
        parts.append(f"{child['count']} {label}")
    if len(parts) <= 1:
        return parts[0] if parts else ""
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def _default_bloon_aliases(bloon_id: str, canonical: str) -> list[str]:
    aliases = [bloon_id, f"{bloon_id}s"]
    canon = canonical.strip().lower()
    if canon and canon not in aliases:
        aliases.append(canon)
    return list(dict.fromkeys(aliases))


def _load_curated_bloons(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {b["id"]: b for b in data.get("bloons", []) if "id" in b}


def fetch_bloons(bloons_json: Path, *, delay: float) -> list[dict]:
    """Fetch btd6_bloons and merge with the curated file.

    Numbers (rbe / health / speed / layers / immunities / children) come from
    the wiki and win; curated aliases / descriptions / trait properties are
    preserved, and the synthesised modifier entries (camo / regrow / fortified,
    absent from Cargo) are carried through unchanged.
    """
    from parse_bloonswiki import parse_bloon_children, parse_bloon_immunity

    from utils.btd6 import bloon_ids

    rows = _cargo_query("btd6_bloons", _BLOON_FIELDS, "id LIKE '%'", order_by="rbe")
    time.sleep(delay)
    name_by_id = {
        bloon_ids.normalize_bloon_name(r.get("id", "")): str(r.get("name", "")).strip()
        for r in rows
    }
    curated = _load_curated_bloons(bloons_json)

    merged: list[dict] = []
    for row in rows:
        raw_id = str(row.get("id", "")).strip()
        if raw_id.startswith("TestBloon"):
            continue
        bloon_id = bloon_ids.normalize_bloon_name(raw_id)
        if not bloon_id:
            continue
        immune, status = parse_bloon_immunity(str(row.get("immunity", "")))
        children = parse_bloon_children(str(row.get("parent of", "")))
        is_moab = str(row.get("is moab", "")).strip() not in ("", "0")
        canonical = str(row.get("name", "")).strip() or raw_id
        entry: dict = {
            "id": bloon_id,
            "canonical": canonical,
            "category": _bloon_category(bloon_id, is_moab),
            "immune_to": immune,
            "children": _children_string(children, name_by_id),
            "children_list": children,
            "properties": _bloon_properties(is_moab, status),
        }
        for key, field_name in (
            ("rbe", "rbe"),
            ("rbe_fortified", "rbe fort"),
            ("health", "health"),
            ("health_fortified", "health fort"),
            ("layers", "layers"),
        ):
            value = _int(row.get(field_name))
            if value is not None:
                entry[key] = value
        speed = _float(row.get("speed"))
        if speed is not None:
            entry["speed"] = speed

        cur = curated.get(bloon_id)
        if cur:
            entry["aliases"] = cur.get("aliases") or _default_bloon_aliases(
                bloon_id,
                canonical,
            )
            entry["description"] = cur.get("description", "")
            if cur.get("popped_by"):
                entry["popped_by"] = cur["popped_by"]
            entry["properties"] = list(
                dict.fromkeys([*cur.get("properties", []), *entry["properties"]]),
            )
        else:
            entry["aliases"] = _default_bloon_aliases(bloon_id, canonical)
            entry["description"] = ""
        merged.append(entry)

    # Carry forward the synthesised modifier entries (camo/regrow/fortified).
    merged.extend(cur for cur in curated.values() if cur.get("category") == "modifier")
    merged.sort(
        key=lambda e: (
            _BLOON_CATEGORY_ORDER.get(e.get("category"), 9),
            e.get("rbe") or 0,
            e.get("id", ""),
        ),
    )
    return merged


def write_bloons_file(bloons: list[dict], path: Path, *, game_version: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "schema_version": 2,
        "data_version": "2.0",
        "game_version": game_version,
        "source": "bloonswiki.com Cargo btd6_bloons (CC BY-NC-SA)",
        "bloons": bloons,
    }
    path.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def _run_bloons(args: argparse.Namespace) -> int:
    bloons = fetch_bloons(args.bloons_json, delay=args.delay)
    basics = [b["id"] for b in bloons if b.get("category") == "basic"]
    print(f"fetched {len(bloons)} bloons (basics: {', '.join(basics) or 'none'})")
    for b in bloons[:6]:
        print(
            f"  {b['id']}: rbe={b.get('rbe')} speed={b.get('speed')} "
            f"immune={b.get('immune_to')} -> {b.get('children') or '(none)'}",
        )
    if not args.dry_run:
        write_bloons_file(bloons, args.bloons_json, game_version=args.game_version)
        print(f"Wrote {len(bloons)} bloons to {args.bloons_json}")
    return 0


# ---------------------------------------------------------------------------
# Rounds (Module:BTD6_rounds/Default -> rounds.json)
# ---------------------------------------------------------------------------


def _load_bloon_rbe(bloons_json: Path) -> tuple[dict[str, dict], dict[str, str]]:
    """Read bloons.json into (id -> {rbe, rbe_fortified}, id -> canonical name)."""
    if not bloons_json.exists():
        return {}, {}
    data = json.loads(bloons_json.read_text(encoding="utf-8"))
    rbe_map: dict[str, dict] = {}
    name_map: dict[str, str] = {}
    for bloon in data.get("bloons", []):
        bloon_id = bloon.get("id")
        if not bloon_id:
            continue
        rbe_map[bloon_id] = {
            "rbe": bloon.get("rbe"),
            "rbe_fortified": bloon.get("rbe_fortified"),
        }
        name_map[bloon_id] = bloon.get("canonical", bloon_id)
    return rbe_map, name_map


def _load_curated_rounds(path: Path) -> dict[int, dict]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {int(r["round"]): r for r in data.get("rounds", []) if "round" in r}


def fetch_rounds(rounds_json: Path, bloons_json: Path, *, delay: float) -> list[dict]:
    """Fetch Module:BTD6_rounds/Default -> per-round composition + RBE.

    Curated summary / danger / common_threats from the existing rounds.json are
    kept where present (the strategic blurbs); composition (groups) and the
    derived RBE are added to every one of the 140 rounds.
    """
    from parse_bloonswiki import parse_rounds_json

    rbe_map, name_map = _load_bloon_rbe(bloons_json)
    if not rbe_map:
        print("  ! bloons.json has no RBE data — run --all-bloons first")
    default_data = json.loads(_get(f"{_BASE}/Module:BTD6_rounds/Default?action=raw"))
    time.sleep(delay)
    parsed = parse_rounds_json(default_data, rbe_map=rbe_map, name_map=name_map)

    curated = _load_curated_rounds(rounds_json)
    for entry in parsed:
        cur = curated.get(entry["round"])
        if not cur:
            continue
        if cur.get("summary"):
            entry["summary"] = cur["summary"]
        if cur.get("danger"):
            entry["danger"] = cur["danger"]
        if cur.get("common_threats"):
            entry["common_threats"] = list(cur["common_threats"])
    return parsed


def write_rounds_file(rounds: list[dict], path: Path, *, game_version: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "schema_version": 2,
        "data_version": "2.0",
        "game_version": game_version,
        "source": "bloonswiki.com Module:BTD6_rounds/Default (CC BY-NC-SA)",
        "rounds": rounds,
    }
    path.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def _run_rounds(args: argparse.Namespace) -> int:
    rounds = fetch_rounds(args.rounds_json, args.bloons_json, delay=args.delay)
    print(f"parsed {len(rounds)} rounds")
    for number in (1, 40, 63, 100):
        entry = next((r for r in rounds if r["round"] == number), None)
        if entry:
            print(
                f"  R{number}: {entry['summary']} "
                f"danger={entry['danger']} threats={entry['common_threats']}",
            )
    if not args.dry_run:
        write_rounds_file(rounds, args.rounds_json, game_version=args.game_version)
        print(f"Wrote {len(rounds)} rounds to {args.rounds_json}")
    return 0


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
    group.add_argument(
        "--paragon",
        help="Tower/paragon id or name to fetch the paragon stats for",
    )
    group.add_argument(
        "--all-paragons",
        action="store_true",
        help="Fetch every tower's paragon stats -> stats/paragons/<id>.json",
    )
    group.add_argument(
        "--all-bloons",
        action="store_true",
        help="Fetch the btd6_bloons table -> bloons.json",
    )
    group.add_argument(
        "--all-rounds",
        action="store_true",
        help="Fetch Module:BTD6_rounds/Default -> rounds.json",
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
    parser.add_argument(
        "--paragon-stats-dir",
        type=Path,
        default=_DEFAULT_PARAGON_STATS_DIR,
    )
    parser.add_argument("--bloons-json", type=Path, default=_DEFAULT_BLOONS_JSON)
    parser.add_argument("--rounds-json", type=Path, default=_DEFAULT_ROUNDS_JSON)
    parser.add_argument("--game-version", default=_CATALOG_GAME_VERSION)
    args = parser.parse_args(argv)

    if args.all_bloons:
        return _run_bloons(args)

    if args.all_rounds:
        return _run_rounds(args)

    if args.hero or args.all_heroes:
        return _run_heroes(args)

    if args.paragon or args.all_paragons:
        return _run_paragons(args)

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
