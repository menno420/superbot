# Map every idea (and bug) to its cog / command

> **Status:** `idea` — **owner-directed (2026-06-19)**, captured during the website two-site-split fan-out.
> Near-term effort: *"start correctly mapping each idea to a command or cog as fast as possible (not
> rushing)."* Foundational to the bot site's discoverability + status features.

## Why

The site's vision (website plan §"Site identity & experience") wants, per command:
- **status** — `in-progress` if the command has **any related ideas or bugs**, else `finished`;
- **linked ideas** — the ideas/plans for that command/cog, surfaced right where the command lives.

Both require a **reliable mapping idea → cog/command** (and bug → cog/command). Today there is none — the
v1 browser (unit S1.1) uses a **heuristic** (subsystem-level name-match) as an interim. The heuristic is
approximate; the owner wants the **real, correct mapping**, built deliberately over time.

## Mechanism (recommended)

1. **Authoritative tag at the source.** Add an explicit `subsystem:` / `cog:` / `command:` field to each
   `docs/ideas/*.md` (and each bug-book entry) — front-matter or a one-line header field. The producer
   (`export_dashboard_data.py`) reads it; no guessing.
2. **A validator** (`scripts/check_idea_mapping.py`, stdlib, Q-0105-disposable): every idea/bug maps to a
   **real** cog/command/subsystem (resolved against the subsystem registry), and flags unmapped ones — so
   the mapping is *checkable* and the backlog of "still unmapped" is visible and drains.
3. **Heuristic as fallback only.** Where no explicit tag exists yet, the subsystem name-match heuristic
   fills in (clearly marked lower-confidence), so the site degrades gracefully while the mapping is filled.

## Effort shape ("fast as possible, not rushing")

- ~80+ ideas + the bug book to map — do it in **batches**, correctly, not in one rushed pass.
- A small **assist tool** can *propose* a mapping per idea (from its text + the subsystem registry) for a
  human/agent to confirm — turning a manual slog into a review.
- Each mapped batch immediately sharpens the site's `status` + `linked_ideas` accuracy (incremental payoff).

## Connections

- Feeds the v1 browser's `status` + `linked_ideas` (S1.1) — replacing the interim heuristic with truth.
- Shares the key with **per-command feedback threads** (`per-command-feedback-threads-2026-06-19.md`):
  notes/threads key on the same cog/command identity, so one mapping serves both.
- Complements the existing subsystem registry (cog→subsystem) — this adds the idea/bug→cog/command edge
  that registry doesn't carry.

→ relates: `scripts/export_dashboard_data.py` (`build_site_subset`) · the subsystem registry ·
`docs/ideas/` + the bug book · website plan unit S1.1.
