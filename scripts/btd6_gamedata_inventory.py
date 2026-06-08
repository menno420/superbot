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

# Fetch status per domain — does ``parse_gamedata.py`` (or a derived pipeline)
# currently extract this into committed data / the runtime? This is the bridge
# from "what exists" to "what we fetch": ⬜ rows are the un-mined surface. Keep in
# sync with the decode-status doc when a domain's ingestion changes.
_INGEST_STATUS: dict[str, tuple[str, str]] = {
    # domain: (status_glyph, what we pull / why not)
    "Towers": ("✅", "stats, attacks, projectiles, abilities, subtowers, zones, buffs"),
    "Upgrades": ("✅", "names, per-difficulty cost, xp, path/tier, descriptions"),
    "Maps": ("✅", "full cutover: difficulty, has_water, names (curated removables)"),
    "Bloons": ("🟡", "structure known; still wiki-sourced (children/immunity partial)"),
    "Bosses": ("⬜", "wiki-sourced; cosmetic Bosses/ — combat lives in Bloons/"),
    "Rounds": (
        "🟡",
        "composition drives derived RBE + per-round cash; not ingested as-is",
    ),
    "IncomeSets": ("🟡", "decay bands feed the per-round cash derivation"),
    "Powers": (
        "✅",
        "powers.json: name, desc, MM cost, quantity, between-rounds, effect factors",
    ),
    "Knowledge": (
        "✅",
        "monkey_knowledge.json: name, category, description, MM cost, investment",
    ),
    "Achievements": ("⬜", "not ingested"),
    "Artifacts": ("⬜", "not ingested (Rogue Legends artifacts)"),
    "Mods": ("⬜", "not ingested (game-mode rule mods — partially explored)"),
    "Skins": ("⬜", "cosmetic; not ingested"),
    "GeraldoItems": (
        "✅",
        "all 16 shop items: name, description, cash cost, unlock level, quantity",
    ),
    "TrophyStoreItems": ("⬜", "cosmetic; not ingested"),
    "BloonOverlays": ("⬜", "cosmetic overlays; not ingested"),
    "Buffs": ("⬜", "UI buff ICONS only — effects live inline in Towers/"),
}
_LOOSE_INGEST: dict[str, str] = {
    "textTable.json": "✅",
    "paragonDegreeData.json": "🟡",
    "frontierData.json": "⬜",
    "rogueData.json": "⬜",
    "resources.json": "⬜",
}


def _dump_version(dump: Path) -> str:
    """Game version the dump was taken at (Mod Helper stamps it on the commit,
    e.g. ``55.1``) + the short sha — the map's provenance line. Best-effort.
    """
    import subprocess

    out = []
    for fmt in ("%s", "%h"):
        try:
            val = subprocess.check_output(
                ["git", "-C", str(dump), "log", "-1", f"--format={fmt}"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            out.append(val.split()[0] if (fmt == "%s" and val) else val)
        except Exception:  # noqa: BLE001 - best-effort provenance
            out.append("")
    version, sha = out[0], out[1]
    return f"{version} (sha {sha})" if version or sha else "unknown"


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


# Domains where the closest-to-file-count heuristic picks a per-file singleton
# (e.g. a CreateSoundOnSellModel) instead of the data-bearing root — name the
# real root explicitly so the field catalog is useful.
_PRIMARY_OVERRIDE: dict[str, str] = {"Towers": "TowerModel"}


def _primary_model(domain: str, counter: Counter, files: int) -> str | None:
    """The entity's root model: the non-noise type whose count is closest to the
    file count (``BloonModel`` 235 ≈ 235 files), tie-broken toward the larger.
    A curated override wins for domains where that heuristic misfires.
    """
    override = _PRIMARY_OVERRIDE.get(domain)
    if override and override in counter:
        return override
    candidates = [t for t in counter if t not in _ASSET_NOISE]
    if not candidates or not files:
        return None
    return min(candidates, key=lambda t: (abs(counter[t] - files), -counter[t]))


def _loose_structure(dump: Path, name: str, limit: int = 24) -> list[str]:
    """Top-level keys (+ value kind) of a loose JSON file — what it holds."""
    path = dump / name
    if not path.exists():
        return ["(missing)"]
    try:
        data = json.loads(path.read_text("utf-8"))
    except Exception:  # noqa: BLE001 - report unreadable rather than crash
        return ["(unreadable)"]
    if not isinstance(data, dict):
        return [
            (
                f"({type(data).__name__} of {len(data)})"
                if isinstance(data, list)
                else "(scalar)"
            ),
        ]
    kind = {
        dict: "obj",
        list: "list",
        str: "str",
        bool: "bool",
        int: "num",
        float: "num",
    }
    keys = [f"{k}:{kind.get(type(v), '?')}" for k, v in list(data.items())[:limit]]
    tail = f" … (+{len(data) - limit} more)" if len(data) > limit else ""
    return [f"{len(data):,} top-level keys", ", ".join(keys) + tail]


def render_full_map(dump: Path) -> str:
    """The complete, regenerable coverage map: every domain's file count, all
    model ``$types``, the primary model's fields, every loose file's structure,
    and a fetch-status column. Markdown, written to the coverage-map doc.
    """
    out: list[str] = [
        "# BTD6 dump coverage map — what's in each file",
        "",
        "> **Status:** `living-ledger` · **auto-generated — do not hand-edit.**",
        "> Generated by `python3.10 scripts/btd6_gamedata_inventory.py --full-map`",
        f"> from BTD Mod Helper game-data dump **v{_dump_version(dump)}**.",
        "> Re-run on every dump re-pull; the file counts double as a change"
        " fingerprint.",
        "",
        "**Fetch status** — does our pipeline extract this yet? `✅` ingested ·"
        " `🟡` partial · `⬜` present in dump, not yet fetched. The `⬜` rows are"
        " the remaining surface for the goal of *fetching everything on each"
        " update*.",
        "",
        "## Domains",
        "",
        "| Domain | Files | Fetch | What we pull / why not |",
        "|---|---:|:---:|---|",
    ]
    domains = list_domains(dump)
    summaries: dict[str, tuple[int, Counter]] = {}
    for domain in domains:
        files, counter = domain_summary(dump, domain)
        summaries[domain] = (files, counter)
        glyph, note = _INGEST_STATUS.get(domain, ("⬜", "—"))
        out.append(f"| `{domain}/` | {files:,} | {glyph} | {note} |")

    out += [
        "",
        "## Loose top-level files",
        "",
        "| File | Fetch | Meaning |",
        "|---|:---:|---|",
    ]
    for name, meaning in _LOOSE_FILES.items():
        glyph = _LOOSE_INGEST.get(name, "⬜")
        mark = glyph if (dump / name).exists() else "—(absent)"
        out.append(f"| `{name}` | {mark} | {meaning} |")

    out += ["", "## Per-domain detail", ""]
    for domain in domains:
        files, counter = summaries[domain]
        glyph, note = _INGEST_STATUS.get(domain, ("⬜", "—"))
        out.append(f"### `{domain}/` — {files:,} files {glyph}")
        out.append("")
        types = ", ".join(f"`{t}`×{n:,}" for t, n in counter.most_common(20))
        out.append(f"- **Model types:** {types}")
        primary = _primary_model(domain, counter, files)
        if primary:
            cat = field_catalog(dump, domain, primary)
            fields = ", ".join(f"`{f}`" for f, _ in cat.most_common(40))
            out.append(
                f"- **Primary model `{primary}` scalar fields:** {fields or '(none)'}",
            )
        out.append("")

    out += ["## Loose-file structure", ""]
    for name in _LOOSE_FILES:
        out.append(f"### `{name}`")
        for line in _loose_structure(dump, name):
            out.append(f"- {line}")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dump", required=True, type=Path, help="game-data clone path")
    ap.add_argument("--domain", help="drill into one domain's model types + fields")
    ap.add_argument(
        "--text-link",
        action="store_true",
        help="report name/description linkage to textTable.json",
    )
    ap.add_argument(
        "--full-map",
        action="store_true",
        help="render the complete per-domain coverage map (markdown)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        help="with --full-map, write the markdown here instead of stdout",
    )
    args = ap.parse_args(argv)

    dump: Path = args.dump
    if not dump.is_dir():
        raise SystemExit(f"--dump {dump} is not a directory")

    if args.full_map:
        md = render_full_map(dump)
        if args.out:
            args.out.write_text(md, "utf-8")
            print(f"wrote {args.out} ({md.count(chr(10))} lines)")
        else:
            print(md)
    elif args.text_link:
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
