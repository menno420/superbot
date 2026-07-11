# Session — round-3 dispatch, part 4h: session close + next-session prep

> **Status:** `complete`
> **Run type:** owner-directed ("properly end the current session and prepare the repo
> for the next one … make sure everything we discussed has a durable home") · same live
> dispatch chat (parts 4/4b/4c/4d/4e/4f/4g merged; fleet-manager #51 merged; superbot-idle
> seeded)
> **Model/time:** fable-5 · 2026-07-11 ~00:2xZ → ~00:4xZ
> Branch: `claude/sim-lab-repo-setup-ujglev` (restarted from main post-#1969) · PR #1971.

## What is about to happen

Close this session with a durable home for everything since #1969 and write a
next-session handoff brief (the next session finalizes the last dispatches so everything
fully runs).

## What happened — durable homes given

- **Router Q-0268** (autonomy vs. money/account line): burner-signup refused
  (KYC/ToS/classifier reality); autonomy comes from real-identity one-time setup then API
  keys; venture-lab emits an owner-setup-checklist + proves the paid path in Stripe TEST
  mode. The owner's live question got a doctrine answer so no seat re-opens it.
- **Runbook §5**: two new boot rows — World Games (`superbot-games failsafe wake` @ `15
  */2`, verified) + Idle Engine (seeded born-right ~23:3xZ, `superbot-idle failsafe wake`
  @ `45 */2`, verified). Both BOOTED; games program complete (both seats live).
- **Runbook §6.4**: Codex fleet-wide enablement relay for the manager (retires the
  fleet-manager Codex wall, closes sim-lab OA-002; committed, not chat-only per the §6
  convention).
- **Runbook §7**: session-close record — owner clicks COMPLETED this session (Pages,
  sim-lab Codex, idle settings, next up-to-date, kit-quality swap, 12-repo Codex) +
  the owner-authored permissions landing (`c23223f8`, PR #51) + the Q-0268 pointer.
- **Next-session brief** `round3-dispatch-next-session-brief-2026-07-11.md` (homed in the
  planning README): verified roster + the finalization-verification items + owner-click
  tail + Q-0268 posture. The next session boots straight from it.

## ⚑ Self-initiated

- Q-0268's buildable steer (venture-lab owner-setup-checklist + test-mode-first) —
  composed from the money protocol + the D1 lesson; the seat can veto/adjust.
- The next-session brief as a dedicated homed doc rather than a runbook subsection — a
  fresh session finds a named handoff faster than a buried section (the same discoverability
  logic as the §6 durable-paste-block convention).

## 💡 Session idea

**A fleet `capability-facts` file the manager keeps and seats read at boot** — tonight's
recurring failure was live seats acting on STALE capability truth (Codex not enabled,
sim-lab toggle pending, old merge walls) because agents can't see owner-side settings. A
single manager-owned `projects/_capability-facts.md` (Codex-enabled repos, required-check
names per repo, which walls are retired, model/quota caveats), version-stamped and read at
every boot, would kill the "seat skips @codex on stale info" class mechanically — the read
half of the capability-self-awareness idea (part-4c), maintained centrally instead of
probed per seat. Dedup: distinct from `capabilities --probe` (that probes a seat's own
toolset; this is owner-side facts the seat can't probe). Home: fleet-manager `projects/`.

## ⟲ Previous-session review

Part-4g's `verified-against: <sha>` idea proved itself immediately this session — the
World Games boot needed re-de-staling because `superbot-games` moved from `4493292` to
`b134961` (kit v1.7.1, pointer-stub status) between 4f drafting and 4h boot, and pinning
the SHA is exactly what caught it fast. Improvement surfaced: the games-idle seat's ORDER
000 hasn't been ground-truth-verified yet (PR #1 exists but merge unconfirmed at close) —
the next session's brief makes that its item 1 rather than leaving it implicit, so the
"BOOTED → LIVE" transition is an explicit checklist item, not a memory.

## Documentation audit (Q-0104)

`check_docs --strict` ✓ · `check_plan_homing --strict` ✓ (next-session brief homed in the
planning README) · `check_current_state_ledger --strict` ✓ (benign newest-merge lag only) ·
chat-only material swept: the autonomy/money conversation → Q-0268; owner clicks + Codex
enablement + permissions landing → runbook §7/§6.4; games boots → runbook §5; the whole
handoff → the next-session brief. Claim file deleted this commit.

## Handoff

The next session reads `round3-dispatch-next-session-brief-2026-07-11.md` + runbook §5/§7
and finalizes: confirm the two games boots close their loops (BOOTED → LIVE), venture-lab
relaunched, the manager consumed the three relays (§6.3/§6.4 + v2 fold), first @codex
proof, Pages serving. Owner tail: paste wave (on the manager's fold), venture-lab ⚑A–D,
EAP email before 07-14. A fleet check-in is armed (~00:52Z) as a backstop.
