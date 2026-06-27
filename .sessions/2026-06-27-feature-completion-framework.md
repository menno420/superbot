# 2026-06-27 — Feature-completion certification framework (S1 bot units)

> **Status:** `complete`

## Arc

Owner-directed in-session: a way to mark parts of the bot **complete** — feature- and UX-complete
("all the functions, the right buttons in the right places, works as intended, the most convenient
version of itself") — and to *prove/show* it, with a standing bias toward **finishing existing
features before new ideas**. Designed it, surfaced the three real forks via `AskUserQuestion` (owner
picked per-feature grain · soft completion-first · evidence + owner sign-off → **Q-0209**), then built
the whole system in PR #1513.

The key reframe that shaped everything: this is a **different axis** from the existing
`docs/planning/production-readiness/` maps. Those grade *risk/hardening* (P0/P1/P2). This grades
*feature + UX completeness* and ends in the owner's judgment. A unit is "done-done" only when high on
both.

## Shipped (PR #1513)

- **`docs/planning/feature-completion/README.md`** — the system: the two-axes reframe, the
  per-feature unit model (registry-keyed), the `▢ → ◐ → ✔` state machine + evidence/sign-off bar,
  the soft completion-first policy, and the **completion ledger** of all **36 S1 units** (1 assessed,
  35 unassessed, 0 certified).
- **`rubric-game.md`** + **`rubric-server-function.md`** — the two Definition-of-Complete checklists,
  grounded in `command-integration-standard` / `hub-ui-standard` / `config-input-standard`, each with
  a copy-paste certificate template.
- **`units/blackjack.md`** — a real, source-assessed worked pilot (◐ assessed; 5-item punch-list,
  including one genuine product decision: split/insurance/surrender → build or owner-waive).
- **`scripts/completion_scoreboard.py`** + `tests/unit/scripts/test_completion_scoreboard.py` — a
  generated certified-% scoreboard mirroring `readiness_scoreboard.py` (5 tests).
- **Wire-ins:** router **Q-0209** · `docs/ideas/README.md` § "Completion-first gate" · an
  `AGENT_ORIENTATION` task route · the games folio · the planning index · an S1 sector posture note.

## Decisions made alone (owner ratify if wrong — all reversible docs/tooling)

- **Unit families + scope:** 36 units across 7 families; **BTD6 (S2) + Project Moon excluded** as
  knowledge domains (own sector/folio), and routing-only hubs / dev-internal subsystems excluded as
  infrastructure. (Per-feature grain itself was Q-0209.)
- **Certificate badge** = `living-ledger`; **policy home** = the system docs + `ideas/README` + the
  router decision, **not** a CLAUDE.md binding rule — deferred to a future DISCUSS Q per the
  graduate-when-proven pattern (Q-0105). Did **not** self-edit CLAUDE.md/executable config.

## Context delta

- **Needed but not pointed to:** the `production-readiness/` map set + `readiness_scoreboard.py` were
  the critical prior art to avoid duplicating, but no orientation route says "completeness/maturity
  tracking lives there." → fixed: added a "Marking a feature complete" route to `AGENT_ORIENTATION`.
- **Pointed to but didn't need:** `hub-ui-standard` / `config-input-standard` — referenced by pointer
  in the rubrics but `command-integration-standard` (esp. § "Game panel requirements") carried the
  bulk; didn't need to read them in full.
- **Discovered by hand:** a second scoreboard parser must **not** strip glyphs (only whitespace +
  `*`, like `readiness_scoreboard`) or the doc's `▢ unassessed` example cells get miscounted — now
  encoded in the script docstring + a dedicated `test_glyph_prefixed_cells_are_not_counted`.

## 💡 Session idea (Q-0089)

`completion-ledger-registry-parity-guard-2026-06-27.md` — a stdlib checker asserting every
user-facing registry game/server-fn key has a completion-ledger row (and vice-versa), so a new game
can't silently miss a certificate. The completeness-axis sibling of `subsystem-inventory-homed-guard`;
reuses the new scoreboard's table reader. Disposable (Q-0105). Indexed in `docs/ideas/README.md`.

## ⟲ Previous-session review (Q-0102)

Reviewing the **btd6-absence-guard-layer-b** session (#1511, Q-0208). **Did well:** it used
`AskUserQuestion` to surface three genuinely owner-gated calls in one round and shipped only the
*safe* slice (grounded-contradiction, no false-floor) while holding the live-needing half — exactly
the act-vs-ask discipline the model wants. **Could improve / system improvement it surfaces:** it left
a third `[needs-live-bot]` item (Setup PR 3b) on the S1 `▶ Next` line, and these
blocked-on-a-live-session items now accumulate across sessions with **no single queue** of "what the
owner should verify next time the bot is up." A cheap system win: a `[needs-live-bot]` aggregator
(grep the sector files + bug book for the tag → one owner checklist), so a single live session can
clear the whole backlog instead of rediscovering it. The feature-completion **live walkthrough** step
shipped this session is adjacent — both need the same "owner-at-a-running-bot" moment, so they could
share one checklist surface.

## 🛠 Friction → guard

A new completion certificate tripped `check_docs` (missing `> **Status:**` badge). Fixed the file
**and** added the badge line to **both** rubric certificate templates — the durable fix (every future
cert is born with it), and `check_docs` already enforces it, so no new guard needed (enforce, don't
exhort).

## Flagged for maintainer (known limits)

- The framework is **proven only on the Blackjack pilot** — one unit assessed, **none certified
  end-to-end**, so the `◐ → ✔` half (live walkthrough + sign-off) is untested in practice.
- Completion-first is a **soft** default living in docs, **not enforced** — a future autonomous
  session could ignore it. Hardening it to a CLAUDE.md line is the noted future DISCUSS Q.
- The ledger is **hand-maintained** (the Q-0089 parity-guard idea addresses that).

## 📤 Run report

- **Did:** built the feature-completion certification framework (system · 2 rubrics · scoreboard ·
  Blackjack pilot · wire-ins) · **Outcome:** shipped
- **Shipped:** #1513 — feature-completion framework for S1 bot units (full CI mirror green locally;
  auto-merge armed, born-red card flipped to complete)
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none blocking — Q-0209 answered live. *Optional future:* promote
  completion-first to a binding CLAUDE.md line (DISCUSS) if you want it enforced, not just default.
- **⚑ Owner manual steps:** none required. *When you want the first `✔`:* make the Blackjack
  split/insurance/surrender call (punch-list #1) and play a live walkthrough for sign-off (#5).
- **⚑ Self-initiated:** none (owner-directed in-session)
- **↪ Next:** drive one near-complete unit to `✔` (clear Blackjack punch-list #2–#4, get owner #1/#5)
  or assess the next game; optionally build the Q-0089 parity guard.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (PR #1513 open; auto-merge armed, CI green locally) |
| CI-red rounds | 0 (ran full `check_quality --full` before first push to green) |
| Repo-rule trips | 1 (missing cert Status badge — fixed + templated) |
| New ideas contributed | 1 (completion-ledger registry-parity guard) |
| Ideas groomed | 0 explicit moves (but added the structural completion-first gate to idea routing) |
