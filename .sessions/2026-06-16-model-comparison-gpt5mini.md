# 2026-06-16 — gpt-5-mini vs gpt-5.4-mini comparison + apply_context_fixes --set-model fix

> **Status:** `in-progress` — capturing a model-comparison finding (owner asked) + fixing one latent
> script bug. Docs/scripts only; one push.

## What I'm about to do

Owner asked whether switching Hermes from `gpt-5.4-mini` to `gpt-5-mini` would raise the TPM ceiling
("this one has a lot more tokens per minute") and to "get the diffs for those 2 models." Researched
both from OpenAI's own model pages. Capturing the finding durably + fixing an adjacent bug it exposed.

- **Finding:** the published per-tier rate-limit tables are **identical** for both models — switching
  alone does not raise TPM. The 200K observed is *below* Tier 1's published 500K → the limiter is the
  **org usage tier / gpt-5-family verification throttle**, not the model name. Trade-off if switched:
  5-mini is ~2–3× cheaper but weaker/slower/staler (the class the repo left in #913→#921).
- **Adjacent bug:** `apply_context_fixes.sh --set-model` runs `hermes config set model`, which the
  model-switch playbook says reverts routing to the Nous catalog (the custom-provider setup is now the
  norm). Fixing it to warn + point at `hermes model` instead of silently doing the wrong thing.
