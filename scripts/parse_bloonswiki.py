"""Parse pasted bloonswiki.com tower pages into structured BTD6 data.

This is the ingestion front-end for the *second* data source (bloonswiki,
which is paste-only — its content isn't reachable over the network from CI,
so pages are copied into local text files and parsed here). It is separate
from ``fetch_btd6_wiki_data.py`` (the Fandom MediaWiki API fetcher), whose
cost values proved inaccurate.

Handles two page types (auto-detected — JSON ⇒ stats, else ⇒ upgrades):

* **upgrades** page: tower intro, the three upgrade paths, and the optional
  Paragon — name, XP cost, description, and the four difficulty prices.
* **stats** page: the ``Module:BTD6 stats/<tower>/new`` JSON, flattened into
  per-tier stats with damage types decoded. ``--out`` writes the distilled
  runtime file.

Robustness — the format varies slightly between towers, so the parser:

* strips Markdown links first (``[Text](url)`` → ``Text``), so a page works
  whether copied as Markdown or as plain text;
* anchors on the very stable ``XP cost:`` label rather than on line counts —
  the upgrade *name* is the line above it and the *cost line* is the next
  line carrying four ``$`` amounts, so reordering or extra blank lines
  don't break it;
* never trusts itself silently: it cross-checks every parsed difficulty
  price against ``utils.btd6.difficulty_costs`` and reports any mismatch,
  and flags any path that doesn't have five upgrades.

Only the Medium cost is persisted downstream; the other three prices are
parsed solely to verify the formula, per the "store standard + formula"
data model.

    python3.10 scripts/parse_bloonswiki.py path/to/<tower>.upgrades.txt
    python3.10 scripts/parse_bloonswiki.py path/to/<tower>.upgrades.txt --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
# Allow ``from utils.btd6...`` when run as a script (pytest already has it).
if str(_REPO_ROOT / "disbot") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "disbot"))

# Section header → canonical path key used throughout the BTD6 data set.
_SECTION_KEYS = {
    "path 1": "top",
    "path 2": "mid",
    "path 3": "bot",
    "paragon": "paragon",
}

# Link URLs contain parentheses (e.g. ``Bigger_Bombs_(BTD6)``), so the URL
# matcher allows one level of nested parens rather than stopping at the first.
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^()]*(?:\([^()]*\)[^()]*)*\)")
_MONEY_RE = re.compile(r"\$([\d,]+)")
_XP_RE = re.compile(r"XP cost:\s*([\d,]+)", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedUpgrade:
    """One upgrade (or the Paragon) parsed from an upgrades page."""

    section: str  # top | mid | bot | paragon
    tier: int  # 1..5 within a path; 0 for Paragon
    name: str
    xp_cost: int
    description: str
    costs: tuple[int, int, int, int]  # easy, medium, hard, impoppable

    @property
    def medium_cost(self) -> int:
        return self.costs[1]


@dataclass
class UpgradesResult:
    intro: str
    upgrades: list[ParsedUpgrade] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.warnings


def _strip_links(text: str) -> str:
    """``[Text](url)`` → ``Text`` so Markdown and plain pastes parse alike."""
    return _LINK_RE.sub(r"\1", text)


def _money(line: str) -> list[int]:
    return [int(m.replace(",", "")) for m in _MONEY_RE.findall(line)]


def _is_cost_line(line: str) -> bool:
    return len(_MONEY_RE.findall(line)) >= 4


def parse_upgrades_page(text: str) -> UpgradesResult:
    """Parse an upgrades page into a validated :class:`UpgradesResult`."""
    lines = [ln.strip() for ln in _strip_links(text).splitlines()]

    intro = ""
    for idx, line in enumerate(lines):
        if line.lower() == "upgrades":
            intro = " ".join(p for p in lines[:idx] if p).strip()
            break

    result = UpgradesResult(intro=intro)
    section: str | None = None
    tier_counter: dict[str, int] = {}

    for idx, line in enumerate(lines):
        key = _SECTION_KEYS.get(line.lower())
        if key is not None:
            section = key
            continue

        xp_match = _XP_RE.search(line)
        if not xp_match:
            continue

        name = lines[idx - 1] if idx > 0 else ""
        xp_cost = int(xp_match.group(1).replace(",", ""))

        # Description runs from here to the cost line; collect, then parse costs.
        desc_parts: list[str] = []
        cost_line: str | None = None
        for ahead in lines[idx + 1 :]:
            if _is_cost_line(ahead):
                cost_line = ahead
                break
            if ahead and not _SECTION_KEYS.get(ahead.lower()):
                desc_parts.append(ahead)

        if section is None:
            result.warnings.append(f"{name!r}: upgrade found before any Path header")
            continue
        if cost_line is None:
            result.warnings.append(f"{name!r}: no cost line found after XP cost")
            continue

        money = _money(cost_line)
        if len(money) != 4:
            result.warnings.append(
                f"{name!r}: expected 4 difficulty prices, got {len(money)}: {money}",
            )
            continue

        tier = 0 if section == "paragon" else tier_counter.get(section, 0) + 1
        tier_counter[section] = tier
        result.upgrades.append(
            ParsedUpgrade(
                section=section,
                tier=tier,
                name=name,
                xp_cost=xp_cost,
                description=" ".join(desc_parts).strip(),
                costs=(money[0], money[1], money[2], money[3]),
            ),
        )

    _validate(result)
    return result


def _validate(result: UpgradesResult) -> None:
    """Append warnings for structural and formula problems."""
    from utils.btd6.difficulty_costs import all_difficulty_costs

    for path in ("top", "mid", "bot"):
        count = sum(1 for u in result.upgrades if u.section == path)
        if count != 5:
            result.warnings.append(f"path {path!r} has {count} upgrades, expected 5")

    for upgrade in result.upgrades:
        derived = all_difficulty_costs(upgrade.medium_cost)
        expected = (
            derived["easy"],
            upgrade.medium_cost,
            derived["hard"],
            derived["impoppable"],
        )
        if expected != upgrade.costs:
            result.warnings.append(
                f"{upgrade.name!r}: formula {expected} != page {upgrade.costs} "
                "(store an explicit override for this tier)",
            )


def _to_dict(result: UpgradesResult) -> dict:
    paths: dict[str, list[dict]] = {}
    paragon: dict | None = None
    for u in result.upgrades:
        entry = {
            "tier": u.tier,
            "name": u.name,
            "xp_cost": u.xp_cost,
            "medium_cost": u.medium_cost,
            "description": u.description,
        }
        if u.section == "paragon":
            paragon = entry
        else:
            paths.setdefault(u.section, []).append(entry)
    return {"intro": result.intro, "paths": paths, "paragon": paragon}


def _render_report(result: UpgradesResult) -> str:
    lines = [f"intro: {result.intro[:80]}{'…' if len(result.intro) > 80 else ''}", ""]
    for path in ("top", "mid", "bot", "paragon"):
        ups = [u for u in result.upgrades if u.section == path]
        if not ups:
            continue
        lines.append(f"{path}:")
        for u in ups:
            lines.append(
                f"  T{u.tier} {u.name} — ${u.medium_cost:,} (Medium), {u.xp_cost:,} XP",
            )
    lines.append("")
    if result.warnings:
        lines.append(f"⚠ {len(result.warnings)} warning(s):")
        lines.extend(f"  - {w}" for w in result.warnings)
    else:
        lines.append("✓ no warnings — all prices match the formula")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Stats pages — Module:BTD6 stats/<tower>/new JSON
# ---------------------------------------------------------------------------

# The 16 single-path crosspath codes a stats page must define: base + 5 per
# path. Codes are [Path1][Path2][Path3] tiers; nested crosspath deltas (e.g.
# "_110") are intentionally dropped — they're pro-extra and need delta-merging.
_MAIN_CODES: tuple[str, ...] = (
    "000",
    "100", "200", "300", "400", "500",
    "010", "020", "030", "040", "050",
    "001", "002", "003", "004", "005",
)  # fmt: skip


@dataclass
class StatsResult:
    game_version: str
    tiers: dict[str, dict] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.warnings


def _clean_node(raw: dict) -> dict:
    """Recursively clean a raw stats node.

    Flattens ``_order``-keyed containers into ordered lists of named children,
    decodes ``immuneBloonProperties`` into a readable damage type, and drops
    ``_``-prefixed keys (``_order`` handled here; ``_NNN`` crosspath deltas
    dropped). Every other field passes through verbatim — pro stats keep full
    fidelity.
    """
    from utils.btd6.damage_types import decode_damage_type

    out: dict = {}
    for key, value in raw.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict) and "_order" in value:
            out[key] = [
                {"name": child, **_clean_node(value[child])}
                for child in value["_order"]
                if isinstance(value.get(child), dict)
            ]
        elif key == "immuneBloonProperties":
            dt = decode_damage_type(value)
            out["damage_type"] = dt.name
            out["cannot_pop"] = dt.cannot_pop
            out["immuneBloonProperties"] = value
        else:
            out[key] = value
    return out


def parse_stats_json(text: str) -> StatsResult:
    """Parse a ``Module:BTD6 stats/<tower>/new`` JSON page.

    Raises ``ValueError`` (via :func:`json.loads`) on malformed JSON — that's
    the completeness guard against a truncated paste.
    """
    data = json.loads(text)
    game_version = str(data.get("_last_updated", ""))
    result = StatsResult(game_version=game_version)

    for code in _MAIN_CODES:
        node = data.get("_" + code)
        if not isinstance(node, dict):
            result.warnings.append(f"missing tier {code}")
            continue
        cleaned = _clean_node(node)
        cleaned["code"] = code
        cleaned["crosspath"] = "-".join(code)
        result.tiers[code] = cleaned

    if not game_version:
        result.warnings.append("missing _last_updated (game version)")
    return result


def _headline(tier: dict) -> str:
    """One-line headline (damage / type / pierce / cooldown / range) for a tier."""
    attacks = tier.get("attacks", [])
    best: dict | None = None
    for attack in attacks:
        for proj in attack.get("projectiles", []):
            if (proj.get("damage") or 0) > (best.get("damage", 0) if best else 0):
                best = proj
    parts: list[str] = []
    if best:
        parts.append(f"dmg {best.get('damage')}")
        if best.get("damage_type"):
            parts.append(str(best["damage_type"]))
        parts.append(f"pierce {best.get('pierce')}")
    if attacks and attacks[0].get("cooldown") is not None:
        parts.append(f"cd {attacks[0]['cooldown']}s")
    if tier.get("range") is not None:
        parts.append(f"range {tier['range']}")
    for ability in tier.get("abilities", []):
        parts.append(f"ability {ability.get('cooldown')}s")
    return ", ".join(parts)


def _render_stats_report(result: StatsResult) -> str:
    lines = [f"game version: {result.game_version or '?'}", ""]
    for code in _MAIN_CODES:
        tier = result.tiers.get(code)
        if tier is None:
            continue
        lines.append(f"  {tier['crosspath']}: {_headline(tier)}")
    lines.append("")
    if result.warnings:
        lines.append(f"⚠ {len(result.warnings)} warning(s):")
        lines.extend(f"  - {w}" for w in result.warnings)
    else:
        lines.append(f"✓ no warnings — all {len(result.tiers)} tiers parsed")
    return "\n".join(lines)


def _looks_like_json(text: str) -> bool:
    try:
        json.loads(text)
    except ValueError:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        type=Path,
        help="Pasted upgrades (.txt) or stats (.json) file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON (upgrades)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Write distilled stats JSON here (stats)",
    )
    parser.add_argument(
        "--tower-id",
        help="Tower id for the distilled file (default: filename stem)",
    )
    args = parser.parse_args(argv)

    text = args.path.read_text(encoding="utf-8")

    if _looks_like_json(text):
        stats = parse_stats_json(text)
        print(_render_stats_report(stats))
        if args.out:
            tower_id = args.tower_id or args.path.stem.replace(".stats", "")
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps(
                    {
                        "tower_id": tower_id,
                        "game_version": stats.game_version,
                        "source": "bloonswiki.com Module:BTD6 stats (CC BY-NC-SA)",
                        "tiers": stats.tiers,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            print(f"\nWrote {args.out}")
        return 1 if stats.warnings else 0

    result = parse_upgrades_page(text)
    if args.json:
        print(json.dumps(_to_dict(result), indent=2, ensure_ascii=False))
    else:
        print(_render_report(result))
    return 1 if result.warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
