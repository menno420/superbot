# Kickoff brief — §5 steps 6–8: create `superbot-next`, extract the kit repo, bootstrap, control plane (2026-07-07)

> **Status:** `plan` — the launch brief + paste-ready prompt for the dedicated **kickoff session**
> that starts the new repo. Owner-ratified sequencing: **Q-0247** (superbot-next now → kit
> extraction rides step 7 → trading repo third). Governance: **Q-0241** (never-wait,
> silence=consent) + **Q-0240** (decide-and-flag). The plan of record is
> [`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md) — this brief adds
> nothing to it; it packages steps 6–8 + the Q-0247 kit-extraction fork for one session.
>
> **Model:** Claude **Fable 5**, `/effort ultracode` (foundational session: it sets two repos'
> shape and the control plane). Per Q-0248, log model/effort/task-class/outcome telemetry from
> session one — the kickoff is the first data point of the model-allocation dataset.

## 1. Reading route (in order)

1. `.claude/CLAUDE.md` → `docs/collaboration-model.md` → `docs/current-state.md` (S3 row) →
   `.session-journal.md` ⚡ Quick reference.
2. **The plan of record §5 steps 6–8** + §2.1 (K0 row) + §11/§11b (the amendments bind the new
   repo's CI from birth — especially A-16 parity-depth in the gate-5 schema, A-19
   `check_escape_hatches` in manifest-validate, A-21 extra-owner config, A-22/R-18 permission
   tiers).
3. **The program frame:** [`../ideas/multi-repo-program-kit-lab-trading-2026-07-07.md`](../ideas/multi-repo-program-kit-lab-trading-2026-07-07.md)
   — Part 0 is binding for this session: **fresh-from-kit; the old repo attaches read-only as the
   oracle; never clone-as-base.**
4. **Kit mechanics:** `substrate-kit/` (esp. `dist/bootstrap.py`, the adopt/upgrade discipline,
   the 432-test suite) + the Phase-2.5 report
   ([`phase-2.5-cold-start-report-2026-07-07.md`](phase-2.5-cold-start-report-2026-07-07.md)) so
   the unproven-benefit caveat is carried honestly into the kit repo's README.
5. **Control plane specs:** design-spec §6 (the six named required gates, verbatim contract) +
   [`railway-setup-plan-2026-07-02.md`](railway-setup-plan-2026-07-02.md) §4/R-3.

## 2. The mandate — three steps + one fork, one session

### Step 6 — create the repos (both; the fork is pre-decided, ⚑ vetoable)

- Create **`superbot-next`** (empty, private) and **`substrate-kit`** (the extraction target —
  Q-0247 ratified extract-at-step-7; creating both now avoids a second kickoff).
- Seed `substrate-kit` from this repo's `substrate-kit/` tree (a `git subtree split` preserves
  the kit's commit history if cheap; a clean snapshot + provenance README is acceptable —
  decide-and-flag). Its CI = the kit's own test suite (432 green) + `check --strict` on a
  scratch adoption — the kit repo is born self-verifying.
- **superbot-next starts EMPTY.** No clone, no history import, no code carry (capture doc Part 0).
  The old `superbot` repo is attached to the session read-only as the oracle.

### Step 7 — bootstrap-adopt into superbot-next

- `python3 dist/bootstrap.py adopt` **from the `substrate-kit` repo's dist** (superbot-next is
  consumer #2; this old repo becomes a version-pinned consumer of the same dist — record the pin
  note here, don't rewire this repo's copy in this session).
- Verify cold: doc skeletons planted, hooks staged + resolving in-repo, `check --strict` green,
  orientation-budget checker armed. Render honestly: the UNRENDERED banner discipline stands.
- Instantiate the governance layer the kit plants as templates: CLAUDE.md skeleton, decision
  ledger, question-router file, claims dir, session-log convention. **Program-governance fork
  (decide-and-flag):** program-level owner rulings (Q-0240/Q-0241/Q-0247/Q-0248 class) get a home
  the kit repo carries as the canonical copy, with per-repo routers for repo-local rulings —
  recommended shape; flag whatever you decide.

### Step 8 — control plane

- Rulesets + OIDC, CODEOWNERS, branch protection; the **six named required gates** exactly per
  design-spec §6 — `golden-parity` born-red with `parity/parity.yml` all-`pending` **and the
  A-16 depth section in its schema from birth**; `check_compat_frozen` diffing the pinned compat
  artifacts; `manifest-validate` carrying **A-19 `check_escape_hatches`** from the first kernel
  PR.
- **Railway (owner-dependent — never block on it):** if the owner is present, project
  `superbot-next` per railway plan §4/R-3 (he pastes secrets, approves the plan/spend; sealed +
  reference variables; `EXTRA_OWNER_USER_IDS` goes in from day one per A-21/Q-0245). If he is
  not, **defer Railway whole** — nothing before CUT-1 (step 12) needs it; record the deferral on
  the run report. Per Q-0249: no spend caps yet — instrument spend telemetry instead
  (observation window, ~2 months).

### Definition of done

Both repos exist · kit repo CI green on its own suite · superbot-next: adoption committed,
`check --strict` green cold, six gates armed (parity red-by-design, everything else green) ·
CODEOWNERS + protections live · pinned-artifact import path documented (goldens/compat stay in
the old repo until step 11 — record where the new repo will read them from) · run report with
every ⚑ (subtree-vs-snapshot, governance home, Railway done/deferred) · this repo updated:
current-state S3 ▶ advances to step 9, consumer-pin note landed.

## 3. What NOT to do

- No K-band code (S1+ is the next session per §5 step 9 — one ultracode session per band).
- No golden import (step 11), no data anywhere near it (CUT-2).
- Never clone-as-base; never copy `disbot/` code into superbot-next "for reference" — the oracle
  stays in the old repo.
- Don't wire the trading repo (third, per Q-0247 rail-before-scale).
- Don't re-litigate anything in §11/§11b or the final review.

## 4. Owner-input checklist (the session proceeds without any of these; they gate only their own line items)

1. **GitHub access:** the kickoff session needs permission to create the two repos (or the owner
   pre-creates two empty private repos — 2 minutes — and grants the session access to them).
2. **Railway** (deferrable): login/secrets/plan approval when he wants the projects to exist.
3. Standing reminder (unrelated to this session): set `EXTRA_OWNER_USER_IDS` on the live bot's
   Railway service (Q-0245).

## 5. Paste-ready prompt

> You are a **Claude Fable 5** session at **`/effort ultracode`**. Read
> `docs/planning/rebuild-kickoff-steps-6-8-brief-2026-07-07.md` first — it is your full brief.
> Execute the canonical rebuild plan's §5 steps 6–8: create `superbot-next` AND extract
> `substrate-kit` to its own repo (Q-0247), bootstrap-adopt superbot-next from the kit repo,
> then arm the control plane (the six named gates, born-red parity with the A-16 depth schema,
> CODEOWNERS, protections; Railway only if I'm present — defer it otherwise, never wait).
> The old repo attaches read-only as the oracle — never clone it as a base. You operate under
> Q-0241: decide reversible calls yourself, flag every decision on the run report, silence = consent.
