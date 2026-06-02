#!/usr/bin/env python3
"""Upload the BTD6 deterministic data tree to a public-read object store.

One-shot operator tool for the BTD6 cloud-storage migration. It walks
``disbot/data/btd6/`` (the fixtures + the ``stats/`` subtree), writes an
integrity ``manifest.json`` (sha256 + size per file), and uploads every file
(plus the manifest) to an S3-compatible bucket (Cloudflare R2 / AWS S3 / GCS).

The bot then reads the fixtures from ``{BTD6_DATA_BASE_URL}/<path>`` at startup
(see ``docs/btd6-cloud-data.md``). For a public-read bucket no secret is needed
at *runtime*; this *upload* uses your S3 credentials locally only.

Usage::

    # Inspect what would be uploaded (no network, no boto3 needed):
    python3.10 scripts/upload_btd6_data.py --check

    # Write manifest.json next to the fixtures (no upload):
    python3.10 scripts/upload_btd6_data.py --write-manifest

    # Upload to the bucket (needs boto3 + S3 creds in the environment):
    AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... \
    python3.10 scripts/upload_btd6_data.py \
        --bucket my-btd6-bucket \
        --endpoint-url https://<accountid>.r2.cloudflarestorage.com \
        --prefix btd6

Credentials are read from the standard AWS env vars / shared config by boto3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / "disbot" / "data" / "btd6"
MANIFEST_NAME = "manifest.json"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_manifest(root: Path) -> dict:
    """Build the integrity manifest for every ``*.json`` under ``root``.

    Returns ``{"files": {relpath: {"sha256", "size"}}, "count", "generated_at"}``.
    ``manifest.json`` itself is excluded.
    """
    files: dict[str, dict] = {}
    for path in sorted(root.rglob("*.json")):
        rel = path.relative_to(root).as_posix()
        if rel == MANIFEST_NAME:
            continue
        data = path.read_bytes()
        files[rel] = {"sha256": _sha256(data), "size": len(data)}
    return {
        "files": files,
        "count": len(files),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def write_manifest(root: Path, manifest: dict) -> Path:
    target = root / MANIFEST_NAME
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return target


def upload(
    root: Path,
    manifest: dict,
    *,
    bucket: str,
    endpoint_url: str | None,
    prefix: str,
) -> int:
    """Upload every manifest file + the manifest to the bucket. Returns count."""
    try:
        import boto3  # noqa: PLC0415 - optional ops dependency, imported lazily
    except ImportError:  # pragma: no cover - depends on the operator's env
        print(
            "boto3 is required to upload (pip install boto3). "
            "Use --check / --write-manifest for offline runs.",
            file=sys.stderr,
        )
        raise SystemExit(2) from None

    client = boto3.client("s3", endpoint_url=endpoint_url)
    key_prefix = prefix.strip("/")

    def _key(rel: str) -> str:
        return f"{key_prefix}/{rel}" if key_prefix else rel

    uploaded = 0
    for rel in manifest["files"]:
        client.put_object(
            Bucket=bucket,
            Key=_key(rel),
            Body=(root / rel).read_bytes(),
            ContentType="application/json",
        )
        uploaded += 1
    client.put_object(
        Bucket=bucket,
        Key=_key(MANIFEST_NAME),
        Body=json.dumps(manifest, indent=2).encode("utf-8"),
        ContentType="application/json",
    )
    return uploaded


def _print_summary(manifest: dict, root: Path) -> None:
    total = sum(f["size"] for f in manifest["files"].values())
    print(f"BTD6 data root: {root}")
    print(f"Files: {manifest['count']}  Total: {total / 1024:.1f} KiB")
    for rel, meta in list(manifest["files"].items())[:10]:
        print(f"  {rel:40s} {meta['sha256'][:12]}  {meta['size']:>8} B")
    if manifest["count"] > 10:
        print(f"  … and {manifest['count'] - 10} more")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Build + print the manifest summary; no write, no upload.",
    )
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help="Write manifest.json next to the fixtures; no upload.",
    )
    parser.add_argument("--bucket", default="")
    parser.add_argument("--endpoint-url", default=None)
    parser.add_argument("--prefix", default="btd6")
    args = parser.parse_args(argv)

    root: Path = args.root
    if not root.is_dir():
        print(f"data root not found: {root}", file=sys.stderr)
        return 2

    manifest = build_manifest(root)
    _print_summary(manifest, root)

    if args.check:
        return 0
    if args.write_manifest:
        target = write_manifest(root, manifest)
        print(f"wrote {target}")
        return 0
    if not args.bucket:
        print(
            "no --bucket given; nothing uploaded. Use --check / --write-manifest "
            "for offline runs, or pass --bucket to upload.",
            file=sys.stderr,
        )
        return 2

    count = upload(
        root,
        manifest,
        bucket=args.bucket,
        endpoint_url=args.endpoint_url,
        prefix=args.prefix,
    )
    print(f"uploaded {count} files + manifest to s3://{args.bucket}/{args.prefix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
