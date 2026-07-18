# docs/eap/ — Claude Code Projects EAP record

> **Status:** `reference` — entry point for the EAP (Early Access Program) corpus in this
> repo. The running incident journal and the older planning-side EAP docs live in
> [`docs/planning/`](../planning/projects-eap-evaluation-log.md) (files prefixed
> `projects-eap-*`). Newest first within each group.

## Follow-up + de-wall evidence (2026-07-18)

- [`2026-07-18-followup-email-draft.md`](2026-07-18-followup-email-draft.md) — **draft of the
  next Anthropic follow-up email** (owner sends): Part 1 owner voice + Part 2 paste-ready. New
  evidence, not a new ask — the venue-scoped guard, the agent-memory wall propagation + CI
  antidote, the stale-text-outranks-live-instruction failure, and the trigger-tool
  forced-approval finding (no owner setting suppresses it; ~1,900 tombstones as the cost;
  session-ender v3.8 as the agent-side mitigation).
- [`2026-07-18-dewall-capabilities-evidence.md`](2026-07-18-dewall-capabilities-evidence.md) —
  the evidence pack behind that email, every claim linked to a public PR: venue-scoped
  capability proof (2,115 branch deletes, reversible probes), the de-wall repair (18 repos +
  templates + the `check_no_false_walls` CI guard), the precedence rule, post-EAP recreation
  prep, and §5 the trigger-tool forced-approval finding + the v3.8 ender verified live.

## Permission classifier — consolidated (2026-07-16)

- [`anthropic-email-4-classifier-regression-sent-2026-07-16.md`](anthropic-email-4-classifier-regression-sent-2026-07-16.md)
  — **archived record of the 4th Anthropic email (SENT 2026-07-16 ~21:12Z)**: the auto-mode
  classifier-regression report. Part 1 (owner) + Part 2 (agent, six findings), the scoped-grant
  ask, the changelog correlation (v2.1.178 / v2.1.210), and an "open threads" list of the
  follow-ups still pending (attachment reply, feature-release reply, new-vs-old project test,
  cross-project-messaging email, post-EAP interactivity note, kit fresh-repo re-test).
- [`permission-classifier-findings-consolidated-2026-07-16.md`](permission-classifier-findings-consolidated-2026-07-16.md)
  — **one durable home for the whole permission-problem picture**: the stable 2026-07-08 boundary,
  the 2026-07-15→16 regression (~30 denials · 8 projects · 36h · 10 classes), the *session-not-action*
  mechanism and its four consequences (candor hardens enforcement; the self-documentation recursion;
  the collateral cascade), the two compounding factors, the two-layer prompt finding, the scoped-grant
  proposal, and the state of the Anthropic correspondence. Consolidates (does not replace) the probe
  report, the evaluation journal, the sent emails, the `CAPABILITIES` ledgers, and the 2026-07-16
  classifier-regression evidence pack; each claim is source-mapped in §9.

## Closeout (2026-07-14 — EAP final day)

- [`../eap-closeout-walkthrough-2026-07-14.md`](../eap-closeout-walkthrough-2026-07-14.md) —
  **the seat closeout walkthrough** (ORDER 006 b): what the hub did during the EAP, current
  state + exact verify commands, the OWNER ACTIONS checklist (every pending click with a
  bolded recommendation + VERIFY step), a 5-minute tour, and the handoff batons.
- [`../audits/eap-project-audit-2026-07-14.md`](../audits/eap-project-audit-2026-07-14.md) —
  the hub seat's EAP project audit (11-section fleet format: measured scale, verbatim
  permission walls, ranked pains with FLEET-FIX/ANTHROPIC/ACCEPTED dispositions, honest gaps).

## Gen-2 night reviews (2026-07-11 →)

- [`fleet-cleanup-audit-2026-07-13.md`](fleet-cleanup-audit-2026-07-13.md) — owner-directed
  cross-repo audit + PR-cleanup pass over all 20 repos (EAP final night), run complementary
  to the owner's own live fleet-manager ORDER 045 dispatch: direct cleanup in superbot (8
  dependabot PRs merged, 2 root-cause CI bugs fixed — a codeql-action version split and a
  tool-pin three-places violation) and gba-homebrew (4 stale PRs closed as superseded, 5
  real Tiltstone-stack PRs flagged for a coordinator rather than blind-conflict-resolved),
  plus an 18-repo parallel audit (one subagent per repo) that merged/closed zero PRs
  inappropriately and surfaced 10 cross-cutting fleet patterns (worklist staleness, dead
  `project.index.json` scaffolding, control-bus size walls, the born-red false-positive
  class, a `list_pull_requests` "merged" boolean quirk, and more).
- [`night-review-2026-07-12.md`](night-review-2026-07-12.md) — owner-directed fleet night
  review of the 2026-07-12 batch — **the trigger-scheduler incident**: primary-evidence
  timeline (~02:30–08:00Z degradation: 9 dropped `send_later` one-shots, 2 wedged crons,
  partial 08:0x catch-up), per-seat digest (manager's prompts-v3.2 + 12 relocation ORDERs
  led the night; Venture Lab dark, kit-lab manually re-fired), the Q-0265 failsafe doctrine
  validated in production (coverage must exist *and* be alive), the org-policy discovery that
  sibling sessions cannot revive each other via triggers, new lessons + fix-first +
  owner-action queue.
- [`anthropic-email-2-draft-2026-07-11.md`](anthropic-email-2-draft-2026-07-11.md) — the
  **second Anthropic email** (in progress, owner sends): Part 1 = a MOCK in Menno's voice
  built from his real documented/this-session words for him to rewrite; Part 2 = the agents'
  technical companion updated to the full arc (gen-1 → autonomous fleet → tonight), incl. the
  merge-classifier context-sensitivity finding, the model-attribution + routine-repo bugs,
  the owner-click backlog; + a curated screenshot shot-list. Supersedes the gen-1-only
  `gen1-wrapup-email-final-candidate.md` as the send-candidate. Reply on Gmail thread
  `19f41cd2e5380bb3`; window through 2026-07-14.
- [`screenshots-2026-07-11/index.md`](screenshots-2026-07-11/index.md) — the curated figure
  set for the second email: 16 keepers triaged from 64 uploaded screenshots (fig-NN names +
  captions mapped to the email's figure slots); as of 2026-07-12 also holds the recovered
  model-mismatch trio (15a/b/c) + fig-17, formerly phone-only.
- [`screenshots-2026-07-12/index.md`](screenshots-2026-07-12/index.md) — the
  scheduler-incident figure set (figs 20–32): curated from the owner's two raw uploads
  (PRs #2023/#2024, 27 files reviewed one by one; 22 kept, 5 dispositioned with reasons) —
  the 8-seat grid, the dropped daily Routine's config, the operator's before/after routine
  fix, a lane's first-person dropped-tick account, the Auto-mode allowlist-not-honored
  prompt family, plus tier-2 story material for the review site.
- [`night-review-2026-07-11.md`](night-review-2026-07-11.md) — owner-directed independent
  night review of the whole fleet (2026-07-10 18:00Z → 07-11 11:40Z): per-lane digest across
  13 active lanes (3 survey agents), what's genuinely valuable / playable, the two evidenced
  platform bugs (`add_repo` "Unauthorized Persistence" denials + configured-vs-actual model
  mismatch), the fix-first list, the owner-action queue (routine repo-attach + model set +
  unblock-value clicks), lessons, and what-went-well.

## Gen-1 wrap-up (2026-07-09 → 10)

- [`../planning/round3-launch-pack-2026-07-10.md`](../planning/round3-launch-pack-2026-07-10.md) —
  the round-3 (gen-3 prep) launch pack: manager brief, per-lane continuation prompts, games
  wave, Codex review prompts, owner decision sheet (§4b records the Q-0259 owner rulings),
  standing autonomous core (§5), fleet-watching guide.
- [`eap-program-review-2026-07-10.md`](eap-program-review-2026-07-10.md) — owner-directed deep
  review of the whole EAP period (07-07 → 07-10): day-by-day story, verdicts, root-cause log,
  the 10 structural findings, the centralization agenda, and the consolidated next-action queue.
- [`fleet-overnight-review-2026-07-10.md`](fleet-overnight-review-2026-07-10.md) — owner-directed
  morning-after review of the launch night itself (all 13 repos, one subagent per lane):
  headline verdict, per-repo table, ender-compliance exceptions, ranked findings, the
  consolidated cross-fleet owner-action queue.
- [`gen1-grand-review-2026-07-09.md`](gen1-grand-review-2026-07-09.md) — the independent
  fleet-wide verification: old-vs-new gap map, open-PR sweep, email fact audit, wind-down
  audit, gen-2 synthesis, efficiency verdict, ⚑ owner actions.
- [`gen1-wrapup-email-final-candidate.md`](gen1-wrapup-email-final-candidate.md) — the
  SEND-READY wrap-up email candidate (Part 1 = owner's slot). Supersedes:
- [`gen1-wrapup-email-draft-v2-2026-07-09.md`](gen1-wrapup-email-draft-v2-2026-07-09.md) —
  draft v2 (superseded as send-candidate; kept for provenance).
- [`gen1-gen2-doctrine-review-2026-07-10.md`](gen1-gen2-doctrine-review-2026-07-10.md) —
  independent doctrine comparison, fleet-manager vs superbot (parallel session).
- [`fleet-winddown-audit-2026-07-09.md`](fleet-winddown-audit-2026-07-09.md) — independent,
  adversarial audit of the 7 wind-down lanes' succession packages + the `venture-lab` seed +
  `fleet-manager`'s ping-test report: 21/21 spot-checked incidents verified against live
  GitHub PR/commit/CI data, zero fabrication found, 5 real (non-fabrication) inaccuracies
  logged including a false "NO ACK" claim inside fleet-manager's own report. Complements
  `gen1-grand-review-2026-07-09.md` §5 (structural completeness across all 6 repos) with
  deep, per-incident evidence verification on the 7 wind-down lanes + seed + ping-test.

- [`superbot-next-runtime-review-2026-07-10.md`](superbot-next-runtime-review-2026-07-10.md) —
  external (Codex/Sol) runtime review of superbot-next bands 1–5: warn-escalation fix confirmed,
  `end_access` compensation gap confirmed; Claude verification addendum adds the missed
  `moderation.timeout` same-class instance.
- [`codex-review-round-verification-2026-07-10.md`](codex-review-round-verification-2026-07-10.md) —
  Claude's ground-truth verification of the three Codex review PRs (#1940/#1941/#1942):
  scores, the missed `moderation.timeout` compensation gap, and an independent
  assessment of the gen-1/gen-2 program work.
- [`hostile-audit-checking-the-checkers-2026-07-10.md`](hostile-audit-checking-the-checkers-2026-07-10.md) —
  external (Codex/Sol) hostile re-verification of the grand review + overnight review: 12/15
  claims confirmed, the superbot-next "~20 PRs" narrative refuted; Claude addendum re-verifies
  5 claims by a second method (all exact).

## Fleet reviews and instruments (2026-07-09)

- [`fleet-manifest.md`](fleet-manifest.md) — **superseded 2026-07-11**: now a pointer stub;
  canonical fleet/seat state is the fleet-manager generated roster
  (`menno420/fleet-manager` `docs/roster.md`, fm PR #59; superbot PR #1974).
- [`external-review-pack-2026-07-09.md`](external-review-pack-2026-07-09.md) — single
  audit entry point for outside reviewers (no GitHub auth needed).
- [`fleet-review-2026-07-09.md`](fleet-review-2026-07-09.md) — independent cross-repo
  review (first-party re-run of superbot-next's suite).
- [`fleet-quality-review-2026-07-09.md`](fleet-quality-review-2026-07-09.md) —
  four-reviewer honesty/quality audit of one day's fleet output.

## Earlier

- [`campaign-self-audit-2026-07-08.md`](campaign-self-audit-2026-07-08.md) — coordinator
  memory of the 3-wave campaign graded against git (≈0.98 precision).

## Retro (protocol-canonical location: `docs/retro/`)

- [`../retro/self-review-2026-07-09.md`](../retro/self-review-2026-07-09.md) — the
  coordinator lane's own answers to the #1901 fleet retro question set (written
  2026-07-10, assembled from this corpus) — the 10th and final lane's answers, closing
  the gap the grand review §5 flagged. Question set:
  [`../planning/fleet-retro-questions-2026-07-09.md`](../planning/fleet-retro-questions-2026-07-09.md).
