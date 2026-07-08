"""Gate 5: `golden-parity` (design-spec SS6 gate 5) -- the acceptance oracle, required
from day one; pending = reported-not-failing; green is a one-way door; A-16
check_parity_depth runs INSIDE this gate (no 7th gate).

Day-0 posture: STRUCTURALLY ARMED, red-until-parity by design.
  * parity/parity.yml is born with every subsystem (the 43 frozen keys + the A-16(3)
    kernel_governance row) `pending` and the A-16 depth section present in its schema.
  * REAL from day 0: schema validation of parity.yml; the FROZEN KEY SET (the 43 subsystem
    keys + kernel_governance, hardcoded below -- a row cannot be deleted, renamed, or the
    whole map emptied to disarm the gate; deletions are additionally diffed against the PR
    base); the ONE-WAY DOOR (ported -> pending rejected against the PR base); the A-16
    depth floor at every pending -> ported flip (100% declared-surface-or-exempt, with the
    `declared` denominators RECOMPUTED from manifest.snapshot.json -- never trusted from
    parity.yml alone) and the post-flip count ratchet. A PR trying to flip a subsystem
    today FAILS (no manifest denominators exist yet, so the flip is ungradeable) --
    exactly right.
  * Reported-not-failing: pending subsystems print as the port-progress dashboard.
  * Golden replay arms when parity/run.py (the in-repo replay runner, plan SS5 step 11)
    lands AND any subsystem is `ported`: the oracle repo is fetched READ-ONLY at the SHA
    pinned in parity/goldens-source.lock (goldens live in menno420/superbot until step 11
    and are NEVER copied into this repo); `python -m parity.run check` must be green for
    every ported subsystem against the CI Postgres service container (provisioned from
    day 0 so step 11 cannot discover a missing container -- linchpin spike item 4).
Arming triggers: flips in parity.yml (depth floor); parity/run.py + first `ported`
(replay); manifest.snapshot.json (real denominators).

Contract imposed on the S3 compiler (recorded so S3 builds to it, DECISIONS.md D-16):
manifest.snapshot.json carries `declared_surfaces` -- {subsystem_key: {"events": [names],
"tables": [names], "settings": [names]}} -- the exact A-16 denominators. `declared` counts
in parity.yml are validated against the lengths of these lists whenever the snapshot
exists; a hand-written declared count that disagrees is red.

FROZEN_KEYS maintenance note: the set below was extracted from
disbot/utils/subsystem_registry.py at the goldens-source.lock SHA (DECISIONS.md R-8).
Once S4 lands sb/namespace/legacy_reservations.json, this gate additionally cross-checks
FROZEN_KEYS against the reservations' `subsystem_key` kind (one source of truth; update
both together with gate 6's 43-key assertion).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

from _gatelib import Gate, load_json, load_yaml, p, run, show_at_base

g = Gate("golden-parity")

PARITY = "parity/parity.yml"
LOCK = "parity/goldens-source.lock"
RUNNER = "parity/run.py"
SNAPSHOT = "manifest.snapshot.json"
REASON_CLASSES = (
    "requires-live-discord",
    "nondeterministic-external",
    "deprecated-surface",
    "owner-exempt",
)
KINDS = ("events", "tables", "settings")
SURFACE_PREFIXES = ("event:", "table:", "setting:")

# The frozen expected key set: the 43 subsystem keys + the A-16(3) kernel_governance row.
# Hardcoded HERE (in the runner, not a deletable side file) so that emptying `subsystems:`
# or deleting rows from parity.yml can never disarm the gate (DECISIONS.md D-20).
FROZEN_KEYS = frozenset(
    {
        "admin",
        "server_management",
        "moderation",
        "economy",
        "inventory",
        "treasury",
        "ticket",
        "mining",
        "fishing",
        "creature",
        "farm",
        "xp",
        "karma",
        "role",
        "channel",
        "cleanup",
        "automod",
        "image_moderation",
        "games",
        "community",
        "community_spotlight",
        "welcome",
        "counters",
        "security",
        "blackjack",
        "casino",
        "btd6",
        "project_moon",
        "deathmatch",
        "rps_tournament",
        "counting",
        "chain",
        "leaderboard",
        "proof_channel",
        "utility",
        "general",
        "four_twenty",
        "help",
        "diagnostic",
        "ux_lab",
        "ai",
        "settings",
        "logging",
        "kernel_governance",
    }
)


def all_rows(doc: dict) -> dict:
    rows = dict(doc.get("subsystems", {}))
    if "kernel_governance" in doc:
        rows["kernel_governance"] = doc["kernel_governance"]
    return rows


def check_key_set(head_rows: dict, base_rows: dict) -> None:
    """B-2: the gate cannot be disarmed by deleting rows (or the whole map)."""
    head_keys = set(head_rows)
    missing = sorted(FROZEN_KEYS - head_keys)
    extra = sorted(head_keys - FROZEN_KEYS)
    if missing or extra:
        g.fail(
            "parity.yml key set must equal the frozen expected set "
            f"(43 subsystem keys + kernel_governance); missing={missing} extra={extra} "
            "-- deleting/renaming a row does not disarm the gate"
        )
    deleted = sorted(set(base_rows) - head_keys)
    if deleted:
        g.fail(f"subsystem rows deleted relative to the PR base: {deleted}")


def validate_schema(rows: dict) -> None:
    for k, row in rows.items():
        if row.get("status") not in ("pending", "ported"):
            g.fail(f"{k}: status must be pending|ported")
        d = row.get("depth")
        if not d or not all(sec in d for sec in ("declared", "covered", "exempt")):
            g.fail(
                f"{k}: A-16 depth section missing/incomplete (born-with-depth is binding)"
            )
        seen_surfaces: set[str] = set()
        for ex in d["exempt"]:
            surface = str(ex.get("surface", "")).strip()
            if not surface or not surface.startswith(SURFACE_PREFIXES):
                g.fail(
                    f"{k}: exempt row needs a non-empty kind-prefixed surface "
                    f"({'|'.join(SURFACE_PREFIXES)}<id>): {ex}"
                )
            if surface in seen_surfaces:
                g.fail(
                    f"{k}: duplicate exempt row for {surface} -- duplicates must not pad "
                    "covered + exempt == declared"
                )
            seen_surfaces.add(surface)
            reason = str(ex.get("reason", "")).strip()
            if not any(reason.startswith(c) for c in REASON_CLASSES):
                g.fail(
                    f"{k}: exempt reason must cite a reason class {REASON_CLASSES}, "
                    f"never a bare excuse: {ex}"
                )


def exempt_count(row: dict, kind: str) -> int:
    prefix = {"events": "event:", "tables": "table:", "settings": "setting:"}[kind]
    return sum(
        1
        for surface in {str(ex.get("surface", "")) for ex in row["depth"]["exempt"]}
        if surface.startswith(prefix)
    )


def manifest_declared() -> dict | None:
    """A-16 denominators recomputed from manifest.snapshot.json (None pre-manifest)."""
    if not p(SNAPSHOT).exists():
        return None
    surfaces = load_json(p(SNAPSHOT)).get("declared_surfaces", {})
    return {
        k: {kind: len(v.get(kind, [])) for kind in KINDS} for k, v in surfaces.items()
    }


def check_depth(head_rows: dict, base: dict | None) -> None:
    """A-16: floor at the flip + count-ratchet after it, against MANIFEST denominators."""
    base_rows = all_rows(base) if base else {}
    check_key_set(head_rows, base_rows)
    denominators = manifest_declared()
    for k, row in head_rows.items():
        prev = base_rows.get(k)
        prev_status = prev["status"] if prev else "pending"
        if prev_status == "ported" and row["status"] == "pending":
            g.fail(f"{k}: ported -> pending is rejected -- green is a one-way door")
        d = row["depth"]
        if denominators is not None:
            # M-1: declared is never self-graded -- any non-null declared count must
            # equal the manifest-recomputed denominator, exactly (A-16: "against
            # manifest denominators (exact)").
            for kind in KINDS:
                claimed = d["declared"][kind]
                if claimed is None:
                    continue
                actual = denominators.get(k, {}).get(kind)
                if actual is None:
                    g.fail(
                        f"{k}: declared.{kind}={claimed} but the manifest snapshot "
                        "declares no surfaces for this subsystem -- declared counts "
                        "come from the manifest, never by hand"
                    )
                if claimed != actual:
                    g.fail(
                        f"{k}: A-16 declared.{kind}={claimed} != manifest-recomputed "
                        f"{actual} -- the manifest is the denominator-setter"
                    )
        if row["status"] == "ported":
            if denominators is None:
                g.fail(
                    f"{k}: ported before manifest.snapshot.json exists -- no manifest "
                    "denominator, so the flip is ungradeable by definition (A-16)"
                )
            for kind in KINDS:
                declared = d["declared"][kind]
                if declared is None:
                    g.fail(
                        f"{k}: ported with null declared.{kind} -- the manifest is the "
                        "denominator-setter; flip only after its manifest compiles"
                    )
                covered = d["covered"][kind]
                if covered + exempt_count(row, kind) != declared:
                    g.fail(
                        f"{k}: A-16 floor: covered({covered}) + exempt != declared({declared}) "
                        f"for {kind} (100%-or-exempt at and after the flip)"
                    )
                if prev and prev["status"] == "ported":
                    if covered < prev["depth"]["covered"][kind]:
                        g.fail(f"{k}: A-16 ratchet: covered.{kind} decreased")


def fetch_oracle(lock: dict) -> str:
    dest = tempfile.mkdtemp(prefix="oracle-")
    url = f"https://github.com/{lock['repo']}.git"
    for cmd in (
        ["git", "init", "-q", dest],
        ["git", "-C", dest, "fetch", "-q", "--depth", "1", url, lock["ref"]],
        ["git", "-C", dest, "checkout", "-q", "FETCH_HEAD"],
    ):
        if subprocess.run(cmd).returncode != 0:
            g.fail(
                f"oracle fetch failed at: {' '.join(cmd)} (see goldens-source.lock.fetch)"
            )
    return dest


def main() -> None:
    if not p(PARITY).exists() or not p(LOCK).exists():
        g.fail(
            "parity/parity.yml or parity/goldens-source.lock missing -- born-with files"
        )
    lock = load_json(p(LOCK))
    if len(lock["ref"]) != 40:
        g.fail("goldens-source.lock ref must be a full 40-char pinned SHA")

    head_rows = all_rows(load_yaml(p(PARITY)))
    validate_schema(head_rows)
    base_text = show_at_base(PARITY)
    check_depth(head_rows, load_yaml(base_text) if base_text else None)

    ported = sorted(k for k, r in head_rows.items() if r["status"] == "ported")
    pending = sorted(k for k, r in head_rows.items() if r["status"] == "pending")
    g.note(f"dashboard: {len(ported)} ported / {len(pending)} pending")
    for k in pending:
        g.note(f"  pending (reported, not failing): {k}")

    if not ported:
        g.ok(
            "no ported subsystems yet -- schema + key-set + one-way door + depth checks "
            "green; golden replay arms at the first pending -> ported flip "
            "(needs parity/run.py)"
        )
    if not p(RUNNER).exists():
        g.fail(
            f"{len(ported)} subsystem(s) ported but parity/run.py (replay runner, step 11) "
            "is missing -- a flip without the harness is red"
        )
    oracle = fetch_oracle(lock)
    env = dict(os.environ, ORACLE_GOLDENS=oracle)
    only = [a for k in ported for a in ("--only", k)]
    if (
        run([sys.executable, "-m", "parity.run", "check", *only], env=env).returncode
        != 0
    ):
        g.fail(
            "golden replay red for a ported subsystem -- any regression is a hard failure"
        )
    g.ok(
        f"golden replay green for all {len(ported)} ported subsystem(s); "
        f"{len(pending)} pending reported"
    )


if __name__ == "__main__":
    main()
