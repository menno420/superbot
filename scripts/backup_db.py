#!/usr/bin/env python3.10
"""
Manual Postgres backup — creates a timestamped .sql.gz in --output-dir.

Wraps pg_dump so the flags stay consistent with the GitHub Actions backup
workflow.  Requires pg_dump on PATH (install: `brew install libpq` on macOS,
`apt-get install postgresql-client` on Debian/Ubuntu).

Usage:
    DATABASE_URL=postgres://... python3.10 scripts/backup_db.py
    DATABASE_URL=postgres://... python3.10 scripts/backup_db.py --output-dir /tmp

Restore:
    gunzip -c superbot-backup-<timestamp>.sql.gz | psql <DATABASE_URL>
"""

import argparse
import gzip
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write the backup file (default: cwd)",
    )
    args = parser.parse_args()

    # Check pg_dump is available.
    if not shutil.which("pg_dump"):
        sys.exit(
            "pg_dump not found on PATH.\n"
            "  macOS:  brew install libpq && brew link --force libpq\n"
            "  Ubuntu: sudo apt-get install postgresql-client",
        )

    # Use DATABASE_PUBLIC_URL first (Railway external proxy, needed outside Railway),
    # fall back to DATABASE_URL (Railway internal, works inside Railway/local Postgres).
    db_url = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit(
            "Set DATABASE_PUBLIC_URL (Railway external) or DATABASE_URL in the environment.",
        )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"superbot-backup-{timestamp}.sql.gz"

    print(f"Dumping database → {output_path} …")

    dump_proc = subprocess.run(
        ["pg_dump", "--no-owner", "--no-acl", db_url],
        capture_output=True,
    )
    if dump_proc.returncode != 0:
        sys.stderr.buffer.write(dump_proc.stderr)
        sys.exit(f"pg_dump failed (exit {dump_proc.returncode})")

    with gzip.open(output_path, "wb") as fh:
        fh.write(dump_proc.stdout)

    size_kb = output_path.stat().st_size // 1024
    print(f"Done. {output_path} ({size_kb} KB compressed)")
    print()
    print("Restore:")
    print(f"  gunzip -c {output_path.name} | psql <DATABASE_URL>")


if __name__ == "__main__":
    main()
