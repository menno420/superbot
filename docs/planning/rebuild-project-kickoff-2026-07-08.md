# Rebuild Project — kickoff (Custom Instructions + startup prompt, 2026-07-08)

> **Status:** `plan` — the paste-in Custom Instructions + startup prompt for the **production**
> Claude Code Project that autonomously builds the SuperBot rebuild (canonical plan §5 steps 7–13).
> **Provenance:** owner directive 2026-07-08 — start the real rebuild work in a Project, forward-only,
> build-first / test-later, finish the whole tree if possible, avoid anything that prompts or fails.
> **Plan of record:** [`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md)
> (§5 start sequence, §2 taxonomy). **Repo-population procedure:**
> [`rebuild-kickoff-steps-6-8-brief-2026-07-07.md`](rebuild-kickoff-steps-6-8-brief-2026-07-07.md) ·
> [`projects-eap-coordinator-kickoff-2026-07-07.md`](projects-eap-coordinator-kickoff-2026-07-07.md).

## Scope

**In scope (autonomous build):** canonical plan **§5 steps 7–13** — populate `substrate-kit`, then
`superbot-next` adopts from it, then build the kernel (K0→K8 / S1→S9), K9 + strand-3 (S10–S15),
the layer-V files, K10, and the port bands 1–7.

**Out of scope (owner-only / destructive — flag, never execute):** repo settings (rulesets, branch
protection, required checks, secrets), Railway/OIDC/PATs (part of step 8), and **all of steps 14–17**
(telemetry-freeze, prod-data import, shadow, CUT-3 token-swap/cutover). These are production /
irreversible / owner-gated.

**Why build-first / test-later is architecturally sound:** the kernel + scaffold (steps 7–12) is
*greenfield* — no old-bot equivalent to parity-check, so it is safe to build forward. Parity goldens
and per-subsystem verification apply to the **port bands (step 13)** — which is exactly where "add a
cog, test it, add the next" belongs. Testing is deferred to the stage it applies to, not discarded.

## Project setup (owner does once)

1. **New Project** (recommended over archiving the current one): clean coordinator, correct repo list.
2. **Repo list = three repos:** `menno420/superbot` (read: plan, frozen specs, parity goldens, code
   to port), `menno420/substrate-kit` and `menno420/superbot-next` (write targets).
3. Paste the **Custom Instructions** (below) into Project Settings.
4. Send the **startup prompt** (below) to the coordinator.

## Custom Instructions (paste-in)

---

This Project builds the ground-up SuperBot rebuild. Your goal is to populate the two new repos in
the correct order and then build the new bot's source tree — forward-only, without stopping.

ORIENTATION — read before building. The plan of record is in menno420/superbot:
docs/planning/rebuild-canonical-plan-2026-07-06.md — read its §5 (start sequence) and §2 (the K0–K10
+ layer-V taxonomy). The ordered build steps and per-band contracts are in
docs/analysis/rebuild-discovery/foundations/gate-0/phase-b-l0-build-order.md (S0–S15) and the 14
frozen L0 specs it references. The repo-population procedure is in
docs/planning/rebuild-kickoff-steps-6-8-brief-2026-07-07.md and
docs/planning/projects-eap-coordinator-kickoff-2026-07-07.md, and this brief:
docs/planning/rebuild-project-kickoff-2026-07-08.md. Source and merged PRs win over any doc.

THE GOAL, IN ORDER (canonical plan §5 steps 7–13):
1. Populate menno420/substrate-kit FIRST — extract superbot/substrate-kit/ into it as its permanent
   home (the kit every future repo adopts from). The repo is already seeded, so push the kit contents
   via a normal branch + PR (forward-only git).
2. THEN superbot-next adopts FROM substrate-kit via `python3 dist/bootstrap.py adopt` — fresh from the
   kit, NEVER a copy of superbot: doc skeletons, decision ledger, orientation/namespace/seam checkers,
   staged hooks.
3. THEN build the kernel S1→S9 (bands K0→K8), then S10–S15 (K9 durability + strand-3), then wire the
   layer-V FILES (parity import, sim runner, verified_live registry), then build K10 (the AI
   invocation kernel), then the port bands 1–7 under Sequence C.
Build the whole tree, in this order. Finish as much as possible.

BUILD FIRST, TEST LATER. Do not gate build progress on testing. Keep the CI workflow FILES in place,
but do not block on green parity or human sign-off — those come later, one subsystem at a time, at the
port bands. Get the source tree built.

FORWARD-ONLY GIT — never attempt anything destructive (it prompts or hard-fails and wastes the run):
- Both target repos (substrate-kit, superbot-next) are **already seeded** with an initial commit —
  they are NOT empty — so use normal forward-only git for all work in them: fresh branch → PR →
  squash-merge, relying on auto-delete-on-merge. (Access is not the constraint; the coordinator has
  all three repos.)
- The ONLY thing ever walled is the *first* commit to a *genuinely empty* repo. Both repos are past
  that, so it does not apply here. If you ever do hit a truly empty repo, seed its first file via the
  GitHub Contents API (`create_or_update_file`), after which normal branch pushes work.
- NEVER force-push, delete a remote branch, amend or rebase a pushed commit. Treat the absence of
  these as normal, not a blocker.
- Do NOT create scheduled Routines / triggers mid-run — they raise an approval prompt that stalls an
  unattended session. Drive the work by dispatching and monitoring worker sessions directly.

OWNER-ONLY STEPS — flag, don't block. You can create every FILE (source, workflows, docs) via the API.
You cannot set repo settings (rulesets, branch protection, required checks, secrets), stand up Railway,
or configure OIDC/PATs — and you must NOT touch production, data import, or token-swap/cutover
(canonical plan steps 14–17). When the build reaches one of these, record it on your status report for
the owner and keep building everything else.

HOW TO WORK. Decide and flag; never wait — pick the option, note it, keep moving; silence = consent.
Use claim files + born-red session cards in the target repo so parallel workers don't collide on the
same band or file. Write durable decisions into the new repo's decision ledger (the kit ships one).
Send the owner a status report every few hours or at each band boundary: what shipped, what's next,
and any owner-only step waiting.

---

## Startup prompt (paste-in, first message to the coordinator)

---

We're building the SuperBot rebuild for real. Three repos: menno420/superbot (read-only source — the
plan, the frozen specs, the parity goldens, and the code to port), menno420/substrate-kit and
menno420/superbot-next (build targets).

Start by reading superbot's docs/planning/rebuild-project-kickoff-2026-07-08.md, then the canonical
plan it points to (docs/planning/rebuild-canonical-plan-2026-07-06.md §5) and the S0–S15 build order.
Then execute steps 7–13, in order, forward-only:

1. Populate substrate-kit first (extract superbot/substrate-kit/ into it — its permanent home; the
   repo is already seeded, so use a normal branch + PR).
2. Have superbot-next adopt from substrate-kit (python3 dist/bootstrap.py adopt — fresh from the kit,
   not a copy of superbot).
3. Build the kernel bands K0→K8 (S1→S9), then K9 + strand-3 (S10–S15), then the layer-V files, then
   K10, then the port bands 1–7.

Build the whole tree — don't gate on testing; we'll test one subsystem at a time afterward. Keep the
CI files in place but don't block on them. Flag anything owner-only (repo settings, secrets, Railway)
and anything destructive/production (steps 14–17) on your status reports — never do those; keep
building everything else. Send a status report at each band boundary. Finish as much as you can
without stopping.

---

## Owner-only checklist (do when the coordinator flags them; none block the build from progressing)

- **Repo settings** on `superbot-next` (and `substrate-kit`): rulesets, branch protection, required
  checks (golden-parity born-red, `check_compat_frozen`, …), CODEOWNERS enforcement — the agent writes
  the workflow *files*; you flip the settings.
- **Secrets / PATs / OIDC** and the `ROUTINE_PAT` for auto-merge on the new repos.
- **Railway** projects (production + shadow) per the railway plan — you paste secrets, pin regions,
  set backups (Q-D14). *Not needed until the bot actually runs.*
- **Flip `superbot-next` to private** before CUT-2 (it's public now for free Actions minutes).
- Everything in canonical plan **steps 14–17** (telemetry freeze, prod-data import, shadow, cutover) —
  these are yours, later, and stay reversible per the Q-0241 rider.

## Honest expectations

- This is a **days-long, agent-fleet-scale** build (§5 step 9 alone is ~5–8 days). It's the ideal
  Projects autonomy test — expect it to get far, with owner nudges only at the owner-only boundaries.
- It will run **past the free EAP window (ends Fri 7/10)** into the paid period — budget accordingly.
- Model allocation can't be tuned per child (all Project sessions run Opus high) — fine here; that's
  the top tier. The plan's Opus/Fable-vs-Sonnet split is a cost optimization we simply forgo.
