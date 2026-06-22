# 2026-06-22 — Mining grid: dig-moves-you (unified mine+move)

> **Status:** `complete` — shipped; PR #1282 auto-merges on green.

## Arc

Owner design correction in-chat, right after the grid Mine (#1281) merged: *"each mining action
would move you on the grid — mining down goes down one cell, mining forwards goes one cell forward,
etc."* #1281 shipped **separate** movement buttons + a "Mine here" button (built to the
hub-redesign plan's literal "6 movement buttons + Mine here" sketch). The owner's actual model is
**unified directional digging**: mining *is* locomotion.

Reworked it to that model and shipped PR #1282.

## Shipped (PR #1282)

- `mining_workflow.dig(direction)` **replaces** `move` + `mine_here`: resolve the adjacent cell
  (`_resolve_dig_target` — Down light-gated via `world.descend`, Up ascends, lateral always), then
  **move into it AND mine that cell** in ONE transaction (position/depth write + loot grant +
  fog-of-war mark + wear + the down-dig depth-record bonus). `DigResult` replaces `MoveResult` and
  carries the loot; `MineResult.cell_note` is removed (it existed only for the deleted `mine_here`).
- `views/mining/grid_mine_view.py` — the six movement buttons + "Mine here" collapse into **six
  directional dig buttons** (⛏️ North/South/East/West/Deeper/Up); each digs-and-moves, re-rendered
  in place.
- `grid.move_phrase(UP)` → "upward" (reads in "You dig upward and mine …").
- Tests rewritten onto `dig`; the `mine` characterization test stays green (removing `cell_note`
  left `!fastmine` byte-identical). Plan + games folio updated.
- **No command-surface change** (`!mine`/`!fastmine`/`!mineworld` unchanged; buttons are ephemeral)
  → no generated-artifact regen needed (freshness tests stayed green).

## Decisions made alone (ratify if wrong)

- **Every direction digs uniformly** — including Up (you dig upward into the shallower cell). Up is
  never gated; Down is light-gated. Kept symmetric for simplicity.
- **Cells are re-mineable** (infinite) — re-digging a cell yields again; the light/depth ladder is
  the real gate, not depletion. (A "mined-out" depletion layer is noted as a possible future idea.)
- **No pure-move** — there's no "reposition without mining"; mining is the only locomotion (the
  owner's stated model). Reversible if they later want a separate move.

## Context delta (reflection interview)

- **Where orientation/plan fell short:** the hub-redesign plan listed the grid's *controls*
  ("6 movement buttons + Mine here") but not the *interaction model* (does a button move, mine, or
  both?). #1281 built to the literal control list; the owner meant mining-as-movement. The gap was
  "buttons named, behaviour-per-button unstated."
- **Discovered by hand:** `game_xp_service.award` returns `GameXpAward` (I'd guessed `XpAward`) —
  caught by grep before mypy. Minor; no doc change warranted.
- **Pointed to but didn't need:** nothing new — this was a contained edit of code I wrote last
  session, so the file-level context maps were enough.

## ⟲ Previous-session review (#1281 — grid Mine)

- **Did well:** the pure/seam split (pure `grid.py`, audited `mining_workflow`, fog-of-war windowed
  reads) made *this* rework cheap — swapping move+mine_here for one `dig` touched one workflow op +
  one view, with the cell model and DB layer untouched. Good seams pay off immediately.
- **Missed:** it shipped a movement model the owner didn't intend, because I built to the plan's
  literal button list rather than confirming what each button *does*. The plan's "Proposed v1"
  sketch even said "Mine here digs the current cell" — I should have flagged "move vs. mine-here is
  an interaction-model assumption" as a thing to verify, not silently picked the literal reading.
- **System improvement (the session idea below):** a planning convention — when a plan lists UI
  controls, state the *behaviour per control against the model*, not just the label.

## 🛠 Friction → guard

- The genuine friction was **conceptual, not tooling** — a plan-ambiguity that produced a
  build→rework cycle (#1281 → #1282). There's no cheap *enforcing* guard for "did you confirm the
  interaction model?"; the prevention is the planning convention captured as the session idea. No
  tooling guard shipped (inventing a checker for human design-intent would be the wrong tool).

## 💡 Session idea

- **Planning convention: a plan that lists UI controls must state the behaviour-per-control against
  the model, not just the control label.** This session's #1281→#1282 rework happened purely because
  the plan named "6 movement buttons + Mine here" without pinning whether a dig *moves* you. One line
  per control ("Mine here = dig current cell, no move" vs "dig N = move north + mine") would have
  surfaced the fork at plan time. Log-only capture (a convention nudge, not a checker) — promote to
  a router DISCUSS Q if it recurs.

## 📤 Run report

- **Did:** reworked the grid Mine to the owner's unified model — every directional dig moves you
  into the cell and mines it (replaced separate move + Mine-here). · **Outcome:** shipped (PR #1282,
  auto-merge on green)
- **Shipped:** #1282 — mining grid: dig-moves-you
- **Run type:** `manual` (owner in-chat design correction)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (merge auto-deploys). *Optional live check:* `!mine` → the six
  dig buttons; each dig should move you one cell and yield that cell's loot.
- **⚑ Self-initiated:** none — this was an owner-directed correction; no unprompted build/plan.
- **↪ Next:** mining grid v2 = **depth-gated sparse encounters** (own session, owner-paced —
  [idea](../docs/ideas/mining-grid-encounters-2026-06-22.md)); else the current-state ▶ Next action
  queue.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 at write (#1282 auto-merges on green) |
| CI-red rounds | 0 real (born-red hold by design; full suite green locally before the completing push) |
| Repo-rule trips | 0 (formatters clean; arch 0; the `GameXpAward` name caught by grep pre-mypy) |
| New ideas contributed | 1 (planning convention: behaviour-per-control) |
| Ideas groomed | 0 (contained owner-directed rework; no backlog move) |
