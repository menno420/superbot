# AI review-log backlog — the answer loop (runbook)

> **Status:** `reference` — the operator + agent procedure for turning the AI answer
> review-log (`ai_review_log`, #1494) into correct answers. Source + merged PRs win.
>
> **Subsystem:** ai · **Reads:** `docs/subsystems/ai.md`, `docs/btd6/qa-accuracy-corpus-2026-06-27.md`

## What this closes

The bot records every question it got wrong or couldn't answer in `ai_review_log`
(`kind='unknown'` — it engaged but couldn't answer; `kind='correction'` — a user 👎-reacted
or replied-with-a-fix). That capture half shipped in #1494. This runbook is the **other
half**: how that backlog becomes correct answers — through both a **root-cause fix +
regression probe** (the durable, data-backed path) and a **vetted answer preset** (the
zero-API path for recurring / opinion questions).

## The loop

```
  !aireview export  →  ai_review_triage.py  →  fix (root-cause) | preset  →  probe  →  !aireview resolve
```

### 1 — Export the backlog (operator, in Discord)

```
!aireview export                # all unreviewed entries, both kinds → a JSON file
!aireview export unknown        # only didn't-know entries
!aireview export correction     # only user corrections
!aireview export all            # include already-resolved entries too
```

The dump is **already redacted** (text was scrubbed through the outbound redactor at write
time and capped at 2000 chars), so it is safe to paste. Download the JSON or copy its
contents.

### 2 — Triage (agent / dev, offline)

```
python3.10 scripts/ai_review_triage.py export.json
python3.10 scripts/ai_review_triage.py export.json --scaffold   # + probe/preset stubs
```

The triage script groups by `task` / `reason_code`, dedupes by normalized question
(`utils.ai_text_normalize` — the *same* key the preset lookup uses), and assigns each unique
question a suggested action:

| Action | Trigger | What to do |
|---|---|---|
| `preset` | a user **correction** exists | The right answer is already in hand — author a vetted preset (step 3a). |
| `fix` | `unknown` + grounding / route gap | Root-cause fix + a regression probe (step 3b). |
| `infra` | `provider_unavailable` / `errored` | A provider outage, **not** a knowledge gap — no action unless it recurs. |

### 3a — Author a preset (the zero-API path)

For recurring questions, opinion questions, or anything with no clean data fix, store the
exact vetted answer so the bot serves it directly with **no model call**:

```
!aireview preset from <entry_id> <the correct answer>   # reuses the logged question text
!aireview preset add "<question>" <the correct answer>  # author from scratch
!aireview preset list                                   # review what's stored
!aireview preset remove <preset_id>                     # un-promote (cheap, reversible)
```

Presets are keyed on the normalized question (exact match, no fuzzy matching — a false match
would confidently serve the wrong answer), audited, and **byte-identical when the table is
empty** (no preset → the normal answer path runs unchanged).

### 3b — Root-cause fix + regression probe (the durable path)

For data-backed questions, fix where the answer actually comes from — don't just paper over
it with a preset:

- **grounding / retrieval gap** (data exists but isn't retrieved) → add a trigger token /
  alias / fact (the BTD6 `damage_types.json` + interaction-service pattern).
- **data gap** (the fact isn't in the dump) → add curated, sourced data.
- **routing gap** (the question didn't route to the right task) → fix `ai_task_router`.
- **guard over-refusal** (a faithfulness floor rejected a correct answer) → tune the guard.

Then **pin it** so it can't regress: add a probe to `tests/evals/btd6_corpus.py`
(`GroundingProbe`) for BTD6, or `tests/evals/cases.py` (`EvalCase`) for general questions.
`--scaffold` prints the stubs. This is the same loop that fixed the 2026-06-27 BTD6
QA-accuracy misses — see `docs/btd6/qa-accuracy-corpus-2026-06-27.md`.

### 4 — Resolve

```
!aireview resolve <entry_id>    # mark each handled entry reviewed
```

Resolved entries drop out of the default `!aireview export` (which exports unreviewed only),
so the next export is the *remaining* backlog.

## Why both paths

A preset makes one exact question answer correctly *immediately* and cheaply, but it doesn't
generalize — a paraphrase still misses. A root-cause fix generalizes (and a probe keeps it
fixed) but needs the data to exist. Use a preset to stop the bleeding on a hot question; use
a root-cause fix to actually teach the bot. The triage script's `preset` vs `fix` split is
exactly this call, made per question.

## Files

| Piece | Where |
|---|---|
| Capture (didn't-know + corrections) | `services/ai_review_log_service.py`, `cogs/ai_review_cog.py`, migration `100_ai_review_log.sql` |
| Export command | `cogs/ai_review_cog.py` (`!aireview export`) → `services.ai_review_log_service.export` |
| Triage bridge | `scripts/ai_review_triage.py` |
| Shared question key | `utils/ai_text_normalize.py` |
| Preset layer | `services/ai_preset_service.py`, `utils/db/ai_presets.py`, the `natural_language_stage` short-circuit |
| Regression probes | `tests/evals/btd6_corpus.py`, `tests/evals/cases.py` |
