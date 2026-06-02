#!/usr/bin/env python3
"""Seed the BTD6 deterministic data tree into Postgres (``btd6_data_blobs``).

One-shot operator tool for the Postgres data backend. Walks
``disbot/data/btd6/`` (the fixtures + the per-entity ``stats/`` subtree) and
upserts each ``*.json`` file as a row keyed by repo-relative path. Run it
against your deployment database, then set ``BTD6_DATA_BACKEND=postgres`` (see
``docs/btd6-data-backends.md``).

Usage::

    # Inspect what would be seeded (no DB connection):
    python3.10 scripts/seed_btd6_data.py --dry-run

    # Seed into the configured database (uses the bot's DSN env vars):
    python3.10 scripts/seed_btd6_data.py

Writes go through ``utils.db.btd6_data`` (the sanctioned DB layer), the same
path the bot reads from.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / "disbot" / "data" / "btd6"
MANIFEST_NAME = "manifest.json"

# Make ``from utils import db`` resolve the same way the bot does.
if str(REPO_ROOT / "disbot") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "disbot"))


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_rows(root: Path) -> list[tuple[str, Any, str]]:
    """Return ``(name, body, sha256)`` for every ``*.json`` under ``root``.

    ``manifest.json`` is excluded. ``body`` is the parsed JSON object; the
    sha256 is over the original file bytes (provenance).
    """
    rows: list[tuple[str, Any, str]] = []
    for path in sorted(root.rglob("*.json")):
        rel = path.relative_to(root).as_posix()
        if rel == MANIFEST_NAME:
            continue
        raw = path.read_bytes()
        rows.append((rel, json.loads(raw), _sha256(raw)))
    return rows


def _print_summary(rows: list[tuple[str, Any, str]], root: Path) -> None:
    print(f"BTD6 data root: {root}")
    print(f"Files: {len(rows)}")
    for name, _body, sha in rows[:10]:
        print(f"  {name:40s} {sha[:12]}")
    if len(rows) > 10:
        print(f"  … and {len(rows) - 10} more")


async def seed(root: Path) -> int:
    # The DB write path lives in one place (btd6_data_service), shared with the
    # in-app !btd6ops seed-data command.
    from services import btd6_data_service
    from utils import db
    from utils.db import pool

    await db.init()
    try:
        return await btd6_data_service.seed_postgres_from_files(root)
    finally:
        await pool.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build + print the row summary; no DB connection, no write.",
    )
    args = parser.parse_args(argv)

    root: Path = args.root
    if not root.is_dir():
        print(f"data root not found: {root}", file=sys.stderr)
        return 2

    rows = build_rows(root)
    _print_summary(rows, root)
    if args.dry_run:
        return 0

    count = asyncio.run(seed(root))
    print(f"seeded {count} blobs into btd6_data_blobs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
