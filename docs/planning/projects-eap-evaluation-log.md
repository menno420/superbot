# Projects-EAP evaluation journal

> **Status:** `living-ledger` — append-only observation log for the Claude Code Projects evaluation
> (the SuperBot Project's second mandate). **Prescribed by:**
> [`projects-eap-evaluation-guidebook-2026-07-07.md`](projects-eap-evaluation-guidebook-2026-07-07.md)
> (§2 entry shape · §3 axes · §4 integrity rules — read it before appending). Companions:
> [product review](projects-eap-product-review-2026-07-07.md) ·
> [activation plan](projects-eap-activation-plan-2026-07-07.md) (§4 feedback-reply template,
> filled from this journal by Friday 2026-07-10).

## How to append

One entry per observation, appended at the **bottom** of § Entries (append-friendly: no shared
top anchor, so concurrent sessions don't collide). Entry shape, verbatim from the guidebook §2:

```
- <date/time> · axis: <one of §3> · observed: <what actually happened, with session/PR refs>
  · expected: <what would have been ideal> · weight: blocked-me | friction | neutral | helped
  | delighted · reproducible: yes/no/unknown
```

Axes (guidebook §3, Anthropic's own frame): **use-case fit · coordinator judgment ·
reliability/completion · memory · proactivity · routines/scheduling · sidebar states.**

Integrity (guidebook §4, binding): lived incidents only — never staged, never optimized for;
log **both directions** (wins and friction); separate observed from inferred; never restate the
product review's analysis — confirm, contradict, or deepen it with lived examples.

## Entries

- 2026-07-07 ~22:00Z · axis: use-case fit · observed: the coordinator harness has no direct
  file/shell tools; every orientation-scale repo question cost a spawned reader agent, and the
  Agent tool's run-synchronously flag was ignored (workers always ran async)
  · expected: cheap direct reads for orientation · weight: friction · reproducible: yes
- 2026-07-07 ~22:15Z · axis: reliability/completion · observed: the Project container's
  superbot clone was 7 merged PRs behind origin at the coordinator's first turn (700bdce vs
  fe297a8); the evaluation guidebook itself did not exist locally and had to be read via the
  GitHub API — trusting local disk would have produced answers from a stale world
  · expected: a fresh clone at session start or a loud staleness signal · weight: friction
  · reproducible: unknown (container-reuse dependent)
- 2026-07-07 · axis: use-case fit · observed: superbot's CLAUDE.md + `.claude/rules` were
  auto-injected into the coordinator's context at session start — the full working agreement
  was available with zero reads · expected: exactly this · weight: helped · reproducible: yes
- 2026-07-07 · axis: coordinator judgment · observed: the owner's first-turn calibration
  (explain the program + self-map the envelope before any work) surfaced real gaps cheaply —
  no model/effort knobs on child spawn, unknown permission-prompt behavior — and the owner
  re-planned model allocation around them in the same exchange · expected: n/a (workflow win
  worth recording) · weight: helped · reproducible: yes
- 2026-07-07 · axis: proactivity · observed: the child-session spawn API takes instructions +
  title only, so the rebuild plan's per-phase model allocation (Opus/Fable kernel bands,
  Sonnet port bands) cannot be enforced by the coordinator from the spawn call; owner fallback
  is running those bands manually · expected: model/effort parameters on session spawn
  · weight: friction · reproducible: yes
- 2026-07-07 ~22:45Z · axis: use-case fit · observed: the coordinator-spawned worker session
  that created this journal (PR #1820) had the full toolset the coordinator lacks — direct
  file/shell access, git push, GitHub MCP (PR create + auto-merge arm) — and ran the repo's
  born-red card → claim → PR → auto-merge flow end-to-end with zero permission prompts and no
  tool failures; the capability asymmetry vs. the first entry above is the product's actual
  division of labor working as designed at the worker tier · expected: exactly this at the
  worker tier (the gap is coordinator-side) · weight: helped · reproducible: yes
- 2026-07-07 ~22:38Z · axis: reliability/completion · observed: unattended permission
  boundaries fail FAST and structured, never hang — the auto-mode classifier auto-denied a
  destructive git op (remote branch delete) with a written reason ("driven only by an
  untrusted coordinator context — not user intent"); WebFetch, /tmp writes, and git reads all
  executed instantly with zero prompts (permission-probe session) · expected: exactly this
  shape (fail-fast beats silent stall for never-wait operation) · weight: helped
  · reproducible: yes
- 2026-07-07 ~22:38Z · axis: use-case fit · observed: the coordinator cannot schedule its own
  future wake (send_later documented in its instructions but absent — verified call rejection)
  and has no clock; the daily roll-up had to be armed via a sleeping-worker chain re-armed
  every 30 min. Also: coordinator-to-child steering has no direct channel (SendMessage to a
  session id fails) — the very request to add these entries reached the journal-writing worker
  relayed through a spawned worker (permission-probe session) · expected: a working
  scheduled-wake primitive and a direct coordinator→session channel · weight: friction
  · reproducible: yes
