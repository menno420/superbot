"""Convert ``data/btd6/*.csv`` scaffolds into runtime JSON fixtures.

The team edits ``data/btd6/towers.csv`` and ``data/btd6/heroes.csv``
collaboratively (typically in Google Sheets). This script converts the
CSVs into the JSON shape that ``disbot/services/btd6_data_service`` reads
at boot.

Validation runs before any file is written: if anything fails, nothing
is touched and the error message points at the offending row + column.
The validation mirrors what ``btd6_data_service._parse_*`` would catch
later, so a successful import guarantees the runtime loader will accept
the result.

Usage::

    python3.10 scripts/import_btd6_data_from_csv.py

Optional flags::

    --towers-csv PATH      Override the towers CSV path
    --heroes-csv PATH      Override the heroes CSV path
    --towers-json PATH     Override the towers JSON output path
    --heroes-json PATH     Override the heroes JSON output path
    --game-version 54.0    Stamp this game_version into the JSON envelopes
                           (default: read from existing towers.json if present,
                           else "TBD")
    --check                Validate the CSVs and report errors without
                           writing any output. Exit non-zero on any error.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_TOWERS_CSV = _REPO_ROOT / "data" / "btd6" / "towers.csv"
_DEFAULT_HEROES_CSV = _REPO_ROOT / "data" / "btd6" / "heroes.csv"
_DEFAULT_TOWERS_JSON = _REPO_ROOT / "disbot" / "data" / "btd6" / "towers.json"
_DEFAULT_HEROES_JSON = _REPO_ROOT / "disbot" / "data" / "btd6" / "heroes.json"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


_TOWER_CATEGORIES = frozenset({"primary", "military", "magic", "support"})

_TOWER_COLUMNS: tuple[str, ...] = (
    "id",
    "canonical",
    "category",
    "aliases",
    "base_cost",
    "description",
    "top_1",
    "top_2",
    "top_3",
    "top_4",
    "top_5",
    "mid_1",
    "mid_2",
    "mid_3",
    "mid_4",
    "mid_5",
    "bot_1",
    "bot_2",
    "bot_3",
    "bot_4",
    "bot_5",
    "wiki_url",
)

_HERO_COLUMNS: tuple[str, ...] = (
    "id",
    "canonical",
    "aliases",
    "base_cost",
    "description",
    "ability_3_name",
    "ability_3_summary",
    "ability_10_name",
    "ability_10_summary",
    "wiki_url",
)


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------


@dataclass
class ConversionError:
    """One row-level validation failure with enough context to fix it."""

    file: str
    row: int  # 1-indexed including header (so the first data row is row 2)
    field: str
    reason: str

    def render(self) -> str:
        return f"  {self.file}: row {self.row}, column {self.field!r}: {self.reason}"


def _split_aliases(raw: str) -> list[str]:
    """Parse the ``aliases`` cell: comma-separated, trimmed, deduped."""
    seen: set[str] = set()
    out: list[str] = []
    for piece in raw.split(","):
        clean = piece.strip()
        if not clean:
            continue
        lowered = clean.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        out.append(clean)
    return out


def _read_csv(
    path: Path,
    expected_columns: tuple[str, ...],
) -> tuple[list[dict[str, str]], list[ConversionError]]:
    """Read a CSV; verify column set; return rows + any header errors."""
    if not path.exists():
        return [], [
            ConversionError(
                file=str(path),
                row=0,
                field="<file>",
                reason=f"CSV not found: {path}",
            ),
        ]
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            return [], [
                ConversionError(
                    file=str(path),
                    row=1,
                    field="<header>",
                    reason="empty CSV (no header row)",
                ),
            ]
        missing = [c for c in expected_columns if c not in reader.fieldnames]
        if missing:
            return [], [
                ConversionError(
                    file=str(path),
                    row=1,
                    field="<header>",
                    reason=f"missing columns: {missing}",
                ),
            ]
        rows = list(reader)
    return rows, []


def _validate_required_string(
    value: str | None,
    *,
    file: str,
    row: int,
    field: str,
    errors: list[ConversionError],
) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        errors.append(
            ConversionError(
                file=file,
                row=row,
                field=field,
                reason="required field is empty",
            ),
        )
    return cleaned


def _validate_positive_int(
    value: str | None,
    *,
    file: str,
    row: int,
    field: str,
    errors: list[ConversionError],
) -> int:
    raw = (value or "").strip()
    if not raw:
        errors.append(
            ConversionError(
                file=file,
                row=row,
                field=field,
                reason="required positive integer is empty",
            ),
        )
        return 0
    try:
        parsed = int(raw)
    except ValueError:
        errors.append(
            ConversionError(
                file=file,
                row=row,
                field=field,
                reason=f"not a valid integer: {raw!r}",
            ),
        )
        return 0
    if parsed <= 0:
        errors.append(
            ConversionError(
                file=file,
                row=row,
                field=field,
                reason=f"must be > 0, got {parsed}",
            ),
        )
    return parsed


def _convert_tower_row(
    row: dict[str, str],
    *,
    file: str,
    row_number: int,
    errors: list[ConversionError],
) -> dict[str, Any]:
    tower_id = _validate_required_string(
        row.get("id"),
        file=file,
        row=row_number,
        field="id",
        errors=errors,
    )
    canonical = _validate_required_string(
        row.get("canonical"),
        file=file,
        row=row_number,
        field="canonical",
        errors=errors,
    )
    category = _validate_required_string(
        row.get("category"),
        file=file,
        row=row_number,
        field="category",
        errors=errors,
    )
    if category and category not in _TOWER_CATEGORIES:
        errors.append(
            ConversionError(
                file=file,
                row=row_number,
                field="category",
                reason=(
                    f"must be one of {sorted(_TOWER_CATEGORIES)}; got {category!r}"
                ),
            ),
        )
    base_cost = _validate_positive_int(
        row.get("base_cost"),
        file=file,
        row=row_number,
        field="base_cost",
        errors=errors,
    )
    description = _validate_required_string(
        row.get("description"),
        file=file,
        row=row_number,
        field="description",
        errors=errors,
    )
    wiki_url = _validate_required_string(
        row.get("wiki_url"),
        file=file,
        row=row_number,
        field="wiki_url",
        errors=errors,
    )
    aliases = _split_aliases(row.get("aliases") or "")

    upgrade_paths: dict[str, list[str]] = {}
    for path_key, prefix in (("top", "top_"), ("mid", "mid_"), ("bot", "bot_")):
        tiers: list[str] = []
        for tier in range(1, 6):
            field = f"{prefix}{tier}"
            tier_value = _validate_required_string(
                row.get(field),
                file=file,
                row=row_number,
                field=field,
                errors=errors,
            )
            tiers.append(tier_value)
        upgrade_paths[path_key] = tiers

    return {
        "id": tower_id,
        "canonical": canonical,
        "aliases": aliases,
        "category": category,
        "base_cost": base_cost,
        "description": description,
        "upgrade_paths": upgrade_paths,
        "wiki_url": wiki_url,
    }


def _convert_hero_row(
    row: dict[str, str],
    *,
    file: str,
    row_number: int,
    errors: list[ConversionError],
) -> dict[str, Any]:
    hero_id = _validate_required_string(
        row.get("id"),
        file=file,
        row=row_number,
        field="id",
        errors=errors,
    )
    canonical = _validate_required_string(
        row.get("canonical"),
        file=file,
        row=row_number,
        field="canonical",
        errors=errors,
    )
    base_cost = _validate_positive_int(
        row.get("base_cost"),
        file=file,
        row=row_number,
        field="base_cost",
        errors=errors,
    )
    description = _validate_required_string(
        row.get("description"),
        file=file,
        row=row_number,
        field="description",
        errors=errors,
    )
    wiki_url = _validate_required_string(
        row.get("wiki_url"),
        file=file,
        row=row_number,
        field="wiki_url",
        errors=errors,
    )
    aliases = _split_aliases(row.get("aliases") or "")

    abilities: list[dict[str, Any]] = []
    for level, name_field, summary_field in (
        (3, "ability_3_name", "ability_3_summary"),
        (10, "ability_10_name", "ability_10_summary"),
    ):
        name = _validate_required_string(
            row.get(name_field),
            file=file,
            row=row_number,
            field=name_field,
            errors=errors,
        )
        summary = _validate_required_string(
            row.get(summary_field),
            file=file,
            row=row_number,
            field=summary_field,
            errors=errors,
        )
        abilities.append({"level": level, "name": name, "summary": summary})

    return {
        "id": hero_id,
        "canonical": canonical,
        "aliases": aliases,
        "base_cost": base_cost,
        "description": description,
        "abilities": abilities,
        "wiki_url": wiki_url,
    }


# ---------------------------------------------------------------------------
# Cross-row validation (uniqueness, alias collisions)
# ---------------------------------------------------------------------------


def _check_unique_ids(
    entries: list[dict[str, Any]],
    *,
    file: str,
    errors: list[ConversionError],
) -> None:
    seen: dict[str, int] = {}
    for idx, entry in enumerate(entries, start=2):  # row 2 = first data row
        entry_id = entry.get("id")
        if not entry_id:
            continue
        if entry_id in seen:
            errors.append(
                ConversionError(
                    file=file,
                    row=idx,
                    field="id",
                    reason=(
                        f"duplicate id {entry_id!r} (first seen at row {seen[entry_id]})"
                    ),
                ),
            )
        else:
            seen[entry_id] = idx


def _check_alias_collisions(
    *,
    towers: list[dict[str, Any]],
    heroes: list[dict[str, Any]],
    errors: list[ConversionError],
    towers_file: str,
    heroes_file: str,
) -> None:
    """Catch alias collisions before they reach the runtime validator."""
    owners: dict[str, tuple[str, str, int]] = {}
    for idx, tower in enumerate(towers, start=2):
        all_terms = [*tower.get("aliases", [])]
        canonical = tower.get("canonical")
        if canonical:
            all_terms.append(canonical)
        for term in all_terms:
            key = term.strip().lower()
            if not key:
                continue
            owner_label = f"tower:{tower.get('id')}"
            if key in owners and owners[key][0] != owner_label:
                existing_owner, existing_file, existing_row = owners[key]
                errors.append(
                    ConversionError(
                        file=towers_file,
                        row=idx,
                        field="aliases",
                        reason=(
                            f"alias collision: {key!r} also owned by "
                            f"{existing_owner} ({existing_file} row {existing_row})"
                        ),
                    ),
                )
            else:
                owners[key] = (owner_label, towers_file, idx)
    for idx, hero in enumerate(heroes, start=2):
        all_terms = [*hero.get("aliases", [])]
        canonical = hero.get("canonical")
        if canonical:
            all_terms.append(canonical)
        for term in all_terms:
            key = term.strip().lower()
            if not key:
                continue
            owner_label = f"hero:{hero.get('id')}"
            if key in owners and owners[key][0] != owner_label:
                existing_owner, existing_file, existing_row = owners[key]
                errors.append(
                    ConversionError(
                        file=heroes_file,
                        row=idx,
                        field="aliases",
                        reason=(
                            f"alias collision: {key!r} also owned by "
                            f"{existing_owner} ({existing_file} row {existing_row})"
                        ),
                    ),
                )
            else:
                owners[key] = (owner_label, heroes_file, idx)


# ---------------------------------------------------------------------------
# Top-level convert
# ---------------------------------------------------------------------------


def _existing_game_version(json_path: Path) -> str:
    if not json_path.exists():
        return "TBD"
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "TBD"
    value = data.get("game_version")
    return str(value) if value else "TBD"


def convert(
    *,
    towers_csv: Path,
    heroes_csv: Path,
    towers_json: Path,
    heroes_json: Path,
    game_version: str | None,
    check_only: bool,
) -> int:
    """Run a full CSV→JSON conversion. Return process exit code."""
    errors: list[ConversionError] = []

    tower_rows, header_errors = _read_csv(towers_csv, _TOWER_COLUMNS)
    errors.extend(header_errors)
    hero_rows, header_errors = _read_csv(heroes_csv, _HERO_COLUMNS)
    errors.extend(header_errors)

    converted_towers: list[dict[str, Any]] = []
    for offset, row in enumerate(tower_rows):
        converted_towers.append(
            _convert_tower_row(
                row,
                file=str(towers_csv),
                row_number=offset + 2,
                errors=errors,
            ),
        )

    converted_heroes: list[dict[str, Any]] = []
    for offset, row in enumerate(hero_rows):
        converted_heroes.append(
            _convert_hero_row(
                row,
                file=str(heroes_csv),
                row_number=offset + 2,
                errors=errors,
            ),
        )

    _check_unique_ids(
        converted_towers,
        file=str(towers_csv),
        errors=errors,
    )
    _check_unique_ids(
        converted_heroes,
        file=str(heroes_csv),
        errors=errors,
    )
    _check_alias_collisions(
        towers=converted_towers,
        heroes=converted_heroes,
        errors=errors,
        towers_file=str(towers_csv),
        heroes_file=str(heroes_csv),
    )

    if errors:
        print(f"Refusing to write — {len(errors)} validation error(s):")
        for err in errors:
            print(err.render())
        return 1

    resolved_game_version = (
        game_version if game_version else _existing_game_version(towers_json)
    )
    source_label = "hand-curated from public BTD6 reference data"

    towers_envelope = {
        "data_version": "1.0",
        "game_version": resolved_game_version,
        "source": source_label,
        "towers": converted_towers,
    }
    heroes_envelope = {
        "data_version": "1.0",
        "game_version": resolved_game_version,
        "source": source_label,
        "heroes": converted_heroes,
    }

    if check_only:
        print(
            f"OK — {len(converted_towers)} tower(s) and "
            f"{len(converted_heroes)} hero(es) validated. "
            "No files written (--check).",
        )
        return 0

    towers_json.parent.mkdir(parents=True, exist_ok=True)
    heroes_json.parent.mkdir(parents=True, exist_ok=True)
    towers_json.write_text(
        json.dumps(towers_envelope, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    heroes_json.write_text(
        json.dumps(heroes_envelope, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {towers_json} ({len(converted_towers)} towers) and "
        f"{heroes_json} ({len(converted_heroes)} heroes) "
        f"at game_version={resolved_game_version}.",
    )
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert data/btd6/*.csv scaffolds into runtime JSON.",
    )
    parser.add_argument(
        "--towers-csv",
        type=Path,
        default=_DEFAULT_TOWERS_CSV,
    )
    parser.add_argument(
        "--heroes-csv",
        type=Path,
        default=_DEFAULT_HEROES_CSV,
    )
    parser.add_argument(
        "--towers-json",
        type=Path,
        default=_DEFAULT_TOWERS_JSON,
    )
    parser.add_argument(
        "--heroes-json",
        type=Path,
        default=_DEFAULT_HEROES_JSON,
    )
    parser.add_argument(
        "--game-version",
        type=str,
        default=None,
        help="Game version stamp for the JSON envelopes.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate without writing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return convert(
        towers_csv=args.towers_csv,
        heroes_csv=args.heroes_csv,
        towers_json=args.towers_json,
        heroes_json=args.heroes_json,
        game_version=args.game_version,
        check_only=args.check,
    )


if __name__ == "__main__":
    sys.exit(main())
