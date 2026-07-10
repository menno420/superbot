# 2026-07-10 — command-collision checker (overnight shift, session A)

> **Status:** `complete`
> **Branch:** `claude/command-collision-checker` · **PR:** #1918

**Intent:** implement `scripts/check_command_collisions.py` + tests — the static
duplicate-command guard from `docs/ideas/command-collision-checker-2026-06-29.md`
(gate `ready`; prevents the #1541/#1544 `give` collision prod-outage class). CI
wiring into `code-quality.yml` is deliberately deferred (workflow edits are out of
overnight scope) and noted as a follow-up in the idea file. Also dispositioning
open PR #1917 (codex docstring-only PR) per the shift plan.

## What shipped

- **PR #1917 dispositioned (merged, `f0737de`).** Codex docstring-only PR on
  `disbot/utils/duration.py`; docstring verified accurate against source (Q-0120),
  all checks green on head `41d8a56` (code-quality success). `enable_pr_auto_merge`
  correctly refused (PR already clean) → merged directly per the Q-0123 manual
  carve-out (CI re-verified green on final head; codex branches don't auto-arm).
- **`scripts/check_command_collisions.py`** — pure-stdlib AST walk over
  `disbot/cogs/**`; fails (exit 1) when two declarations claim one top-level
  command token within a namespace. Prefix registry (names + `aliases=[...]`,
  `@commands.command`/`group`) and slash tree (`@app_commands.command`,
  `app_commands.Group(name=...)` assignments) are separate namespaces, mirroring
  discord.py; `hybrid_command`/`hybrid_group` claim both. Dynamic `name=SOME_VAR`
  is skipped, never fabricated from the function name. `--list` prints the census.
  Q-0105 unverified-tier provenance header.
- **`tests/unit/scripts/test_check_command_collisions.py`** — 20 tests: extraction
  edges (alias list/tuple, name fallback, dynamic-name skip, subcommand exclusion,
  hybrid both-namespaces), collision rules (cross-cog, alias-vs-name, same-cog,
  namespace isolation), staged-tree `main()` exit codes/sites, and a standing
  `test_live_tree_has_zero_collisions` regression (every pytest run re-checks the
  real cog tree — this is the CI enforcement path until the workflow step lands).
- **Docs:** idea file re-badged `historical` — implemented (PR #1918) with the CI-wiring
  follow-up spelled out; `docs/ideas/README.md` index entry updated;
  `docs/current-state.md` Recently-shipped entries for #1917 + #1918.

## Verification (all local, python3.10)

- `pytest tests/unit/scripts/test_check_command_collisions.py -q` → **20 passed**
- `scripts/check_command_collisions.py` on live tree → **OK — 403 token claims, 0 collisions**
  (368 prefix incl. aliases, 35 slash; spot-checked: `btd6` correctly coexists as prefix + slash group)
- `check_quality.py --full` → formatters/lint ✓, check_docs ✓, **pytest 13,854 passed / 50 skipped / 2 xfailed**;
  mypy leg was env-red (`No module named mypy`, fresh container) → installed `requirements-dev.txt`,
  re-ran: `mypy disbot/` → **Success: no issues found in 881 source files**
- `check_architecture.py --mode strict` → exit 0 (same 50 known warnings as scout baseline)
- `check_docs.py --strict` → exit 0 (pre-existing soft Recently-shipped ratchet warning only)
- `check_current_state_ledger.py --strict` → exit 0

## Session enders

- **💡 Session idea (Q-0089):**
  `docs/ideas/command-surface-extractor-consolidation-2026-07-10.md` — three
  stdlib-AST tools (`scan_commands.py`, this checker, `check_command_reachability.py`)
  each re-implement the cog-decorator parse with different edge coverage; factor one
  `scripts/lib/command_surface_ast.py` declaration stream. Dedup-grepped: concrete
  first slice of `warn-first-checker-authoring-kit-2026-07-06.md`, cross-referenced.
- **⟲ Previous-session review (Q-0102):** #1916 (GPT-5.6 Sol eval) delivered strong
  dual-format output (durable doc + inline copy-paste prompts) and modeled honest
  sourcing. What it could have done better: its trust findings (Sol's eval-gaming /
  fabrication rates) never fed back into the *live* cross-agent rules — tonight's
  #1917 disposition still leaned on ad-hoc Q-0120 verification. Concrete improvement:
  when a session produces evaluation data about an external agent, add one line to the
  cross-agent verification guidance (or the trust-ledger idea it filed) pointing at the
  measured result, so the next dispositioning session inherits it instead of re-deriving.
- **📋 Docs audit (Q-0104):** `check_current_state_ledger.py --strict` ✓ (marker #1890
  newest-merge lag is benign and routine-owned — next recon at #1920, not this session
  per Q-0124); `check_docs.py --strict` ✓; new idea reachable from the README index;
  no chat-only conclusions left unhomed.
- **🛠 Friction → guard:** (1) fresh-container missing mypy turned `check_quality.py
  --full` env-red — same B5 class the scout hit with ruff/pytest; guard is the scout's
  Q3 journal quick-reference line (left to the hygiene lane to avoid a cross-PR collision
  on `.session-journal.md`; if no session ships it tonight, next session should). (2) The
  docs badge checker rejects `implemented` as a badge token with no hint of the
  `historical` + prose convention — cost one red loop; noted here rather than patched
  (checker message wording is a one-line improvement any docs session can take).
  (3) The telemetry-row gate (enforced 2026-07-09, `check_session_gate.py`) held the
  first complete push red because the shift orientation predated it — the guard worked
  exactly as designed and its error message contained the complete fix; no further
  guard needed, but overnight shift-plan templates should mention the telemetry row
  next to the born-red card step.
- **⚑ Self-initiated:** hybrid-command support in the checker (gap found by comparing
  against `scan_commands.py` — not in the idea spec) and the
  command-surface-extractor-consolidation idea file. Both contained/reversible.

## Context delta

- **Needed but not pointed to:** `scripts/scan_commands.py` — a sibling AST
  command-surface extractor the idea file never mentions; finding it changed the
  implementation (hybrid support) and produced the session idea. The idea lifecycle
  could ask "what existing tool already parses this surface?" at promotion time.
- **Pointed to but didn't need:** CodeGraph — for a new standalone script + grep-sized
  questions, `grep` + reading `check_migration_collision.py` as a template carried
  the whole session.
- **Discovered by hand:** the docs badge token allowlist (badge=`historical`, prose
  "implemented" convention) — lives only in `check_docs.py` behavior + scattered
  examples; and the `.relative_to(REPO_ROOT)`/default-arg-binding pattern that makes
  checker scripts testable against tmp trees (worth a line in the authoring-kit idea).
- **Decisions made alone:** same-cog duplicates also fail (boot registry semantics,
  not just the idea's "two different cogs" wording); prefix and slash namespaces
  isolated (mirrors discord.py registries — `btd6` proves the real tree relies on it);
  dynamic `name=` skipped rather than guessed. All flagged here for ratification.
- **Flagged for maintainer / known limits:** checker scope is `disbot/cogs/**` only
  (no `bot.add_command` sites); it is *not yet a CI workflow step* — until the
  follow-up lands, enforcement rides on the live-tree regression test inside pytest.
  Recently-shipped is at 23 (ratchet 20, soft) — trim (`trim_recently_shipped.py`) is
  the hygiene lane's ride-along, left untouched to avoid a cross-PR ledger collision.
