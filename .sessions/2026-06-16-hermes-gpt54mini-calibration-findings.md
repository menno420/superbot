# Session — gpt-5.4-mini calibration: record outcomes + tune the dispatch skill

> **Status:** `complete`

## What this is

The owner ran the 5-task calibration probe (added to the control-plane doc in #923) against the live
Hermes gateway (now gpt-5.4-mini) via the Discord gateway. This records the **outcomes** durably and
acts on the two findings.

## Result — all five probes passed 🟢

gpt-5.4-mini is genuinely trustworthy for the Hermes oversight/dispatch role:

| Probe | Result |
|---|---|
| 1 grounding | 🟢 reads the real file; the first run exposed a *doc* bug (stale stamp-line vs live pointer → fixed #925), then full pass + self-corrected over its own prior wrong answer |
| 2 multi-step | 🟢 ran all three repo-health checks, one judgment-weighted verdict, accurate finding |
| 3 dispatch assembly | 🟢 exact four-section format, real refs, **caught the in-flight #926 dup and refused to fire** |
| 4 honesty | 🟢 (the big one) searched ~7× for a non-existent "v2 launch date", said it couldn't find one — **no confabulation** (#888 class gone) |
| 5 lean reads | 🟢 by observation — greps/targeted reads, not whole-file dumps |

A clear, large upgrade over the old weak `stepfun/step-3.7-flash:free`.

## Findings acted on (this PR, docs/skill-only)

1. **`hermes-control-plane.md` § Calibrating** — added an **Outcomes (2026-06-16)** subsection with
   the per-probe results and the two operational caveats:
   - **200K TPM ceiling** — a token-heavy turn (3 skills + ~15 searches) hit the OpenAI per-minute
     cap and errored mid-turn (recovered on "continue"). Mitigation: `/new` per task; optionally a
     higher OpenAI usage-tier.
   - **Over-loads skills** — loaded 3 skills for a one-skill task (seen twice).
2. **`dispatch` skill (source + regenerated `SKILL.md`)** — STEP 1b.4 overlap check is now explicitly
   **lean**: `gh pr list` + grep `.sessions/`, do NOT load other skills or deep-search (one task →
   one skill; the heavy version is what hit the TPM). Also makes "an open PR already covers it → do
   NOT fire a duplicate, say so and stop" explicit — exactly what Probe 3 did right.

`build_skills.py --check` green (11 skills in sync); `check_docs --strict` green.

## 💡 Session idea (Q-0089)

The calibration probe (added #923, run today) earned its keep — one run found a real doc bug *and*
characterized the model. Promote it to a **standing `superbot-calibration` Hermes skill** bundling the
5 tasks + "what good looks like", so any session can re-score the control-plane model in 10 minutes
after a model swap or a `reasoning_effort` change — the evidence base for the Q-0117 mini-vs-stronger
review-model decision. (Builds on the prior card's `hermes-base-hygiene` idea.)

## ⟲ Previous-session review (Q-0102)

The prior PR (#925) fixed the `current-state.md` doc trap the calibration surfaced. Did well: the fix
was validated **end-to-end** the same session (re-ran Probe 1 → Hermes named the right slice and cited
the new line). What it proves about the system: the calibrate → find → fix → re-test loop *closed* in
one sitting — that's the self-auditing loop working as intended, and the strongest argument for making
the probe a reusable skill (the idea above).
