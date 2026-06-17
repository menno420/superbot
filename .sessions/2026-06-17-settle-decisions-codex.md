# 2026-06-17 — Settle mining/seed decisions + surface Codex's reviews

> **Status:** `complete`
> Manual session (owner-live), context-conscious: settle decisions/ideas, let the routines finish the
> build after the weekly reset. Docs-only. Born-red per Q-0133; flipped to `complete` after CI green +
> the Codex-integration follow-up (Q-0174) + 3 verified Codex-flagged drift fixes landed.

**Branch:** `claude/settle-decisions-codex`

## Goal

Two owner asks: (1) document the current decisions/ideas so the routines can build them after the
weekly limit reset; (2) surface what Codex replied on a PR (the owner flagged it; I'd claimed I could
read Codex's reviews directly — time to prove it).

## What was done

**Codex reviews — found them + verified I read them directly.** Codex left real inline review comments
(P1/P2 severity badges) on #1023 / #1024 / #1027 / #1028. Two classes:
- **Genuine catches on docs/plan PRs (#1028):** 2 of its 4 points **verified correct and fixed this
  session** — `/session-close` still said "10th-PR / ~9 PRs" (stale vs. the 30-PR / full-band cadence,
  Q-0134/Q-0164), and the procedures-to-skills plan wasn't on `roadmap.md` (routines wouldn't discover
  it). All 4 catches folded into the plan.
- **Born-red false-positives (#1023/#1024/#1027):** Codex reviews on PR *open* = our card-first commit,
  *before* the code lands — so it flagged "implementation missing / flip the card / script doesn't
  exist," all `is_outdated` noise. Captured the fix (trigger `@codex review` on the final head) in the
  Codex idea doc as an owner call.

**Decisions settled:**
- **Q-0173 — mining grid world = seed-deterministic procedural** (owner picked option #1 over literal
  Minecraft-terrain replication). Recorded in the router + the mining-hub-redesign plan (resolves the
  "fixed vs procedural" question; other grid-Mine design Qs stay owner-pending).
- Vault cap = soft / warning-only (recorded #1031).

**Routine-discoverability (so the routines can finish the job after the reset):**
- Added the **procedures→skills conversion plan** to `roadmap.md` S4 (Codex catch #4).
- Folded Codex's 4 review notes into the procedures-to-skills plan for the batch executors.
- Fixed the `/session-close` cadence drift (Codex catch #1).

## Left open / owner-pending (for after the reset)

- **Grid-Mine design Qs** (Q-0173 tail): shared vs per-level grid · do moves cost a turn? · cell-yield
  ↔ depth bands. **Fishing design Qs** (Q-0172): own loot ladder vs reskinned · water-gated? · rod on
  the character doll? **Mining lane order:** hub declutter (PR2) recommended first.
- **Buildable queue for the routines:** mining hub-declutter (PR2) · grid Mine (PR3, seed) · skills
  batches 2–4 · Hermes house-style remaining skills · fishing plan. All on the roadmap + planning docs.

## 💡 Session idea

**Idea:** a tiny GitHub Action (or a line in `auto-merge-enabler`) that posts **`@codex review` when a
`claude/*` PR's session card flips to `complete`** (the final head), so Codex reviews the *complete*
diff instead of the born-red opening commit. **Why:** today Codex's auto-review fires at PR-open, which
in our born-red flow is the card-only commit — wasting most of its code reviews on incomplete state
(the #1023/#1024/#1027 false positives). Re-triggering on the final head turns Codex into a real
second-reviewer on the actual diff. Pairs with Q-0171.

## ⟲ Previous-session review

The previous run (#1031, the preview tool) was a strong self-initiated call — pure tooling that solved
the owner's stated pain. **What it (and I) missed:** it never checked whether Codex had reviewed the
recent PRs, so the owner had to prompt me about Codex's reply. **System improvement:** when a session
touches subscribed-PR activity, it should proactively sweep for **bot reviews (Codex/Copilot) on its
own + recent PRs before closing**, not wait to be asked — fold a "check bot reviews" line into the
`/session-close` audit.

## 📤 Run report

- **Did:** settled the seed decision (Q-0173) + the **Codex-integration directive (Q-0174** — the "real bug" bar + the issue-only Hermes-PR-check spec); surfaced/verified Codex's reviews + **fixed 3 real drift items it flagged** (`/session-close` cadence · roadmap "~9 PRs" · the manifest card's `Previous-slice`→`Previous-session` heading); made the buildable lanes routine-discoverable · **Outcome:** shipped
- **Shipped:** (this PR) — docs-only settle (Q-0173 · Codex feedback folded · session-close drift fix · roadmap homing)
- **Run type:** `manual`
- **⚑ Owner decisions needed:** grid-Mine + fishing design Qs (Q-0173/Q-0172 tails); **Codex mode** — keep it comment-only or allow its "open a fix PR" mode? (Q-0174); whether to switch Codex to review-on-final-head
- **⚑ Owner manual steps:** (optional) set the Codex connector to review on the final head (or we add the `@codex review`-on-complete Action)
- **⚑ Self-initiated:** `none` (both tasks were owner-asked: document decisions + surface Codex) (Q-0172)
- **↪ Next:** routines build the queue after the weekly reset; you answer the grid-Mine / fishing design Qs when ready

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 3 (#1029/#1030/#1031); this docs PR is the 4th |
| CI-red rounds | 0 (born-red gate only) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (`@codex review` on card-complete) |
| Ideas groomed | 1 (seed decision Q-0173 settled; vault-cap closed) |
