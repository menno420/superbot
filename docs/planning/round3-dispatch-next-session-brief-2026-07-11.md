# Round-3 dispatch — NEXT-SESSION brief (2026-07-11)

> **Status:** `plan` — the handoff from part-4h (session close) to the next dispatch
> session, whose job is to **finalize the last dispatches so everything fully runs**.
> State home: [`round3-dispatch-runbook-2026-07-10.md`](round3-dispatch-runbook-2026-07-10.md)
> (§5 boot log · §6 paste blocks · §7 close). Read that runbook + this brief and you are
> oriented. **Verify every claim below against live GitHub + the trigger registry before
> acting (Q-0120)** — this is a dated snapshot written at ~00:2xZ.

## The one-line state

The dispatch board is **essentially clear**: all six core seats + every manual/game lane
are LIVE or BOOTED. What remains is **finalization verification** (did the last-booted
seats' first PRs land and their loops stay hot?) plus a short owner-click tail. This is a
*confirm-and-close* session, not a build-more session.

## Fleet roster at close (verify at boot)

| Seat / lane | State | Failsafe (cron) | What to verify |
|---|---|---|---|
| fleet-manager | LIVE, continuous | `30 */2` | v2 permissions fold re-landed citing `c23223f8`? projects/superbot-games + projects/superbot-idle ingested (§6.3)? Codex relay (§6.4) adopted? |
| substrate-kit | LIVE | `0 */2` | kit-quality now the sole required check (owner swapped) — first kit PR shows it Required |
| Builder (superbot-next) | LIVE | `0 */2` | band-6 (games) progressing; `superbot-plugin-hello` package pushed |
| Idea Engine | LIVE, pipeline flowing | `0 */2` | outbox feeding sim-lab |
| Product Forge | LIVE | `0 */2` | **GitHub Pages now enabled (owner ✅)** — confirm `menno420.github.io/product-forge/` serves after the next merge |
| Simulator (sim-lab) | LIVE | `0 1-23/2` | **Codex toggle done (owner ✅, OA-002 closed)** — confirm first real @codex reply on an INTAKE verdict (proves the toggle); quota refusals are retry-later, not a wall |
| Trading | LIVE, paper lane operational | `0 */2` | ORDER 008 DONE (holdout SPENT, 13 verdicts on main); Round 2 closed (5 KEEP/9 KILL); old wake `trig_01Mvn5xRmqGmZJNRHgjqyLpN` DELETED ✅ |
| World Games (superbot-games) | BOOTED (part-4h) | `15 */2` | ORDER-001 walking-skeleton PR landed (gate 73→121 tests)? gen-1 pointer stub overwritten with real unified heartbeat? |
| Idle Engine (superbot-idle) | BOOTED (part-4h) | `45 */2` | ORDER-000 PR #1 merged? theme-gate ran in CI? egg-farm.yaml nouns loaded (NOT hard-coded)? |
| venture-lab | RELAUNCHING (owner sent boot prompt) | `0 */2` (self-arm on boot) | ORDER 004 (heartbeat repair) → ORDER 003 (real Stripe-path fix) executing? failsafe self-armed? |
| websites | LIVE | 4-hourly (v1-era) | rides the paste wave for its Q-0265 cutover + v2 re-paste |

## Remaining finalization items (the next session's actual work)

1. **Verify the two games boots close the loop** — superbot-games ORDER 001 PR + superbot-idle
   ORDER 000 PR both merged; both heartbeats fresh at HEAD; both failsafes fired at least once
   (registry, not "first fire as proof"). Tick their §5 verdicts from BOOTED → LIVE.
2. **Verify venture-lab relaunched** — state repaired (ORDER 004), Stripe fix (ORDER 003) in
   flight or merged, failsafe armed; the `substrate-gate`-required settings change let it
   self-land (re-verify the old merge wall is gone).
3. **Confirm the manager consumed the session's relays** — v2 permissions fold re-landed
   (owner-provenance `c23223f8`), §6.3 games-registry ingest, §6.4 Codex-enablement update.
4. **First @codex proof** — sim-lab's first real Codex reply on a verdict; if quota-blocked,
   note retry-later (not a wall).
5. **Product Forge Pages live** — `menno420.github.io/product-forge/` serving after a merge.

## Owner-click tail (only genuinely owner-only items left)

- **The paste wave** — once the manager re-lands the v2 instruction fold, one sitting of
  re-pastes to the live seats (incl. websites' Q-0265 cutover + venture-lab boot if not done).
  The copilot flags when the fold lands.
- **venture-lab ⚑A–D** — Stripe TEST keys (⚑A) unblock the E2E; the $49/$19 publish clicks
  (⚑B/⚑D) stay FROZEN until ORDER 003's real-path fix merges green (do NOT publish before).
- **EAP wrap-up email** — owner writes Part 1 + sends, **before 2026-07-14** (carries the
  capability-self-awareness item).
- **Parked, no rush:** orphan-watchdog deletion (owner's explicit go); pokemon-mod-lab playtest.

## Autonomy posture (Q-0268, this session)

The revenue lanes push toward autonomy through **API keys after a one-time real-identity
account setup**, NOT burner-signup — the money/account hard line stays (KYC/ToS/classifier
reality). venture-lab emits a `docs/owner-setup-checklist.md` to make the one human gate
turnkey, and proves the paid path in Stripe TEST mode first. Full reasoning: router Q-0268.
