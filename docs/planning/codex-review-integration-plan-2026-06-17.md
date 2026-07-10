# Plan — Codex review integration: routines fix flagged issues first; Hermes scans PRs (issue-only)

> **Status:** `historical` — **FULLY EXECUTED 2026-06-19 (PR #1132, lane B5).** Owner-directed
> 2026-06-17 (**Q-0174**). Builds on Q-0171 (Codex live) + the
> born-red-timing finding ([`codex-automated-pr-review-2026-06-17.md`](../ideas/codex-automated-pr-review-2026-06-17.md)).
> Source + binding contracts win over this plan.
>
> **Both parts shipped 2026-06-19 (PR #1132, lane B5):**
> - **Part A** — the "check Codex first, verified" first-priority step is in BOTH routine prompts:
>   the **dispatch** routine ([`hermes-dispatch-bridge.md`](../operations/hermes-dispatch-bridge.md)
>   § "The routine's saved prompt", step 1b) and the **reconciliation** routine
>   ([`autonomous-routines.md`](../operations/autonomous-routines.md) § "superbot docs reconciliation",
>   STEP 1b — docs defect fixed in pass, runtime bug captured to the bug-book). These are the in-repo
>   canonical mirror; the **owner re-pastes** each into its routine's console config to take effect.
> - **Part B** — the `superbot-pr-check` Hermes skill is built:
>   [`hermes-skills/pr-check.md`](../operations/hermes-skills/pr-check.md) (doc = source of truth, house
>   style) + an `EXTRAS` entry with the 6H `schedule "0 */6 * * *"` in `scripts/hermes/build_skills.py`
>   + a README row + the regenerated `scripts/hermes/skills/pr-check/SKILL.md`. **Issue-only** (no merge
>   or dispatch authority). **Owner manual step:** redeploy on the VPS
>   (`bash scripts/hermes/install-skills.sh` + restart `hermes-gateway`) to activate the schedule.

## Owner directive (2026-06-17)

- **Every routine's first priority: check recent PRs for Codex's comments and fix anything Codex
  flagged — verified, never blindly** (Claude verifies by default; stated explicitly here so it's a
  rule, not a habit).
- **Hermes on a 6H timer checks PRs and OPENS AN ISSUE** for real problems. **NOT auto-dispatch** — it
  "dispatches only on command" until it is proven a valuable dispatcher.
- **Budget rationale (why issue-only):** only **~15 routine fires/day** (~12 scheduled dispatch, ~1–2
  reconciliation). Routine fires are scarce, so Hermes must never burn one on a false positive. Hence
  the issue-only default + the "real bug" bar below.

## What counts as a "real bug" / actionable flag (the bar)

A Codex/bot review comment (or CI signal) is **ACTIONABLE only if ALL** hold:

1. **Verified against current `main` source — real *now*, not an artifact.** Reject the common non-bugs:
   - **the born-red timing class** — Codex reviews the *card-first* commit *before* the code lands, so
     it flags "implementation missing / flip the card / script doesn't exist" (the #1023/#1024/#1027
     false positives); an `is_outdated` thread; a since-fixed line.
2. **A genuine defect or contradiction** — one of: a **correctness bug** (wrong behaviour / crash /
   broken contract or invariant) · a real **architecture/ownership violation** (services→views, raw SQL
   outside `utils/db/`, an unaudited mutation) · a **docs-vs-code contradiction or stale-fact drift**
   that would mislead an agent (e.g. the `/session-close` cadence Codex caught) · a **security / safety /
   privacy** gap.
3. **Not a nitpick / preference / false positive** — "could be cleaner", speculative "might want to", or
   anything the repo's own checkers already pass is **not** a real bug.

**Unsure → open an issue describing what you found; do not dispatch.** Never act blindly — the bot is
one input, verified against shipped source (Q-0120).

## Part A — routines check Codex first (prompt change) — ✅ SHIPPED (PR #1132)

Add to the **dispatch** + **reconciliation** routine prompts a first-priority step: *before* taking new
work, scan the **few most-recent merged PRs (and any open ones)** for **unresolved** Codex/bot review
comments; apply the bar above; **fix the verified-real ones first** (they jump the queue like a bug).
Bounded read (the recent PRs, not the whole history) to respect the token budget. A born-red
false-positive is acknowledged-and-skipped, not "fixed."

### Where Codex's edits live — read its COMMENT, don't hunt for a PR/branch (owner-confirmed 2026-06-17)

**Codex cannot push a branch or open a PR autonomously** — a human must press "create PR" in the Codex
UI for anything to land. So when its auto-review runs a "task / make changes," the result is a
**comment**: a summary + a *proposed* diff + a `[View task →]` chatgpt.com link, describing changes in
**Codex's own sandbox copy** — even when it says "Committed `<sha>`" / "Created PR." **Nothing reaches
our repo.** Therefore an agent acting on a Codex flag:
- reads the **proposed change from Codex's comment** (the diff / the `file·Lnn` references it cites),
- **verifies each against current `main`** (the bar above),
- **applies the real ones itself** (one writer per file — the agent's own PR),
- does **NOT** hunt for a Codex-pushed branch or a Codex PR (there is none — that hunt was the only
  real friction Codex caused, a verification detour on #1032).

## Part B — Hermes 6H PR-check skill — ✅ SHIPPED (PR #1132)

A new hermes-skill `superbot-pr-check`, self-scheduled **every 6H** (`blueprint.schedule "0 */6 * * *"`),
that:

1. Lists open + recently-merged PRs; for each reads Codex review comments, CI status, unresolved review
   threads.
2. Applies the **"real bug" bar** above.
3. For each real bug → **opens a GitHub issue** (clear title · the PR/file/line · what's wrong · which
   bar clause it meets), labelled so the dispatch routine can pick it up as a bug-book-class item.
4. **Does NOT auto-dispatch a fixer.** Dispatch happens only on the owner's command (or a routine
   picking the issue up on its normal fire).
5. Output in the plain-language **house style** (`_house-style.md`).

**Build steps (when a routine executes this):** `docs/operations/hermes-skills/pr-check.md` (doc =
source of truth) + an `EXTRAS` entry with the 6H `schedule` in `scripts/hermes/build_skills.py` +
a README row + rebuild. **Owner manual step:** redeploy on the VPS (`install-skills.sh`).

**Graduation:** once Hermes's issues prove consistently real (a few cycles), revisit **auto-dispatch on
a real bug** — a later owner decision, not part of this build.

## Verification / rollback

Docs + prompt edits are fully reversible. The skill is additive and **issue-only** (no merge or
dispatch authority), so it is low-risk; it never gains dispatch authority without an explicit owner
decision. The routine `@codex review`-on-final-head idea (codex idea doc) is the complementary fix that
makes Codex's *code* reviews land on the complete diff instead of the born-red opening commit.

## Part C — the @codex review relay (owner directive Q-0258, 2026-07-10)

Whenever a session has a question that is **review-worthy but not owner-only** — it would
otherwise have parked it for the owner, yet it is not product intent, not irreversible,
not external/money — it **relays the question to Codex on the PR** instead of the
owner-queue. The owner-queue keeps only genuinely owner-only items; Codex becomes the
named standing drainer of the post-merge review convention (EAP program review §5.2).

**Relay comment template** (post via `add_issue_comment` on the session's own PR):

```
@codex Review request from an autonomous session.
Context: <2–3 lines — what this PR does and where the doubt sits>.
Question: <the ONE specific thing you want checked — a diff hunk, a design choice,
a claim to refute>.
Please reply with findings on this PR. A follow-up session will verify your reply
against source before acting (house rule: cross-agent output is input to verify).
```

Rules: one relay = one specific question (not "review everything"); relay on the **final
head** (after the card flip), so Codex sees the complete diff; the receiving/next session
treats the reply per **Q-0120** — verify against source, never obey. Owner-side
prerequisite: Codex GitHub integration enabled per repo (owner is rolling this out to all
valuable repos). Fleet propagation: round-3 launch pack §1 orders the manager to mint the
matching playbook rule.
