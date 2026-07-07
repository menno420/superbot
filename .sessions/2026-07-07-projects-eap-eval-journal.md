# 2026-07-07 — Projects-EAP evaluation journal (guidebook-prescribed) + seed entries

> **Status:** `in-progress`
> **Model:** Fable 5 (worker session under the SuperBot Project coordinator) · **Governance:** Q-0241 never-wait applies

## What is about to happen

Create `docs/planning/projects-eap-evaluation-log.md` exactly as the evaluation guidebook
(`docs/planning/projects-eap-evaluation-guidebook-2026-07-07.md` §2) prescribes, and seed it
with the coordinator's five onboarding observations. Docs-only; no runtime code.

## What shipped (PR #1820)

- **`docs/planning/projects-eap-evaluation-log.md`** — the second-mandate journal, exactly per
  guidebook §2: verbatim entry template, the seven §3 axes named, §4 integrity rules pointed to,
  append-at-bottom structure (no shared top anchor). Seeded with the coordinator's five
  onboarding observations (2× use-case fit, reliability/completion, coordinator judgment,
  proactivity) reformatted into the template with substance kept faithful.
- **+1 lived entry from this session** (per the guidebook's log-both-directions rule): the
  worker-tier flow (full file/shell/git/MCP toolset, zero permission prompts, born-red →
  auto-merge end-to-end) as the "helped" contrast to seed #1's coordinator-side tool gap.
- **+2 coordinator-relayed entries added mid-session, pre-flip** (permission-probe session,
  both ~22:38Z): fail-fast structured auto-denials at unattended permission boundaries
  (reliability/completion, helped) and the missing scheduled-wake primitive + missing direct
  coordinator→session channel (use-case fit, friction). Relayed observations, reformatted
  faithfully — same verification caveat as the five seeds.
- **`docs/planning/README.md`** — one row for the guidebook + journal in the rebuild sector
  table (the guidebook shipped in #1811 with no index row while its siblings
  activation-plan/kickoff have rows — spotted drift, fixed on sight per Q-0166); "Last updated"
  bumped; one clarifying sentence in "Adding / retiring a plan" for non-`plan` companions
  (`reference`/`living-ledger` docs homed in `docs/planning/`).
- **Idea filed:** `docs/ideas/session-start-staleness-banner-2026-07-07.md` + README index entry
  (see 💡 below).

## Context delta (reflection interview)

- **Needed but not pointed to:** nothing — the task prompt named the guidebook and the
  conventions directly; `.sessions/README.md` supplied the run-report/telemetry shape.
- **Pointed to but didn't need:** `docs/owner/claims/README.md` (the CLAUDE.md claim rule alone
  was sufficient for a single-file claim).
- **Discovered by hand:** `check_docs --strict` enforces a badge-token whitelist — `living` is
  not a valid badge (`living-ledger` is); found by running the checker, not documented anywhere
  I was routed. Also: the planning README's homing rule only covers `plan`-badged docs; the
  non-`plan` companion case was unwritten (now written — one sentence added).
- **Decisions made alone:** (1) badge `living-ledger` for the journal; (2) adding index rows for
  guidebook+journal though the written rule didn't require them (sibling-row precedent);
  (3) appending one lived worker-tier entry beyond the five seeds under the guidebook's
  log-both-directions rule; (4) the one-sentence homing clarification. All reversible docs calls.
- **Flagged for maintainer:** the journal's five seeds are the coordinator's observations
  relayed through the spawn prompt — I reformatted faithfully but could not independently verify
  the coordinator-side facts (e.g. the ignored run-synchronously flag); they're marked with the
  coordinator's own refs.
- **One docs change that would have helped most:** a badge-token list somewhere findable
  (currently only discoverable by running `check_docs` or reading its source) — small, left as a
  note here rather than filed; the checker's error message does list the allowed tokens, which
  is arguably enough.
- **🛠 Friction → guard:** the invalid-badge trip was caught pre-push by running
  `check_docs --strict` locally — the existing checker IS the guard; nothing new needed. No
  other friction hit.

## ⟲ Previous-session review (Q-0102)

The understand-and-reflect-rule session (#1806, same day) was a model of tight scoping: it
applied the owner's live directive without over-adopting the kit's whole stance system, and its
context delta caught a real doc/reality mismatch (section-marker prose vs. literal names). What
it left: its own review re-flagged the planning-README homing-convention split for the *third*
time and said the next session touching that file should resolve it rather than re-flag.
**Improvement executed, not re-flagged:** this session touched `docs/planning/README.md` and
wrote the missing convention down — non-`plan` companions get a row only while they're active
program artifacts, else inbound links suffice ("Adding / retiring a plan" section). If the split
the earlier sessions meant was a different one (plan-index row vs. *sector-file* entry), that
half remains open — but the concrete instance class that kept recurring (reference/living-ledger
docs with no homing rule) is now settled in writing.

## 💡 Session idea (Q-0089)

[`session-start-staleness-banner-2026-07-07.md`](../docs/ideas/session-start-staleness-banner-2026-07-07.md) —
a cheap session-start staleness check (`git fetch` + `HEAD..origin/main` count → loud banner).
Worth having because the coordinator's 7-PR-stale container (journal seed #2) is a silent
wrong-answers failure mode, and grep confirms nothing in `scripts/claude_session_start.sh`
detects it today. Dedup-checked against `docs/ideas/` + roadmap: no existing capture.

## 📤 Run report

- **Did:** created the guidebook-prescribed Projects-EAP evaluation journal + 5 coordinator seed
  entries + 1 lived worker entry; fixed the guidebook's missing plan-index row · **Outcome:** shipped
- **Shipped:** #1820 — journal + seeds, planning-README rows + homing sentence, staleness-banner idea
- **Run type:** `manual` (coordinator-dispatched worker under the SuperBot Project)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** (1) planning-README index rows for guidebook+journal + the non-`plan`
  homing sentence — spotted-drift fix + third-flag resolution (Q-0166 / prior session's carry-forward);
  (2) one extra journal entry beyond the 5 seeds — the guidebook's own log-both-directions rule
  applied to this session's lived flow. Both docs-only, reversible.
- **📊 Model:** Fable 5 · standard · docs-only (journal bookkeeping)
- **↪ Next:** journal is live — coordinator + sessions append as things happen; by Friday
  2026-07-10 fill the activation-plan §4 feedback template from it (flag empty slots honestly).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged | 1 (#1820, auto-merge on card flip) |
| CI-red rounds | 0 unexpected (born-red gate holds by design) |
| Repo-rule trips | 1 (invalid badge token `living`, caught locally pre-push) |
| New ideas contributed | 1 (session-start-staleness-banner) |
| Ideas groomed | 0 (grooming pass skipped — bounded worker task; backlog untouched by design) |
