"""Gate 4: `sim-gate` (design-spec SS6 gate 4 / SS2.10.6) -- sim-reviewed-or-exempt.

Semantics (SS2.10.6, binding): diff the [A]-tagged arrangement fields against the merge
base; any change without a matching new sim record or an explicit Exempt(reason) is red.
Provenance lives in the manifest/layout/<subsystem>.lock.json overlays (SS2.10.3) --
each [A]-field-group entry stamps SimRef(record_id, input_hash) or Exempt(reason).

Day-0 posture: SELF-ARMING BY DIFF -- the diff semantics are correct at every stage:
  * No snapshot on either side (pre-S3): the arrangement surface is empty on both sides
    of every diff -> nothing changed -> PASS. Not a stub: the same comparison that will
    catch a real [A] drift is executing against two empty sets.
  * Snapshot exists (S3+) but tools/check_sim_gate.py (an S11/step-11 deliverable) does
    not yet: an INLINE conservative check runs -- every changed/added [A] group key must
    carry overlay provenance (SimRef or Exempt). Unchanged arrangement passes, so S3-S10
    PRs are never bricked, while an [A] change without provenance is red from the very
    first snapshot commit.
  * tools/check_sim_gate.py present: it is authoritative and this runner delegates
    (build it to the design-spec SS5 ~L992/L1029 contract -- canonical plan SS5 step 11).
Arming trigger: the first committed manifest.snapshot.json (inline tier), then the
first tools/check_sim_gate.py (authoritative tier).

Snapshot contract imposed on S3 (recorded so S3 builds to it): the snapshot carries an
`arrangement` mapping -- {"<namespace-id>": <[A]-field-group value>} grouped per SS2.10.1.
"""

from __future__ import annotations

import json
import sys

from _gatelib import Gate, load_json, p, run, show_at_base

g = Gate("sim-gate")

SNAPSHOT = "manifest.snapshot.json"
CHECKER = "tools/check_sim_gate.py"
OVERLAY_DIR = "sb/manifest/layout"


def arrangement(doc: dict | None) -> dict:
    return (doc or {}).get("arrangement", {})


def overlay_provenance() -> dict:
    """Union of all layout overlays: {[A]-group key: SimRef|Exempt entry}."""
    prov: dict = {}
    d = p(OVERLAY_DIR)
    if d.is_dir():
        for f in sorted(d.glob("*.lock.json")):
            prov.update(load_json(f).get("provenance", {}))
    return prov


def main() -> None:
    head_doc = load_json(p(SNAPSHOT)) if p(SNAPSHOT).exists() else None
    base_text = show_at_base(SNAPSHOT)
    base_doc = json.loads(base_text) if base_text else None

    # M-4: once the authoritative checker exists it can never silently vanish -- deleting
    # it must not downgrade this gate to the weaker inline tier (same rule the
    # architecture gate applies to tools/check_architecture.py). Checked FIRST, in every
    # state, so no early-ok path bypasses it.
    if show_at_base(CHECKER) is not None and not p(CHECKER).exists():
        g.fail(
            "tools/check_sim_gate.py existed at the PR base but is deleted at HEAD -- "
            "removing the authoritative checker does not disarm the sim gate"
        )

    if head_doc is None and base_doc is None:
        g.ok(
            "arrangement surface empty on both diff sides (pre-manifest). The identical "
            "diff logic arms the moment manifest.snapshot.json is first committed."
        )
    if head_doc is None and base_doc is not None:
        g.fail(
            "manifest.snapshot.json deleted relative to base -- the arrangement surface "
            "cannot silently vanish"
        )

    if p(CHECKER).exists():
        g.note("delegating to authoritative tools/check_sim_gate.py (S11)")
        if run([sys.executable, CHECKER]).returncode != 0:
            g.fail("check_sim_gate red: [A]-field change without sim record or Exempt")
        g.ok("check_sim_gate green")

    head_a, base_a = arrangement(head_doc), arrangement(base_doc)
    changed = sorted(
        k for k in set(head_a) | set(base_a) if head_a.get(k) != base_a.get(k)
    )
    if not changed:
        g.ok(
            "no [A]-field drift against base (inline tier; authoritative checker lands S11)"
        )
    prov = overlay_provenance()
    naked = [k for k in changed if k not in prov]
    if naked:
        g.fail(
            "[A]-field changes without overlay provenance (SimRef or Exempt, SS2.10.3): "
            + ", ".join(naked)
        )
    g.ok(
        f"{len(changed)} [A]-field change(s), all carrying overlay provenance (inline tier)"
    )


if __name__ == "__main__":
    main()
