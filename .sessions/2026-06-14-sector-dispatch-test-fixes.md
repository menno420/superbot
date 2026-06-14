# Session: dispatch-test fixes — executor dimension + startability tags + S1 freshness

> **Status:** `complete`

**Branch:** `claude/ecstatic-euler-bslyvd` · **PR:** #880 · **Date:** 2026-06-14 · **Type:** owner-directed workflow substrate (docs-only)

## What this session did
A continuation of the sector work. Earlier this session I restructured the roadmap by sector (PR #877,
merged); the owner then asked me to **dogfood-test** the structure — pick 3 sectors and measure how
fast a fresh session gets "ready to work." The test passed on speed and surfaced 3 findings; the owner
chose to **build all 3 into one docs PR** (executor dimension decided-by-derivation → **Q-0143**).

### The test (the input to this PR)
Traced **S1 / S2 / S5** from *dispatched → ready-to-work* using only sector → `Now` → plan/folio →
code. **Result: 2–3 targeted reads per sector, all links resolved, the index ranked even 8-area S1 to
one `Now`, and a 20-min-stale `Now` (S1 vs #878) self-corrected at the linked authority in one hop.**
Three findings: (1) `Now` lags merges; (2) a non-empty `Now` can be un-startable (S2 was demand-driven
+ maintainer-only); (3) `sector + action` assumed a Claude-in-repo executor, but most of **S5** is
Hermes-VPS / maintainer.

### Shipped (docs-only — zero `disbot/`)
1. **Executor dimension (finding 3)** → `repo-sector-map.md` § dispatch targets: a complete dispatch is
   **sector + action + executor** (**Claude-in-repo** default S1–S4 · **Hermes-on-VPS** · **maintainer**);
   **S5 is the executor outlier** — don't fire a repo-editing agent at an S5 token/deploy task. Augmented
   the sector table with a Default-executor column + per-sector executor on every roadmap Dispatch line.
2. **Startability tag (finding 2)** → the legend (**▶ startable / ⛔ gated / 👤 maintainer**) in the
   contract, and the tags applied to every sector's `Now` (21 marks). A `Now` entirely ⛔/👤 is **not
   autonomously dispatchable** → fall through to the first ▶ (S2's case, now explicit).
3. **S1 freshness (finding 1)** → de-drifted S1's `Now` for **#878** (offline eval/smoke matrix shipped
   → next = live half ⛔ creds + ▶ Layer B) and **linked P1-1's plan** (hardening roadmap) from the S1
   block — the one missing hop the test hit.
4. **Q-0143** recorded (refines Q-0137 Thread 1) + `current-state.md` stamp.

## 💡 Session idea (Q-0089)
**`scripts/dispatch_menu.py`** (or a `superbot-dispatch-menu` Hermes skill) — a **read-only generator**
that parses the roadmap's sector index + the new tags and prints, per sector, the **first ▶ startable
item + its executor + the linked plan** — i.e., the machine version of the dispatch test I just did by
hand. A dispatcher (or Hermes) then picks from a **generated, always-fresh menu** instead of reading
prose, and the "falls through to Next" logic (Q-0143) is computed, not eyeballed. **Distinct from**
`check_sector_map.py` (structural coverage) and `sector_health.py` (attention telemetry): this is
*dispatch resolution* — the read-side bridge between the Q-0143 contract and the Q-0137 Thread-1 `/fire`
wiring. Dedup-grepped `docs/ideas/` + roadmap: no overlap.

## ⟲ Previous-session review (Q-0102)
Reviewing **PR #877** (my own immediate predecessor — the sector restructure this PR refines).
**Did well:** made the sectors genuinely dispatchable *fast* — the test empirically confirmed 2–3 hops
to ready, which is the whole point. **Missed (and the test caught):** it operationalized "every sector
has a non-empty `Now`" as the Q-0137 deep-clean terminal condition — but that's **necessary, not
sufficient**: S2 had a non-empty Now that was entirely un-startable (finding 2), and the model had no
executor dimension so S5's queue pointed a repo-agent at VPS work (finding 3). #877's terminal
condition should be tightened to *"every sector has a non-empty Now containing at least one ▶ startable
item with a named executor."* **System improvement:** the **build → dogfood-test → fix** loop this
session ran (restructure #877 → trace 3 sectors → ship the 3 fixes #880) is worth making a **standing
move**: when you ship a navigational/structural change, *traverse it as a fresh consumer would* before
declaring it done. That's the internal mirror of the live-test-the-bot practice, applied to the docs
substrate. (Parallel **#878** shipped the P1-1 offline eval matrix cleanly — its only cross-effect was
making S1's `Now` stale, which finding 1 fixed.)

## Doc audit (Q-0104)
`check_docs --strict` ✓ (badges unchanged from #877's state; all links incl. the new
hardening-roadmap §P1-1 link reachable). 21 startability marks + 5 per-sector executor labels verified
present. `check_current_state_ledger` still shows the expected **between-pass lag** (#872–#878 not yet
in Recently-shipped) — the reconciliation routine's job at #900 (Q-0124), **not** a CI gate for
docs-only PRs. No `disbot/` touched → `check_quality` n/a.

**Grooming (Q-0015):** this PR groomed the dispatch design itself — turning a felt gap (the test
findings) into a recorded decision (Q-0143) + applied convention, and queuing three concrete tooling
follow-ons (`check_sector_map.py` extended to enforce tags/executor · `sector_health.py` ·
`dispatch_menu.py`).

## Context delta
- **Discovered by hand:** the test *was* the discovery — three real gaps in the dispatch model that
  only surfaced by traversing the structure as a consumer, not by reading it as an author. Cheap, high
  signal. **One change that would have helped:** had #877 shipped a `check_sector_map.py` that asserted
  tag + executor coverage, findings 2–3 would have been caught at author-time; that checker is now the
  named follow-on in Q-0143.
- **Decided alone (within the delegated envelope):** the three executor *names* (Claude-in-repo /
  Hermes-VPS / maintainer) and the three tag *symbols* (▶/⛔/👤) — derived from the existing safety
  model (Q-0117/Q-0140 Hermes writes; the maintainer-only deploy/secret boundary) rather than invented.
- **Weak point of what shipped:** the tags + executors are **prose-asserted, not machine-checked**, so
  they can drift exactly like finding 1 — a new `Now` item could land untagged. The fix is the queued
  `check_sector_map.py` extension; until then the convention relies on session discipline.
