# Session — round-3 dispatch, part 4: sim-lab repo setup (seat 6)

> **Status:** `complete`
> **Run type:** owner-directed · dispatch continuation (brief §2.3 — seat 6 seed)
> **Model/time:** fable-5 · 2026-07-10 ~19:0xZ → ~19:4xZ
> Branch: `claude/sim-lab-repo-setup-ujglev` · PR #1957. Part 3:
> `.sessions/2026-07-10-round3-dispatch-3.md` (#1955, merged). Brief:
> [`round3-dispatch-part4-brief-2026-07-10.md`](../docs/planning/round3-dispatch-part4-brief-2026-07-10.md).

## What is about to happen

Owner ask: prepare the sim-lab repo + env/startup script + Custom Instructions +
startup prompt (= brief §2.3). Copilot work: seed `menno420/sim-lab` born-right per
the brief §3 recipe; de-stale the Simulator package; tick runbook §3/§5; hand the
owner the final paste set.

## What happened

- **sim-lab SEEDED born-right** (the recipe's third consumer): seed `32dc75d`
  direct-pushed to empty `main` (~19:17Z). Kit v1.7.0 adopted + fully engaged — all
  9 interview slots answered with real design values from the founding package,
  `render --live` 0 unfilled, mode guided, `check --strict` green as the direct `&&`
  predecessor of the push (part-3 masked-exit lesson applied). **Gate LIVE from
  birth:** run #1 on the seed push completed green; check name `substrate-gate`
  (verified via Actions API, same as forge). Lane layer: lab-contract README (method
  ladder, the five validity-gate questions verbatim, verdict grammar, harness note),
  CONVENTIONS (+ the lane's @codex rider), PLATFORM-LIMITS (incl. the Codex-toggle
  wall), claims/, review-queue, retro set, control/ bus — inbox extended with the
  INTAKE-pull convention (two appenders, disjoint block types), **outbox added**
  (verdict bus, sole-writer), seed heartbeat with OA-001 (required check
  `substrate-gate` + Allow auto-merge, six-field) and OA-002 (Codex toggle)
  pre-filed — sims/ + harness/ skeletons, seed card with kit enders.
- **Deliberately NOT done:** the walking skeleton (branch → PR → gate → merge) — left
  to the coordinator's ORDER 000 as its calibration-by-doing; and idea-engine
  **PROPOSAL 001 was NOT pre-pulled** (re-verified waiting, sim-ready, 18:05Z — the
  first wake's pull is the Q-0264 pipeline's end-to-end proof).
- **Package de-staled** ([simulator package](../docs/planning/round3-founding-package-simulator-2026-07-10.md)):
  §0.1 done, §0.5 now clickable-now with the verified check name, §2 boot step 1
  rewritten to verify-the-seed + ORDER 000 (the third package needing exactly this —
  evidence for the kit-seed-command idea).
- **Copilot verification sweep (part-4 items 1–2 of the brief queue, partial):**
  forge routine **verified in the registry** (`trig_01XjviWNduYqF5jeRnRBMSFN`, 2-hourly
  even :00, enabled, next 20:02Z); manager's games-web **ORDER 001 verified landed** in
  the forge inbox (18:41Z, raw @ HEAD) — no dedup needed; forge status @ HEAD
  self-reports ORDER 001 phase-1 merged (its PR #2). Runbook §3.5 flipped ☑ (LIVE per
  registry + artifacts; calibration paste-back stays unverified — owner-side), §3.6 +
  §5 rows updated. No sim-lab trigger exists yet (correct). The orphan `send_later`
  watchdog chain is still alive (one live link, 19:34Z) — **untouched, still awaiting
  the owner's explicit go** (brief §2.5).
- **Friction → guard:** the kit's reachability walk roots at `docs/` only (repo-root
  README doesn't count) — bit this seed via `docs/retro/questions.md`; fix recorded in
  the brief §3 recipe (checker already enforces; the recipe now names the fix).
- **Post-close (same session): Q-0194 gate miss + Q-0265 fold-in.** (a) First flip
  reddened on the telemetry-row gate (card added, no `telemetry/model-usage.jsonl`
  row) — row appended at `4c20284`. (b) conflict-guard fired: a parallel session had
  landed **owner directive Q-0265 (continuous mode)** + forge-LIVE verification
  (#1958–#1961) — merged main in, resolved the runbook §3.5/§5 conflicts by combining
  both sessions' facts (their owner-screenshot/heartbeat evidence + this session's
  registry + raw-inbox verifications), and confirmed the package's §1/§2 pastes are
  now **continuous-native** (their Q-0265 rewrite + this session's seeded-reality
  step 1 compose cleanly — sim-lab is the first seat born continuous). (c) sim-lab's
  seed-status routine note was pre-Q-0265 → de-staled via **sim-lab PR #1** (squash
  `7f149f0`), which also verified the ruleset live (direct push now rejected) and the
  REST merge-on-green landing path — ORDER 000 still runs the coordinator's own proof.

## ⚑ Self-initiated

- sim-lab seed executed cross-repo at the owner's ask (in-scope repo, branch-per-task
  harness session). Seed pushed to `main` directly — the empty-repo first push, per
  the recipe; every later sim-lab change rides a PR.
- Forge §3.5/§5 runbook flip from part-4 copilot verification (registry + raw
  artifacts) — flagged: calibration paste-back not chat-verifiable from here.
- The INTAKE-block inbox convention (two appenders, disjoint block types) — a design
  call the package implied but didn't spell out; flagged for the coordinator's boot to
  confirm in practice.

## 💡 Session idea

[`seat-boot-verification-harness-2026-07-10.md`](../docs/ideas/seat-boot-verification-harness-2026-07-10.md)
— script the four-times-repeated per-seat boot verification into
`scripts/check_seat.py` emitting a ready-to-paste §5 row; the 3 games-seat boots are
imminent consumers.

## ⟲ Previous-session review

Part 3's brief §3 recipe was exact enough that the third seed replayed with only ONE
new surprise (the reachability-root gotcha, now folded in) — that's what a good runbook
looks like. Miss: the §1 snapshot marked seat 5 "Project boot next" but the forge was
fully booted + executing within the hour, and part 4 only learned it by accident
(fetching the forge status as a seeding reference). **Workflow improvement:** the §5
re-verification at session start should be a standing first step of every dispatch
session — cheap once `check_seat.py` (this session's idea) exists; until then, one raw
status fetch per non-LIVE seat before trusting any snapshot row.

## Documentation audit (Q-0104)

`check_current_state_ledger --strict` ✓ (#1955 = benign newest-merge lag, next recon
records; #1957 = this session, records at merge) · `check_docs --strict` ✓ · chat-only
material swept: seed facts + owner clicks → package §0/§2 + runbook §3.6/§5 + sim-lab
seed status; recipe gotcha → brief §3; registry sweep findings → runbook §5. Claim file
deleted this commit.

## Handoff

Owner paste set delivered in-chat (also derivable from the package): env = §0.3
(archetype-python-lab raw link, repo-only, no vars) · Custom Instructions = package §1
verbatim · chat brief = package §2 (de-staled) · clicks = §0.2/§0.4/§0.5 (Project,
Codex toggle, `substrate-gate` required + Allow auto-merge). First-wake proof: the
coordinator pulls idea-engine PROPOSAL 001. Still open from brief §2: seat-5
calibration paste-back (owner-side), kit/manager wake outcomes since 18:08Z/18:31Z
(§2.4), the owner click batch (§2.5 — incl. the orphan watchdog chain, awaiting
explicit go), games ORDER relay verification on the manager's next :30 wake.
