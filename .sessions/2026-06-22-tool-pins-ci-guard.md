# 2026-06-22 — make `check_tool_pins` a CI guard (close the #1315 drift class at the root)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Routine · dispatch ("Continue from where you left off"; promotes PR #1317's logged idea).
> PR #1320 → auto-merges on green (Q-0123).

## Arc

Three botsite/hygiene PRs already merged this session (#1305, #1308, #1317). #1317 had to *fix* a
ruff tool-pin drift that reached `main` (#1315 — Dependabot bumped `requirements-dev.txt` alone),
and I logged the root fix as that session's idea: the `check_tool_pins` guard was **local-only**
(in `check_quality.py`), so nothing stopped the desync at the PR gate. This PR promotes that idea →
build (Q-0172). With the product lanes gated (PR 2 cutover needs attended browser verification;
Project Moon ingestion is network/IP-sensitive), this is the cleanest high-value safe slice.

This PR:
1. **`tool-pins.yml`** — a dedicated, `paths`-filtered CI workflow (sibling of botsite-ci /
   design-system-ci) that runs `scripts/check_tool_pins.py` on any change to the three pin sources,
   so a Dependabot lone-file bump now goes **red on the PR** instead of merging green. (Not yet a
   *required* check — making it block auto-merge is a one-line owner repo-Settings step, flagged.)
2. **Extend the checker to genuinely validate all THREE places.** It claimed "three places" in its
   docstring + error text but only compared `code-quality.yml` ↔ `requirements-dev.txt` —
   `.pre-commit-config.yaml` was never read (a latent gap: a pre-commit `rev:` drift went
   undetected). Added a `rev:`-format parser (repo→tool map, strips the inconsistent `v` prefix) and
   made `check()` compare all three. All currently aligned, so no behavior change today.
3. **First unit test** (`tests/unit/scripts/test_check_tool_pins.py`) — the checker is now
   CI-gating + load-bearing, so it gets the Q-0105 "verify before you trust" treatment: parser
   cases, each pairwise drift (incl. the new pre-commit case), missing-pin, missing-file, and a
   live "the real repo stays aligned" guard. `check()` gained an injectable `sources` param for
   hermetic testing.

## Shipped (PR — this session)

- **`.github/workflows/tool-pins.yml`** — new guard workflow (SHA-pinned checkout + setup-python
  3.10, stdlib check, no pip install). Triggers on `requirements-dev.txt` · `.pre-commit-config.yaml`
  · `code-quality.yml` · the script · itself. Carries the Q-0105 disposable-guard header.
- **`scripts/check_tool_pins.py`** — now reads `.pre-commit-config.yaml` too (the third place its
  own message always named); `check(sources=…)` is injectable; success message names all three.
- **`tests/unit/scripts/test_check_tool_pins.py`** — 8 cases, all green.
- **Verification:** new tests 8/8 ✓ · `check_quality --check-only` ✓ · real-repo `check_tool_pins`
  ✓ · `tool-pins.yml` YAML valid · pre-commit parse verified (black 26.5.1 / isort 8.0.1 /
  ruff 0.15.14 / mypy 2.1.0, all aligned).

## Session enders

- **♻ Grooming (Q-0015):** promoted PR #1317's logged session idea (the CI-step half) down its
  lifecycle to a shipped build — idea → build in one hop (Q-0172), the dispatch routine's intended
  flow when product lanes are gated.
- **💡 Session idea (Q-0089):** *Auto-derive CI's tool versions from `requirements-dev.txt` so the
  three-places rule collapses to one.* `code-quality.yml` hard-codes `pip install black==… ruff==…`
  inline — the root cause of the drift class is that the pin lives in 3 hand-synced spots. If the
  workflow instead did `pip install -r requirements-dev.txt` (or read the versions from it), CI and
  the dev install could never disagree, leaving only pre-commit to guard. Bigger change to the
  critical workflow → wants its own focused/attended slice; logged, not done here.
- **⟲ Previous-session review:** #1317 (this turn's predecessor) correctly *fixed* the #1315 ruff
  drift and *logged* the root fix instead of stopping — exactly the "fix the symptom now, capture
  the durable fix" discipline. What it (understandably) didn't do: notice the checker only covered
  2 of the 3 places it claimed. **System note:** when you fix a drift a guard *should* have caught,
  also confirm the guard actually covers what its own message promises — a guard that under-checks
  is worse than none, because it implies coverage it doesn't have.
- **🧾 Doc audit (Q-0104):** `check_docs --strict` ✓; no current-state/sector change needed (a CI
  guard, not a product feature); the new workflow is self-documented (header) + this log; ledger
  auto-updates for this PR on merge. Nothing left only in chat.

## ⚑ Self-initiated: yes (Q-0172) — promotes my own PR-#1317 logged idea (CI-enforce the tool-pin
   guard) to a build, no dispatch/owner ask (empty "continue" fire, gated product lanes). Additive CI
   workflow + a checker extension that's behavior-neutral today + tests — fully reversible → self-merged
   on green. Owner follow-ups flagged: (a) mark `tool-pins` a *required* check to actually block merges;
   (b) the Dependabot-`ignore`-the-trio policy option (deferred as a policy call, not applied unilaterally).

## 📤 Run report

- **Did:** CI-enforced the tool-pin guard — a new `tool-pins.yml` workflow runs `check_tool_pins` on any pin-file change (closing the local-only hole that let #1315 reach `main`), extended the checker to genuinely validate all THREE pin sources (it only checked 2), and added its first unit test. · **Outcome:** shipped
- **Shipped:** #1320 — `.github/workflows/tool-pins.yml` + `scripts/check_tool_pins.py` (now reads `.pre-commit-config.yaml`, injectable `sources`) + `tests/unit/scripts/test_check_tool_pins.py` (8 cases).
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** (optional, not blocking) mark **`tool-pins`** a *required* check in repo Settings so a pin desync actually BLOCKS auto-merge (today it only shows red); optionally add a Dependabot `ignore` rule for black/isort/ruff/mypy so the desyncing PR is never created.
- **⚑ Self-initiated:** **yes** — promotes PR #1317's logged idea (CI-enforce the guard) to a build on an empty "continue" fire with gated product lanes; additive CI + behavior-neutral checker extension + tests → self-merged on green.
- **↪ Next:** product lanes remain the priority once attended/un-gated — botsite React-SPA migration **PR 2** (the live `/` cutover; needs a **manual browser click-through**, best attended) is the top S1 item, its data side now de-risked by #1305/#1308/#1317. Other lanes: Project Moon runtime PR 1 (ingestion — network + IP/licensing-sensitive → weigh ask-first). Tooling backlog from this turn's ideas: collapse the three-places pin to one by having `code-quality.yml` install from `requirements-dev.txt` (a focused/attended slice on the critical workflow).
