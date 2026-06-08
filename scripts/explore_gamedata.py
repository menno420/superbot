"""Search and explore the BTD Mod Helper game-data dump.

Provenance: added 2026-06-08 to support BTD6 decode sessions. Unverified —
confirm outputs against the raw dump a few times before trusting them fully.

Point --dump at a local clone of github.com/Btd6ModHelper/btd6-game-data:

    git clone --depth 1 https://github.com/Btd6ModHelper/btd6-game-data /tmp/btd6gd

Modes (pick one):

    --list-types          Print all unique $type short names + occurrence counts.
    --search PATTERN      Find nodes whose $type contains PATTERN (case-insensitive).
                          Combine with --struct to show field names only (no values).
    --field FIELD         Find nodes that have a specific field name (exact match).
    --list-files          Print all JSON files found under --dump (or --in glob).

Scope filters (optional):

    --in SUBPATH          Restrict to files whose path contains SUBPATH
                          (e.g. "Towers/DartMonkey", "Heroes/Quincy").
                          Prefix-matched, case-insensitive.

Display options:

    --show-path           Include the JSON path to each matching node.
    --struct              Show matching node's keys only (no values). Useful for
                          understanding what fields a model type exposes.
    --limit N             Max nodes to print (default 20).
    --depth N             Max recursion depth when walking JSON (default 30).

Examples:
    python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --list-types
    python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --list-types --in Towers/Village

    python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --search RangeSupportModel
    python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --search RangeSupportModel --struct
    python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --search RangeSupportModel --show-path

    python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --field damageAddative
    python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --field damageAddative --in Towers/DartMonkey

    python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --search MoabShoveZoneModel --struct --in Towers/HeliPilot
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Generator
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# JSON tree walker
# ---------------------------------------------------------------------------


def _walk(
    node: Any,
    *,
    path: str = "",
    depth: int = 0,
    max_depth: int = 30,
) -> Generator[tuple[str, dict[str, Any]], None, None]:
    """Yield (json_path, dict_node) for every dict in the JSON tree."""
    if depth > max_depth:
        return
    if isinstance(node, dict):
        yield path, node
        for key, value in node.items():
            child_path = f"{path}.{key}" if path else key
            yield from _walk(
                value,
                path=child_path,
                depth=depth + 1,
                max_depth=max_depth,
            )
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from _walk(
                item,
                path=f"{path}[{i}]",
                depth=depth + 1,
                max_depth=max_depth,
            )


def _short_type(node: dict[str, Any]) -> str:
    """'Il2Cpp…Behaviors.AttackModel, Assembly-CSharp' → 'AttackModel'."""
    raw = node.get("$type")
    if not isinstance(raw, str):
        return ""
    return raw.split(",", 1)[0].rsplit(".", 1)[-1]


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def _find_json_files(dump: Path, *, in_filter: str | None) -> list[Path]:
    """Return sorted JSON files under dump, optionally filtered by subpath."""
    all_files = sorted(dump.rglob("*.json"))
    if not in_filter:
        return all_files
    needle = in_filter.lower().replace("\\", "/")
    return [
        f
        for f in all_files
        if needle in str(f.relative_to(dump)).lower().replace("\\", "/")
    ]


def _load(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"  [skip] {path.name}: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


def _fmt_node(node: dict[str, Any], *, struct: bool) -> str:
    if struct:
        keys = [k for k in node if not k.startswith("$")]
        return "{ " + ", ".join(keys) + " }"
    parts: list[str] = []
    for k, v in node.items():
        if k == "$type":
            continue
        if isinstance(v, (dict, list)):
            parts.append(f"{k}: <{type(v).__name__}>")
        else:
            parts.append(f"{k}: {v!r}")
    return "{ " + ", ".join(parts) + " }"


def _print_match(
    *,
    source_file: Path,
    dump: Path,
    json_path: str,
    node: dict[str, Any],
    show_path: bool,
    struct: bool,
    type_label: str = "",
) -> None:
    rel = source_file.relative_to(dump)
    header = f"  [{rel}]"
    if type_label:
        header += f"  {type_label}"
    if show_path and json_path:
        header += f"  @{json_path}"
    print(header)
    print(f"    {_fmt_node(node, struct=struct)}")


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------


def cmd_list_types(files: list[Path], dump: Path, *, max_depth: int) -> None:
    counts: Counter[str] = Counter()
    for path in files:
        data = _load(path)
        if data is None:
            continue
        for _, node in _walk(data, max_depth=max_depth):
            t = _short_type(node)
            if t:
                counts[t] += 1
    if not counts:
        print("No $type values found.")
        return
    print(f"{len(counts)} unique $type values across {len(files)} file(s):\n")
    for name, count in counts.most_common():
        print(f"  {count:>6}  {name}")


def cmd_search(
    files: list[Path],
    dump: Path,
    pattern: str,
    *,
    show_path: bool,
    struct: bool,
    limit: int,
    max_depth: int,
) -> None:
    needle = pattern.lower()
    found = 0
    for path in files:
        if found >= limit:
            break
        data = _load(path)
        if data is None:
            continue
        for json_path, node in _walk(data, max_depth=max_depth):
            if found >= limit:
                break
            t = _short_type(node)
            if needle in t.lower():
                _print_match(
                    source_file=path,
                    dump=dump,
                    json_path=json_path,
                    node=node,
                    show_path=show_path,
                    struct=struct,
                    type_label=t,
                )
                found += 1
    if found == 0:
        print(f"No nodes found with $type containing '{pattern}'.")
    elif found >= limit:
        print(f"\n  (limit {limit} reached — use --limit N to see more)")


def cmd_field(
    files: list[Path],
    dump: Path,
    field_name: str,
    *,
    show_path: bool,
    struct: bool,
    limit: int,
    max_depth: int,
) -> None:
    found = 0
    for path in files:
        if found >= limit:
            break
        data = _load(path)
        if data is None:
            continue
        for json_path, node in _walk(data, max_depth=max_depth):
            if found >= limit:
                break
            if field_name in node:
                _print_match(
                    source_file=path,
                    dump=dump,
                    json_path=json_path,
                    node=node,
                    show_path=show_path,
                    struct=struct,
                    type_label=_short_type(node) or "",
                )
                found += 1
    if found == 0:
        print(f"No nodes found with field '{field_name}'.")
    elif found >= limit:
        print(f"\n  (limit {limit} reached — use --limit N to see more)")


def cmd_list_files(files: list[Path], dump: Path) -> None:
    print(f"{len(files)} file(s) under {dump}:\n")
    for f in files:
        print(f"  {f.relative_to(dump)}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--dump",
        required=True,
        metavar="PATH",
        help="Path to the btd6-game-data clone.",
    )

    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--list-types",
        action="store_true",
        help="List all unique $type values with counts.",
    )
    mode.add_argument(
        "--search",
        metavar="PATTERN",
        help="Find nodes whose $type contains PATTERN.",
    )
    mode.add_argument(
        "--field",
        metavar="FIELD",
        help="Find nodes that have a specific field name.",
    )
    mode.add_argument(
        "--list-files",
        action="store_true",
        help="List all JSON files found (respecting --in).",
    )

    p.add_argument(
        "--in",
        dest="in_filter",
        metavar="SUBPATH",
        help="Restrict search to files whose path contains SUBPATH.",
    )
    p.add_argument(
        "--show-path",
        action="store_true",
        help="Print the JSON path to each matching node.",
    )
    p.add_argument(
        "--struct",
        action="store_true",
        help="Show field names only (no values).",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max matching nodes to print (default 20).",
    )
    p.add_argument(
        "--depth",
        type=int,
        default=30,
        help="Max recursion depth (default 30).",
    )
    return p


def main() -> None:
    args = _build_parser().parse_args()
    dump = Path(args.dump)
    if not dump.is_dir():
        sys.exit(f"error: --dump path not found or not a directory: {dump}")

    files = _find_json_files(dump, in_filter=args.in_filter)
    if not files:
        sys.exit(
            f"error: no JSON files found under {dump}"
            + (f" matching '{args.in_filter}'" if args.in_filter else ""),
        )

    if args.list_types:
        cmd_list_types(files, dump, max_depth=args.depth)
    elif args.search:
        cmd_search(
            files,
            dump,
            args.search,
            show_path=args.show_path,
            struct=args.struct,
            limit=args.limit,
            max_depth=args.depth,
        )
    elif args.field:
        cmd_field(
            files,
            dump,
            args.field,
            show_path=args.show_path,
            struct=args.struct,
            limit=args.limit,
            max_depth=args.depth,
        )
    elif args.list_files:
        cmd_list_files(files, dump)


if __name__ == "__main__":
    main()
