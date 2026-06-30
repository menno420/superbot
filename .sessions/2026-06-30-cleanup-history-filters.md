# 2026-06-30 — Cleanup history filters + age gate (completion-first deepening)

> **Status:** `complete`

**Run type:** routine · dispatch

## What this run did
Empty-fire dispatch advancing the S1 completion-first arc (Q-0209). Picked the **Cleanup** unit —
its completion certificate listed four offline punch-list items. Closed the buildable deepening ones
in one focused PR (#1566).

### Cleanup history content-type filters (punch-list #2)
- **`services/history_cleanup.py`** — `build_history_cleanup_plan` gained three content-type sweep
  modes: `embeds` (message has embeds), `links` (URL via `_LINK_RE`), `attachments` (has attachments),
  for Carl-bot/MEE6/Dyno parity. The supported set is now the named tuple `HISTORY_CLEANUP_MODES`
  (one source of truth, imported by the cog for validation).

### Cleanup history age gate (punch-list #3)
- **`older_than: dt.datetime | None`** parameter on the plan builder — a cutoff that composes with
  *every* mode (including the spam second-pass): only messages created at/before the cutoff match.
- **Cog parsing** (`cleanup_cog.py`) — an `older:<duration>` token (`older:7d`/`12h`/`30m`/`45s`/bare
  seconds) parsed by a new `_parse_duration_seconds` helper, stripped from the token stream before the
  mode/keyword resolve (so it never leaks into a keyword search), converted to a cutoff via
  `discord.utils.utcnow()`. Invalid duration → friendly usage message, no sweep. Command docstring +
  the dashboard `usage`/`description` updated to list all seven modes + the age gate.

### Punch-list #1 — already covered (drift corrected, Q-0166)
The cert claimed the panel authority re-check was "covered only via the pipeline backstop." It is
**already pinned** by `test_policy_panel.py::test_apply_button_requires_admin` (non-admin → apply not
called, message sent). No redundant test added; corrected the stale cert note instead.

### #4 deferred, honestly
Making `SPAM_DUPLICATE_WINDOW_SECONDS` a *real* per-guild setting needs a config-input widget — a
constant rename isn't "configurable" in the rubric sense — so it's left for a follow-up, recorded in
the cert. #5/#6 (live walkthrough + owner ✔) stay owner-gated.

### Tests (+12)
- `tests/unit/services/test_history_cleanup.py` — embeds/links/attachments modes, bot-skip,
  unsupported-mode raise, age gate (links + spam-mode composition).
- `tests/unit/cogs/test_cleanup_history.py` — embeds-mode routing, `older:7d` cutoff + query-strip,
  invalid-duration early stop.

## Verification
- `python3.10 scripts/check_quality.py --full` GREEN (after regenerating `botsite/data/site.json` +
  `data.js` — the command docstring feeds the dashboard `commands` family; the freshness test caught it).
- `python3.10 scripts/check_architecture.py --mode strict` — 0 errors.
- `check_current_state_ledger --strict` / `check_docs --strict` — clean (only benign newest-merge lag).

## Handoff — next ▶
The turn-key leaderboard-provider lane is exhausted (prev run) and the operator-command lane (#1561)
+ this Cleanup lane are closed. **Next completion-first slices, all turn-key offline deepening:**
- **Counters** — preset bundles (cert punch #1).
- **Diagnostics** — pagination follow-up for long lists (cert punch #2).
- **Cleanup #4** (deferred here) — surface the spam window as a real setting *with* a config-input widget.
  *(Note: Inventory sort/filter is already CLOSED — #1553 — don't re-chase it.)*
Most remaining cert punch-lists are best-in-class breadth (moderation tempban/case-IDs, economy
shop/items) or owner-gated walkthroughs — pick a contained one and close it; see
`docs/planning/feature-completion/units/`.

## 💡 Session idea
**A `scripts/check_help_usage_quality.py` lint** (or a warn-tier test): flag any registered command
whose dashboard `usage`/`description` (the docstring first line) is generic/duplicated or shorter than
~25 chars. This run's first docstring rewrite accidentally shortened the `cleanuphistory` summary to a
bland "Clean matching channel history." and only the dashboard freshness test caught it incidentally —
a dedicated check would catch low-quality help copy at the source. Small, stdlib, disposable (Q-0105).

## ⟲ Previous-session review
The previous run (#1561, operator command gaps) was a clean, well-scoped completion-first slice — it
routed the two channel *mutations* through the audited `ChannelLifecycleService` seam correctly and
extracted `role_info.py` to keep `role_cog` under the 800-LOC threshold (good arch hygiene, not just
the feature). One thing it could have done: it named "channel slowmode/topic" as a command gap but
those are *also* configurable surfaces — a follow-up could check whether slowmode belongs in the
channel Settings panel, not only as a command. **System improvement surfaced this run:** the dashboard
`commands` freshness test is doing real work as an incidental help-copy guard — the session idea above
proposes promoting that into an explicit, intentional check rather than relying on it as a side effect.

## 📤 Run report
- **Run type:** routine · dispatch
- **PR:** #1566 (Cleanup history filters + age gate) — self-merge on green.
- **⚑ Self-initiated:** none (completion-first arc is the standing S1 dispatch lane; no idea→plan promotion).
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (no migration, no data step; merge auto-deploys).
- **Bugs:** none opened; none fixed (corrected one stale cert note, not a bug-book entry).
