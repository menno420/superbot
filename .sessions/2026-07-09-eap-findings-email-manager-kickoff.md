# 2026-07-09 — EAP findings write-back + interim email + manager kickoff

> **Status:** `complete`

Owner-directed (2026-07-09, continued): (1) document tonight's findings durably; (2) draft an
INTERIM Anthropic email locking in the most important findings (owner adds Part 1 before sending);
(3) manager Project launch materials — durable Custom Instructions + a start-off prompt that reviews
all repos, plants the `control/` files, seeds a first status explanation, and emits the per-project
init prompt.

## Shipped

- `docs/eap/fleet-review-2026-07-09.md` — evening update: superbot-next now boots (CUT-1, step-1 live
  PASS, real bug caught on first boot); grade B+ → toward A-.
- `docs/planning/projects-eap-evaluation-log.md` — 3 new entries + feedback-note links.
- `docs/planning/projects-eap-anthropic-email-interim-2026-07-09.md` (new) — interim feedback draft.
- `docs/planning/manager-project-kickoff-2026-07-09.md` (new) — Custom Instructions + start-off +
  per-project init prompt.
- `docs/planning/README.md` — homed the manager kickoff.

## Context delta

1. **Needed but not pointed to:** nothing new — the 7/8 email (read earlier this session) supplied the
   interim-email format and the "rules of the road".
2. **Pointed to but didn't need:** n/a.
3. **Discovered by hand:** `superbot-next` moved fast — **5 new merged PRs (#51–#55)** since my morning
   clone, including CUT-1 (the bot now boots) and the retrospective/testing docs. **Re-fetching the
   target repo before assessing "its review" was essential** — a stale clone would have missed the boot
   entirely. Reinforces the audit-checklist "re-sync + run under the repo's own interpreter" lesson.
4. **Decisions made alone (reversible):** which findings to lock into the interim email; the manager
   kickoff's three-part shape (Custom Instructions / start-off / init) + the "manager seeds `status.md`
   once, then hands off" bootstrap; the grade tick B+ → toward A-.
5. **Genuine weak point:** the manager start-off assumes the manager can write files via the Contents
   API **or** spawn a worker — but the manager-tier session's actual toolset is **unverified** (the eval
   log suggests coordinator-tier may lack GitHub MCP). The prompt handles it (verify + fall back to a
   worker) but it's untested until the manager runs. And the interim email is a draft — "complete enough
   to send" is the owner's call, and Part 1 is his.

## 🛠 Friction → guard

- No substantive friction this slice (one self-corrected Edit-anchor whitespace miss on the eval-log
  header — not worth a guard). `none`.

## ⟲ Previous-session review

The prior slice (fleet-coordination-protocol, #1889) designed the manager as observe+dispatch but
stopped at the design — it didn't ship the concrete "how to actually launch it" (settings text +
bootstrap). This slice closed that gap with the kickoff doc. **Improvement folded in:** a design doc
should ship with its launch companion in the same pass when the owner will act on it soon — the gap
between "designed" and "paste-ready to run" is where momentum leaks.

## 💡 Session idea

**A `bootstrap fleet-init` verb in the substrate-kit** — bake the manager start-off's bootstrap
(review N repos → plant `control/inbox.md`/`status.md` → seed a first status → build `fleet-manifest.md`)
into the kit as one command, so standing up coordination across a fleet is a verb, not a hand-written
start-off prompt. Routed to kit-lab / `substrate-kit`. Natural once the `control/` convention (coordination
protocol §2) ships.

## 📤 Run report

- **Did:** documented tonight's findings + interim Anthropic email + manager Project launch materials · **Outcome:** shipped
- **Shipped:** #1890 — fleet-review evening update · 3 eval entries · interim email · manager kickoff · homing
- **Run type:** `manual`
- **⚑ Owner decisions needed:** is the interim email "complete enough" to send as an in-between? (owner's call — add Part 1 first)
- **⚑ Owner manual steps:** (email) add Part 1 + send from your own mail; (manager) create/point the manager Project + give it write on all repos + paste the Custom Instructions + send the start-off + create per-Project self-poll routines (gate owner-side)
- **⚑ Self-initiated:** none (all owner-directed)
- **↪ Next:** owner stands up the manager (send start-off → per-project init prompts → routines); kit-lab builds the `control/` convention + (idea) a `fleet-init` verb

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 2 (#1887, #1889; this #1890 pending) |
| CI-red rounds | 0 (born-red by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (`bootstrap fleet-init` verb) |
| Ideas groomed | 0 |
