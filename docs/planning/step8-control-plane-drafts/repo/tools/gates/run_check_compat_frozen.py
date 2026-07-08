"""Gate 6: `check_compat_frozen` (design-spec SS6 gate 6) -- diffs the pinned compat
artifacts (legacy custom_id list, subsystem keys, event literals, AITask names, audit
payload field sets) against the manifest export; any drift from the SS5.3 contract is red
until docs/compat-contract.md is explicitly amended with owner sign-off.

Day-0 posture: SELF-ARMING with a staged partial-state rule matched to the build order.
  * Pre-kernel (neither sb/namespace/legacy_reservations.json nor manifest.snapshot.json):
    positive assertion -- the goldens-source lock exists, parses, pins a full SHA, and the
    compat-contract doc exists with an empty amendment ledger. PASS.
  * Reservations WITHOUT snapshot (S4 lands before manifests compile): validates the
    reservations file internally -- extracted_from must equal the lock ref (one oracle
    snapshot for goldens AND compat pins), the 5 artifact kinds present, the 43 subsystem
    keys among them. PASS with "diff arms when the manifest export exists".
  * Snapshot WITHOUT reservations: FAIL -- a manifest export with nothing pinned against
    it is the dangerous state and never reads green.
  * Both present (armed): every compat=True reservation must appear VERBATIM in the
    snapshot's compat_export, per kind; audit payload field sets must be supersets.
    Drift is red unless the compat doc's amendment ledger names every drifted id with the
    sign-off token.
Arming triggers: legacy_reservations.json (internal tier), + manifest.snapshot.json (diff).

Contract imposed on S4 (recorded so S4 builds to it): legacy_reservations.json shape --
{"extracted_from": <sha>, "kinds": {"subsystem_key"|"custom_id"|"event"|"ai_task"|
"audit_payload": {name: {"compat": bool, ...}}}} where audit_payload values also carry
"fields": [...]. The compiler's snapshot carries `compat_export` with the same kind keys
(audit_payload values = field lists).
"""

from __future__ import annotations

import re

from _gatelib import Gate, load_json, p

g = Gate("check_compat_frozen")

RESERVATIONS = "sb/namespace/legacy_reservations.json"
SNAPSHOT = "manifest.snapshot.json"
LOCK = "parity/goldens-source.lock"
CONTRACT_DOC = "docs/compat-contract.md"
KINDS = ("subsystem_key", "custom_id", "event", "ai_task", "audit_payload")


def amended_ids() -> set[str]:
    """Identifiers named in the compat-contract amendment ledger rows that carry sign-off."""
    ids: set[str] = set()
    for line in p(CONTRACT_DOC).read_text().splitlines():
        if line.startswith("|") and "Signed-off: menno420" in line:
            cells = [c.strip() for c in line.split("|")]
            if len(cells) >= 4:
                ids.update(x.strip() for x in cells[3].split(",") if x.strip())
    return ids


def validate_reservations(res: dict, lock: dict) -> None:
    if res.get("extracted_from") != lock["ref"]:
        g.fail(
            f"reservations extracted_from != goldens-source.lock ref ({lock['ref']}) -- "
            "compat pins and goldens must describe the same oracle snapshot"
        )
    missing = [k for k in KINDS if k not in res.get("kinds", {})]
    if missing:
        g.fail(f"reservations missing artifact kinds: {missing}")
    n_sub = len(res["kinds"]["subsystem_key"])
    if n_sub != 43:
        g.fail(f"expected the 43 frozen subsystem keys, found {n_sub} (SS5.3 item 1)")


def main() -> None:
    if not p(LOCK).exists() or not p(CONTRACT_DOC).exists():
        g.fail(
            "goldens-source.lock or docs/compat-contract.md missing -- born-with files"
        )
    lock = load_json(p(LOCK))
    if not re.fullmatch(r"[0-9a-f]{40}", lock["ref"]):
        g.fail("lock ref is not a full 40-hex SHA")

    have_res, have_snap = p(RESERVATIONS).exists(), p(SNAPSHOT).exists()
    if not have_res and not have_snap:
        g.ok(
            "pre-kernel: no reservations, no manifest export; lock pinned at "
            f"{lock['ref'][:12]} and contract doc present. Diff arms at S4 + first compile."
        )
    if have_snap and not have_res:
        g.fail(
            "manifest export exists with no pinned reservations -- never green unpinned"
        )

    res = load_json(p(RESERVATIONS))
    validate_reservations(res, lock)
    if not have_snap:
        g.ok(
            "reservations internally valid (pin matches lock; 5 kinds; 43 subsystem keys). "
            "Verbatim diff arms when manifest.snapshot.json first compiles."
        )

    export = load_json(p(SNAPSHOT)).get("compat_export")
    if export is None:
        g.fail("snapshot carries no compat_export -- compiler contract broken")
    pardons = amended_ids()
    drift: list[str] = []
    for kind in KINDS:
        for name, meta in res["kinds"][kind].items():
            if not meta.get("compat", True):
                continue
            tag = f"{kind}:{name}"
            if kind == "audit_payload":
                exported = set(export.get(kind, {}).get(name, []))
                if not set(meta["fields"]) <= exported:
                    drift.append(
                        f"{tag} (payload no longer a superset of the frozen fields)"
                    )
            elif name not in export.get(kind, {}):
                drift.append(f"{tag} (frozen name absent from the manifest export)")
    hard = [d for d in drift if d.split(" ")[0] not in pardons]
    if hard:
        g.fail(
            "compat drift without a signed compat-contract amendment naming it:\n  "
            + "\n  ".join(hard)
        )
    if drift:
        g.note(f"{len(drift)} drift(s) pardoned by signed amendments")
    g.ok("manifest export honors every frozen compat artifact (SS5.3)")


if __name__ == "__main__":
    main()
