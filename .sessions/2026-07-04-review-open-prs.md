# 2026-07-04 — Open-PR review + merge sweep

> **Status:** `complete`
> **Branch:** `claude/review-open-prs-1k48kg` · **PR:** #1719

## Intent

Owner-directed: review **all 13 open PRs** and drive each to a terminal state (merged or
closed), improving contents where necessary.

## Outcome — all 13 (+1 that appeared mid-sweep) dispositioned

**Dependabot (6 + 1):**

- **#1555 / #1557 / #1558 / #1559** — CI green on the bumped installs (the full suite runs against
  the new deps in CI, so green = verified); Pillow's 11→12 major additionally re-verified locally
  (render tests green on 12.3 against today's main). **Merged.**
- **#1560** — had rotted into a conflict (adjacent `requirements.txt` lines); resolved on-branch,
  merged on green.
- **#1556** — `tool-pins` + `code-quality` red: dependabot bumped `requirements-dev.txt`'s tool pins
  alone (the #1074/#1315 drift class). Fixed properly instead of realigning down: the deliberate
  **three-place bump** (ruff 0.15.20 · pytest 9.1.1 · pytest-xdist 3.8.0 in `code-quality.yml` +
  `requirements-dev.txt` + `.pre-commit-config.yaml`), verified by the full local CI mirror
  (**14 059 passed**) + a `botsite/app.py` prose-comment reword for ruff 0.15.20's ERA001 false
  positive (the `(#/commands, …)` line — same class as BUG-0022). Dependabot auto-closed the PR
  mid-sweep (sibling merges); reopened, merged on green.
- **#1720** — dependabot's recreated group PR (appeared mid-sweep): after #1556, its remaining delta
  = grimp 3.15 + fastapi 0.139/uvicorn 0.50 (botsite + dashboard); conflict-resolved on-branch,
  auto-merge armed, merged on green.

**Codex rebuild reviews (5):** #1695 (sanity) · #1696 (decision-log consistency) · #1697
(ultracode-outputs review) · #1698 (Stage-2 readiness) · #1699 (verification strategy). #1698 was
already green → merged as-is. The other four failed `check_docs --strict` (invalid `review` badge +
orphan/unreachable); fixed on each branch — badge → `audit`, a planning-README link at spaced-out
anchors (parallel-merge-safe), and a **post-review status note** per doc: all five were written
2026-07-03, *before* the design bridge (#1708) and the Gate-0 grammar-freeze + Phase-B L0 build-order
(#1716), so their Gate-0-blocker / owner-question / oracle-spec items were **not consumed** by that
freeze — each note routes readers to reconcile against the Gate-0 packet before acting. All merged.

**Codex June audit (1):** **#1509 closed with reason** — the band-#1530 pass had already harvested
its one actionable thread (#1510) and flagged it "owner merge-or-close"; verified stale against
today's source (its top finding, unwired `light_radius`/`luck`, is resolved — `_UNWIRED_STATS` is
empty; recon marker 5 passes behind; S3 lane pre-rebuild-arc). Reversible if the owner wants it as
a dated record.

**Session PR #1719** — this card + ledger entries + the session idea.

## ⚑ Self-initiated

- The **three-place toolchain bump** on #1556 (the alternative was realigning `requirements-dev.txt`
  back down to 0.15.14, the #1315 precedent) — chosen because it's the durable fix (dependabot
  re-opens the bump forever otherwise), and verified end-to-end locally before pushing.
- Closing **#1509** instead of merging it (evidence above; the sweep's "properly merged" mandate read
  as "properly dispositioned" for a stale, already-harvested snapshot).

## 💡 Session idea (Q-0089)

[`docs/ideas/dependabot-automerge-enabler-2026-07-04.md`](../docs/ideas/dependabot-automerge-enabler-2026-07-04.md)
— extend the auto-merge-enabler to `dependabot/**` PRs: CI (full suite on the bumped install) is the
gate, and the `tool-pins` guard already holds the dangerous drift class red. Worth having because
this exact session was the manual version of that workflow: five days of green dependency PRs
piling up, breeding one conflict and one closed-and-recreated duplicate. Workflow edit ⇒ owner-gated.

## ⟲ Previous-session review (Q-0102)

Previous session = the **Gate-0 grammar-freeze** (#1716, merged ~90 min before this sweep started).
Genuinely strong: the fan-out → adversarial-critic → hand-close pattern caught a Q-0120 false-green
*in the amendment checker itself*, and the 6 corrected mis-cites show the re-verification discipline
working. What it missed: it froze the grammar while **five directly-relevant review PRs (#1695–#1699)
sat open and unconsumed** — including #1696's explicit "block Gate-0 until clarified" list (authority
vocabulary, C-1 contract, preset semantics) and #1699's "block Phase B until oracle specs exist"
list. Nothing in the workflow makes a consolidation session scan *open PRs* for unmerged review
input (the claim/PR scan is lane-overlap-only). **Concrete improvement:** freeze/consolidation
session prompts should include one `list_pull_requests` content-scan for open review docs targeting
the artifact being frozen — and the cheaper systemic fix is merging review docs fast (this sweep +
the dependabot-automerge idea both push that way).

## 🧹 Grooming (Q-0015)

Consumed by the sweep itself: the 14-PR disposition *was* a backlog-grooming pass over the repo's
open-PR backlog (including retiring the stale #1509 audit whose tails are already tracked in the
sector queues). No separate `docs/ideas/` promotion this session — capacity honestly spent.

## 📋 Docs audit (Q-0104)

- `check_current_state_ledger.py --strict` — green after adding the two grouped Recently-shipped
  entries (dependabot batch · Codex-review batch, both crediting #1719).
- `check_docs --strict` — green locally (idea file linked from the ideas README; the five review
  docs linked from the planning README on their own branches; badges valid).
- Claim file deleted at close. Recently-shipped is over the 20-entry soft ratchet (pre-existing;
  the next Q-0107 pass at #1740 trims).
