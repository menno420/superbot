# 2026-06-30 — AI review-log answer loop (export → triage → presets)

> **Status:** `complete`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**PR:** [#1569](https://github.com/menno420/superbot/pull/1569) — AI review-log answer loop.
**Branch:** `claude/ai-answer-storage-plan-3fvdit`
**Run type:** manual (owner-directed)

## What this run did

Owner: *"I recently added a function for the AI to store corrected or wrong answers… find out
how that works and come up with a plan to make it answer the current listed questions."*

That "function" is the **AI answer review-log** (`ai_review_log`, #1494): it records every
question the bot got **wrong** (a 👎 / correction-reply) or **couldn't answer** (`unknown`), with
the redacted question + answer. But nothing turned that backlog *back* into correct answers, and
the rows are only viewable via `!aireview list` in Discord — the **prod Postgres** the sandbox
can't read (I flagged this; "you should be able to see them" isn't true from the code env).

Two owner decisions (AskUserQuestion, 2026-06-30):
- **Answer mechanism = Both** — root-cause fixes + regression evals **and** a runtime preset layer.
- **Getting the backlog = build `!aireview export` then paste** — so the owner exports + pastes.

Built the **machinery** for both, in one PR (PR1 + PR2). PR3 (working the actual backlog) is
gated on the owner's export paste.

## Shipped (PR #1569)

**PR1 — surface the backlog + the dev-loop bridge (low-risk):**
- `!aireview export [unknown|correction|all]` → a JSON file attachment (already redacted at
  write time). New export-grade query past the 25-row cap + `ai_review_log_service.export()`.
- `scripts/ai_review_triage.py` — group by task/reason_code, dedupe by normalized question,
  classify each as **preset** (a correction exists) / **fix** (grounding-route gap) / **infra**
  (provider outage), `--scaffold` prints probe/preset stubs. Generalizes the BTD6 corpus loop
  (`tests/evals/btd6_corpus.py`) to any task.
- `utils/ai_text_normalize.py` — the shared question key (triage dedup == preset lookup), now
  strips Discord mention/emoji tokens so the stored raw question and the runtime mention-stripped
  text key the same preset.
- `docs/operations/ai-review-backlog-runbook.md` + an ai-folio pointer.

**PR2 — the vetted answer-preset layer (the "bot answers it itself, zero API" half):**
- Migration 102 `ai_answer_presets` + `utils/db/ai_presets.py` (exact-match by normalized key).
- `services/ai_preset_service.py` — audited `set_preset`/`remove_preset` (emit
  `audit.action_recorded`) + a **fail-safe** `lookup` for the hot path.
- `natural_language_stage` short-circuit (after routing, before feature-facts/gateway): an exact
  match is served verbatim with **no model call**; the Q&A is still `remember_answer`'d so a 👎 on
  a preset is captured. **Byte-identical when the table is empty** (pinned by a test).
- `!aireview preset add/from/list/remove` (`from <entry_id>` turns a logged question straight into
  a preset); `ownership.md` rows; guild teardown; regenerated dashboard/site artifacts.

**Friction → guard (free lane):** wired `check_generated_artifacts_fresh.py --strict` into
`check_quality --check-only` so dashboard/site drift is caught in the fast pre-push pass.

Tests: 60 new. Full CI mirror green (`check_quality --full`: 13,184 + artifacts passed, 0 failed);
`check_architecture --mode strict` 0 errors.

## How it works (the loop)

`!aireview export` → `scripts/ai_review_triage.py` → **fix** (root-cause grounding/data/routing +
a regression probe) *or* **preset** (`!aireview preset from <id> <answer>`) → `!aireview resolve`.
Runbook: `docs/operations/ai-review-backlog-runbook.md`.

## Decisions made alone (owner should be aware)

- **Presets are exact-match only** (normalized key, no fuzzy/semantic matching). A preset serves
  with zero model in the loop, so a false match would confidently serve the wrong answer; the cost
  (a paraphrase needs its own preset) is acceptable for v1.
- **`normalize_question` strips Discord tokens** (mentions/emoji) — required for key consistency
  (the review log stores raw text *with* the bot mention; the runtime sees it stripped).
- **Preset short-circuit fires before feature-facts** — the cheapest answer wins; a preset is an
  operator override of even the deterministic/grounded paths (operator authored it deliberately).
- **Preset answers are not redacted** (operator-authored, not user content). The audit row caps
  prev/new value snippets at 200 chars.

## Flagged for maintainer (weak point / unverified)

- **No live Discord run** — the export attachment, the preset short-circuit, and a real 👎→log are
  unverified on a live bot (sandbox has no provider key / prod DB). Verify on the next prod walk:
  `!aireview export`, then `!aireview preset add "<a question the bot flubs>" <answer>` and ask it.
- **PR3 is yours to unblock**: run `!aireview export`, paste me the JSON, and I'll work the backlog
  (root-cause fixes + presets + probes, then `!aireview resolve`).
- **Migration 102 applies on next boot/auto-deploy** (merge = deploy, Q-0193) — no manual step.

## 💡 Session idea (Q-0089)

[`review-log-frequency-preset-suggestions-2026-06-30.md`](../docs/ideas/review-log-frequency-preset-suggestions-2026-06-30.md)
— flip the loop from operator-pull to **bot-push**: when the same normalized question recurs as an
`unknown` N times in a window, nudge the review channel ("asked 4×, author a preset?"). Turns the
log into a **demand-ranked** worklist; reuses the existing redacted rows + the new shared
`normalize_question` key; no new table. Dedup-checked vs `ai-self-curated-memory-notebook` (that's
AI self-writing notes; this is frequency analytics over the operator log).

## ⟲ Previous-session review (Q-0102)

Previous = the Project Moon combat-mechanics layer (#1549). **Did well:** exemplary scope
discipline — shipped the *stable, hand-authorable* combat **rules** and explicitly deferred the
fragile per-unit numbers, and reused the already-wired grounding seam so the AI path barely
changed. **Missed / system improvement:** like #1494 and this session, it added runtime surface
(`!pm mechanic` + grounding triggers) and rode the same **add-a-surface ripple**. This session hit
that ripple concretely — the dashboard/site JSON drifted and was only caught by the 3-min full
suite, exactly the friction #1494's Q-0089 (`check_new_extension.py`) predicted and that's *still
unbuilt*. Rather than re-propose it, I shipped the cheapest slice of it now: the artifact-freshness
guard is in the fast pre-push pass (above), so the next session surfaces this ripple in ~2s, not
3min. The recurring "new surface → silent generated-artifact drift" class is now one tier cheaper
to catch.

## 🛠 Friction → guard

- **Friction:** the new commands drifted `dashboard.json` / `site.json`, surfaced only by the full
  3-min pytest suite (`test_committed_artifacts_are_currently_fresh`). **Guard shipped now (free
  lane, Q-0194):** `check_generated_artifacts_fresh.py --strict` now runs inside
  `check_quality --check-only`, so the drift is caught in the fast pre-push pass. The CI test
  remains the hard gate; this just moves discovery earlier.

## ⚑ Self-initiated

None unprompted — owner-directed feature (the two AskUserQuestion answers set the direction). The
contained implementation calls are under *Decisions made alone* for ratification; the
artifact-freshness guard is a free-lane friction→guard (Q-0194), not a new owner rule.

## Doc audit (Q-0104)

`check_current_state_ledger.py --strict` exit 0 (6 PRs of benign newest-merge lag, recorded by the
next recon — not drift). `check_docs --strict` green (new runbook + idea file reachable).
`ownership.md` updated (preset service + table, sole-writer rows). No new owner *rules* (the two
AskUserQuestion answers are feature-config) — router untouched. Did **not** add #1569 to
Recently-shipped (convention: merged-PRs-only; the next session reconciles the merge).
