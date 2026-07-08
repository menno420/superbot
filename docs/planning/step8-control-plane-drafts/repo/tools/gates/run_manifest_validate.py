"""Gate 2: `manifest-validate` (design-spec SS6) -- compile + snapshot drift + namespace
collisions (incl. on the merge-tree result, SS3.2) + the manifest validator family +
payload-superset checks, PLUS the two amendment checkers that live INSIDE this gate:
  * A-2  check_schema_ledger   -- grammar field growth vs gates/schema-growth-ledger.yml
  * A-19 check_escape_hatches  -- tier-3 counts vs gates/escape-hatch-baseline.json (ratchet)

Day-0 posture: SELF-ARMING, positive pre-kernel assertion.
  * Pre-kernel: NONE of {sb/spec/**/*.py, tools/manifest_compile.py, tools/check_namespace.py,
    manifest.snapshot.json} exist, AND the A-2 ledger is empty, AND the A-19 baseline is
    all-zero. Anything partial -> FAIL (grammar without compiler, snapshot without grammar,
    a non-virgin ledger with nothing compiled -- every mixed state is red).
  * Armed (trigger: sb/spec/**/*.py or tools/manifest_compile.py appears -- S3): the full
    chain runs; the compiler must regenerate the committed snapshot byte-identically
    (drift check), namespace validation runs on HEAD and on the `git merge-tree` result
    against the PR base, then the validator family, then A-2, then A-19.

A-19 base-diff semantics (M-2 fix): a baseline RISE relative to the PR base requires a NEW
ledger entry (in the baseline's `ledger` array, absent at base) naming the risen subsystem
with non-empty `why` and `rejected_tier2_alternative` fields -- "any rise fails CI unless
the same PR updates the baseline with a ledger entry (what grew, why, the rejected tier-2
alternative)" (canonical plan A-19). Entry shape:
  {"subsystem": <key or "repo_total">, "grew": "...", "why": "...",
   "rejected_tier2_alternative": "...", "pr": 0, "date": "YYYY-MM-DD"}

A-2 frozen_baseline semantics (M-3 fix): `frozen_baseline` entries are legitimate ONLY in
the S3 freeze PR -- the PR whose base has no manifest snapshot yet. Any NEW frozen_baseline
entry in a PR whose base already had a snapshot is red (growth is measured from the freeze;
the freeze happens once).

Contract this runner imposes on the S3 compiler (recorded so S3 builds to it):
  * `tools/manifest_compile.py` (re)writes `manifest.snapshot.json` and
    `escape_hatch_report.json` deterministically, exit 0 on success.
  * the snapshot carries `schema_field_inventory`: the flat list of grammar declaration
    fields ("Dataclass.field") -- the A-2 denominator.
  * the report carries {"repo_total": int, "per_subsystem": {key: int}} tier-3 counts.
  * `tools/check_namespace.py <snapshot>` validates reservations/collisions, exit != 0 on any.
  * `tools/manifest_validators.py <snapshot>` runs the SS6-listed validator family
    (never-strand, destructive-requires-confirmation, external_side_effects =>
    off_until_opt_in + external-cost-honesty, activation-explicitly-chosen, layout coverage,
    leaderboard-has-writer, ownership completeness, payload-superset).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile

from _gatelib import Gate, any_py, base_sha, load_json, load_yaml, p, run, show_at_base

g = Gate("manifest-validate")

COMPILER = "tools/manifest_compile.py"
NS_CHECK = "tools/check_namespace.py"
VALIDATORS = "tools/manifest_validators.py"
SNAPSHOT = "manifest.snapshot.json"
EH_REPORT = "escape_hatch_report.json"
LEDGER = "gates/schema-growth-ledger.yml"
BASELINE = "gates/escape-hatch-baseline.json"


def pre_kernel_check() -> None:
    ledger = load_yaml(p(LEDGER))
    if ledger.get("fields"):
        g.fail("pre-kernel but the A-2 schema-growth ledger has entries (inconsistent)")
    base = load_json(p(BASELINE))
    if base["repo_total"] != 0 or base["per_subsystem"]:
        g.fail(
            "pre-kernel but the A-19 escape-hatch baseline is non-zero (inconsistent)"
        )
    g.ok(
        "pre-kernel: no grammar, no compiler, no snapshot; A-2 ledger empty, A-19 baseline "
        "zero. Arms automatically when sb/spec/ or tools/manifest_compile.py lands (S3)."
    )


def check_schema_ledger(snapshot: dict) -> None:
    inventory = set(snapshot.get("schema_field_inventory", []))
    if not inventory:
        g.fail(
            "A-2: snapshot carries no schema_field_inventory -- compiler contract broken"
        )
    entries = {e["field"]: e for e in load_yaml(p(LEDGER)).get("fields", [])}
    missing = sorted(inventory - entries.keys())
    if missing:
        g.fail(
            "A-2: grammar fields with no schema-growth-ledger entry: "
            + ", ".join(missing)
        )
    stale = sorted(entries.keys() - inventory)
    if stale:
        g.fail(
            "A-2: stale ledger entries naming fields absent from the compiled inventory "
            "(remove or fix them -- a dead entry hides a real gap): " + ", ".join(stale)
        )
    base_ledger_text = show_at_base(LEDGER)
    base_frozen = (
        {
            e["field"]
            for e in (load_yaml(base_ledger_text) or {}).get("fields", [])
            if e.get("status") == "frozen_baseline"
        }
        if base_ledger_text is not None
        else set()
    )
    base_had_snapshot = show_at_base(SNAPSHOT) is not None
    for name in sorted(inventory):
        e = entries[name]
        if e.get("status") == "frozen_baseline":
            # M-3: the freeze happens exactly once (the S3 PR, whose base has no
            # snapshot). A NEW frozen_baseline entry after that -- including a
            # ledgered -> frozen_baseline status flip -- is the A-2 escape hatch.
            if base_had_snapshot and name not in base_frozen:
                g.fail(
                    f"A-2: new frozen_baseline entry {name} in a post-freeze PR -- "
                    "frozen_baseline is only legitimate for the S3 freeze set; new fields "
                    "are `ledgered` (>= 2 consumers + rejected tier-3 alternative)"
                )
            continue
        if len(e.get("consumers", [])) < 2:
            g.fail(
                f"A-2: ledgered field {name} has < 2 consuming manifest paths (Q-0219)"
            )
        if not str(e.get("rejected_tier3_alternative", "")).strip():
            g.fail(
                f"A-2: ledgered field {name} has an empty rejected_tier3_alternative"
            )
    g.note("A-2 schema-growth ledger: green")


def _new_ledger_entries(head_baseline: dict, base_baseline: dict | None) -> list[dict]:
    base_entries = (base_baseline or {}).get("ledger", [])
    base_keys = {json.dumps(e, sort_keys=True) for e in base_entries}
    return [
        e
        for e in head_baseline.get("ledger", [])
        if json.dumps(e, sort_keys=True) not in base_keys
    ]


def check_escape_hatches(report: dict) -> None:
    base = load_json(p(BASELINE))
    problems = []
    keys = set(report["per_subsystem"]) | set(base["per_subsystem"])
    for k in sorted(keys):
        measured = report["per_subsystem"].get(k, 0)
        pinned = base["per_subsystem"].get(k, 0)
        if measured > pinned:
            problems.append(
                f"{k}: tier-3 count {measured} > baseline {pinned} (rise needs a same-PR "
                "baseline bump WITH a ledger entry)"
            )
        elif measured < pinned:
            problems.append(
                f"{k}: tier-3 count {measured} < baseline {pinned} (reductions "
                "auto-tighten one-way: lower the baseline in this PR)"
            )
    if report["repo_total"] > base["repo_total"]:
        problems.append(
            f"repo_total {report['repo_total']} > baseline {base['repo_total']}"
        )
    elif report["repo_total"] < base["repo_total"]:
        problems.append(
            f"repo_total {report['repo_total']} < baseline {base['repo_total']} (tighten)"
        )
    if problems:
        g.fail("A-19 escape-hatch ratchet:\n  " + "\n  ".join(problems))

    # M-2: A-19 ledger-on-rise -- a baseline bump relative to the PR base only passes
    # with a NEW ledger entry naming what grew, why, and the rejected tier-2 alternative.
    base_text = show_at_base(BASELINE)
    if base_text is None:
        g.note(
            "A-19: no baseline at base (born-with PR or no base SHA) -- rise diff skipped"
        )
    else:
        base_pin = json.loads(base_text)
        risen = sorted(
            k
            for k in base["per_subsystem"]
            if base["per_subsystem"][k] > base_pin.get("per_subsystem", {}).get(k, 0)
        )
        if not risen and base["repo_total"] > base_pin.get("repo_total", 0):
            risen = ["repo_total"]
        if risen:
            new_entries = _new_ledger_entries(base, base_pin)
            for k in risen:
                match = [e for e in new_entries if e.get("subsystem") == k]
                if not match:
                    g.fail(
                        f"A-19: baseline for {k} rose vs the PR base with NO new ledger "
                        "entry naming it -- any rise needs {subsystem, grew, why, "
                        "rejected_tier2_alternative} in the same PR"
                    )
                for e in match:
                    if (
                        not str(e.get("why", "")).strip()
                        or not str(e.get("rejected_tier2_alternative", "")).strip()
                    ):
                        g.fail(
                            f"A-19: ledger entry for {k} has empty why / "
                            "rejected_tier2_alternative -- honesty fields are mandatory"
                        )
            g.note(f"A-19: baseline rise for {risen} covered by new ledger entries")
    g.note("A-19 escape-hatch ratchet: green")


def merge_tree_namespace_pass() -> None:
    """SS3.2 phase 2: two individually-green PRs that collide together are caught before
    either merges -- rerun compile+namespace on the merge-tree result against base."""
    b = base_sha()
    if not b:
        g.note(
            "no base SHA (push event) -- merge-tree pass skipped, HEAD pass suffices"
        )
        return
    r = run(
        ["git", "merge-tree", "--write-tree", b, "HEAD"], capture_output=True, text=True
    )
    if r.returncode != 0:
        g.fail("git merge-tree reports conflicts against base -- resolve before merge")
    tree = r.stdout.strip().splitlines()[0]
    with tempfile.TemporaryDirectory() as td:
        archive = run(["git", "archive", tree], capture_output=True)
        subprocess.run(["tar", "-x", "-C", td], input=archive.stdout, check=True)
        for cmd, what in (
            ([sys.executable, COMPILER], "compile on merge result"),
            ([sys.executable, NS_CHECK, SNAPSHOT], "namespace check on merge result"),
        ):
            if subprocess.run(cmd, cwd=td).returncode != 0:
                g.fail(f"{what} failed (SS3.2 merge-tree validation)")
    g.note("merge-tree namespace validation: green")


def main() -> None:
    artifacts = {
        "grammar": any_py("sb/spec"),
        "compiler": p(COMPILER).exists(),
        "ns_check": p(NS_CHECK).exists(),
        "snapshot": p(SNAPSHOT).exists(),
    }
    if not any(artifacts.values()):
        pre_kernel_check()
    if not all(artifacts.values()):
        g.fail(f"partial kernel state is red, never silently green: {artifacts}")

    if run([sys.executable, COMPILER]).returncode != 0:
        g.fail("manifest compile failed")
    drift = run(["git", "diff", "--exit-code", "--", SNAPSHOT, EH_REPORT])
    if drift.returncode != 0:
        g.fail(
            "snapshot drift: committed manifest.snapshot.json / escape_hatch_report.json "
            "do not match a fresh compile -- commit the regenerated artifacts"
        )
    if run([sys.executable, NS_CHECK, SNAPSHOT]).returncode != 0:
        g.fail("namespace collision check failed on HEAD")
    merge_tree_namespace_pass()
    if not p(VALIDATORS).exists():
        g.fail(
            "compiler exists but tools/manifest_validators.py does not (partial state)"
        )
    if run([sys.executable, VALIDATORS, SNAPSHOT]).returncode != 0:
        g.fail("manifest validator family failed")

    snapshot = load_json(p(SNAPSHOT))
    check_schema_ledger(snapshot)
    check_escape_hatches(load_json(p(EH_REPORT)))
    g.ok(
        "compile + drift + namespace (HEAD & merge-tree) + validators + A-2 + A-19 green"
    )


if __name__ == "__main__":
    main()
