"""Inventory the BTD Mod Helper game-data dump — *what* data exists and *where*.

Companion to ``scripts/parse_gamedata.py`` (which maps the dump into our stats
schema) and its ``--audit`` mode (which checks fidelity of the numbers we
already pull). This script answers the prior question: across the whole dump,
which domains and model types exist, what do they hold, and is the name /
description text linked? It is a **discovery** tool — point it at a clone to
build (or refresh, per patch) the data dictionary in
``docs/btd6/btd6-gamedata-dictionary.md``.

    git clone --depth 1 https://github.com/Btd6ModHelper/btd6-game-data /tmp/btd6gd
    python3.10 scripts/btd6_gamedata_inventory.py --dump /tmp/btd6gd            # domain overview
    python3.10 scripts/btd6_gamedata_inventory.py --dump /tmp/btd6gd --domain Powers
    python3.10 scripts/btd6_gamedata_inventory.py --dump /tmp/btd6gd --text-link

Nothing is written and the raw dump is never vendored — only the derived
findings (in the dictionary doc) are committed.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

# Pure asset-reference / geometry models — never the entity's data-bearing root.
_ASSET_NOISE = {
    "SpriteReference",
    "PrefabReference",
    "AudioClipReference",
    "AudioClip",
    "Vector2",
    "Vector3",
}

# Loose top-level files carry their own meaning; they are not entity domains.
_LOOSE_FILES = {
    "textTable.json": "every display string + description (names & tooltips)",
    "paragonDegreeData.json": "universal paragon degree-scaling constants",
    "frontierData.json": "Boss Bloon / Legends scaling data",
    "rogueData.json": "Rogue Legends mode data",
    "resources.json": "asset/resource references",
}


def _short_type(node: Any) -> str:
    """The bare model class from a ``$type`` string, or ``""``."""
    if not isinstance(node, dict):
        return ""
    raw = node.get("$type")
    if not isinstance(raw, str):
        return ""
    return raw.split(",", 1)[0].rsplit(".", 1)[-1]


def _walk_types(node: Any, counter: Counter) -> None:
    if isinstance(node, dict):
        short = _short_type(node)
        if short:
            counter[short] += 1
        for value in node.values():
            _walk_types(value, counter)
    elif isinstance(node, list):
        for value in node:
            _walk_types(value, counter)


def _iter_domain_files(dump: Path, domain: str):
    """Yield parsed JSON for every ``*.json`` under ``dump/<domain>`` (recursive)."""
    for fp in sorted((dump / domain).rglob("*.json")):
        try:
            yield fp, json.loads(fp.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            continue


def list_domains(dump: Path) -> list[str]:
    return sorted(
        p.name for p in dump.iterdir() if p.is_dir() and not p.name.startswith(".")
    )


def domain_summary(dump: Path, domain: str, top: int = 8) -> tuple[int, Counter]:
    """``(file_count, model-type Counter)`` for one domain."""
    counter: Counter = Counter()
    files = 0
    for _fp, data in _iter_domain_files(dump, domain):
        files += 1
        _walk_types(data, counter)
    return files, counter


def field_catalog(dump: Path, domain: str, model_type: str, limit: int = 25) -> Counter:
    """How often each scalar field appears on a given ``$type`` within a domain —
    the raw material for documenting what a model holds.
    """
    fields: Counter = Counter()

    def scan(node: Any) -> None:
        if isinstance(node, dict):
            if _short_type(node) == model_type:
                for key, value in node.items():
                    if not key.startswith("$") and isinstance(
                        value,
                        (int, float, str, bool),
                    ):
                        fields[key] += 1
            for value in node.values():
                scan(value)
        elif isinstance(node, list):
            for value in node:
                scan(value)

    for _fp, data in _iter_domain_files(dump, domain):
        scan(data)
    return fields


def text_link_report(dump: Path) -> list[str]:
    """How well entity names link to a ``<name>`` / ``<name> Description`` string
    in ``textTable.json`` — the name/description coverage that decides how much
    prose we can source straight from the game.
    """
    tt_path = dump / "textTable.json"
    if not tt_path.exists():
        return ["textTable.json missing"]
    tt = json.loads(tt_path.read_text("utf-8"))
    values = {v for v in tt.values() if isinstance(v, str)}

    lines: list[str] = [f"textTable: {len(tt):,} keys"]
    for domain, name_key in (("Upgrades", "name"), ("Powers", None)):
        named = desc = total = 0
        for fp, data in _iter_domain_files(dump, domain):
            total += 1
            name = data.get(name_key) if name_key else fp.stem
            if not isinstance(name, str):
                continue
            if name in tt or name in values:
                named += 1
            if f"{name} Description" in tt:
                desc += 1
        lines.append(
            f"  {domain}: {named}/{total} have a name string, "
            f"{desc}/{total} have a '<name> Description'",
        )
    return lines


def render_overview(dump: Path) -> str:
    lines = [f"BTD6 game-data dump inventory — {dump}", ""]
    lines.append(f"  {'domain':22}{'files':>8}   top model types")
    for domain in list_domains(dump):
        files, counter = domain_summary(dump, domain)
        top = ", ".join(f"{t}×{n}" for t, n in counter.most_common(4))
        lines.append(f"  {domain:22}{files:>8}   {top}")
    lines.append("")
    lines.append("  loose top-level files:")
    for name, meaning in _LOOSE_FILES.items():
        mark = "✓" if (dump / name).exists() else "·"
        lines.append(f"    {mark} {name:24} {meaning}")
    return "\n".join(lines)


def render_domain(dump: Path, domain: str) -> str:
    files, counter = domain_summary(dump, domain)
    lines = [f"{domain}/  ({files} files)", "", "  model types:"]
    for model_type, n in counter.most_common(20):
        lines.append(f"    {model_type:36}{n:>7}")
    # field catalog for the entity's *root* model. That model occurs about once
    # per file (BloonModel 235 ≈ 235 files), so among the substantive types
    # (after dropping pure asset-reference / geometry noise) pick the one whose
    # count is closest to the file count.
    candidates = [t for t in counter if t not in _ASSET_NOISE]
    primary = (
        min(candidates, key=lambda t: (abs(counter[t] - files), -counter[t]))
        if candidates and files
        else None
    )
    if primary:
        cat = field_catalog(dump, domain, primary)
        lines += ["", f"  scalar fields on {primary}:"]
        lines.append("    " + ", ".join(f for f, _ in cat.most_common(30)))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dump", required=True, type=Path, help="game-data clone path")
    ap.add_argument("--domain", help="drill into one domain's model types + fields")
    ap.add_argument(
        "--text-link",
        action="store_true",
        help="report name/description linkage to textTable.json",
    )
    args = ap.parse_args(argv)

    dump: Path = args.dump
    if not dump.is_dir():
        raise SystemExit(f"--dump {dump} is not a directory")

    if args.text_link:
        print("\n".join(text_link_report(dump)))
    elif args.domain:
        if not (dump / args.domain).is_dir():
            raise SystemExit(f"no domain {args.domain!r} under {dump}")
        print(render_domain(dump, args.domain))
    else:
        print(render_overview(dump))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
