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
import copy
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

# The 16 single-path codes a stats page must define: base + 5 per path. Codes
# are [Path1][Path2][Path3] tiers. Nested crosspath deltas (e.g. "_110") live
# inside these nodes; _clean_node strips them when flattening a single-path
# tier, and _reconstruct_crosspaths merges them back into full crosspath tiers.
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

    _reconstruct_crosspaths(data, result)

    if not game_version:
        result.warnings.append("missing _last_updated (game version)")
    return result


def _canonical(node: dict) -> str:
    """Stable string for comparing two reconstructions of the same crosspath.

    Ignores dict key order and the int/float spelling of equal numbers, plus the
    synthetic ``code``/``crosspath`` labels, so a real stat divergence is the
    only thing that registers.
    """

    def norm(value: object) -> object:
        if isinstance(value, dict):
            return {
                k: norm(v)
                for k, v in sorted(value.items())
                if k not in ("code", "crosspath")
            }
        if isinstance(value, list):
            items = [norm(v) for v in value]
            # Named children (attacks/projectiles/effects/abilities/subtowers)
            # are merged append-only, so the two bases can list the same set in a
            # different order. Compare them as a set keyed by name, not by index.
            if items and all(isinstance(it, dict) and "name" in it for it in items):
                items = sorted(items, key=lambda d: str(d.get("name", "")))
            return items
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value

    return json.dumps(norm(node), sort_keys=True, ensure_ascii=False)


def _reconstruct_crosspaths(data: dict, result: StatsResult) -> None:
    """Reconstruct full crosspath tiers from the nested ``_NNN`` deltas.

    Faithful to the wiki's own renderer (``Module:BTD6 stats`` ``upgrade_crosspaths``):
    a single-path base node carries its crosspath deltas nested by full code, and
    they are applied **cumulatively** along the cross path. For base ``_200`` the
    path-2 chain is ``_210`` then ``_220``, so ``220`` = ``_200 ∘ _210 ∘ _220`` —
    *not* ``_200 ∘ _220`` (which would skip the tier-1 step and lose its stats).

    A crosspath is nested under whichever base path holds the higher tier; equal
    tiers (e.g. ``220`` under both ``_200`` and ``_020``) appear under both. Those
    are reconstructed from each base via its own chain, the cleaned results are
    compared, divergence is warned, and the deterministic preferred base wins. We
    only ever build legal codes (one path 0-5, the cross path 1-2), so a wiki-side
    helper/test node can never become committed data.
    """
    from utils.btd6 import tier_codes

    discovered: dict[str, dict[str, dict]] = {}  # code -> {base_code: cleaned}
    for base_code in _MAIN_CODES:
        if tier_codes.is_base(base_code):
            continue
        base_raw = data.get("_" + base_code)
        if not isinstance(base_raw, dict):
            continue
        primary = tier_codes.primary_path(base_code)
        if primary is None:
            continue
        main_tier = tier_codes.digits(base_code)[primary - 1]
        for cross_path in (1, 2, 3):
            if cross_path == primary:
                continue
            acc = base_raw
            # Cumulative cross-path chain: tiers 1..2, but only those this base
            # owns (cross_tier <= main_tier), exactly as the wiki nests them.
            for cross_tier in (1, 2):
                if cross_tier > main_tier:
                    break
                code_digits = [0, 0, 0]
                code_digits[primary - 1] = main_tier
                code_digits[cross_path - 1] = cross_tier
                code = "".join(str(d) for d in code_digits)
                delta = base_raw.get("_" + code)
                if not isinstance(delta, dict):
                    continue
                acc = _deep_merge_raw(acc, delta)
                discovered.setdefault(code, {})[base_code] = _clean_node(acc)

    for code, by_base in discovered.items():
        preferred = tier_codes.preferred_parent(by_base.keys())
        baseline = _canonical(by_base[preferred])
        if any(
            _canonical(node) != baseline
            for base_code, node in by_base.items()
            if base_code != preferred
        ):
            # The two reconstruction orders disagree on a stat the final delta
            # doesn't reconcile — a genuine, non-commutative ambiguity. We can't
            # verify the in-game value offline, so drop it rather than commit a
            # coin-flip: trustworthy data over complete data.
            result.warnings.append(
                f"crosspath {code} diverges between bases {sorted(by_base)} "
                f"— dropped (cannot verify offline)",
            )
            continue
        chosen = dict(by_base[preferred])
        chosen["code"] = code
        chosen["crosspath"] = "-".join(code)
        result.tiers[code] = chosen


# ---------------------------------------------------------------------------
# Hero stats — Module:BTD6 stats/<Hero>/new JSON (per-LEVEL, delta-encoded)
# ---------------------------------------------------------------------------
#
# Unlike towers (complete `_000`.._005` crosspath tiers), a hero page stores
# level 1 as the top-level node and `_2`.._20` as *partial deltas* over the
# running level state. We deep-merge each delta cumulatively (mirroring the
# wiki's own render) and clean each resulting level. Only ~6 heroes have such
# a module; the rest are prose-only and have no machine-readable stats.

_HERO_MAX_LEVEL = 20


@dataclass
class HeroStatsResult:
    game_version: str
    levels: dict[str, dict] = field(default_factory=dict)  # "1".."20" -> tier
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.warnings


def _deep_merge_raw(base: dict, delta: dict) -> dict:
    """Recursively merge a raw level delta onto the running base.

    Dicts merge key-by-key; every other value (scalars, lists) overwrites.
    Hero ``_N`` deltas mirror the base structure (``attacks`` → ``_order``
    containers → projectiles), so a recursive dict-merge reconstructs the
    full per-level node before :func:`_clean_node` flattens it.
    """
    out = copy.deepcopy(base)
    for key, value in delta.items():
        if (
            key == "_order"
            and isinstance(value, list)
            and isinstance(out.get(key), list)
        ):
            # An `_order` list enumerates which named children exist; a partial
            # delta (e.g. a crosspath that only re-states one attack) must
            # *extend* the parent's order, not replace it — otherwise a
            # multi-attack tower loses the siblings the delta didn't mention.
            out[key] = list(out[key]) + [c for c in value if c not in out[key]]
        elif isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge_raw(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def parse_hero_stats_json(text: str) -> HeroStatsResult:
    """Parse a hero ``Module:BTD6 stats/<Hero>/new`` JSON page into per-level
    stats by cumulatively merging the ``_2``..``_20`` deltas onto the base.

    Raises ``ValueError`` (via :func:`json.loads`) on malformed JSON.
    """
    data = json.loads(text)
    game_version = str(data.get("_last_updated", ""))
    result = HeroStatsResult(game_version=game_version)

    base_raw = {k: v for k, v in data.items() if not k.startswith("_")}
    if not base_raw:
        result.warnings.append("no base (level 1) stats at top level")
        return result

    running = copy.deepcopy(base_raw)
    for level in range(1, _HERO_MAX_LEVEL + 1):
        if level > 1:
            delta = data.get(f"_{level}")
            if isinstance(delta, dict):
                running = _deep_merge_raw(running, delta)
            # A missing delta means the level changed nothing statistically
            # (e.g. an ability-only level) — not a warning.
        cleaned = _clean_node(running)
        cleaned["level"] = level
        result.levels[str(level)] = cleaned

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
    if attacks and attacks[0].get("rate") is not None:
        parts.append(f"cd {attacks[0]['rate']}s")
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


# ---------------------------------------------------------------------------
# Bloon Cargo parsing (btd6_bloons: immunity + children wikitext)
# ---------------------------------------------------------------------------

_BLOON_COUNT_RE = re.compile(r"×\s*(\d+)")
_DT_BLOCK_RE = re.compile(r"\[\[\s*damage type\s*\|([^\]]+)\]\]", re.IGNORECASE)
_BRACKET_TOKEN_RE = re.compile(r"\[\[([^\]|]+)\]\]")


def parse_bloon_immunity(text: str) -> tuple[list[str], list[str]]:
    """Parse a ``btd6_bloons.immunity`` value into (damage types, status tokens).

    Handles the three shapes seen on the wiki:
      * ``[[damage type|Sharp, Shatter, Cold, Energy]]`` (also ``Damage type``);
      * a bare comma list ``Energy, Plasma, Acid`` (Glass Bloon);
      * status immunities ``[[Slow]], [[blowback]], [[knockback]]`` (BAD etc.).
    """
    text = (text or "").strip()
    if not text:
        return [], []
    immune: list[str] = []
    status: list[str] = []
    block = _DT_BLOCK_RE.search(text)
    if block:
        immune = [t.strip() for t in block.group(1).split(",") if t.strip()]
    bracket_tokens = [t.strip() for t in _BRACKET_TOKEN_RE.findall(text)]
    for tok in bracket_tokens:
        if tok.lower() != "damage type":
            status.append(tok)
    if not immune and not bracket_tokens and "[[" not in text:
        immune = [t.strip() for t in text.split(",") if t.strip()]
    return immune, status


def parse_bloon_children(text: str) -> list[dict]:
    """Parse a ``btd6_bloons.parent_of`` value into structured children.

    Returns ``[{"bloon_id", "count", "modifiers"}]``. Leading Camo/Regrow/
    Fortified tokens become ``modifiers``; the remaining text names the child
    bloon (which may itself be unlinked, as in Glass Bloon's children).
    """
    from utils.btd6 import bloon_ids

    text = (text or "").strip()
    if not text:
        return []
    out: list[dict] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        count_match = _BLOON_COUNT_RE.search(part)
        count = int(count_match.group(1)) if count_match else 1
        plain = bloon_ids.strip_links(_BLOON_COUNT_RE.sub("", part))
        tokens = plain.split()
        modifiers: list[str] = []
        while tokens and tokens[0].lower() in bloon_ids.MODIFIER_TOKENS:
            modifiers.append(tokens.pop(0).lower())
        bloon_id = bloon_ids.normalize_bloon_name(" ".join(tokens))
        if bloon_id:
            out.append({"bloon_id": bloon_id, "count": count, "modifiers": modifiers})
    return out


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
