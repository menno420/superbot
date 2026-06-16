# 2026-06-16 — gpt-5-mini vs gpt-5.4-mini comparison + apply_context_fixes --set-model fix

> **Status:** `complete` — docs/scripts only; one PR (#978).

## Arc

Owner asked whether switching Hermes from `gpt-5.4-mini` to `gpt-5-mini` would raise the live bot's
200K TPM ceiling ("this one has a lot more tokens per minute") and to "get the diffs for those 2
models." Researched both from OpenAI's own model pages, captured the finding durably, fixed an
adjacent script bug it exposed. Mid-session the owner confirmed the **dashboard caps 5.4-mini at
200K** and is empirically testing 5-mini — which sharpened the doc into a decisive either/or test.

## The finding (verified 2026-06-16 from OpenAI's model pages)

- **The published per-tier rate-limit tables are identical for both models** (Tier 1 500 RPM / 500K
  TPM, Tier 2 5K / 2M, Tier 3 5K / 4M, Tier 4 10K / 10M, Tier 5 30K / 180M). So a model swap **does
  not** lift TPM on paper.
- The owner-observed/dashboard 200K is **below** Tier 1's published 500K → the limiter is the **org
  usage tier or a gpt-5-family rollout/verification throttle, not the model name**.
- **Decisive test (no live switch needed):** the dashboard lists limits **per model**, so compare
  gpt-5-mini's number — **(a)** also ~200K → org-wide throttle, raise the tier (1→2 = 2M); **(b)**
  higher (≈500K) → a throttle on the *newer* 5.4-mini, switching to 5-mini genuinely helps. Only case
  (b) justifies the switch.
- Trade-off if switched: 5-mini is ~2–3× cheaper ($0.25/$2.00 vs $0.75/$4.50) but weaker, ~2× slower,
  and staler (May 2024 vs Aug 2025) — the model class the role deliberately left in #913→#921.

## Shipped (PR #978 — docs/scripts only)

- `docs/operations/hermes-control-plane.md` — added the side-by-side comparison + the
  "lever is the tier, not the model" finding + the owner-confirmed decisive-test either/or in the
  Model/provider section; pointed the existing 200K-TPM caveat at it.
- `scripts/hermes/apply_context_fixes.sh` — fixed the adjacent bug: `--set-model` ran
  `hermes config set model`, which the model-switch playbook shows reverts routing to the Nous catalog
  (wrong for the own-key custom provider). The flag is now a no-op that prints the correct path
  (re-run `hermes model`); usage + tip text updated to match.

`bash -n` ✓ · dry-ran the deprecated `--set-model` path ✓ · `check_docs --strict` ✓ · no Python
touched (no mypy/pytest/lint impact).

## Context delta

- **Load-bearing fact:** within a model *class*, OpenAI's per-tier rate limits are uniform — so "use a
  different mini for more TPM" is usually a category error. The real TPM levers are **usage tier** and
  **per-call size** (compaction), and the *only* source of an org's actual cap is the dashboard. A
  model swap helps **only** when a newer model is rollout-throttled below its tier.
- **Decision made alone:** landed the comparison + the `--set-model` fix without waiting on the live
  test outcome — both are correct regardless of whether 5-mini's cap turns out higher. The pending
  test result will be a one-line follow-up to the doc, not a change to this PR.
- **Flagged for owner:** check gpt-5-mini's dashboard cap *before* switching — if it's also 200K the
  switch is wasted effort and the tier is the real fix.

## 💡 Session idea (Q-0089)

**`docs/operations/openai-account-state.md` — an owner-pasted ground-truth snapshot.** Agents reason
about TPM/cost from *published* tables, but the org's actual caps, usage tier, and verification status
live on a dashboard no agent can see — so every such question (like today's) forces the owner to go
look. A tiny dated doc the owner pastes their dashboard limits into (per-model TPM/RPM, tier, verified
models) would give agents ground truth and let them answer definitively instead of "check your
dashboard." Worth it the moment a second rate-limit/cost question comes up; not yet filed as an idea
doc (small, and partly satisfied by the new control-plane note) — promote if it recurs.

## ⟲ Previous-session review (Q-0102)

Reviewing the #976 TPM-docs session (`2026-06-16-hermes-tpm-rate-limit-docs.md`). **Did well:** nailed
the TPM-vs-context-window distinction and the verified no-clean-CLI-reset reality — genuinely
load-bearing corrections that stopped a wrong-direction fix (`apply_context_fixes.sh`). **Missed:** it
concluded on "compaction / raise the tier" but never evaluated the **model-choice** lever — so when
the owner immediately asked "what about gpt-5-mini?", the answer wasn't pre-captured and needed a
fresh research pass this session. **System improvement (acted on here):** a finding doc about a
constraint (rate limit, cost) should also enumerate the *adjacent levers it considered and ruled out*
(here: a model swap) so the obvious next question is already answered — which is exactly the
comparison this session added. The chain self-corrected; the durable lesson is "capture the ruled-out
alternatives, not just the chosen fix."

## 📤 Run report

- **Did:** researched gpt-5-mini vs gpt-5.4-mini, captured the comparison + the "TPM lever is the tier,
  not the model" finding, fixed the `--set-model` routing bug · **Outcome:** shipped (PR #978).
- **⚑ Owner decisions needed:** `none`.
- **⚑ Owner manual steps (VPS):** check **gpt-5-mini's dashboard TPM cap first**; switch only if it's
  higher than 5.4-mini's 200K — via `hermes model` (not `hermes config set model`) + allowlist the id +
  `sudo systemctl restart hermes-gateway`. If 5-mini is also 200K, raise the OpenAI usage tier instead.
- **↪ Next:** owner reports 5-mini's dashboard cap / live behavior → one-line doc follow-up with the
  result (which lever won).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened this session | 1 (#978) |
| CI-red rounds | 0 (docs/scripts only; verified locally) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (openai-account-state snapshot) |
| Ideas groomed | 0 |
