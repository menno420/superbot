#!/usr/bin/env python3.10
"""fleet_status.py — one-command fleet orientation sweep (read-only).

Fetches every fleet repo's heartbeat (`control/status.md`) plus the
fleet-manager's roster/owner-queue over raw.githubusercontent.com and prints a
compact per-seat table: updated stamp, phase, health, blockers, owner-flag
presence. The point is to replace multi-turn cross-repo discovery with one
command at session start (owner directive Q-0272, 2026-07-12 — the standing
read-only authorization + reading path live in `docs/fleet-reading-path.md`).

Usage:
    python3.10 scripts/fleet_status.py              # active-seat table
    python3.10 scripts/fleet_status.py --all        # + parked/archived repos
    python3.10 scripts/fleet_status.py --repo NAME  # one repo, full file
    python3.10 scripts/fleet_status.py --save DIR   # also write raw files

Provenance / reliability (Q-0105): added 2026-07-12 at the owner's direction
(save-3-turns ask). Unverified: confirm its output against the live repos a few
times across sessions before trusting it. Delete this if it proves unreliable
over multiple sessions. Network-dependent by design; it is an orientation aid,
never a CI gate — it exits 0 even when fetches fail (failures are shown in the
table, not raised).
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import urllib.error
import urllib.request

RAW = "https://raw.githubusercontent.com/menno420/{repo}/{branch}/{path}"
# Cloudflare 403s urllib's default UA on some hosts (mineverse #45 lesson);
# raw.githubusercontent tolerates it, but send a real one anyway.
UA = "superbot-fleet-status/1 (+https://github.com/menno420/superbot)"
TIMEOUT = 12

# Active seats (repo → one-line role). Heartbeat = control/status.md unless noted.
ACTIVE: dict[str, str] = {
    "fleet-manager": "Project Manager hub — registry, roster, owner-queue, ORDERs",
    "idea-engine": "Ideas Lab (generate) — idea heads, probes, blueprints",
    "sim-lab": "Ideas Lab (verify) — sims, verdicts V###",
    "venture-lab": "Venture Lab — revenue products, publish queue",
    "trading-strategy": "Venture Lab (parked research) — weekly grading",
    "superbot-next": "SuperBot 2.0 — the rebuild (parity program, cutover)",
    "superbot-mineverse": "SuperBot World flagship — mining browser game (+ carries games/idle cross-repo notes)",
    "superbot-games": "SuperBot World — world/fishing engines (status FROZEN — read mineverse's)",
    "superbot-idle": "SuperBot World — idle engine + themes (status FROZEN — read mineverse's)",
    "substrate-kit": "Self Improvement — the portable agent-memory kit",
    "websites": "Websites — control plane, review site, arcade (merge=deploy)",
    "gba-homebrew": "Game Lab — GBA homebrew (GLOAMLINE / Lumen Drift)",
}
# Long tail — only swept with --all.
EXTENDED: dict[str, str] = {
    "product-forge": "on-demand incubator (not a standing seat)",
    "superbot-plugin-hello": "plugin-contract example (near-empty by design)",
    "codetool-lab-fable5": "archived CLI lab",
    "codetool-lab-opus4.8": "archived CLI lab",
    "codetool-lab-sonnet5": "archived CLI lab",
}
PRIVATE = {"pokemon-mod-lab": "PRIVATE/DARK — skip, never guess (raw reads 404)"}

# Extra truth files worth pulling alongside the fleet-manager heartbeat.
MANAGER_EXTRAS = ("docs/roster.md", "docs/owner-queue.md")

HEADER_FIELDS = ("updated", "phase", "health", "kit", "blockers", "orders")


def fetch(repo: str, path: str) -> tuple[str | None, str]:
    """Return (text, note). text=None means the fetch failed; note says why."""
    for branch in ("main", "master"):
        req = urllib.request.Request(
            RAW.format(repo=repo, branch=branch, path=path), headers={"User-Agent": UA}
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read().decode("utf-8", "replace"), branch
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            return None, f"HTTP {e.code}"
        except Exception as e:  # noqa: BLE001 — orientation aid: report, never raise
            return None, f"{type(e).__name__}: {e}"
    return None, "404 on main+master"


def parse_status_header(text: str, max_len: int = 140) -> dict[str, str]:
    """Extract the conventional heartbeat header fields from a status.md body.

    Pure + testable. Reads only the first ~60 lines; a field is a line starting
    with `<name>:` (case-insensitive). Values are single-line-truncated so a
    long phase narrative can't flood the table. Also flags owner-asks: any line
    containing `⚑` sets `owner_flag`.
    """
    out: dict[str, str] = {}
    for line in text.splitlines()[:60]:
        stripped = line.strip().lstrip("#").strip()
        low = stripped.lower()
        for field in HEADER_FIELDS:
            if field not in out and low.startswith(f"{field}:"):
                val = stripped.split(":", 1)[1].strip()
                out[field] = (val[: max_len - 1] + "…") if len(val) > max_len else val
        if "⚑" in line:
            out.setdefault("owner_flag", "⚑")
    return out


def sweep(repos: dict[str, str], save: pathlib.Path | None) -> None:
    for repo, role in repos.items():
        text, note = fetch(repo, "control/status.md")
        print(f"\n── {repo} — {role}")
        if text is None:
            print(f"   [no heartbeat: {note}]")
            continue
        fields = parse_status_header(text)
        for key in ("updated", "phase", "health", "blockers"):
            if key in fields:
                print(f"   {key:9} {fields[key]}")
        if "owner_flag" in fields:
            print("   ⚑ owner-ask present — read the file for the six-field block")
        if save:
            (save / f"{repo}__control_status.md").write_text(text)
        if repo == "fleet-manager":
            for extra in MANAGER_EXTRAS:
                etext, enote = fetch(repo, extra)
                mark = "✓" if etext else f"✗ {enote}"
                print(f"   extra     {extra} {mark}")
                if etext and save:
                    (save / f"{repo}__{extra.replace('/', '_')}").write_text(etext)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--all", action="store_true", help="include parked/archived repos")
    ap.add_argument("--repo", help="dump one repo's control/status.md in full")
    ap.add_argument("--save", metavar="DIR", help="also write fetched files to DIR")
    args = ap.parse_args()

    save = None
    if args.save:
        save = pathlib.Path(args.save)
        save.mkdir(parents=True, exist_ok=True)

    if args.repo:
        text, note = fetch(args.repo, "control/status.md")
        if text is None:
            print(f"{args.repo}: no heartbeat ({note})")
            return 0
        print(text)
        if save:
            (save / f"{args.repo}__control_status.md").write_text(text)
        return 0

    print("Fleet status sweep (read-only raw fetches — Q-0272; superbot itself is")
    print("the local hub: read docs/current-state.md, not a heartbeat).")
    repos = dict(ACTIVE)
    if args.all:
        repos.update(EXTENDED)
    sweep(repos, save)
    for repo, why in PRIVATE.items():
        print(f"\n── {repo} — {why}")
    print("\nTruth rule: heartbeats are dated snapshots — verify load-bearing claims")
    print("at HEAD (Q-0120). Full reading path: docs/fleet-reading-path.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
