# Session — Hermes follow-up: VPS context-fix script + SOUL size guard

> **Status:** `complete`

## What I did

Continuation after #913 merged. The owner asked for **a script that applies the fixes** (not
manual steps) and added a key data point: even ~5-message, clearly-directed sessions still fail.
That sharpened the diagnosis — it's per-turn **doc volume**, not message count: one large
whole-file read can cross the 50% compaction line in a single turn, and compaction then prunes the
doc Hermes just read. Confirmed the `hermes config set` CLI (dot-notation, validated) via the
upstream config docs so the script edits config safely instead of doing raw YAML surgery.

## What shipped (PR #914)

- **`scripts/hermes/apply_context_fixes.sh` (NEW)** — idempotent, reversible VPS operator script:
  backs up `config.yaml`, sets `compression.threshold` 0.50→0.75 + `compression.protect_last_n`
  20→30 + attempts `prompt_caching.cache_ttl 1h` via `hermes config set`, re-installs the
  sync-fixed SOUL.md, runs `hermes config check`, reminds to restart the gateway. `--dry-run` and
  `--set-model=` flags. Provenance + kill-switch header (Q-0105).
- `scripts/hermes/install-soul.sh` — SOUL.md size guard: warns >budget, infos >80%, override via
  `HERMES_SOUL_BUDGET` (default 8000). Confirmed it fires the >80% line for the current 6478-byte
  prompt.
- `docs/operations/hermes-token-efficiency-investigation-2026-06-15.md` — the owner's 5-message
  data point + sharpened levers (raise `compression.threshold`, larger-window model, read doc
  SECTIONS not whole files) + a pointer to the new script.
- **Verified:** `apply_context_fixes.sh --dry-run` is side-effect-free and prints the plan; the
  size guard fires; `check_docs --strict` ✓. **Caveat:** the `hermes config set` calls can't be
  exercised here (no Hermes on this container) — only `--dry-run` was tested.

## Handoff / next

- **Maintainer action (VPS):** `bash scripts/hermes/apply_context_fixes.sh` (try `--dry-run`
  first), then `sudo systemctl restart hermes-gateway`. Consider a larger-context-window model.
- The deeper bounded-re-grounding gateway fix stays a documented plan (not approved to build).
- BUG-0011 (gateway crash-loop) still OPEN.

## 💡 Session idea (Q-0089)

**A Hermes "context self-check" skill/command.** A read-only skill Hermes runs at session start
that reports its own context health: current model + window, `compression.threshold`, SOUL.md
bytes vs budget, and "≈N% headroom before compaction at this fill." Compaction is *invisible*
today (the root cause of the owner's frustration — Hermes silently forgot and never said so);
making the budget legible lets Hermes (and the owner) SEE when a turn is about to lose its
grounding and proactively `/new`. Dedup-checked `docs/ideas/` + `hermes-skills/` — none cover
Hermes introspecting its own context budget. Small: one skill reading `hermes config` + `wc -c`.

## ⟲ Previous-session review (Q-0102)

Previous: `2026-06-15-hermes-research-deepening.md` (#913). It nailed the root cause (compaction,
not overflow), verified against Hermes source rather than the report, and fixed the sync bug —
strong. **What it could have done better:** it stopped at *documenting* the VPS config knobs; the
owner's very next message was "just give me a script." **System improvement:** when a session's
deliverable is "VPS/external config the owner must change," default to also shipping the operator
**script** that applies it — for a non-coding owner a steps-list is a half-deliverable, a script is
the deliverable (the working agreement's "build the path to the goal, don't just describe it"). I
applied that this session; worth making it a standing reflex for control-plane work.

## 📋 Doc audit (Q-0104)

`check_docs --strict` green. The new script is referenced from the investigation doc (discoverable);
its own header is self-documenting. No new owner decision to route (the config values are reversible
suggestions, not decisions). No chat-only content left undocumented — the script + the sharpened
diagnosis are both in the repo. Ledger unaffected until #914 merges; active-work claim updated.
