# Hermes token-efficiency — investigation + fix plan (tomorrow's focus)

> **Status:** `plan` — owner-prioritized (2026-06-15, captured fresh from the live failure).
> **Investigation half is now DONE** — see "## Findings (verified against Hermes source/docs)" at the
> bottom; the four "investigate first" questions are answered and the root cause is corrected
> (it is **compaction**, not unbounded growth). The *fix* is still not approved to build.
> Home: the Hermes control plane ([`hermes-control-plane.md`](hermes-control-plane.md)).

## The smoking gun (observed live 2026-06-14/15)

Hermes `/status` after only a handful of small messages:

```
Cumulative API tokens (re-sent each call): 2,207,496
Agent Running: No
```

**2.2M cumulative tokens ≈ 8–9× the stated ~256K working window**, that fast. The label is the tell:
*"re-sent each call."* Hermes runs as **one long-lived, accumulating gateway session** — every turn
re-injects the full system prompt (`soul.md`) **+ the entire conversation history + every prior tool
output**. So per-turn **input** grows ~linearly and the cumulative grows ~**O(N²)**.

## Root cause (hypothesis — one cause, all the symptoms)

By the 3rd–4th tool call, the repo state Hermes read early (the plan, the folio, what it had already
verified) is **pushed out of the effective working window**, and it falls back to pattern-matching the
**always-present injected system prompt** instead of the repo facts it read ten tool calls ago.

Every symptom Hermes self-diagnosed is **downstream of that one cause**:
- *Invented scope instead of reading the repo* — dispatched "Phase 2 mining" without opening
  `docs/planning/mining-structures-skill-tree-plan-2026-06-14.md` (the canonical plan, on `main`).
- *Didn't use the subsystem folio* (`docs/subsystems/games.md`).
- *Fired twice without re-grounding* — re-fired vague instead of stopping to read.
- *Context collapse by the 3rd–4th tool call* — lost the thread, repeated/reinvented.

Concrete result tonight: Hermes opened a docs-only re-declaration (**#888**, closed as churn) that
re-stated the existing plan, put it in the wrong dir, and targeted the **owner-blocked** V-16 slice.

## Investigate first (answer before changing anything)

Consolidates the owner's + Hermes's own questions:
1. **Where does per-turn context come from?** Is `soul.md` injected *whole* every turn, **on top of**
   the accumulated history — or is something else bounding what stays loaded?
2. **Working cutoff vs. the counter.** The 2.2M is *cumulative re-sent*, not the live window — what is
   the *actual* working-context cutoff per call, and at which turn does the early repo-read fall out?
3. **Session memory vs. working context.** Is there a difference between `.sessions/` logs (durable
   memory) and what actually stays in the model's working context across tool calls? (Yes in
   principle — confirm it in Hermes's pipeline.)
4. **Can history be capped/summarized/flushed?** Is there a seam to cap or summarize history before
   re-injection, or to **flush context between bounded tasks**?

Where to look (VPS-side, owner has access): the Hermes gateway code that builds each API call's
`messages` array; `soul.md`; [`hermes-control-plane.md`](hermes-control-plane.md) ·
[`hermes-dispatch-bridge.md`](hermes-dispatch-bridge.md) ·
[`hermes-operating-prompt.md`](hermes-operating-prompt.md) · the `hermes-skills/`.

## Candidate fixes (levers, cheapest-impact first)

1. **Stateless, bounded dispatch (the big one).** Each Hermes work order should run in a **fresh
   context** — *read the work order → open the canonical plan/folio → execute → end* — **not** appended
   to a growing session. This is the §10 bounded-session protocol (already used for Claude sessions)
   applied to Hermes; it kills the O(N²) growth at the root and forces re-grounding by construction.
2. **History cap / sliding window / running summary** before re-injection — keep the last *K* turns +
   a compact summary, never the full transcript.
3. **`soul.md` injection strategy** — inject once / cache it (prompt-cache), or trim it; stop re-sending
   the whole thing every turn on top of growing history.
4. **Force re-grounding at dispatch start** — the dispatch skill's **step 1** must *open* the canonical
   plan (`docs/planning/…`) + folio (`docs/subsystems/…`), never act from the injected prompt's memory.
   (A prompt fix, but only *durable* once the context actually retains the read — i.e. after #1/#2.)
5. **Explicit flush between tasks** — reset context between bounded work orders.

## Success criteria

- **Per-dispatch input tokens roughly constant (O(1))** regardless of how many turns/tool calls a
  dispatch takes — not growing toward the window.
- A dispatch **reliably reads the canonical plan/folio and acts on repo state**, not the injected prompt.

## Note — the in-repo Claude sessions don't hit this (and why)

These Claude Code sessions re-send history each call too (it's how the harness works), **but** the
harness **summarizes/manages** the context window, and each session **re-orients from disk** every
resume (`git fetch` + read `current-state` / the plan / the folio). The fix for Hermes is to give it the
*same* discipline: **bounded, re-grounding dispatches** instead of one ever-growing session. That is the
deeper reason #1 above is the right primary lever.

---

## Findings (verified against Hermes source/docs, 2026-06-15)

> Added after the owner asked for deeper research and supplied a ChatGPT deep-research report on the
> Nous Research Hermes Agent. Hermes IS that agent (`github.com/NousResearch/hermes-agent` — confirmed
> by our SOUL.md/skills/gateway/cron). Findings below are checked against Hermes' own source + dev docs,
> **not** the report or marketing (the report itself warns Hermes docs drift from code).
> **Trust note (Q-0105, unverified):** these are upstream-doc-derived — re-confirm a knob against the live
> `~/.hermes/config.yaml` on the VPS before relying on it; delete this caveat once confirmed there.

### The root cause was mis-diagnosed — it is COMPACTION, not unbounded growth

The body above (and the report) assumed the gateway just re-sends an ever-growing history → O(N²) →
overflow. Hermes' source says otherwise: the gateway has a **two-layer compaction system**, and the
*forgetting* is what that compaction PRUNES — not window overflow.

| Layer | Fires at | What it does |
|---|---|---|
| Agent `ContextCompressor` | **50%** of context (`compression.threshold: 0.50`) | summarizes the middle, prunes old tool outputs |
| Gateway session hygiene | **85%** (fixed) + a **400-message** hard valve | safety net; the 400-msg valve fires on COUNT regardless of token pressure (bug #12626) |

What compaction does (verified `compression` defaults):
- **KEEPS:** the system prompt (SOUL.md); `protect_first_n: 3` (system + first exchange);
  `protect_last_n: 20` (recent turns); `target_ratio: 0.20` tail budget.
- **SUMMARIZES** the middle turns into Goal / Progress / Key Decisions / Relevant Files / Next Steps /
  Critical Context.
- **PRUNES** tool outputs >200 chars → `[Old tool output cleared to save context space]`.

**So the mechanism behind "forgets / misunderstands":** Hermes reads the canonical plan or folio early
(a large file = a >200-char tool output), makes a few more tool calls, crosses 50% — and that file read
is **pruned to a stub**. It keeps a *summary* of "Relevant Files" but loses the actual contents, then
falls back to pattern-matching the always-present SOUL.md. That is exactly the #888 failure (re-stated
the plan from memory, wrong dir, owner-blocked slice).

### Re-framing the 2.2M "cumulative tokens"

It is **cumulative spend** (sum of input tokens across all turns), **not** the live working window (which
IS bounded by the compaction above). So:
- **Cost** (€30/mo Q-0082 cap): cumulative matters — a long gateway session is expensive.
- **Correctness** (forgetting): cumulative is a red herring; the lever is *what survives compaction*,
  not *how many tokens were billed*. Chasing "lower cumulative tokens" alone would not fix the forgetting.

### Answers to the four "investigate first" questions

1. **Where does per-turn context come from?** SOUL.md is slot #1, re-injected (and **truncated if too
   large** — verify the operating prompt fits) every message, on top of the **compacted** history (not the
   whole raw transcript).
2. **Working cutoff vs. the counter.** Working window is bounded by the 50%/85%/400-msg compaction; the
   2.2M is cumulative spend. The early repo-read falls out at the **first compaction crossing 50%**, not at
   window overflow.
3. **Session memory vs. working context.** Confirmed distinct: `.sessions/` logs + `state.db` + cron-output
   files are durable disk memory; the working context is the compacted in-RAM transcript. Hermes does NOT
   auto-reload disk memory mid-session — it must re-read on demand.
4. **Can history be capped/summarized/flushed?** Yes, three ways: (a) the `compression.*` knobs above tune
   summarize-vs-keep; (b) `prompt_caching.cache_ttl` (`5m` default → `1h` for long sessions); (c) the real
   flush is **cron** — each cron run is a fresh stateless `AIAgent` (`skip_memory=True`, source comment
   "Cron system prompts would corrupt user representations").

### The bounded-dispatch fix already exists in Hermes — it's cron

Candidate fix #1 above ("stateless, bounded dispatch") is not something to build — Hermes *ships* it as
the cron subsystem:
- **Fresh session per run**, no memory of prior runs → kills O(N²) growth AND forces re-grounding by
  construction.
- **`context_from=["job_a"]`** prepends a prior job's latest output — the state-passing seam between
  bounded runs (the "collect → triage → ship" pipeline).
- **Pre-run `script`** runs a shell command before the agent turn, stdout injected as context → the
  **deterministic place to enforce `git fetch && git reset --hard origin/main`** so sync stops depending on
  the LLM remembering (the "forgets to sync to main" fix). `no_agent=True` makes a script-only job.
- Per-job **`model`/`provider`** override, **`skills=[]`**, **`deliver=`** routing.
- **Caveat:** cron disables `clarify`/`messaging`/`cronjob` — a cron run CANNOT ask a follow-up, so its
  prompt MUST be fully self-contained (the same discipline as a bounded Claude routine).

Nuance for SuperBot: build *execution* already runs as bounded **Claude Code routines** (Q-0146 console
Schedule) which re-orient from disk — those are fine. What still blows up is the **interactive Telegram
gateway** Hermes (the control plane the owner talks to); its context collapse then propagates into *bad
work orders* (wrong scope → bad dispatch). So the fix targets the gateway session, not the routines.

### Symptom → mechanism → fix

| Owner symptom | Mechanism (verified) | Fix | Side |
|---|---|---|---|
| "forgotten tasks" | compaction prunes early tool outputs at 50%; 400-msg silent valve (#12626) | re-ground at point of use; raise `protect_last_n`; short sessions; bounded cron / `/new` | VPS config + prompt |
| "misunderstands assignments" | middle-turn summary loses work-order detail; SOUL.md truncated if oversized | verify SOUL.md size; self-contained work orders; bounded dispatch | VPS + prompt |
| "forgets to sync to main" | SOUL.md did `git fetch` only → stale working tree; no deterministic sync | `git pull --ff-only` (this PR); pre-run `script` `reset --hard` for cron | prompt (done) + VPS |
| "lots of errors" | BUG-0011 gateway crash-loop (Telegram 409); dispatch balks (Q-0136 sensitive-info; py3.10 #869) | BUG-0011 needs a clean foreground repro; the rest are fixed — re-install on VPS | VPS |

### Upstream Hermes issues to watch (re-check during grooming)

- **#12626** — gateway silently auto-compacts at 400 messages even when `/usage` shows low context
  pressure. Directly explains some "forgotten tasks". Mitigate by short sessions; track for a fix.
- **#9763** — cron's `skip_memory=True` also blocks external memory providers in cron context. Only
  relevant if SuperBot ever wires a memory provider into a cron path.

### Owner data point (2026-06-15): even ~5-message sessions fail → it's per-turn doc VOLUME

The owner confirmed the failures happen in sessions of **~5 messages at most, with clear directed
orders that name the skill**. That *sharpens* the diagnosis rather than contradicting it: the
400-message valve is irrelevant at that length, so the culprit is **how much a single turn reads**.
SuperBot's docs are large; one whole-file read (CLAUDE.md ≈30 KB, current-state, a plan, a folio,
the binding contracts) can cross the **50% compaction line in ONE or TWO tool calls** — and the
compaction then prunes the very doc Hermes just read. So "it can't handle our docs" (owner's words)
is exactly right: the read that should have grounded the turn is the read that gets pruned. The
levers below target that, not message count.

### Recommended config to try on the VPS (maintainer, reversible)

**Easiest: run `scripts/hermes/apply_context_fixes.sh`** on the VPS (`--dry-run` to preview) — it
applies the items below via the validated `hermes config set` CLI, backs up `config.yaml` first,
and re-installs the sync-fixed SOUL.md. Then `sudo systemctl restart hermes-gateway`. Manually, in
`~/.hermes/config.yaml` (re-confirm key names against the installed version first):
- **`compression.threshold` ↑ (0.50 → ~0.75)** — the highest-impact knob for the owner's pattern:
  compaction fires LATER, so a big doc read survives the turns that use it.
- `compression.protect_last_n` ↑ (e.g. 20 → 30) so more recent turns survive a compaction.
- `prompt_caching.cache_ttl: "1h"` for long control-plane sessions.
- **Use a larger-context-window model** — 50% of a 1M window is far more room than 50% of 256K, so
  the doc read falls out much later (`hermes config set model <provider/model>`; cost is the owner's
  call — weigh against the €30/mo Q-0082 cap).
- **Read doc SECTIONS, not whole files** — grep / targeted reads keep a single turn small; a skill
  that says "read all of current-state.md" is more likely to trip compaction than one that greps the
  ▶ Next action. (Prompt/skill discipline, not a config knob.)
- Verify the SOUL.md byte size (now guarded in `install-soul.sh`) — at 6478 bytes it is ~81% of the
  likely ~8 KB ceiling, so don't grow the operating prompt without trimming.
- Adopt a **`/new`-per-task** habit (the SOUL.md already preaches it) — the cheapest fix of all.
