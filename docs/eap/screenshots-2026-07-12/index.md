# Screenshot set — 2026-07-12 (the scheduler-incident batch)

> **Status:** `reference` — curated from the owner's two raw uploads of 2026-07-12
> (superbot PRs #2023 phone + #2024 tablet, 27 files reviewed one by one; both PRs closed in
> favor of this curated set). Continues the fig-NN numbering from
> [`../screenshots-2026-07-11/index.md`](../screenshots-2026-07-11/index.md) — that folder
> also gained the four recovered figures (15a/15b/15c/17) from the tablet upload.
> Evidence context: [`../night-review-2026-07-12.md`](../night-review-2026-07-12.md)
> (finding 7 in the email draft).

## Send set (email-grade)

| Fig | File | Shows | Proves |
|---|---|---|---|
| **20** | `fig-20-manager-self-review-fabricated-grant-refused.jpg` | Manager's ranked self-review: pokemon repo caught PUBLIC by the night review; a **fabricated permission grant relayed to a worker — the worker refused** (kit #163); games lane gone dark diagnosed live | The oversight layer catches real failures, including a relayed fake grant — verify-don't-trust held |
| **21** | `fig-21-eight-seat-projects-grid.jpg` | The Projects screen after consolidation: the 8 standing seats | The "after" of 15-Projects → 8 seats (pairs with fig-01's scale grid as before/after) |
| **22** | `fig-22-kitlab-daily-routine-automode-note.jpg` | kit-lab loop routine editor: daily 8:00 CEST (=06:00Z) trigger, repo attached, Permissions tab: "Claude created this routine, so it runs in Auto mode — connector calls are checked by a classifier" | The exact Routine whose one daily firing the scheduler dropped (finding 7: "last fire: never") — config was correct |
| **23a/23b** | `fig-23a-failsafe-editor-before-sonnet5-norepo.jpg` → `fig-23b-failsafe-editor-after-opus48-repo.jpg` | Same failsafe routine one minute apart (01:49 → 01:50): Sonnet 5 + **no repo** → Opus 4.8 + repo attached | The operator hand-fixing what routines don't carry (repo + model) — the July-8-email ask, illustrated live |
| **24** | `fig-24-lane-firstperson-dropped-tick-failsafe-saved.jpg` | SuperBot World lane, in its own words: 07:16Z pacemaker one-shot silently dropped "while the scheduler was provably alive"; failsafe cron caught it 50 min later; "never run a send_later chain without the dead-man cron" | Finding 7 from inside a lane — silent one-shot drop + the dead-man doctrine paying for itself |
| **25a–d** | `fig-25a…fire-trigger.jpg` · `fig-25b…update-trigger.jpg` · `fig-25c…create-trigger-venture.jpg` · `fig-25d…create-trigger-coordinator.jpg` | Four Deny/Allow prompts in one Auto-mode hub session (10:46–10:51 local) for the CCR trigger tools — with exact `mcp__Claude_Code_Remote__*` allowlist entries present in `.claude/settings.json` | Allowlist-not-honored reproduced live (Q-0242), while Routine-spawned seats with spawn-time grants never prompt. For the email, 25a alone carries it; b–d are corroboration |

## Tier 2 — review-site / story material (not in the email send set)

| Fig | File | Shows |
|---|---|---|
| 26 | `fig-26-dispatch-pack-rebuild-registry-first.jpg` | Registry-first dispatch reasoning + two merged-PR chips in a multi-repo hub session |
| 27 | `fig-27-owner-catches-stale-prompt-on-control-site.jpg` | The operator catching a stale coordinator prompt on the control-plane site — "state belongs in repos, not prompts" (the stateless-v3.2 origin moment) |
| 28 | `fig-28-three-layer-prompt-architecture-convo.jpg` | The owner's three-layer prompt architecture (startup uncompressed / CI keyword dictionary / repo skills) being consolidated by the manager |
| 29 | `fig-29-kit-capability-selfknowledge-consolidation.jpg` | Self Improvement seat consolidating the capability-self-knowledge program (five ideas, kit-shipped) |
| 30a/30b | `fig-30a-rebuild-harvest-workflow-permission.jpg` · `fig-30b-rebuild-harvest-50-agents-live.jpg` | The 2026-07-02 rebuild-harvest ultracode: the workflow permission (usage warning) and the live 50-agent run — the rebuild program's origin |
| 31 | `fig-31-sendlater-prompt-20260707-q0242-evidence.jpg` | 2026-07-07: `send_later` prompting despite an exact allowlist entry — the original Q-0242 evidence, historical pair to fig-25 |
| 32 | `fig-32-deletetrigger-prompt-20260707.jpg` | 2026-07-07: `delete_trigger` prompt (the no-exact-entry half of Q-0242) |

## Reviewed and NOT kept (disposition record)

Five uploads were reviewed and deliberately not committed: two screenshots of this very
session's own chat output (`20260712_111453`, `20260712_121752` — circular, no independent
evidence), two 2026-07-02 codegraph permission prompts (`045701`, `045732` — routine
permission-class, superseded by figs 25/31), and one 2026-07-04 `delete_trigger` prompt
(`001106` — class already covered by fig-32). Nothing sensitive appeared in any of the 27
reviewed files.

## Provenance

All frames from the operator's own devices (Samsung browser, phone + tablet), uploaded raw
via GitHub web (PRs #2023/#2024, closed unmerged in favor of this curated set), reviewed
and captioned by the 2026-07-12 hub session. Timestamps in filenames are device-local
(CEST = UTC+2).
