# SuperBot hub — self-review 2026-07-11 (ORDER 002)

> **Status:** `audit` — the hub's answer to **control/inbox.md ORDER 002** (P1,
> owner-requested fleet-wide self-review, relayed by the fleet manager on coordinator
> direction). **Window: 2026-07-10 ~20:00Z → 2026-07-11 ~19:30Z.**
> **Provenance:** written 2026-07-11 by a hub-touching session (PR #2003 lane; the hub has
> no standing seat per Q-0264). Every load-bearing claim below is verified against git
> history / PR state / committed docs — verification method noted per item; where no
> repo-side record exists, that is said rather than estimated. Filed at the
> protocol-canonical `docs/retro/` path (convention: `self-review-2026-07-09.md`, the
> gen-1 question-set answer) so the manager's cross-lane corpus reader finds it in the
> same glob. Heartbeat pointer: `control/status.md` (created by the same PR).

## 1. What went wrong (citations per item)

1. **`codex-final-review` workflow born-broken since 2026-06-19 — ~2,808 instant
   failures, zero successes — fixed today.** The workflow's `gh pr comment --body`
   multi-line string de-indented out of the `run: |` block scalar, so the file was
   invalid YAML **from its creating commit `bfe99084` (PR #1105, 2026-06-19)**: every
   trigger instant-failed at parse and the `@codex review` final-head request never
   fired once. Fixed by **PR #1995 → merge commit `8214200`** (2026-07-11). Verified:
   the merge commit's own message + diff (`git show 8214200`), the ledger entry in
   `docs/current-state.md`, and independently the fleet-manager owner-queue C#20
   manager note ("invalid YAML since 2026-06-19 — 0 successful runs of 2,811; latest
   run 29156086075 instant-fails at parse" — fm `docs/owner-queue.md` @ `7ff1f75`).
   Count discrepancy (~2,808 vs 2,811) is between the two records; order of magnitude
   and dates agree. **Class:** a workflow that was *never green* went unnoticed for
   ~22 days — a born-broken CI lane looks identical to a noisy one.
2. **`docs/eap/fleet-manifest.md` stale on every measured axis → retired to a pointer
   stub (PR #1974, merge `4c21894`).** The fleet-manager parallel run measured the
   hand-maintained manifest ~33.5h stale, 5 live lanes missing, 9 of 10 live-lane rows
   factually wrong; canonical state moved to fm `docs/roster.md` (generated, ≤~2h
   fresh). The companion checker `scripts/check_manifest_freshness.py` was deleted the
   same day per its own Q-0105 kill-switch header. Verified: the stub's own text at
   HEAD + `git log -- docs/eap/fleet-manifest.md` (34ebbac).
3. **The hub had NO fleet-relay landing surface until today** — `control/inbox.md` did
   not exist until **PR #1977 (commit `7877cf2`)** created it (with the 📊 Model line
   convention, ORDER 001). Verified: `git log --diff-filter=A -- control/inbox.md`.
   Same class as item 4 below: the gen-1 retro (F2) had already named the hub's missing
   `control/` surface; it took until 2026-07-11 to start closing it.
4. **The hub still had no `control/status.md` heartbeat** — named as a manager-side
   gap in the gen-1 retro (`docs/retro/self-review-2026-07-09.md` §F2: the hub row went
   stale in the manifest partly because "nothing machine-readable declares the hub's
   state"). Closed by the PR carrying this review (self-initiated, flagged).
5. **Account-wide GraphQL rate-limit exhaustion ~2026-07-11 15:00–15:20Z:** reported by
   the fleet manager; **no repo-side record found** (grepped `.sessions/2026-07-11-*`
   and docs/). Precedent on record: the same exhaustion class is documented for
   2026-07-09 ("API rate limit already exceeded", 10498/5000 used, blocking
   `enable_pr_auto_merge` while REST kept working —
   `docs/eap/gen1-wrapup-email-draft-v2-2026-07-09.md:76`).
6. **Codex usage-cap flapping:** repo-side record exists — the round-3 CAPSTONE card
   (`.sessions/2026-07-11-round3-dispatch-4k-checkin-complete.md:14`) verified Codex
   integration LIVE (replies on sim-lab #15/#16 and superbot #1978) **but usage-capped
   fleet-wide** at ~05:0xZ and surfaced a "raise Codex usage cap" owner click. The
   fleet manager later **retired the hard-cap framing → FLAPPING** (usage-limit replies
   05:08Z, then full reviews 05:54Z/06:31Z; fm owner-queue C#20), making the raise
   optional — i.e. the hub's own "persistent cap" tail line was itself superseded
   within hours (the same stale-owner-tail class the 4j→4k cards flagged internally).
7. **Round-3 chain (#1967–#1986) residue, swept:** (a) product-forge **Pages 404** at
   the CAPSTONE (4k card item 5; now fm owner-queue D#26 — Pages was never enabled,
   owner click); (b) the 4j check-in caught a **misleading stale "FROZEN, do not
   publish" owner-tail line** (recorded in the 4k card's ⟲ review); (c) the 43rd recon
   pass found **10 supersede-banner drift findings, fixed 5** (the other 5 are honest
   cross-repo supersessions the in-repo checker can't model —
   `docs/planning/reconciliation-pass-2026-07-11-band1980.md`); (d) **two stale claim
   files** from an already-complete same-day session (branch
   `claude/multi-project-review-dispatch-myegbp`, cards `complete`, zero open PRs)
   were still in `docs/owner/claims/` at HEAD `050ba69` — removed by this session's
   first commit (fix-on-sight, Q-0166).

## 2. Requiring owner attention — hub-specific

**None new.** Checked against the fleet-manager owner queue (`docs/owner-queue.md` @
`7ff1f75`, rewritten today): the hub's owner tail from the CAPSTONE card (Codex cap →
now optional per C#20 · EAP email by 07-14 · venture publish clicks · Pages) is already
queued there; superbot itself appears only as the optional paste-wave item C#15(7). One
**manager-sweep note (not an owner click):** fm owner-queue **C#20's manager note**
("superbot's codex-final-review workflow has had invalid YAML since 2026-06-19 …
routed to the superbot lane") is now **RESOLVED** — fixed by superbot PR #1995
(`8214200`); the queue line can be retired at the manager's next sweep. Mirrored on
`control/status.md` ⚑.

## 3. One-line health

Round-3 dispatch program **COMPLETE** (#1978, merge `b0e9ab2` — all six core seats
BOOTED→LIVE, copilot loop closed); hub steady as coordination surface — 43rd Q-0107
recon pass done (band-#1980, next due at #2010), dashboard-refresh loop live and
self-firing (latest #1999, merge `2c7d2de`), codex-final-review CI lane repaired
(#1995), fleet relay surface now complete (inbox #1977 + status heartbeat this PR);
rebuild parity is **lane-side** at `superbot-next`, not hub work (repo-recorded figure:
**37/49 ports, gate 218/218**, per #1996 `1eeedb0` — supersedes older lower counts).
