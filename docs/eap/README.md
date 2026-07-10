# docs/eap/ — Claude Code Projects EAP record

> **Status:** `reference` — entry point for the EAP (Early Access Program) corpus in this
> repo. The running incident journal and the older planning-side EAP docs live in
> [`docs/planning/`](../planning/projects-eap-evaluation-log.md) (files prefixed
> `projects-eap-*`). Newest first within each group.

## Gen-1 wrap-up (2026-07-09 → 10)

- [`../planning/round3-launch-pack-2026-07-10.md`](../planning/round3-launch-pack-2026-07-10.md) —
  the round-3 (gen-3 prep) launch pack: manager brief, per-lane continuation prompts, games
  wave, Codex review prompts, owner decision sheet, fleet-watching guide.
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

## Fleet reviews and instruments (2026-07-09)

- [`fleet-manifest.md`](fleet-manifest.md) — living Project registry (manager-maintained).
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
