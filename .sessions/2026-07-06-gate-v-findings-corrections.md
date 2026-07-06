# 2026-07-06 — Gate V evidence-findings corrections (Codex C2–C5 + Agent Mode)

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). Docs-only session (no
> `disbot/` runtime code): `check_plan_homing.py --strict` green (new doc homed in the plan index) and
> `check_docs.py --strict` / `check_current_state_ledger.py --strict` clean.

## What this session did

Owner asked (in-session) to **properly document the corrected findings** of the Codex Arm-B PRs and the
Agent Mode (Arm C) report, so the final Gate V synthesis (Arm Σ) consumes a *verified* evidence layer
rather than the raw sub-reports.

**Shipped (PR #1756):** `docs/planning/rebuild-gate-v-findings-corrections-2026-07-06.md` — the verified
evidence layer, homed in the plan index. It records:

- **C1 (L0/runtime source truth) failed to start** — no PR in any state; C2/C3/C4/C5 produced
  #1755/#1754/#1753/#1752. Re-run prompt included (path-pinned to `docs/planning/`, with the ci-gate
  correction inlined).
- **Codex C2–C5 all verified SOUND** by an independent review fan-out — every load-bearing claim
  reproduces against live source; none hit the ci-gate error or the graph-tool dead-code trap. Caveats:
  all ran on a stale HEAD (`cf5a234`, self-disclosed), all evidence is `source-read` not
  `test-confirmed` (no Postgres/discord in sandbox), and C2/C3/C4 dropped files at the repo root
  (relocate before merge).
- **Agent Mode `ci-gate` error — verified & corrected:** it claimed `ci-gate` is the required gate and
  `code-quality` is stale; false — `.github/` has no `ci-gate`, `code-quality.yml` is the live gate
  (this PR and #1750 merge on it). It misread the `ci-setup-redesign` *plan* as applied. Its
  `.python-version`=3.13.13 runtime nuance is correct.
- **Substantive verified findings** carried to synthesis: economy credit/debit non-transactional + XP
  award emits with no audit companion (contract-freeze); channel lifecycle ownership gap; `ai`/`btd6`
  have zero L3 game-cog dependency (supports games-*feature* deferral, but shared primitives still need
  early replacement proof).
- **§6 directives for Arm Σ:** reject the ci-gate recommendation; don't upgrade any Codex evidence to
  test-confirmed; mark L0 unproven pending C1; relocate root sub-reports.

Also noted: **Arm D (live-testing) already ran and merged** (`af77f6a`, PR #1751 line) — the empirical
pack is on main.

## ⚑ Self-initiated

None beyond owner direction — the whole session is owner-directed (review the Codex PRs + Agent Mode
report, name the failed session, document corrected findings). Docs-only, reversible.

## 💡 Session idea (Q-0089)

**A `verified-evidence-layer` convention for every multi-arm fleet.** This session proved that raw
arm outputs carry propagated errors (the Agent Mode ci-gate misread) and stale-HEAD/source-read-vs-
test-confirmed caveats that a naive synthesis would swallow. The fix that generalizes: every fleet
should produce a *mandatory corrections doc* — one independent pass that re-verifies each arm's
load-bearing claims against live source and emits explicit REJECT/CONFIRM directives — *before* the
synthesis runs, not as an optional extra. Pairs with the earlier `review-fleet-template.md` idea: the
template defines the arms; this defines the verify-before-synthesize gate. Worth having because "the
synthesis silently inherits an arm's error" is the exact failure this session caught by hand.

## ⟲ Previous-session review (Q-0102)

Previous (this branch, pre-reset): the Gate V launch-pad doc (#1750). **Did well:** the shared §3
contracts (pinned enum / claim-anchor keys) are exactly why the four Codex reports came back mergeable
and why this corrections pass could key findings cleanly. **Missed / system delta:** the launch pad
told each Codex session to "emit sub-report {Ck}-<scope>.md" without pinning a **directory**, so three
of four dropped files at the repo root — a concrete instance of the "thin/underspecified step" rubric
class. The launch pad's §5 should pin the output path (`docs/planning/`); folding that back is the
cheap enforcing fix. (Captured in the corrections doc §2 + the C1 re-run prompt; a one-line launch-pad
edit is the durable version.)

## ▶ Next action

Re-run **C1** (prompt in the corrections doc §4). Once C1 lands and Arm A (Sonnet) finishes, run the
final synthesis (Arm Σ, launch-pad §8) — feeding it **this corrections doc**, not the raw sub-reports.
Optional cheap follow-up: pin the sub-report output path in the launch pad §5 so future fleets don't
scatter files at the repo root.
