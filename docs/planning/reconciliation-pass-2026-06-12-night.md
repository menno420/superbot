# Reconciliation pass — 2026-06-12 (night) · the second Q-0107 pass

> **Status:** `plan` — the docs-only review + planning pass for the band that crossed
> **#760** (cadence = every 20th merged PR since #753; last pass
> [#741](reconciliation-pass-2026-06-12.md)). Sections: §1 verified state ·
> §2 decade scorecard · §3 priorities restated · §4 the next ~9 PRs · §5 pruned/fixed.
> Reset target: marker → **#762** (latest merged at pass time).

---

## 1. Verified state at this pass (against live GitHub + git log)

**Merged since the #741 pass:** #742–#756, #758–#762 (#757 is open, not a gap).
Two arcs dominated the band — both owner-steered, neither in the #741 queue (the
queue doc said steering swaps are by design, and they were):

- **The UX Lab arc (#755 design → #758/#760/#762 build, Q-0116)** — `!uxlab` live:
  64-pattern gallery · 10-probe limit bench · the Q-0108–Q-0112 **mock studio** ·
  ⚖️ compare/verdicts · the generated
  [`ux/pattern-library.md`](../ux/pattern-library.md) (doc-pinned). Side effects on
  platform truth: the CV2 limits correction (25 → 40/4000, verified on discord.py
  2.7.1) and the stale modal-select journal rule fixed.
- **The autonomous-loop arc (#742–#754/#756/#759/#761 + Q-0113–Q-0115, Q-0117)** —
  the loop went from *seams* to **LIVE wiring**: Hermes dispatch bridge verified
  end-to-end (#747/#749/#751) · routine prompts in git (#752, #754) ·
  **issue-triggered reconciliation + cadence 10→20** (#753) · **the Q-0117 Hermes
  independent-review merge gate** for substantial executor steps (#756) ·
  **executor-nightly cron** 03:00/05:00 (#759) · free-form `/bugreport` dispatch
  handling (#761). Posture: **Q-0105 calibration** — wired but young; trust grows
  per verified run.
- Also in band: **P0-1 wager money safety executed (#748)** · the direction-lock
  round (#745: Q-0097/Q-0082-interim/Q-0115) · Context7 + CodeGraph/tooling upkeep
  (#736/#737 were pre-band; #743/#744/#746/#750 small closes/routings).

**Open PRs:** **#757** (HermesCog `/bugreport` + `/dispatch` slash commands —
runtime code, another lane's in-flight work; lands via its own session under the
Q-0117/Q-0113 gates) · **#704** (owner screenshot-sharing test, owner's to close).

**Drift found and fixed in this pass (root cause, not symptom):** both
`check_reconciliation_due.py` and `check_current_state_ledger.py` shared a
merge-subject regex missing the **"Merge PR #N: …"** style (the dominant MCP-merge
form since 2026-06) — the cadence checker froze at "latest #751" and the **ledger
checker reported green while #753/#754/#756/#759/#761 were unrecorded**. One regex
fix in both + tests for all three subject styles; the five missing ledger entries
added (grouped arc entry). This is the Q-0105 "confirm tooling against ground
truth" posture doing its job — each checker now has one verified catch; both keep
their `unverified` headers until a few more clean sessions.

## 2. Decade scorecard (the #741 queue, band #741–#750 → reality)

| Slot (from the #741 pass §4) | Outcome |
|---|---|
| 1 · the pass itself | ✅ #741 |
| 2 · P2 doc-drift sweep | ❌ not run → **carried (slot 2 below)** |
| 3 · P0-1 wager money-safety | ✅ #748 |
| 4 · Postgres backup posture | ❌ → **carried (slot 3)** |
| 5 · P0-3 settings convergence | ❌ → carried (slot 7) |
| 6 · P0-4 server-mgmt channel ownership | ❌ → carried (slot 8) |
| 7 · P0-2 media retention | ❌ → carried (slot 9) |
| 8 · safety family plan + automod v1 | ❌ → **carried (slot 4) — now UX-referenced** |
| 9 · logging v1 | ❌ → carried (slot 5) |
| 10 · welcome v1 + counters | ❌ → carried (slot 6) |

The band's capacity went to the two owner-steered arcs instead — a legitimate
steer, not drift. Net effect: **the hardening + safety queue carries forward
intact**, and is now *better equipped* (the mock studio renders the safety lane's
open UX choices; the wager P0 closed).

## 3. Priorities restated (what the next band is for)

1. **The carried hardening spine** (Q-0080 posture unchanged): backup posture is
   the standing irreversible-loss risk; P0-2/3/4 are owner-unblocked
   (Q-0098–Q-0100) and waiting.
2. **The safety/community family** (Q-0108–Q-0112): plan-first, and the family
   plan should **cite `pattern_id`s from
   [`ux/pattern-library.md`](../ux/pattern-library.md)** (e.g.
   `mock_automod_rules`, `mock_logging_routing`, `mock_welcome_ab`) instead of
   describing UI in prose — the lab was built to make exactly this plan reviewable
   by clicking.
3. **The autonomous loop runs in parallel, calibrating** — nightly executor +
   issue-triggered reconciliation + the Q-0117 Hermes gate. Interactive sessions
   and routines now share one queue; the dedup mechanics are the reconciliation
   marker (reset → routine exits at its gate) and the open-PR check before
   claiming a slice. Routines that skip session-enders are expected (they have
   their own prompts); the ledger checker — now actually working — is the net.
4. Owner-led in parallel: walk `!uxlab` (desktop + phone; press probes P-07/P-08)
   · untested-surface checklist walks (P1-4) · #704 disposition.

## 4. The next ~9 PRs (band #761–#780)

> Modular but not over-segmented (Q-0107): each slot a real slice. Numbers are
> **sequence, not reserved PR numbers** — the band already consumed #761/#762
> (executor cron polish + UX Lab C). Owner steers override freely; note swaps here.

| # | PR (one session each) | Scope anchor | Gate |
|---|---|---|---|
| 1 | **This pass** — reconcile + plan + the checker-regex root fix | Q-0107 | — |
| 2 | ✅ **P2 doc-drift sweep** (#764) | [hardening P2 table](production-readiness/hardening-roadmap-2026-06-12.md) — the 5 known fixes | — (small/required) |
| 3 | ✅ **Postgres backup posture** (#769) | [production-deployment §Backups](../operations/production-deployment.md) (OPEN since #685) | Railway facts from owner if needed |
| 4 | ✅ **Safety family plan + automod v1** (#772 — [family plan](safety-community-family-plan-2026-06-13.md)) | Q-0108; UX shapes by `pattern_id` (mock studio); reuse `moderation_service` + `services/server_logging.py` seams | plan-first (this PR is the plan) |
| 5 | **Server event logging v1** | Q-0109 scope; `mock_logging_routing` renders the routing choice for the owner's pick | family plan (slot 4) |
| 6 | ✅ **Welcome v1 + server counters** (#775) | Q-0110 embed-first (the lab's A/B exists); counters quick-win | family plan (slot 4) |
| 7 | **P0-3 settings pointer-lane convergence + delegated-apply** | settings map "recommended next"; Q-0098 | unblocked |
| 8 | **P0-4 server-mgmt channel-ownership convergence** | Q-0100; extend the channel invariant | unblocked |
| 9 | **P0-2 media retention + data-minimization** | Q-0099; `YOUTUBE_CONTEXT_ENABLED` ownership | unblocked |
| 10 | **Buffer / steered slot** — likely: land #757 (its lane), or the `ui_component_census` + `uxlab-verdict` harvester tooling pair if verdicts start flowing | in-flight / ideas | — |

**Deliberately *not* in this band** (unchanged unless the owner steers): image-mod
service + security t1+2 slices (next band, on the family plan) · P1-1 AI eval
matrix · P1-2 findings lifecycle · NL event scheduler (own AI-cost design;
Q-0082 ceiling €30/mo) · help home/navigation plan · V-14 harvest · myprofile
PR A · mining V-16 phase 2 (owner PNG pack) · CV2 adoption ADR (wants the owner's
lab walk first).

## 5. Pruned / fixed by this pass

- **[reconciliation-pass-2026-06-12.md](reconciliation-pass-2026-06-12.md)
  re-badged `historical`** — superseded by this record; its queue is scored in §2.
- **Cadence text verified consistent:** #753's 10→20 raise reached CLAUDE.md, the
  checker, *and* the current-state convention line (checked — no drift); only the
  marker number/link needed this pass's reset.
- **The shared merge-subject regex bug** fixed in both checkers + tests (§1).
- The five missing ledger entries (#753/#754/#756/#759/#761) reconciled as the
  autonomous-loop arc entry; `Last reconciliation pass` marker reset to **#762**.
