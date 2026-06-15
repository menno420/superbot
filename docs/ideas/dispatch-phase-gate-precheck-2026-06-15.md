# Dispatch-side phase-gate pre-check — don't fire agent-feature work orders in fix-phase

> **Status:** `ideas` — proposal, **not** approval. Written by the Claude Code routine that
> received a `CLASS: feature` work order ("Implement Mining Phase 2 — Forge/Vault/Home +
> skill-tree") on 2026-06-15 while the repo was in **fix-phase**. Binding contracts +
> `docs/current-state.md` win.
>
> **⚠ Correction (2026-06-15, owner-directed, same session):** the premise below — that the
> gate "correctly" refused the dispatched feature — is **wrong**, and the owner said so directly.
> A *dispatched* work order is **owner-directed**, and the phase gate (Q-0114) only gates
> **agent-self-originated** features; owner-directed correctness/feature work flows freely (the
> exact distinction `routine-system-improvements-2026-06-14.md` Priority 5 flagged). The routine
> then **built the feature** (mining Slice D skill tree, #891). So the real, sharper idea is
> **§ "The deeper fix" below**: teach the routine prompt + phase-gate doc to treat a *dispatched*
> feature as owner-directed (ungated), and reserve the gate for features the agent invents on its
> own. The dispatch-side pre-check is still a fine *efficiency* guard for genuinely
> agent-originated features, but it must NOT block dispatched ones — that was this run's mistake.

## The concrete event this captures

A feature work order arrived via the dispatch fire endpoint. The executor side did the
**right** thing per the routine prompt: ran `scripts/check_phase_gate.py --require-invent`,
got **exit 1 (fix-phase)** — 2 OPEN bugs + 28 `Not Done` readiness rows — and refused to
build, because agent-*originated* features are gated until correctness work clears (Q-0114).
The work was already captured anyway: the turn-key
[`planning/mining-structures-skill-tree-plan-2026-06-14.md`](../planning/mining-structures-skill-tree-plan-2026-06-14.md)
covers Forge/Vault/Home + skill-tree as source-verified PR-sized slices.

So the run shipped **nothing buildable** — by design, correctly. But two things were wasted:

1. **A whole dispatch was burned** on work the dispatcher could have known was out of season.
   The limited daily routine budget (routine-system-improvements Priority 5, "productive once
   started") was spent capturing-and-stopping on an already-captured plan.
2. **A prior run (#888) left an orphan.** That run received the *same* dispatch, **skipped the
   executor phase gate**, and opened a "slice opener" docs PR pretending to tee up build
   work — a thin duplicate plan in the wrong dir (`docs/plans/` vs the repo's `docs/planning/`),
   stuck `in-progress` (born-red), on a non-`claude/*` branch so it could never auto-merge.
   An un-gated feature dispatch is exactly what produces this kind of stuck artifact.

## The proposal — gate at the dispatcher, not only the executor

The phase gate today is an **executor-side self-guard**: each routine runs
`check_phase_gate.py` *after* it has already spent a fire. Move a copy of that check
**upstream into the dispatch step** (Hermes' `superbot-dispatch` skill):

- Before firing a work order classified `CLASS: feature` (agent-originated), run
  `scripts/check_phase_gate.py --phase`. If it returns `fix`, **do not fire that feature** —
  instead either (a) re-route to the standing fix-phase queue (current-state ▶ Next action →
  else an OPEN bug-book item → else backlog grooming, the same ladder the executor falls back
  to), or (b) hold the feature in a "queued until invent-phase" list and fire it automatically
  when the gate next flips to `invent`.
- `CLASS: fix | ux | docs | correctness` always fire (they flow freely in fix-phase) — the
  pre-check only gates `feature`.
- Keep the executor-side gate as the **backstop** (defense-in-depth): the dispatcher can be
  wrong or stale, so the executor still refuses if it somehow receives a gated feature. The
  point is to stop *wasting the fire*, not to remove the safety net.

This is the dispatch-edge complement to routine-system-improvements Priority 3 ("make Hermes
use the dispatch contract it already has") and Priority 5's owner-vs-agent clarity: Hermes
already *classifies* by `CLASS:`; it should also *check season* before firing the one class
that can be out of season.

## Why it's worth having

- **No burned fires on out-of-season features** — the scarce daily budget goes to in-season
  fix/UX/docs/correctness work that actually moves the phase gate toward invent-phase.
- **No more #888-class orphans** — a feature that never fires in fix-phase can't produce a
  stuck "slice opener" PR.
- **Cheap and reuses an existing primitive** — `check_phase_gate.py --phase` already prints
  `fix`/`invent`; the dispatcher just reads one line and branches. No new contract.

## The deeper fix (the one the owner correction points at)

The pre-check above treats the *symptom* (a feature fired in fix-phase). The **root** is a
classification gap: the routine prompt says "`CLASS: feature` → run `check_phase_gate
--require-invent`; if fix-phase, capture-and-stop," with no branch for **who originated the
feature**. But the phase gate (Q-0114, and `check_phase_gate.py`'s own docstring) gates only
**agent-self-originated** features — *"refuse to originate a new feature until correctness work
is done."* A **dispatched** work order is the owner asking for it = owner-directed, which flows
freely like bug/UX/docs/correctness work. This run (and the #888 run before it) collapsed the
two and wrongly gated owner-directed work.

**Concrete change:** in the routine prompt's `feature` branch, split on origin —
- **dispatched / owner-directed feature** → build it (no phase gate; it's owner-directed, the
  same lane as a bug fix), open a PR, and **leave merge to the owner** if the change is large
  or risky (the existing approve/deny posture), or auto-merge if it's contained + test-covered;
- **agent-self-originated feature** (the agent invents it mid-session) → *then* run the phase
  gate; fix-phase ⇒ capture-and-stop.

Mirror the same one sentence into the phase-gate doc and `check_phase_gate.py`'s help text so a
literal agent can't repeat the mistake. (This is the same "owner-directed vs. agent-originated"
clarity `routine-system-improvements-2026-06-14.md` Priority 5 asked for — now with a live
failure proving it's load-bearing, not theoretical.)

## Recurrence #3 + the discoverability gap (2026-06-15, the #897 run)

A **third** dispatched mining-feature work order arrived ("Implement Mining Slice A — Vault v2")
while the gate read FIX. The #897 routine made the **right** call — it built the feature (Vault v2
soft-cap + vault-cap upgrade, #897) — but only after **grepping `docs/ideas/` and finding the ⚠
Correction at the top of *this* file**. That is the real remaining gap: the owner's decision
("a *dispatched* work order is owner-directed and flows freely; the gate is for *agent-self-originated*
features") currently lives **only** in a `status: ideas` file. A literal agent reading just its
routine prompt (which says, verbatim, `feature (agent-originated) → if fix-phase, capture-and-stop`)
+ CLAUDE.md + current-state would **not** find it, and could repeat the #888 mistake (gate a
dispatched feature) — or, worse, the inverse (build an actually agent-invented feature in fix-phase).

**The cheapest high-value fix is canonical homing, not mechanism:** promote the
dispatched-vs-agent-originated distinction into a discoverable, authoritative home —
- a numbered **router Q-block** (it is effectively a Q-0114 *scope clarification*, owner-decided), and
- one sentence in **`scripts/check_phase_gate.py`**'s help/docstring + the phase-gate doc:
  *"This gate is for **agent-self-originated** features. A **dispatched** work order is
  owner-directed and is NOT gated — build it like a bug fix."*

Then the routine prompt's `feature` branch (and any agent) resolves the ambiguity from a canonical
source instead of from a grep into the ideas backlog. (Mechanism — the dispatch-side pre-check
above — is still worth doing, but it is the *efficiency* layer; canonical homing is the
*correctness* layer and is a one-paragraph docs change.)

## Routing

- Mechanism (add the pre-check to the dispatch skill) is a small Hermes-side change once the
  shape is endorsed; relates to **Q-0137** Thread 1 (Hermes dispatch wiring, owner-undecided)
  and the `routine-dispatch-and-staged-reconciliation` capture. No owner decision is strictly
  required to add a *guard* that only prevents wasted/incorrect fires — but flag it under
  Q-0137 since it touches Hermes' dispatch behavior.
