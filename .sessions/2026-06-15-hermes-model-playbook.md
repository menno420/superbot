# Session — Hermes model-switch playbook + saga close-out

> **Status:** `complete`

## What we did (the whole Hermes thread, this session)

Owner reported Hermes (the Nous Research control-plane agent on the VPS) misbehaving — errors,
forgotten tasks, misunderstood assignments, not syncing to main. Diagnosed + fixed across PRs
**#913–#917 (all merged & live)**:
- **#913** — root cause corrected: the "forgetting" is **context compaction** (tool-output pruning
  at 50%, not unbounded overflow); + fixed the SOUL.md sync bug (`git fetch`→`git pull`).
- **#914** — `scripts/hermes/apply_context_fixes.sh` (VPS operator script: compression knobs +
  re-install SOUL) + a SOUL.md size guard.
- **#915** — self-healing repo sync (recover a diverged mirror clone).
- **#916/#917** — recorded the model/provider decision in `hermes-control-plane.md`.
- **Applied live on the VPS:** `compression.threshold 0.75`, `protect_last_n 30`, `cache_ttl 1h`,
  SOUL reinstalled. The model is the dominant behaviour lever (free Step-Flash was too weak).

This PR (docs-only): rewrote `hermes-control-plane.md` § Model/provider into the accurate **current
state + a 6-trap model-switch playbook**, and corrected the misleading `config set model openai/…`
line in the cheatsheet (the prefix routes to Nous; use the `hermes model` wizard).

## Current state (⬜ OPEN — needs checking in a fresh chat)

Hermes is **switched to `gpt-5.4-mini` on the owner's own OpenAI key** via a custom OpenAI provider
(`openai-api`, 400K detected) — quality is good when it runs — **but it is NOT yet stable:** it
**intermittently** returns `Project proj_OJ… does not have access to model gpt-5.4-mini` (flapped
>15 min, so not mere propagation). **Pick up here:** `hermes-control-plane.md` § "Model / provider"
→ the **⬜ NOT YET STABLE** bullet. Next step = point Hermes at the **exact dated id
`gpt-5.4-mini-2026-03-17`** (the project has it fully granted) instead of the alias; if it still
flaps, pin `auxiliary.*` / `delegation` (both `provider: auto`) in `~/.hermes/config.yaml`.

## 💡 Session idea (Q-0089)

**A Hermes model-health canary.** Model-access flapping was only discovered through the owner's
frustration — nothing surfaced it. A tiny hourly cron (or a `hermes-model-health` skill) that sends
a one-token "ping" to the configured model and reports `ok / denied / flapping` would turn silent
model-access failures into a visible signal — the operator-side analogue of `check_loop_health`.
Dedup-checked `docs/ideas/` — none.

## ⟲ Previous-session review (Q-0102)

Previous: `2026-06-15-hermes-model-record.md` (#916). It captured the model decision well, but
asserted "Provider: openai-api" / "switched" from a single transient `/model` screen and marked only
"live-reply pending" — which this thread had to walk back twice (it was actually routing via Nous,
then a custom provider, and it *flaps*). **Lesson, now enforced here:** for control-plane/external
config, **`configured` ≠ `working` ≠ `stable`** — don't record a switch as done until a live reply is
confirmed *and* holds across several turns. This card marks the model switch **in-progress, not done.**

## 📋 Doc audit (Q-0104)

`check_docs --strict` green. `hermes-control-plane.md` § Model/provider now reflects the real
(flapping) state + the playbook; the cheatsheet's wrong `config set model openai/…` guidance is
corrected. The one open item is a **runtime/ops check** (gpt-5.4-mini stability), explicitly flagged
in the doc as ⬜ — not a docs gap. Ledger unaffected (docs-only).
