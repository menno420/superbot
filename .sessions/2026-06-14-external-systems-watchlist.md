# Session: external-systems watchlist — what to learn from & re-check

> **Status:** `complete`

**Branch:** `claude/modest-ptolemy-2xipoh` · **PR:** #856 · **Date:** 2026-06-14 · **Type:** owner-directed docs (manual)

## What this session did
Owner asked me to document the external AI systems / workflows worth learning from (the shortlist I
gave in chat) as a **living watchlist** a future session can occasionally re-check for new ideas,
and to decide the home myself since future-self must find it.

### Shipped
- **New `docs/research/` folder** — the durable home for *external* intelligence (vs. `docs/ideas/`
  for our own). `README.md` doubles as the reachability root.
- **`docs/research/external-systems-watchlist.md`** (`reference`) — 7 lesson-first entries (Voyager
  · Reflexion · Generative Agents · MemGPT/Letta · SWE-agent/SWE-bench · OpenHands/Devin/Factory ·
  human eng-org practice) + 2 lighter watches (LLM-as-judge for the Hermes seam · multi-agent
  frameworks). Each entry = one transferable lesson + **our adoption status (have/partial/gap)** +
  where to check for new output. Honest framing up top: we're ahead on memory/governance, not the
  execution loop — weight ideas that strengthen the former.
- **Re-check loop** = grooming-driven (no new routine, which would be executable-config): a
  `Last reviewed:` header + a "pick one entry per grooming sweep" convention. Wiring it into the
  reconciliation pass is flagged as a **proposed** Q-block, not self-applied.
- **Discoverability wiring:** cross-linked from `AGENT_ORIENTATION.md` (reference list) and the
  `autonomous-improvement-loop-vision` idea (bidirectional). Verified reachable by `check_docs --strict`.

### Home decision (mine to make)
`docs/research/` over `docs/owner/`: this is agent-facing learning material, not owner intent/routing.
A future session lands on it three ways — the orientation reference list, the loop-vision idea, and
the grooming sweep that re-checks it. README-as-root guarantees it never orphans.

## 💡 Session idea (Q-0089)
**Register the watchlist with `scripts/check_doc_freshness.py` so its `Last reviewed:` date emits a
soft staleness nudge** once it passes a threshold (e.g. 30 days) — turning the "re-check on grooming"
convention into a visible signal an agent actually sees, instead of a rule it must remember. Composes
existing tooling (the freshness checker already exists); small/safe grooming-lane candidate. Dedup-grep
of `docs/ideas/` confirms no existing freshness-nudge idea for this doc class.

## ⟲ Previous-session review (Q-0102)
Reviewing **#853 (workflow-routine audit, this same branch):** strong — it corrected real
control-plane drift with *live GitHub evidence* (not assumption) and shipped `check_loop_health.py`
so that table can't silently drift again. **What it missed:** it pushed with only
`check_quality --check-only` (formatters), and CI then caught two real breakages — stale cadence
tests (a test that *encodes* the changed constant) and an unrebuilt generated skill artifact. Both
are the same class: **editing a source whose downstream is verified elsewhere.** **System
improvement:** a pre-push / Stop-hook guard that detects "you edited a *generator source* (a
`*.md` skill, `index.yml`, a constant with a paired `test_*` that hard-codes it) but did not run the
*full* suite / rebuild" — i.e. make the `--check-only`-is-insufficient case a *detected* condition,
not a remembered one. That closes the exact gap that reddened #853's first push.

## Doc audit (Q-0104)
`check_docs --strict` ✓ (249 docs; new `docs/research/` reachable via README root + orientation link)
· `check_current_state_ledger --strict` ✓ · `check_architecture --mode strict` 0 errors (pre-existing
`[known]` xp warnings only). No new owner decision this session (home choice was delegated to me).
**Grooming (Q-0015):** the watchlist itself seeds the grooming sweep with a recurring structured
target — one entry re-checked per spare-capacity pass — so the backlog gains a renewable item.
