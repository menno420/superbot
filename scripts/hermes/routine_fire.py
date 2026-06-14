#!/usr/bin/env python3
"""Fire a Claude Code routine work order — a robust replacement for the inline curl.

Why this exists (owner-directed 2026-06-14): the ``superbot-dispatch`` skill built the
``/fire`` request inline as ``curl ... -d "$(python3 -c '...json.dumps...' "$WORK_ORDER")"``,
which is shell-quoting-fragile for multi-line work orders containing quotes/newlines
(Hermes hit the failure live). This helper takes the work order on **stdin** — so the
shell never parses it — loads the ``CLAUDE_ROUTINE_*`` config from the environment or
``~/.hermes/routine.env``, POSTs ``{"text": <work order>}``, and prints the response (the
``claude_code_session_url``). It never prints the token.

Usage:
    printf '%s' "$WORK_ORDER" | python3 scripts/hermes/routine_fire.py
    python3 scripts/hermes/routine_fire.py --file work_order.txt
    python3 scripts/hermes/routine_fire.py --dry-run < work_order.txt   # preview, don't fire

Pure stdlib (urllib) so it runs on the Hermes VPS with no extra install.

Provenance + reliability (Q-0105): added 2026-06-14, owner-directed; the dispatch bug was
diagnosed live by Hermes. UNVERIFIED until a real fire succeeds end-to-end — confirm the
first dispatch returns a session URL before trusting it. Delete/revise if it misfires.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

_REQUIRED = ("CLAUDE_ROUTINE_FIRE_URL", "CLAUDE_ROUTINE_TOKEN")
_OPTIONAL = ("CLAUDE_ROUTINE_BETA", "CLAUDE_ROUTINE_VERSION")
_ENV_FILE = Path.home() / ".hermes" / "routine.env"


def _parse_env_file(path: Path) -> dict[str, str]:
    """Parse a ``KEY=value`` env file (mirrors how the dispatch skill sources it)."""
    out: dict[str, str] = {}
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def load_config(
    environ: dict[str, str] | None = None,
    env_file: Path | None = None,
) -> dict[str, str]:
    """Resolve ``CLAUDE_ROUTINE_*`` from the environment, falling back to the env file."""
    environ = os.environ if environ is None else environ
    env_file = _ENV_FILE if env_file is None else env_file
    cfg = {k: environ[k] for k in (*_REQUIRED, *_OPTIONAL) if environ.get(k)}
    if [k for k in _REQUIRED if k not in cfg]:
        file_cfg = _parse_env_file(env_file)
        for k in (*_REQUIRED, *_OPTIONAL):
            if k not in cfg and file_cfg.get(k):
                cfg[k] = file_cfg[k]
    return cfg


def build_request(cfg: dict[str, str], work_order: str) -> urllib.request.Request:
    """Build the POST request for the ``/fire`` endpoint (no network I/O)."""
    headers = {
        "Authorization": f"Bearer {cfg['CLAUDE_ROUTINE_TOKEN']}",
        "Content-Type": "application/json",
    }
    if cfg.get("CLAUDE_ROUTINE_BETA"):
        headers["anthropic-beta"] = cfg["CLAUDE_ROUTINE_BETA"]
    if cfg.get("CLAUDE_ROUTINE_VERSION"):
        headers["anthropic-version"] = cfg["CLAUDE_ROUTINE_VERSION"]
    data = json.dumps({"text": work_order}).encode("utf-8")
    return urllib.request.Request(
        cfg["CLAUDE_ROUTINE_FIRE_URL"],
        data=data,
        headers=headers,
        method="POST",
    )


def redacted_headers(headers: dict[str, str]) -> dict[str, str]:
    """Headers with the bearer token masked — safe to print."""
    return {
        k: ("Bearer ***redacted***" if k.lower() == "authorization" else v)
        for k, v in headers.items()
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fire a Claude Code routine work order.",
    )
    parser.add_argument(
        "--file",
        help="read the work order from this file (default: stdin)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the request (token redacted) and exit without firing",
    )
    args = parser.parse_args(argv)

    raw = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
    work_order = raw.strip()
    if not work_order:
        print(
            "routine_fire: empty work order (nothing on stdin / --file).",
            file=sys.stderr,
        )
        return 2

    cfg = load_config()
    missing = [k for k in _REQUIRED if k not in cfg]
    if missing:
        print(
            f"routine_fire: missing config {missing} (set them in the env or {_ENV_FILE}).",
            file=sys.stderr,
        )
        return 1

    req = build_request(cfg, work_order)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "method": req.method,
                    "url": req.full_url,
                    "headers": redacted_headers(dict(req.headers)),
                    "payload": {"text": work_order},
                },
                indent=2,
            ),
        )
        return 0

    try:
        with urllib.request.urlopen(
            req,
            timeout=30,
        ) as resp:  # noqa: S310 (trusted URL)
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        print(
            f"routine_fire: HTTP {exc.code} firing routine: {detail}",
            file=sys.stderr,
        )
        return 1
    except urllib.error.URLError as exc:
        print(
            f"routine_fire: network error firing routine: {exc.reason}",
            file=sys.stderr,
        )
        return 1

    try:
        parsed = json.loads(body)
    except ValueError:
        print(body)
        return 0
    session_url = parsed.get("claude_code_session_url") or parsed.get("session_url")
    if session_url:
        print(f"Fired. Watch: {session_url}")
    print(json.dumps(parsed, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
