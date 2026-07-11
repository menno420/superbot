# docs/eap/ — Claude Code Projects EAP record

> **Status:** `reference` — entry point for the EAP (Early Access Program) corpus in this
> repo. The running incident journal and the older planning-side EAP docs live in
> [`docs/planning/`](../planning/projects-eap-evaluation-log.md) (files prefixed
> `projects-eap-*`). Newest first within each group.

## Gen-2 night reviews (2026-07-11 →)

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
  captions mapped to the email's figure slots), plus the model-mismatch phone-shot trio.
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
