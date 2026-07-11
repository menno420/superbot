# Round-3 dispatch — NEXT-SESSION brief (2026-07-11)

> **Status:** `plan` — the handoff from part-4h (session close) to the next dispatch
> session, whose job is to **finalize the last dispatches so everything fully runs**.
> State home: [`round3-dispatch-runbook-2026-07-10.md`](round3-dispatch-runbook-2026-07-10.md)
> (§5 boot log · §6 paste blocks · §7 close). Read that runbook + this brief and you are
> oriented. **Verify every claim below against live GitHub + the trigger registry before
> acting (Q-0120)** — this is a dated snapshot written at ~00:2xZ.

## The one-line state

> **✅ DISPATCH PROGRAM COMPLETE (04:54Z capstone check-in, part-4k).** Every seat is LIVE
> and producing; the manager successor consumed all relays; the fleet is now *growing on its
> own* (two new seats born — superbot-mineverse + a retro-games coordinator; kit v1.8.0 + 7
> adopters). Only two non-dispatch residuals remain, both surfaced in the owner-click tail and
> neither needing babysitting: raise the Codex usage cap, and the product-forge Pages deploy
> (auto-fires on the next forge merge). **The copilot check-in loop is CLOSED** — no further
> automated sweeps; the fleet's own failsafes + chains keep it running.

The dispatch board is **clear**: all six core seats + every manual/game lane are LIVE. What
remained was finalization verification (all done — see below) plus a short owner-click tail.

## Fleet roster at close (verify at boot)

| Seat / lane | State | Failsafe (cron) | What to verify |
|---|---|---|---|
| fleet-manager | **SUCCESSOR LIVE** (02:49Z check-in: fresh coordinator running review-queue verifies, fm PR #61; reboot completed) | `30 */2` | on the successor's ladder: v2 permissions fold re-landed citing `c23223f8`? projects/superbot-games + projects/superbot-idle ingested (§6.3)? (Codex fleet-wide already confirmed, ORDER 014/PR #54; registry-truth moved to `docs/roster.md`, fm #59 / superbot #1974) |
| substrate-kit | LIVE | `0 */2` | kit-quality now the sole required check (owner swapped) — first kit PR shows it Required |
| Builder (superbot-next) | LIVE | `0 */2` | band-6 (games) progressing; `superbot-plugin-hello` package pushed |
| Idea Engine | LIVE, pipeline flowing | `0 */2` | outbox feeding sim-lab |
| Product Forge | LIVE | `0 */2` | GitHub Pages enabled (owner ✅); `menno420.github.io/product-forge/` **still 404 at 00:52Z — pending the first post-click deploy** (serves after the next forge merge triggers the Actions deploy) |
| Simulator (sim-lab) | LIVE, **queue drained** (02:49Z: INTAKE 001–005 all finalized as VERDICT 001–005) | `0 1-23/2` | the one open item: first real @codex reply on a verdict (proves OA-002) — verdicts finalized JUDGMENT-ONLY meanwhile; quota refusals are retry-later, not a wall |
| Trading | LIVE, paper lane operational | `0 */2` | ORDER 008 DONE (holdout SPENT, 13 verdicts on main); Round 2 closed (5 KEEP/9 KILL); old wake `trig_01Mvn5xRmqGmZJNRHgjqyLpN` DELETED ✅ |
| World Games (superbot-games) | **LIVE** (verified 00:52Z, HEAD `bb744df`) | `15 */2` | orders 001+002 done, 210 tests green, into theme-slot remediation — producing well past boot; nothing to verify, LIVE |
| Idle Engine (superbot-idle) | **LIVE** (verified 00:52Z, HEAD `2c7ad3f`) | `45 */2` | founding queue COMPLETE (ORDER 000 → slice e), egg-farm nouns from data + guard test, theme-gate required (OA-002 ✅) gating from PR #6 — LIVE, volume phase begun |
| venture-lab | **LIVE** (02:49Z check-in, HEAD `9f1b616`) | `0 */2` (self-armed ✅) | orders 001–004 all DONE (Stripe real-path fix ORDER 003 merged); **⚑B/⚑D publish clicks UNFROZEN**; work loop running (Stripe Webhook Test Kit next). Owner action = the publish clicks (below) |
| websites | LIVE | 4-hourly (v1-era) | rides the paste wave for its Q-0265 cutover + v2 re-paste |

## Remaining finalization items (the next session's actual work)

> **Updated by the 00:52Z check-in (part-4i):** item 1 is DONE — both games seats verified
> LIVE at ground truth. The live remaining items are 2–5.

1. ~~Verify the two games boots close the loop~~ **DONE (00:52Z check-in):** superbot-games
   (HEAD `bb744df`, orders 001+002 done, 210 tests) + superbot-idle (HEAD `2c7ad3f`, founding
   queue complete) are both **LIVE and producing** — §5 verdicts ticked BOOTED → LIVE.
2. ~~Verify venture-lab relaunched~~ **DONE (02:49Z check-in):** LIVE (HEAD `9f1b616`),
   orders 001–004 done, failsafe self-armed, Stripe fix merged; **⚑B/⚑D publish clicks
   UNFROZEN** (see owner tail). The last dark lane is live.
3. ~~Confirm the manager successor consumed the relays~~ **DONE (04:54Z):** successor LIVE
   (`cse_012o8p…`); `projects/superbot-idle/` built + `projects/superbot-games/` at **v2**
   (permissions block folded); games/idle inbox relays landed (fm #63/#64); registry-truth
   machine-generated (`gen_roster.py`, fm #62/#65).
4. ~~First @codex proof~~ **RESOLVED (04:54Z):** the Codex integration IS LIVE — it replies on
   sim-lab verdict PRs (#15/#16) — but every reply is "usage limits." The toggle is proven;
   the residual is a **usage cap** → owner click below. (Not a wall; verdicts finalize
   JUDGMENT-ONLY meanwhile.)
5. **Product Forge Pages** — still 404 at 04:54Z; **auto-serves on the next forge merge** (the
   deploy workflow is on main; no owner action, just time). Not a babysit item.

## Owner-click tail (only genuinely owner-only items left)

- **The paste wave** — once the manager re-lands the v2 instruction fold, one sitting of
  re-pastes to the live seats (incl. websites' Q-0265 cutover + venture-lab boot if not done).
  The copilot flags when the fold lands.
- **venture-lab ⚑B/⚑D — NOW UNFROZEN (02:49Z):** ORDER 003's real-path Stripe fix merged, so
  the two products are publishable for first revenue whenever the owner is ready — $49
  membership-kit (`candidates/membership-kit/LISTING.md` + committed zip) and $19 PWYW
  template-packs (`candidates/template-packs/LISTING.md` + zip) → a marketplace (Gumroad /
  Lemon Squeezy); the $59 bundle goes live after both. ⚑A (Stripe TEST keys) still unblocks
  the live test-mode E2E if wanted first. Not urgent — the products aren't going anywhere.
- **Raise the Codex usage cap (NEW, 04:54Z)** — the Codex integration is LIVE fleet-wide and
  replies on verdict PRs, but every reply is "You have reached your Codex usage limits"
  (confirmed on sim-lab #15/#16 AND superbot #1978). Raise/reset the cap at
  chatgpt.com/codex → usage/limits so substantive @codex reviews actually land. Small click,
  not blocking (verdicts finalize JUDGMENT-ONLY meanwhile).
- **The paste wave** — lower priority now: the v2 permissions fold is landed in the manager
  registry AND the permissions block reaches live seats via the fetched universal WAKE prompt,
  so re-pasting v2 Custom Instructions is a when-convenient hygiene pass, not a gate.
- **EAP wrap-up email** — owner writes Part 1 + sends, **before 2026-07-14** (carries the
  capability-self-awareness item).
- **Parked, no rush:** orphan-watchdog deletion (owner's explicit go); pokemon-mod-lab playtest.

## Autonomy posture (Q-0268, this session)

The revenue lanes push toward autonomy through **API keys after a one-time real-identity
account setup**, NOT burner-signup — the money/account hard line stays (KYC/ToS/classifier
reality). venture-lab emits a `docs/owner-setup-checklist.md` to make the one human gate
turnkey, and proves the paid path in Stripe TEST mode first. Full reasoning: router Q-0268.
