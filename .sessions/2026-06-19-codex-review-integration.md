# 2026-06-19 — Codex review integration (routine fix-first + Hermes 6H pr-check skill)

> **Status:** `complete`

## Arc

Lane B5 of the ultracode fleet (owner-directed, **Q-0174**). Shipped the two unbuilt parts of
`docs/planning/codex-review-integration-plan-2026-06-17.md` — the routine-side "check Codex first,
verified" fix-first step and the additive, issue-only Hermes 6H PR-check skill.

## Shipped (PR #1132)

### Part A — routines check Codex first (in-repo canonical mirror)

A first-priority "**check Codex first, verified**" step added to BOTH autonomous routine prompts:

- **dispatch** routine — `docs/operations/hermes-dispatch-bridge.md` § "The routine's saved prompt",
  new **step 1b** (between ORIENT and DECIDE): scan the few most-recent merged/open PRs for unresolved
  Codex/bot review comments, apply the plan's "real bug" bar (verified against current `main`, genuine
  defect, not a nitpick / born-red false positive), and fix the verified-real ones first. Reads Codex's
  *comment* (it can't push a branch/PR), applies the change itself.
- **reconciliation** routine — `docs/operations/autonomous-routines.md` § "superbot docs
  reconciliation", new **STEP 1b**: same bar, but **routed by shape** to honor the docs-only Q-0107
  rule — a verified-real *docs* defect is fixed in the pass; a verified-real *runtime* bug is captured
  OPEN to the bug-book (step 3) for the dispatch routine.

These are the canonical mirror; the **owner re-pastes** each into its routine's console config to take
effect (the standing routine-prompt convention).

### Part B — `superbot-pr-check` Hermes skill (additive, issue-only)

- `docs/operations/hermes-skills/pr-check.md` — doc = source of truth, in the `_house-style.md`
  output shape (bottom line first, fixed sections, plain words, one screen). Lists open + ~8
  recently-merged PRs, reads Codex comments / CI / unresolved threads, applies the "real bug" bar,
  and **opens a GitHub issue** for each real bug. Explicitly **NO merge and NO dispatch authority** —
  graduation to auto-dispatch is a deliberate later owner decision.
- `scripts/hermes/build_skills.py` — an `EXTRAS` entry registering it with the **6H schedule**
  `"0 */6 * * *"`, tags `[Review, SuperBot, Quality]`, related `superbot-review` / `superbot-review-merge`.
- `docs/operations/hermes-skills/README.md` — count 15 → 16, a new table row, and the scheduled-skills
  list updated with `pr-check (0 */6 * * *)`.
- **Regenerated artifact:** `scripts/hermes/skills/pr-check/SKILL.md` — committed, in sync. The build
  wrote 16 skills (was 15) and the ONLY new/changed generated path is `skills/pr-check/` — the diff is
  exactly the new skill, nothing else regenerated.

## Verification

- `python3.10 scripts/check_docs.py --strict` → **all checks passed ✓** (after fixing the plan's
  badge: `shipped` is not an allowed token → `historical`, the convention for a fully-executed plan).
- `python3.10 scripts/check_quality.py --full` → **All checks passed ✓** (exit 0; 10,884 passed,
  44 skipped; black/isort/ruff/mypy all clean).
- `python3.10 scripts/check_architecture.py --mode strict` → **exit 0, 0 errors** (only pre-existing
  `baseview_inheritance` warnings on untouched `disbot/views/*`; no `disbot/` runtime touched).
- `python3.10 -m pytest tests/unit/scripts/test_build_skills.py` → 22 passed; `build_skills --check`
  → 16 skills up to date.

## Context delta

- **`shipped` is NOT a valid `check_docs` badge token.** Allowed: archive / audit / binding /
  historical / ideas / living-ledger / owner-guidance / plan / reference. A fully-executed plan uses
  **`historical`** (matches every other completed plan in `docs/planning/`). The PR-body / card may
  say "shipped" freely — it's only the `> **Status:** \`...\`` doc-badge that is constrained.
- **The reconciliation Codex-first step had to be shaped differently from dispatch's.** The dispatch
  routine fixes whatever it finds; the reconciliation routine is docs-only (Q-0107), so its 1b routes a
  runtime flag to the bug-book instead of fixing it. Copying dispatch's step verbatim would have created
  a docs-only-rule contradiction — a small but real correctness point in a prompt that an agent obeys.
- **`build_skills.py` invokes with `python3` on purpose** (the Hermes VPS has 3.11, not 3.10) — its
  header explicitly warns against "correcting" it to `python3.10`. I left it; the freshness test runs
  under 3.10 in CI fine because it's pure stdlib.

## ⟲ Previous-session review (Q-0102)

The previous session (`2026-06-19-router-status.md`, PR #1103) shipped `scripts/router_status.py`,
a question-router digest tool — a genuinely useful piece of self-improvement tooling, and it did the
right thing surfacing its own honest limit (116/184 router blocks unclassified) rather than guessing,
which is exactly the Q-0120 "don't fight the evidence" discipline. What it could have done better: it
flagged the 116-block classifier gap as the seed of its *next* idea but left the gap itself open — the
older `Q-0001…Q-0130` blocks predate the `> **MARKER**` convention, so `router_status.py` will keep
reporting most of the router as UNCLASSIFIED until something backfills those markers.

**System improvement it surfaces:** the router-status tool and this session's pr-check skill both
*detect-and-report* (next number / open queue · PR flags → issues) but neither *closes the loop on its
own backlog*. A small follow-up worth a routine fire: a one-time pass (or a `--backfill` dry-run mode)
that proposes leading `> **MARKER**` lines for the legacy router blocks, so the digest tool graduates
from "most blocks unclassified" to a trustworthy OPEN-queue readout. Captured as the session idea below
in adjacent form.

## 💡 Session idea (Q-0089)

**A `codex-flag` issue-label lifecycle dashboard tile.** The new pr-check skill opens
`bug` + `codex-flag` labelled issues; right now nothing measures whether those issues turn out *real*
(the graduation question the plan defers — "once Hermes's issues prove consistently real, revisit
auto-dispatch"). A tiny addition to `scripts/export_dashboard_data.py` that counts `codex-flag` issues
by state (open / closed-fixed / closed-as-not-a-bug, read from the close reason or a `wontfix` label)
gives the owner the *evidence* for the auto-dispatch graduation decision without him hand-auditing the
issue tracker — it turns "a few cycles, see if they're real" into a number on `/updates`. Genuinely
believe in it: it's the measurement that makes the deferred owner decision data-driven instead of
gut-feel. (Dedup-checked `docs/ideas/` — the closest is the codex-automated-pr-review idea doc, which
is about *catching* flags, not *scoring* them; this is the complementary metric.)

## 📤 Run report

- **Did:** shipped Q-0174 Part A (dispatch + reconciliation routine prompts get a verified
  "check-Codex-first" fix-first step) + Part B (additive issue-only `superbot-pr-check` Hermes skill,
  6H schedule, regenerated artifact). · **Outcome:** shipped
- **Run type:** `manual`
- **⚑ Owner decisions needed:** `none` (auto-dispatch graduation stays a deliberate future decision,
  already noted in the plan — not needed now)
- **⚑ Owner manual steps:** (1) re-paste the Part A routine prompts into the **dispatch** + **docs
  reconciliation** routine console configs (routine-prompt mirror convention); (2) redeploy the new
  skill on the VPS — `bash scripts/hermes/install-skills.sh` + restart `hermes-gateway` — to activate
  the 6H schedule.
- **⚑ Self-initiated:** `none` (this build was owner-directed, Q-0174 lane B5)
- **↪ Next:** the codex-review integration is fully shipped; the natural follow-up is the
  `codex-flag` issue-outcome dashboard tile (session idea above) once pr-check has run a few cycles and
  produced real issues to score.
